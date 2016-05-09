# cr-sc-dump
Python script to extract textures from Clash Royale's `*_tex.sc` files.

## Installation
1. Install Python 2.7
2. Install `lzma` with:
         python -m pip install lzma
3. Install `Pillow` with:
         python -m pip install Pillow

## Usage
Download [Clash Royale APK](https://apkpure.com/clash-royale/com.supercell.clashroyale) and navigate to `path_cr_apk/assets/sc/`.
Run script on single file with:

      python dumpsc.py filename_tex.sc
Or on all files with:

      find . -name "*_tex.sc" | xargs python dumpsc.py


##### Credits
* athlan20
* clanner
