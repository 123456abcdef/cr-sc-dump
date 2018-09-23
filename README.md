# cr-sc-dump
Python script to extract pngs from Clash Royale's `*.sc` files.

## Installation
1. Install `Python 3`
2. Pip install `Pillow`
3. Download `dumpsc.py`

## Usage
Download [Clash Royale APK](https://apkpure.com/clash-royale/com.supercell.clashroyale), unzip and navigate to `path_cr_apk/assets/sc/`.

Or pull `/data/data/com.supercell.clashroyale/update` from your rooted Android device.

To extract pngs from files ending with `_tex.sc` try

    python dumpsc.py /path/to/filename_tex.sc

To extract pngs from files ending with `.sc` or `_dl.sc` try

    python dumpsc.py /path/to/filename_dl.sc --old

To decompress files ending with `.csv` try

    python dumpsc.py /path/to/filename.csv


If you want to get single sprites from the extracted pngs try  [sc_decode](https://github.com/Galaxy1036/sc_decode).


## Credits
* [athlan20](https://github.com/athlan20)
* [clanner](https://github.com/clanner)
* [Galaxy1036](https://github.com/Galaxy1036)
* [umop-aplsdn](https://github.com/umop-aplsdn)
