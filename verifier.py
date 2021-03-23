import sys
import os

def latinize(s):
    lat = {
        "й": "y",
        "ц": "cz",
        "у": "u",
        "к": "k",
        "е": "e",
        "н": "n",
        "г": "g",
        "ш": "sh",
        "щ": "sch",
        "з": "z",
        "х": "h",
        "ъ": "'",
        "ф": "f",
        "ы": "yi",
        "в": "v",
        "а": "a",
        "п": "p",
        "р": "r",
        "о": "o",
        "л": "l",
        "д": "d",
        "ж": "j",
        "э": "e",
        "я": "ya",
        "ч": "ch",
        "с": "s",
        "м": "m",
        "и": "i",
        "т": "t",
        "ь": "'",
        "б": "b",
        "ю": "yu",
        "ё": "yo"
    }

    if len(s) == len(s.encode()):
        return False
    new_name = []
    for ch in s:
        if ch in lat:
            new_name.append(lat[ch])
        elif ch.lower() in lat:
            new_name.append(lat[ch.lower()].upper())
        else:
            new_name.append((str(ch.encode())[2:-1]).replace('\\', ''))
    return("".join(new_name))

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
                print(data_pos)
                len1 = (len(arr) - 8).to_bytes(4, "little")
                len2 = (len(arr) - 150).to_bytes(4, "little")
                with open(src, "wb") as ff:
                    new_arr = arr[:4] + len1 + arr[8:36] + b"data" + len2 + arr[data_pos + 8:]
                    ff.write(new_arr)
    new_filename = latinize(filename)
    if new_filename:
        os.rename(os.path.join(dest, directory, filename),os.path.join(dest, directory, new_filename))
