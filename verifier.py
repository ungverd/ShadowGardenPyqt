import sys
import os
import struct

"""
sometimes in .wav file there is more metadata than our program can handle.
This function removes it
"""
dest = os.path.normpath(sys.argv[1])

for directory in os.listdir(dest):
    for filename in os.listdir(os.path.join(dest, directory)):
        src = os.path.join(dest, directory, filename)
        with open(src, "rb") as f:
            arr = f.read()
            data_pos = arr.find(b"data")
            if data_pos > 36:
                will_change = data_pos - 36
                len1_num = len(arr) - will_change - 8
                len2_num = len(arr) - will_change - 150
                len1 = struct.pack("<i", len1_num)
                len2 = struct.pack("<i", len2_num)
                with open(src, "wb") as ff:
                    new_arr = arr[:4] + len1 + arr[8:36] + b"data" + len2 + arr[data_pos + 8:]
                    ff.write(new_arr)
