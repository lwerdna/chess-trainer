#!/usr/bin/env python

import os
import sys

def save(fname, stuff):
    print(f'writing {fname}')
    with open(fname, 'w') as fp:
        fp.write(stuff)

def split_clone(stuff, index=1):
    first = stuff.find('[Event ')
    if first == -1:
        return
    second = stuff.find('[Event ', first+1)
    second = len(stuff) if second == -1 else second
    fname = f'{index:04d}.pgn'
    save(fname, stuff[first:second])
    split_clone(stuff[second:], index+1)

if __name__ == "__main__":
    fpath = sys.argv[1]
    stuff = open(fpath, 'r').read()

    index = 1
    if sys.argv[2:]:
        index = int(sys.argv[2])

    split_clone(stuff, index)

