import sys
import os
"""
sometimes in .wav file there is more metadata than our program can handle.
This function removes it
"""
dest = os.path.normpath(sys.argv[1])

for f in os.listdir(dest):
    if f[-4:] == ".wav":
        src = os.path.join(dest, f)
        with open(src, "rb") as f:
            arr = f.read()
            if arr[37:41] != b"data":
                with open(src, "wb") as ff:
                    data_pos = arr.find(b"data", 37)
                    new_arr = arr[:36] + arr[data_pos:]
                    ff.write(new_arr)

