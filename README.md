# sripy
A python script to record shoutcast streams

sripy writes mp3 files from shoutcast streams and adds ID3v1 tag based on "Artist - Title" within the supplied metadata. It is entirely implemented in Python3, no external dependencies. This script has only been tested with Python3.

Requirements
====
* Python3 (tested with 3.4 and 3.5, Win/Linux)


Usage
====
* Open sripy.py
* Fill lines 13-15 with your stream URL,  if no subpage is preset, use "/"
* run with: python3 sripy.py

License
====
* GPLv2
