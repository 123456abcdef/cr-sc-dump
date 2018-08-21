# cr-sc-dump
Python script to extract textures from Clash Royale's `*_tex.sc` files.

## Installation
1. Install Python 3.5
2. Install `Pillow` with:

         python -m pip install Pillow

## Usage
Download [Clash Royale APK](https://apkpure.com/clash-royale/com.supercell.clashroyale) and navigate to `path_cr_apk/assets/sc/`.
Run script on single file with:

      python dumpsc.py filename_tex.sc
Or on all files with:

      find . -name "*_tex.sc" | xargs python dumpsc.py

## Misc
If you want to extract the content of `*.sc`files, try [sc_decode](https://github.com/Galaxy1036/sc_decode).

For `*_dl.sc`files, try [Old-Sc-Dumper](https://github.com/Galaxy1036/Old-Sc-Dumper).

##### Credits
* athlan20
* clanner
