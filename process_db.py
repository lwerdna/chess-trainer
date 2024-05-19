#!/usr/bin/env python

import os
import re

import chess
import chess.engine

import common
import database
import evaluation

if __name__ == '__main__':
    evaluation.init()

    print('reading database')
    dbinfo = database.read()

    print('scanning')
    for entry in dbinfo:
        if m := re.match(r'^PlayBest(\d+)$', entry['TYPE']):
            if not 'LINE' in entry:
                length = int(m.group(1))
                print(f'calculating line (length={length}) for position {entry["FEN"]}')
                result = evaluation.get_best_line(entry['FEN'], length)
                print(f'  result: {result}')
                entry['LINE'] = result

    print('writing database')
    database.write(dbinfo)
    print('closing engines')
    evaluation.exit()
    print('done')

