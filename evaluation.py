#!/usr/bin/env python

import chess
import chess.engine

engine = None

def init():
    global engine
    engine = chess.engine.SimpleEngine.popen_uci("/usr/local/bin/stockfish")

def exit():
    global engine
    if engine:
        engine.quit()

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

            if info['seldepth'] > 30 or info['depth'] > 30:
                break

    #print(f'  pv(san): {pv_to_san(pv, board)} with score {score}')

    return (pv[1], score)

def evaluate(board, pov):
    global engine

    print(f'evaluate({board.fen()})')

    best_score = None
    best_move = None

    with engine.analysis(board) as analysis:
        # analysis: chess.engine.SimpleAnalysisResult
        #     info: dict with keys like 'depth', 'seldepth', 'multipv', 'score', etc.
        for info in analysis:
            #print('    score: ' + str(info.get('score'))) # chess.engine.Score
            #print('       pv: ' + str(info.get('pv')))
            #print('    depth: ' + str(info.get('depth')))
            #print(' seldepth: ' + str(info.get('seldepth')))

            if 'pv' in info:
                print('  pv(san): ' + pv_to_san(info.get('pv'), board))

            if 'pv' in info and 'score' in info:
                pov_score = info.get('score')
                match pov:
                    case chess.WHITE: score = pov_score.white()
                    case chess.BLACK: score = pov_score.black()

                if best_score == None or score > best_score:
                    best_score = score
                    best_move = info.get('pv')[0]


#            print('    score: ' + str(info.get('score'))) # chess.engine.Score
#            print('       pv: ' + str(info.get('pv')))
#            print('    depth: ' + str(info.get('depth')))
#            print(' seldepth: ' + str(info.get('seldepth')))

            # Arbitrary stop condition.
            if info.get("seldepth", 0) > 40 or info.get('depth', 0) > 40:
                break

    return (best_score, best_move)

if __name__ == '__main__':
    import sys

    init()

    board = chess.Board()

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
