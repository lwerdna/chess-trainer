#!/usr/bin/env python

import os

import chess
import chess.engine

import common

engine = None

def init():
    global engine
    engine = common.get_engine()

def newgame():
    global engine
    engine.protocol._ucinewgame()

def exit():
    global engine
    if engine:
        engine.quit()

def is_winning(result, threshold=10):
    match type(result):
        case chess.engine.Mate: winning = True
        case chess.engine.Cp: winning = result.score() > threshold
        case _: breakpoint()
    return winning

def is_even(result, threshold=.1):
    match type(result):
        case chess.engine.Mate: even = False
        case chess.engine.Cp: even = abs(result.score()) < threshold
        #case _: assert False
        case _: breakpoint()
    return even

def pv_to_san(pv, board):
    btmp = board.copy()
    san_strs = []
    for m in pv:
        san_strs.append(btmp.san(m))
        btmp.push(m)
    return ' '.join(san_strs)

def bestmove(board, tlimit=1.0):
    result = engine.play(board, chess.engine.Limit(time=tlimit))
    return result.move

def best_reply_to(board, move):
    global engine

    with engine.analysis(board, root_moves=[move]) as analysis:
        for info in analysis:
            if not ('pv' in info and 'seldepth' in info and 'depth' in info and 'score' in info):
                continue

            pv = info['pv']
            pov_score = info['score']
            match board.turn:
                case chess.WHITE: score = pov_score.white()
                case chess.BLACK: score = pov_score.black()

            #if info['seldepth'] > 30 or info['depth'] > 30:
            if info['depth'] > 30:
                break

    #print(f'  pv(san): {pv_to_san(pv, board)} with score {score}')

    return (pv[1], score)

def evaluate(board, pov):
    global engine

    print(f'evaluate({board.fen()})')

    best_score = None
    best_line = None

    with engine.analysis(board) as analysis:
        # analysis: chess.engine.SimpleAnalysisResult
        #     info: dict with keys like 'depth', 'seldepth', 'multipv', 'score', etc.
        for info in analysis:
            #print('    score: ' + str(info.get('score'))) # chess.engine.Score
            #print('       pv: ' + str(info.get('pv')))
            #print('    depth: ' + str(info.get('depth')))
            #print(' seldepth: ' + str(info.get('seldepth')))

            if 'pv' in info:
                #print('  pv(san): ' + pv_to_san(info.get('pv'), board))
                pass

            if 'pv' in info and 'score' in info:
                pov_score = info.get('score')
                match pov:
                    case chess.WHITE: score = pov_score.white()
                    case chess.BLACK: score = pov_score.black()

                if best_score == None or score > best_score:
                    best_score = score
                    best_line = info.get('pv')


#            print('    score: ' + str(info.get('score'))) # chess.engine.Score
#            print('       pv: ' + str(info.get('pv')))
#            print('    depth: ' + str(info.get('depth')))
#            print(' seldepth: ' + str(info.get('seldepth')))

            # Arbitrary stop condition.
            if info.get("seldepth", 0) > 40 or info.get('depth', 0) > 40:
                break

    # best move is pv[0]
    return best_score, best_line

def top_three_moves(board):
    with engine.analysis(board, multipv=3) as analysis:
        moves = [None, None, None]
        scores = [None, None, None]

        for info in analysis:
            if not 'multipv' in info:
                continue

            i = info['multipv']-1
            moves[i] = info.get('pv')[0] # get first move from principle variation
            scores[i] = info.get('score')

            if 0:
                print(f'     pv#1: {moves[0]} {scores[0]}')
                print(f'     pv#2: {moves[1]} {scores[1]}')
                print(f'     pv#3: {moves[2]} {scores[2]}')
                print(f'    depth: ' + str(info.get('depth')))
                print(f' seldepth: ' + str(info.get('seldepth')))
                print('----')

            # Arbitrary stop condition.
            if info.get('depth', 0) > 30:
                print('exited loop since depth > 30')
                break            
            #if info.get("seldepth", 0) > 30:
            #    print('exited loop since seldepth > 30')
            #    break

    return list(zip(moves, scores))

def get_best_line(board, fullMoves=None):
    if type(board) == str:
        fen = board
        board = chess.Board()
        board.set_fen(fen)

    score, pv = evaluate(board, board.turn)

    if fullMoves:
        halfMoves = length + (length-1)
        pv = pv[0:halfMoves]

    result = board.variation_san(pv)
    result = result + ' *'
    return result

def does_only_one_move_win(board):
    ttm = top_three_moves(board)

    (m0, s0) = ttm[0]
    (m1, s1) = ttm[1]
    (m2, s2) = ttm[2]

    if board.turn == chess.WHITE:
        (s0, s1, s2) = (s0.white() if s0 else None, s1.white() if s1 else None, s2.white() if s2 else None)
    else:
        (s0, s1, s2) = (s0.black(), s1.black(), s2.black())

    if 0:
        print(f'{m0} has score {s0}')
        print(f'{m1} has score {s1}')
        print(f'{m2} has score {s2}')

    if is_winning(s0) and not is_winning(s1) and not is_winning(s2):
        return m0

def does_only_one_move_draw(board):
    global engine

    ttm = top_three_moves(board)
    ttm = [(m,s) for (m,s) in ttm if s != None]
    ttm = [(m,s.white() if board.turn == chess.WHITE else s.black()) for (m,s) in ttm if s != None]

    move = None
    num_draws = 0
    for (m,s) in ttm:
        if m == None:
            continue
        if is_even(s):
            print(f'YES: {m} has score {s}')
            move = m
            num_draws += 1
        else:
            print(f' NO: {m} has score {s}')

    if num_draws == 1:
        return move

if __name__ == '__main__':
    import sys

    init()

    board = chess.Board()

    board.set_fen('8/8/8/8/8/6KP/8/7k b - - 0 1')
    does_only_one_move_draw(board)

    if sys.argv[1] == 'a':
        board.set_fen('8/4k3/8/4K3/1P6/8/8/8 b - - 3 2')
        evaluate(board, chess.BLACK)

    if sys.argv[1] == 'b':
        board.set_fen('8/5k2/8/8/1P4K1/8/8/8 w - - 0 1')
        evaluate(board, chess.WHITE)
        #board.set_fen('8/5k2/8/5K2/1P6/8/8/8 b - - 1 1')
        #evaluate(board, chess.BLACK)
        board.set_fen('8/4k3/8/4K3/1P6/8/8/8 b - - 3 2')
        evaluate(board, chess.BLACK)

    if sys.argv[1] == 'c':
        board.set_fen('8/5k2/8/8/1P4K1/8/8/8 w - - 0 1')
        print(board)

        move = board.parse_san('Kf5')
        reply = best_reply_to(board, move)
        board.push(move)
        print(board.san(reply))
        board.push(reply)
        print(board)

        move = board.parse_san('Ke5')
        reply = best_reply_to(board, move)
        board.push(move)
        print(board.san(reply))
        board.push(reply)
        print(board)

        move = board.parse_san('Kd5')
        reply = best_reply_to(board, move)
        board.push(move)
        print(board.san(reply))
        board.push(reply)
        print(board)

    exit()
