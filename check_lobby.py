#!/usr/bin/python
import os
import json

OUT_DIR = os.path.abspath(os.path.join('.', 'out'))
IMG_DIR = os.path.abspath(os.path.join(OUT_DIR, 'images'))

CHK_MAX_LOBBY_COUNT = 3
CHK_IMAGE_EXISTS = True


def walklevel(some_dir, level=1):
    some_dir = some_dir.rstrip(os.path.sep)
    assert os.path.isdir(some_dir)
    num_sep = some_dir.count(os.path.sep)
    for root, dirs, files in os.walk(some_dir):
        yield root, dirs, files
        num_sep_this = root.count(os.path.sep)
        if num_sep + level <= num_sep_this:
            del dirs[:]


# traverse root directory, and list directories as dirs and files as files
for root, __, files in walklevel(OUT_DIR, level=1):
    path = root.split(os.sep)
    # print((len(path) - 1) * '---', os.path.basename(root))
    for file in files:
        if file.endswith('.json'):
            with open(os.path.join(root, file), 'r', encoding='utf-8') as fp:
                d = json.load(fp)
                if len(d['lobby']) > CHK_MAX_LOBBY_COUNT:
                    print('Pay attention to %s with lobby items count %d' %
                          (file, len(d['lobby'])))
                if CHK_IMAGE_EXISTS:
                    filename = os.path.splitext(file)[0]
                    for extension in ['.png', '.jpg']:
                        fullname = os.path.join(IMG_DIR, filename + extension)
                        if os.path.isfile(fullname):
                            break
                    else:
                        print('Couldn''t find image for %s' % filename)
