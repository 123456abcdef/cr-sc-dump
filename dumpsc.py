import argparse
import hashlib
import io
import lzma
from math import ceil
import os

from PIL import Image

"""
Tool for extracting Clash Royale "*.sc" files

Download .apk from the net and extract with 7zip.

Linux / Mac:
find ./assets/sc -name "*.sc" | xargs python dumpsc.py

Windows:
for %v in (*.sc) do dumpsc.py %v

Will save all png files.
"""


class Reader(io.BytesIO):
    def __init__(self, stream):
        super().__init__(stream)
        self._bytesLeft = len(stream)

    def __len__(self):
        return 0 if self._bytesLeft < 0 else self._bytesLeft

    def read(self, size):
        self._bytesLeft -= size
        return super().read(size)

    def read_byte(self):
        self._bytesLeft -= 1
        return int.from_bytes(self.read(1), 'little')

    def read_uint16(self):
        self._bytesLeft -= 2
        return int.from_bytes(self.read(2), 'little')

    def read_uint32(self):
        self._bytesLeft -= 4
        return int.from_bytes(self.read(4), 'little')

    def read_string(self):
        length = self.read_byte()
        self._bytesLeft -= 1 + length
        return self.read(length).decode('utf-8')


def decompress(data):
    # Fix header and decompress
    data = data[0:9] + (b'\x00' * 4) + data[9:]
    return lzma.LZMADecompressor().decompress(data)


def process_csv(fileName, data, path):
    decompressed = decompress(data)

    with open(os.path.join(path, fileName), 'wb') as f:
        f.write(decompressed)


def convert_pixel(reader, type):
    if type == 0 or type == 1:  # RGB8888
        pixel = reader.read(4)
        return (int(pixel[0]), int(pixel[1]), int(pixel[2]), int(pixel[3]))
    elif type == 2:  # RGB4444
        pixel = reader.read_uint16()
        return (((pixel >> 12) & 0xF) << 4, ((pixel >> 8) & 0xF) << 4,
                ((pixel >> 4) & 0xF) << 4, ((pixel >> 0) & 0xF) << 4)
    elif type == 3:  # RBGA5551
        pixel = reader.read_uint16()
        return (((pixel >> 11) & 0x1F) << 3, ((pixel >> 6) & 0x1F) << 3,
                ((pixel >> 1) & 0x1F) << 3, ((pixel) & 0xFF) << 7)
    elif type == 4:  # RGB565
        pixel = reader.read_uint16()
        return (((pixel >> 11) & 0x1F) << 3, ((pixel >> 5) & 0x3F) << 2,
                (pixel & 0x1F) << 3)
    elif type == 6:  # LA88
        pixel = reader.read_uint16()
        return ((pixel >> 8), (pixel >> 8), (pixel >> 8), (pixel & 0xFF))
    elif type == 10:  # L8
        pixel = reader.read_byte()
        return (pixel, pixel, pixel)
    else:
        raise Exception('Unknown pixel type \'{}\''.format(type))


def process_sc(baseName, data, path, old):
    decompressed = decompress(data[26:])

    md5_hash = data[10:26]
    if hashlib.md5(decompressed).digest() != md5_hash:
        raise Exception('File seems corrupted')

    reader = Reader(decompressed)

    if old:
        # Credits: https://github.com/Galaxy1036/Old-Sc-Dumper
        reader.read(17)
        count = reader.read_uint16()
        reader.read(count * 2)
        for i in range(count):  # skip strings
            reader.read_string()

    picCount = 0
    while len(reader):
        fileType = reader.read_byte()
        fileSize = reader.read_uint32()

        if fileType not in [1, 24, 27, 28]:
            reader.read(fileSize)
            continue

        subType = reader.read_byte()
        width = reader.read_uint16()
        height = reader.read_uint16()

        print('fileType: {}, fileSize: {}, subType: {}, width: {}, '
              'height: {}'.format(fileType, fileSize, subType, width, height))

        pixels = []
        for y in range(height):
            for x in range(width):
                pixels.append(convert_pixel(reader, subType))

        img = Image.new('RGBA', (width, height))
        img.putdata(pixels)

        if fileType == 27 or fileType == 28:
            pixelAccess = img.load()
            i = 0
            blockSize = 32
            for _h in range(ceil(height / blockSize)):
                for _w in range(ceil(width / blockSize)):
                    h = (_h * blockSize)
                    while h != (_h + 1) * blockSize and h < height:
                        w = (_w * blockSize)
                        while w != (_w + 1) * blockSize and w < width:
                            pixelAccess[w, h] = pixels[i]
                            i += 1
                            w += 1
                        h += 1

        img.save(os.path.join(path, baseName + ('_' * picCount) + '.png'))
        picCount += 1


def check_header(data):
    if data[0] == 0x5d:
        return 'csv'
    if data[:2] == b'\x53\x43':
        return 'sc'
    raise Exception('Unknown file type')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Extract png files from Clash'
                                                 ' Royale \'*_tex.sc\' files')
    parser.add_argument('files', help='sc file', nargs='+')
    parser.add_argument('--old', action='store_true',
                        help='used for \'*_dl.sc\' files')
    parser.add_argument('-o', help='Extract pngs to directory', type=str)
    args = parser.parse_args()

    if args.o:
        path = os.path.normpath(args.o)
    else:
        path = os.path.dirname(os.path.realpath(__file__))

    for file in args.files:
        try:
            baseName, ext = os.path.splitext(os.path.basename(file))
            with open(file, 'rb') as f:
                print(f.name)
                data = f.read()

            type = check_header(data)

            if type == 'csv':
                process_csv(baseName + ext, data, path)
            elif type == 'sc':
                process_sc(baseName, data, path, args.old)
        except Exception as e:
            print('{} {}'.format(e.__class__.__name__, e))
