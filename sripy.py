#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
sripy - a python script to record shoutcast streams
(c)2017 - Yasar L. Ahmed
v0.01
'''

# example URL:
# http://1.2.3.4:8000/stream/

host = "1.2.3.4"
port = 8000
subpage = "/stream/2/"

import os
import io
import socket
import struct
import time
import datetime
from threading import Thread

def start_conn(in_host, in_port, subpage=None):
    s = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
    s.connect((in_host, in_port))
    if subpage != None:
        send_str = "GET {subpage}\r\n".format(subpage=subpage)
        s.sendall(send_str.encode('ascii'))
    return(s)

def get_metaint(s):
    s.sendall(b'GET / HTTP/1.1\n User-Agent:WinAmp/5.55\n Icy-MetaData:1\r\n\r')
    initial_packet = s.recv(4096)
    initial_packet_dec = initial_packet.decode('utf8',errors='ignore')
    metaint_start = initial_packet_dec.find("icy-metaint:") + 12
    metaint_end = metaint_start + initial_packet_dec[metaint_start:].find("\n")
    metaint = int(initial_packet_dec[metaint_start:metaint_end])
    return(metaint)

def find_sync(s):
    print("Syncing...")
    mp3_packet = b''
    while True:
        packet = s.recv(2048)
        if b"StreamTitle" in packet:
            meta_data_clean = check_for_metadata('',packet)
            mp3_packet += packet
            return(meta_data_clean, mp3_packet)
        else:
            mp3_packet += packet

def check_for_metadata(current_metadata, packet):
    if b'StreamTitle' in packet:
        meta_addr = packet.find(b"StreamTitle")
        meta_size_addr = meta_addr - 1
        meta_size_tuple = struct.unpack_from('1B', packet[meta_size_addr:])
        meta_size = meta_size_tuple[0] * 16
        meta_end = meta_addr + meta_size
        meta_data = (packet[meta_addr:meta_end]).decode('utf8')
        new_meta_data_clean = meta_data.split(';')[0][13:-1]
        return(new_meta_data_clean)
    else:
        return(current_metadata)

def generate_id3(metadata):
    header = b'TAG'
    artist,title = metadata.split(" - ")
    title = title.encode('utf8')
    final_title = title.ljust(30,b'\x00')
    artist = artist.encode('utf8')
    final_artist = artist.ljust(30,b'\x00')
    padding = b''.ljust(65,b'\x00')
    final_tag = header + final_title[0:30] + final_artist[0:30] + padding
    return(final_tag)

def patch_and_write(metaint, metadata, raw_data):
    filename = metadata + ".mp3"
    n = 0
    position = 0
    final_data = b''
    start = raw_data.find(b'StreamTitle') - 1
    for i in range(start, len(raw_data), metaint):
        meta_size_start = i + n
        meta_size_end = meta_size_start + 1
        try:
            meta_size_tuple = struct.unpack_from('1B', raw_data[meta_size_start:meta_size_end])
        except:
            meta_size_tuple = (0,)
        meta_size = meta_size_tuple[0] * 16 + 1
        meta_end = meta_size_start + meta_size
        n += meta_size
        final_data += raw_data[position:meta_size_start]
        position = meta_end
    final_data += generate_id3(metadata)
    with open(filename, 'wb+') as mp3file:
        n_bytes = str(len(final_data))
        mp3file.write(final_data)
            
def main():
    s = start_conn(host, port, subpage=subpage)
    metaint = get_metaint(s)
    metadata, initial_data = find_sync(s)
    print("NOW: " + metadata)
    f = io.BytesIO()
    f.write(initial_data)
    while True:
        packet = s.recv(4096)
        new_metadata = check_for_metadata(metadata, packet)
        if new_metadata == metadata:
            f.write(packet)
        else:
            print("NOW: " + new_metadata)
            unpatched_data = f.getvalue()
            t = Thread(target=patch_and_write, args=(metaint, metadata, unpatched_data))
            t.start()
            f.close()
            f = io.BytesIO()
            f.write(packet)
            metadata = new_metadata
    
if __name__ == '__main__':
    main()
