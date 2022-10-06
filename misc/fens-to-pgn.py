#!/usr/bin/env python

# convert .fens file with list of FEN positions to PGN

import sys
import random

if __name__ == '__main__':
    description = ''
    position_i = 0

    with open(sys.argv[1]) as fp:
        for line in fp.readlines():
            if line.isspace():
                continue
            elif line.startswith('#'):
                description = line[1:].strip()
                continue
            
            fen = line.strip()

            print(f'[EVENT "Position #{position_i}"]')
            print(f'[DESCRIPTION "{description}"]')
            print(f'[FEN "{fen}"]')
            print(f'[PROBLEM_TYPE "checkmate_or_promote_to_queen"]')
            print()
            print('*')
            print()

            position_i += 1
