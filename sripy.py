#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
sripy - a python script to record shoutcast streams
(c)2017 - Yasar L. Ahmed
v0.02
'''

# example URL:
# python3 sripy.py http://www.example.com:8000/stream

import os
import io
import sys
import time
import socket
import struct
import logging
import urllib.request
from threading import Thread
from datetime import datetime
from urllib.parse import urlparse

def init_log(name='app'):
    log_formatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s] %(message)s")
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)
    return logger

def check_for_metadata(current_metadata, packet):
    if b'StreamTitle' in packet:
        meta_addr = packet.find(b"StreamTitle")
        meta_size_addr = meta_addr - 1
        meta_size_tuple = struct.unpack_from('1B', packet[meta_size_addr:])
        meta_size = meta_size_tuple[0] * 16
        meta_end = meta_addr + meta_size
        meta_data = (packet[meta_addr:meta_end]).decode('utf8')
        new_meta_data_clean = meta_data.split(';')[0][13:-1]
        if new_meta_data_clean != '':
            log.info('NOW: {}'.format(new_meta_data_clean))
        return(new_meta_data_clean)
    else:
        return(current_metadata)

def generate_id3(metadata):
    header = b'TAG'
    try:
        artist,title = metadata.split(" - ")
    except:
        log.warn("Problem processing metadata: " + metadata)
        artist = metadata
        title = metadata
    title = title.encode('utf8')
    final_title = title.ljust(30,b'\x00')
    artist = artist.encode('utf8')
    final_artist = artist.ljust(30,b'\x00')
    padding = b''.ljust(65,b'\x00')
    final_tag = header + final_title[0:30] + final_artist[0:30] + padding
    return(final_tag)

def patch_and_write(metaint, metadata, raw_data):
    filename = metadata + ".mp3"
    filename = filename.replace("/", "_")
    n = 0
    position = 0
    final_data = b''
    start = raw_data.find(b'StreamTitle') - 1
    for i in range(start, len(raw_data), metaint):
        meta_size_start = i + n
        try:
            data_to_unpack = raw_data[meta_size_start:meta_size_start+1]
            meta_size = struct.unpack('1B', data_to_unpack)[0] * 16 + 1
        except:
            meta_size = 1
        meta_end = meta_size_start + meta_size
        n += meta_size
        final_data += raw_data[position:meta_size_start]
        position = meta_end
    final_data += generate_id3(metadata)
    with open(filename, 'wb+') as mp3file:
        mp3file.write(final_data)

def sync_stream(request):
    log.info("Syncing...")
    mp3_packet = b''
    while True:
        packet = request.read(2048)
        mp3_packet += packet
        if b"StreamTitle" in packet:
            meta_data_clean = check_for_metadata('',packet)
            mp3_packet += packet
            return meta_data_clean, mp3_packet
        else:
            mp3_packet += packet
        
def main():
    url = sys.argv[1]
    req = urllib.request.Request(url)
    req.add_header('Icy-MetaData', '1')
    req.add_header('User-Agent', 'WinAmp/5.565')
    req_data = urllib.request.urlopen(req)
    if req_data.msg != 'OK':
        log.error("Did not receive Metadata, quitting!")
        sys.exit()
    metaint = int(req_data.getheader('Icy-metaint'))
    log.info('Requesting metadata from {}'.format(url))
    log.info('Metaint value: {}'.format(metaint))
    for i in req_data.getheaders():
        log.info(i[0] + ": " + i[1])
    #len(f.getvalue()) <= 1024000
    tmp_buffer = io.BytesIO()
    log.info("Syncing...")
    while True:
        packet = req_data.read(2048)
        tmp_buffer.write(packet)
        if b"StreamTitle" in packet:
            metadata = check_for_metadata('',packet)
            break
    while True:
        packet = req_data.read(2048)
        new_metadata = check_for_metadata(metadata, packet)
        if new_metadata in ['', metadata]:
            tmp_buffer.write(packet)
        else:
            unpatched_data = tmp_buffer.getvalue()
            write_thread = Thread(target=patch_and_write, args=(metaint, metadata, unpatched_data))
            write_thread.start()
            tmp_buffer.close()
            tmp_buffer = io.BytesIO()
            tmp_buffer.write(packet)
            metadata = new_metadata
    
if __name__ == '__main__':
    log = init_log(name='sripy')
    main()
