#!/usr/bin/env python3

import argparse
import hashlib
import io
import logging
import lzma
import os

from PIL import Image
import texture2ddecoder
import zstandard


class Reader(io.BytesIO):
    def __init__(self, stream):
        super().__init__(stream)
        self._bytes_left = len(stream)

    def __len__(self):
        return 0 if self._bytes_left < 0 else self._bytes_left

    def read(self, size=-1):
        if size == -1:
            self._bytes_left = 0
        else:
            self._bytes_left -= size
        return super().read(size)

    def read_byte(self, byteorder="little"):
        return int.from_bytes(self.read(1), byteorder)

    def read_uint16(self, byteorder="little"):
        return int.from_bytes(self.read(2), byteorder)

    def read_int32(self, byteorder="little"):
        return int.from_bytes(self.read(4), byteorder, signed=True)

    def read_uint32(self, byteorder="little"):
        return int.from_bytes(self.read(4), byteorder)

    def read_string(self, encoding="utf-8"):
        length = self.read_byte()
        return self.read(length).decode("utf-8")


def decompress(data):
    if data[0:4] == b"SCLZ":
        logging.debug("Decompressing using LZHAM ...")
        # Credits: https://github.com/Galaxy1036/pylzham
        import lzham

        dict_size = int.from_bytes(data[4:5], byteorder="big")
        uncompressed_size = int.from_bytes(data[5:9], byteorder="little")

        logging.debug(f"dict size: {dict_size}")
        logging.debug(f"uncompressed size: {uncompressed_size}")

        decompressed = lzham.decompress(
            data[9:], uncompressed_size, {"dict_size_log2": dict_size}
        )
    elif data[0:4] == zstandard.FRAME_HEADER:
        logging.debug("Decompressing using ZSTD ...")
        decompressed = zstandard.decompress(data)
    else:
        logging.debug("Decompressing using LZMA ...")
        # fix uncompressed size to 64 bit
        data = data[0:9] + (b"\x00" * 4) + data[9:]

        prop = data[0]
        if prop > (4 * 5 + 4) * 9 + 8:
            raise Exception("LZMA properties error")
        pb = int(prop / (9 * 5))
        prop -= int(pb * 9 * 5)
        lp = int(prop / 9)
        lc = int(prop - lp * 9)
        logging.debug(f"literal context bits: {lc}")
        logging.debug(f"literal position bits: {lp}")
        logging.debug(f"position bits: {pb}")
        dictionary_size = int.from_bytes(data[1:5], byteorder="little")
        logging.debug(f"dictionary size: {dictionary_size}")
        uncompressed_size = int.from_bytes(data[5:13], byteorder="little")
        logging.debug(f"uncompressed size: {uncompressed_size}")

        decompressed = lzma.LZMADecompressor().decompress(data)
    return decompressed


def process_csv(file_name, data, path):
    decompressed = decompress(data)
    with open(os.path.join(path, file_name), "wb") as f:
        f.write(decompressed)


def create_image(width, height, pixels, sub_type):
    if sub_type == 0 or sub_type == 1:  # RGB8888
        return Image.frombytes("RGBA", (width, height), pixels, "raw")
    elif sub_type == 2:  # RGBA4444
        img = Image.new("RGBA", (width, height))
        ps = img.load()
        for h in range(height):
            for w in range(width):
                i = (w + h * width) * 2
                p = int.from_bytes(pixels[i : i + 2], "little")
                ps[w, h] = (
                    ((p >> 12) & 0xF) << 4,
                    ((p >> 8) & 0xF) << 4,
                    ((p >> 4) & 0xF) << 4,
                    ((p >> 0) & 0xF) << 4,
                )
        return img
    elif sub_type == 3:  # RBGA5551
        args = ("RGBA;4B", 0, 0)
        return Image.frombytes("RGBA", (width, height), pixels, "raw", args)
    elif sub_type == 4:  # RGB565
        img = Image.new("RGB", (width, height))
        ps = img.load()
        for h in range(height):
            for w in range(width):
                i = (w + h * width) * 2
                p = int.from_bytes(pixels[i : i + 2], "little")
                ps[w, h] = (
                    ((p >> 11) & 0x1F) << 3,
                    ((p >> 5) & 0x3F) << 2,
                    (p & 0x1F) << 3,
                )
        return img
    elif sub_type == 6:  # LA88
        return Image.frombytes("LA", (width, height), pixels)
    elif sub_type == 10:  # L8
        return Image.frombytes("L", (width, height), pixels)
    else:
        raise Exception(f"Unknown sub type '{sub_type}'")


def pixel_size(sub_type):
    if sub_type in [0, 1]:
        return 4
    elif sub_type in [2, 3, 4, 6]:
        return 2
    elif sub_type in [10]:
        return 1
    else:
        raise Exception(f"Unknown sub type '{sub_type}'")


def process_sctx(reader):
    reader.read(12) # magic
    reader.read(40)
    width = reader.read_uint16()
    height = reader.read_uint16()
    reader.read(24)
    reader.read(reader.read_uint32())
    reader.read(52)
    decompressed = decompress(reader.read())
    block_width = block_height = 8
    pixels = texture2ddecoder.decode_astc(
        decompressed,
        width,
        height,
        block_width,
        block_height,
    )
    img = Image.frombytes(
        "RGBA", (width, height), pixels, "raw", "BGRA"
    )
    return img


def process_file_type_47(file_path):
    logging.info(f"{os.path.basename(file_path)}")
    with open(file_path, "rb") as f:
        data = f.read()
    return process_sctx(Reader(data))


def process_sc(base_dir, base_name, data, path, old):
    reader = Reader(data)
    reader.read(2)
    file_ver_major = reader.read_uint32(byteorder="big")
    file_ver_minor = reader.read_uint32(byteorder="big")
    hash_length = reader.read_uint32(byteorder="big")
    logging.debug(f"sc file version: {file_ver_major}.{file_ver_minor}")
    md5_hash = reader.read(hash_length)
    logging.debug(f"md5 hash: {md5_hash.hex()}")

    decompressed = decompress(reader.read())

    if hashlib.md5(decompressed).digest() != md5_hash:
        logging.debug("File seems corrupted")

    reader = Reader(decompressed)

    if old:
        # Credits: https://github.com/Galaxy1036/Old-Sc-Dumper
        reader.read(17)
        count = reader.read_uint16()
        reader.read(count * 2)
        for i in range(count):  # skip strings
            reader.read_string()

    count = 0
    while len(reader):
        file_type = reader.read_byte()
        file_size = reader.read_uint32()

        if file_size == 0:
            continue

        if file_type not in [1, 8, 12, 24, 27, 28, 45, 47, 49]:
            logging.error(f"Unknown file_type: {file_type}")
            data = reader.read(file_size)
            continue

        if file_type == 8:
            matrix = [reader.read_int32() for _ in range(6)]
            continue

        if file_type == 12:
            data = reader.read(file_size)
            continue

        if file_type == 45:
            file_size = reader.read_uint32()

        if file_type == 47:
            file_name = reader.read_string()

        if file_type == 49:
            data = reader.read(file_size)
            continue

        sub_type = reader.read_byte()
        width = reader.read_uint16()
        height = reader.read_uint16()

        logging.info(
            f"file_type: {file_type}, file_size: {file_size}, "
            f"sub_type: {sub_type}, width: {width}, height: {height}"
        )

        img = None
        if file_type == 27 or file_type == 28:
            pixel_sz = pixel_size(sub_type)
            block_sz = 32
            pixels = bytearray(file_size - 5)
            for _h in range(0, height, block_sz):
                for _w in range(0, width, block_sz):
                    for h in range(_h, min(_h + block_sz, height)):
                        i = (_w + h * width) * pixel_sz
                        sz = min(block_sz, width - _w) * pixel_sz
                        pixels[i : i + sz] = reader.read(sz)
            pixels = bytes(pixels)
            img = create_image(width, height, pixels, sub_type)
        elif file_type == 45:
            img = process_sctx(reader)
        elif file_type == 47:
            img = process_file_type_47(os.path.join(base_dir, file_name))
        else:
            pixels = reader.read(file_size - 5)
            img = create_image(width, height, pixels, sub_type)

        img.save(os.path.join(path, f"{base_name}_{count}.png"))
        count += 1


def check_header(data):
    if data[0] == 0x5D:
        return "csv"
    if data[:2] == b"\x53\x43":
        return "sc"
    if data[:4] == b"\x53\x69\x67\x3a":
        return "sig:"
    raise Exception("  Unknown header")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract png files from SC/CSV files")
    parser.add_argument("files", help="sc file", nargs="+")
    parser.add_argument("--old", action="store_true", help="used for '*_dl.sc' files")
    parser.add_argument("-o", help="Extract pngs to directory", type=str)
    parser.add_argument("--verbose", action="store_true", help="Print debug infos")
    args = parser.parse_args()

    if args.o:
        path = os.path.normpath(args.o)
    else:
        path = os.getcwd()

    level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(format="", level=level)

    for file in args.files:
        try:
            base_dir = os.path.dirname(file)
            base_name, ext = os.path.splitext(os.path.basename(file))
            logging.info(base_name + ext)
            with open(file, "rb") as f:
                data = f.read()

            file_type = check_header(data)

            if file_type == "csv":
                process_csv(base_name + ext, data, path)
            elif file_type == "sig:":
                process_csv(base_name + ext, data[68:], path)
            elif file_type == "sc":
                process_sc(base_dir, base_name, data, path, args.old)
        except Exception as e:
            logging.error(f"{e.__class__.__name__} {e}")
