# sripy
A python script to record shoutcast streams

sripy writes mp3 files from shoutcast streams and adds ID3v1 tag based on "Artist - Title" within the supplied metadata. It is entirely implemented in Python3, no external dependencies. This script has only been tested with Python3. It might not work with streams that don't send metadata, as files are written to disk only on change of metadata.

Requirements
====
* Python3 (tested with 3.4 and 3.5, Win/Linux)


Usage
====
* python3 sripy.py http://www.example.com:8000/stream

License
====
* GPLv2
