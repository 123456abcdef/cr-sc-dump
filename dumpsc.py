import argparse
import os
import struct
import lzma
from PIL import Image

"""
Tool for extracting Clash Royale "*_tex.sc" files

find ./assets/sc -name *_tex.sc | xargs python dump.sc -o output_dir/

Will extract all png files in output_dir.
"""


def convert_pixel(pixel, type):
    if type == 0:
        return struct.unpack('4B', pixel)
    elif type == 2:
        pixel, = struct.unpack('<H', pixel)
        return (((pixel >> 12) & 0xF) << 4, ((pixel >> 8) & 0xF) << 4,
                ((pixel >> 4) & 0xF) << 4, ((pixel >> 0) & 0xF) << 4)
    elif type == 4:
        pixel, = struct.unpack("<H", pixel)
        return (((pixel >> 11) & 0x1F) << 3, ((pixel >> 5) & 0x3F) << 2, (pixel & 0x1F) << 3)
    elif type == 6:
        pixel, = struct.unpack("<H", pixel)
        # TODO figure out correct colors
        return (((pixel >> 12) & 0xF) << 4, ((pixel >> 8) & 0xF) << 4,
                ((pixel >> 4) & 0xF) << 4, ((pixel >> 0) & 0xF) << 4)
    elif type == 10:
        pixel, = struct.unpack("<B", pixel)
        # TODO figure out correct colors
        return (((pixel >> 12) & 0xF) << 4, ((pixel >> 8) & 0xF) << 4,
                ((pixel >> 4) & 0xF) << 4, ((pixel >> 0) & 0xF) << 4)
    else:
        raise Exception("Unknown pixel type {}".format(type))


def process_sc(baseName, data, path):
    # Fix header and decompress
    data = data[0:9] + ('\x00' * 4) + data[9:]
    decompressed = lzma.LZMADecompressor().decompress(data)

    i = 0
    picCount = 0
    while len(decompressed[i:]) > 5:
        fileType, = struct.unpack('<b', decompressed[i])
        fileSize, = struct.unpack('<I', decompressed[i + 1:i + 5])
        subType, = struct.unpack('<b', decompressed[i + 5])
        width, = struct.unpack('<H', decompressed[i + 6:i + 8])
        height, = struct.unpack('<H', decompressed[i + 8:i + 10])
        i += 10

        if subType == 0:
            pixelSize = 4
        elif subType == 2 or subType == 4 or subType == 6:
            pixelSize = 2
        elif subType == 10:
            pixelSize = 1
        else:
            raise Exception("Unknown pixel type {}".format(subType))

        print('fileType: {}, fileSize: {}, subType: {}, width: {}, height: {}'.format(fileType,
                                                                                      fileSize,
                                                                                      subType,
                                                                                      width,
                                                                                      height))

        img = Image.new("RGBA", (width, height))
        pixels = []
        for y in range(height):
            for x in range(width):
                pixels.append(convert_pixel(
                    decompressed[i:i + pixelSize], subType))
                i += pixelSize

        img.putdata(pixels)
        img.save(path + baseName + ('_' * picCount) + '.png', 'PNG')

        picCount += 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Extract png files from Clash Royale "*_tex.sc" files')
    parser.add_argument('files', help='sc file', nargs='+')
    parser.add_argument('-o', help='Extract pngs to directory', type=str)
    args = parser.parse_args()

    if args.o:
        path = args.o
    else:
        path = os.path.dirname(os.path.realpath(__file__)) + '/'

    for file in args.files:
        print file
        if file.endswith('_tex.sc'):
            baseName, ext = os.path.splitext(os.path.basename(file))
            with open(file, 'rb') as f:
                data = f.read()
                process_sc(baseName, data[26:], path)
        else:
            print('{} not supported.'.format(file))
