#!/usr/bin/env python3
import re
import urllib.request
import hashlib
import binascii

with open('./data/map.kml') as f:
    content = f.read()
replace = []
for line in content.splitlines():
    for url in re.findall(r'<img src="(.+?)"', line):
        if url.startswith('http'):
            with urllib.request.urlopen(url) as f:
                data = f.read()
                hash = hashlib.sha256(data).hexdigest()
                
                header_byte = binascii.hexlify(data[0:3]).lower()
                extension = 'bin'
                if header_byte == b'474946':
                    extension = "gif"
                elif header_byte == b'89504e':
                    extension = "png"
                elif header_byte == b'ffd8ff':
                    extension = "jpg"
                filename = './data/images/' + hash + "." + extension

                with open(filename, 'wb') as out:
                    out.write(data)
                replace.append((url, filename))
                print('.', end='', flush=True)

print('\nReplaced %d images' % len(replace))
for url, rel_path in replace:
    content = content.replace(url, rel_path)
with open('./data/map.kml', 'w') as f:
    f.write(content)

        