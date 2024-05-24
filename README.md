# cr-sc-dump
Python script to extract pngs from Supercell’s `*.sc`, `*_dl.sc`, `*_tex.sc`, or `*.csv` files.

## Installation
```console
pip install -r requirements.txt
```
Optional: If you want to use `dumpsc.py` inside a container
```console
docker build --pull -t dumpsc .
```

## Usage
Download [Clash Royale APK](https://apkpure.com/clash-royale/com.supercell.clashroyale), unzip and navigate to `path/to/assets/sc/`.
Works the same for any other Supercell game.

Or pull `/data/data/com.supercell.clashroyale/update/` from your rooted Android device.

To extract pngs from files ending with `_tex.sc` try
```console
python dumpsc.py path/to/filename_tex.sc
```
To extract pngs from files ending with `.sc` or `_dl.sc` try
```console
python dumpsc.py path/to/filename_dl.sc --old
```
To decompress files ending with `.csv` try
```console
python dumpsc.py path/to/filename.csv
```
Here an example on how to use the contianer
```console
docker run --rm -it --volume "$PWD":/data --user="$(id -u):$(id -g)" dumpsc <*_tex.sc>
```

## Additional Links
- [Galaxy1036/sc_decode](https://github.com/Galaxy1036/sc_decode)


## Credits
* [athlan20](https://github.com/athlan20)
* [clanner](https://github.com/clanner)
* [Galaxy1036](https://github.com/Galaxy1036)
* [umop-aplsdn](https://github.com/umop-aplsdn)
