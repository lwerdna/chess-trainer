#!/usr/bin/env python

# search for interesting KP vs. K endgames

import sys
import random

import chess
import chess.engine

TIME = 1.0

#------------------------------------------------------------------------------
# HELPERS
#------------------------------------------------------------------------------

engine = None
def get_evaluation(board):
    global engine
    if not engine:
        engine = chess.engine.SimpleEngine.popen_uci("/usr/local/bin/stockfish")
    #info = engine.analyse(board, chess.engine.Limit(time=TIME))
    info = engine.analyse(board, chess.engine.Limit(depth=60, mate=20))

    best_move = None
    if info.get('pv'):
        best_move = info.get('pv')[0]

    return (best_move, info['score'].white())

def is_winning(result):
    match type(result):
        case chess.engine.Mate: winning = True
        case chess.engine.Cp: winning = result.score() > 10
        case _: assert False
    return winning

#------------------------------------------------------------------------------
# MAIN
#------------------------------------------------------------------------------

if __name__ == '__main__':
    with open(sys.argv[1]) as fp:
        for line in fp.readlines():
            if line.isspace() or line.startswith('#'):
                print(line)
                continue

            board = chess.Board()
            board.set_fen(line)

            (best_move, result) = get_evaluation(board)

            # is this a winning position?
            if is_winning(result):
                comment = ''
            else:
                comment = f' # ERROR: evaluation is {result}'
            print(f'{line.strip()} {comment}')
    if engine:
        engine.quit()
