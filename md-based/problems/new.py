#!/usr/bin/env python

import re
import os
import sys
import uuid

import chess

if len(sys.argv) < 2:
    print(f'supply FEN')
    sys.exit(0)

#if re.match(r'^[prqknbPRQKNB\/wb\d\- ]+$', arg1):
if True:
    print(f'generating problem id...', end='')
    probid = 0
    for probfile in [x for x in os.listdir('.') if x.endswith('.md')]:
        if m := re.match(r'^(\d+) ', probfile):
            probid = max(probid, int(m.group(1)) + 1)
    print(probid)

    fen = sys.argv[1]
    board = chess.Board(fen=fen)

    fname = f'{probid:03d} ' + fen.replace('/', '_') + '.md'

    print(f'writing: "{fname}"')

    with open(fname, 'w') as fp:
        if board.turn == chess.WHITE:
            fp.write('What\'s white\'s best move/line?\n')
        else:
            fp.write('What\'s black\'s best move/line?\n')

        fp.write('\n')
        fp.write('```chess\n')
        fp.write('fen: ' + fen + '\n')

        if board.turn == chess.BLACK:
            fp.write('orientation: black\n')

        fp.write('```\n')
