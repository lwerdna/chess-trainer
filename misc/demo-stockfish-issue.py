#!/usr/bin/env python

# you get a different bestmove if you've called bestmove twice

import sys
import random

import chess
import chess.engine

FIX = True
TIME = 0.2

board = chess.Board()

fen = '8/4k3/8/4K3/1P6/8/8/8 b - - 3 2'

engine = chess.engine.SimpleEngine.popen_uci("/usr/local/bin/stockfish")
board.set_fen(fen)
move = engine.play(board, chess.engine.Limit(time=TIME)).move
print(f'found move: {move}')
engine.quit()

engine = chess.engine.SimpleEngine.popen_uci("/usr/local/bin/stockfish")
if FIX:
    engine.protocol._ucinewgame()
board.set_fen('8/5k2/8/8/1P4K1/8/8/8 w - - 0 1')
engine.play(board, chess.engine.Limit(time=TIME))
if FIX:
    engine.protocol._ucinewgame()
board.set_fen(fen)
move = engine.play(board, chess.engine.Limit(time=TIME)).move
print(f'found move: {move}')
engine.quit()

