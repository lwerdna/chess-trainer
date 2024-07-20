#!/usr/bin/env python

# experiment with continuous analysis of position

import sys
import random

import chess
import chess.engine

def pv_to_san(pv, board):
    btmp = board.copy()
    san_strs = []
    for m in info.get('pv'):
        san_strs.append(btmp.san(m))
        btmp.push(m)
    return ' '.join(san_strs)

#------------------------------------------------------------------------------
# MAIN
#------------------------------------------------------------------------------

if __name__ == '__main__':
    board = chess.Board()
    board.set_fen('2k5/2P5/8/3K4/8/8/8/8 w - - 0 1')
    board.set_fen('8/5k2/8/8/1P4K1/8/8/8 w - - 0 1') # keep opposition, race to key square
    board.set_fen('8/5k2/8/5K2/1P6/8/8/8 b - - 1 1') # after 1.Kf5
    board.set_fen('8/4k3/8/4K3/1P6/8/8/8 b - - 3 2') # after 2.Ke5

    engine = chess.engine.SimpleEngine.popen_uci("/usr/local/bin/stockfish")

    # demonstrate normal streaming evaluation
    if 1:
        with engine.analysis(board) as analysis:
            # analysis: chess.engine.SimpleAnalysisResult
            #     info: dict with keys like 'depth', 'seldepth', 'multipv', 'score', etc.
            for info in analysis:
                #print('    score: ' + str(info.get('score'))) # chess.engine.PovScore
                #print('       pv: ' + str(info.get('pv')))
                #print('    depth: ' + str(info.get('depth')))
                #print(' seldepth: ' + str(info.get('seldepth')))

                if 'pv' in info:
                    print('  pv(san): ' + pv_to_san(info.get('pv'), board))

                # Arbitrary stop condition.
                if info.get("seldepth", 0) > 40:
                    break

    # demonstrate multiple principal variations
    if 0:
        with engine.analysis(board, multipv=3) as analysis:
            p_variations = ['', '', '']
            scores = [None, None, None]

            # analysis: chess.engine.SimpleAnalysisResult
            #     info: dict with keys like 'depth', 'seldepth', 'multipv', 'score', etc.
            for info in analysis:
                if not 'multipv' in info:
                    continue

                pv_i = info['multipv']-1
                pv = info.get('pv') # list of chess.Move
                p_variations[pv_i] = pv_to_san(pv, board)
                scores[pv_i] = info.get('score')

                print(f'     pv#1: {p_variations[0]} {scores[0]}')
                print(f'     pv#2: {p_variations[1]} {scores[1]}')
                print(f'     pv#3: {p_variations[2]} {scores[2]}')
                print(f'    depth: ' + str(info.get('depth')))
                print(f' seldepth: ' + str(info.get('seldepth')))

                print('----')

                # Arbitrary stop condition.
                if info.get("seldepth", 0) > 40:
                    break

    # demonstrate multiple moves
    if 0:
        move0 = chess.Move.from_uci('d5c6')
        move1 = chess.Move.from_uci('d5d6')
        move2 = chess.Move.from_uci('d5e6')

        with engine.analysis(board, multipv=3, root_moves=[move0, move1, move2]) as analysis:
            p_variations = ['', '', '']
            scores = [None, None, None]

            # analysis: chess.engine.SimpleAnalysisResult
            #     info: dict with keys like 'depth', 'seldepth', 'multipv', 'score', etc.
            for info in analysis:
                if not 'multipv' in info:
                    continue

                pv_i = info['multipv']-1
                pv = info.get('pv') # list of chess.Move
                p_variations[pv_i] = pv_to_san(pv, board)
                scores[pv_i] = info.get('score')

                print(f'     pv#1: {p_variations[0]} {scores[0]}')
                print(f'     pv#2: {p_variations[1]} {scores[1]}')
                print(f'     pv#3: {p_variations[2]} {scores[2]}')
                print(f'    depth: ' + str(info.get('depth')))
                print(f' seldepth: ' + str(info.get('seldepth')))

                print('----')

                # Arbitrary stop condition.
                if info.get("seldepth", 0) > 40:
                    break

    if engine:
        engine.quit()
