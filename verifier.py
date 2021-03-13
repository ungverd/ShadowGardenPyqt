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
            data_pos = arr.find(b"data")
            if data_pos > 36:
                with open(src, "wb") as ff:
                    new_arr = arr[:36] + arr[data_pos:]
                    ff.write(new_arr)

