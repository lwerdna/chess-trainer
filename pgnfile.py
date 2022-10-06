#!/usr/bin/env python

import os, sys

import chess
import chess.pgn

class PgnFile(object):
    def __init__(self, fpath=None):
        self.fpath = fpath
        self.games = []
        if self.fpath:
            self.read()

    def read(self):
        with open(self.fpath) as fp:
            while True:
                game = chess.pgn.read_game(fp)
                if not game:
                    break
                self.games.append(game)

    def write(self, fpath=None):
        if fpath==None:
            fpath = self.fpath

        with open(fpath, 'w') as fp:
            for game in self.games:
                fp.write(str(game))
                fp.write('\n\n')

    def commentary_set(self, game_i, message):
        message = message.replace('\n', '\\n')
        self.games[i].headers['commentary'] = message
    
    def commentary_get(self, game_i):
        message = self.games[i].headers['commentary']
        message = message.replace('\\n', '\n')
        return message

    def __getitem__(self, key):
        return self.games[key]

    def __len__(self):
        return len(self.games)

if __name__ == '__main__':
    fpath = sys.argv[1]
    pgnfile = PgnFile(fpath)

    print(f'loaded {len(pgnfile.games)} games')

    pgnfile.write('wtf.pgn')
