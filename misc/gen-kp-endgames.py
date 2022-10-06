#!/usr/bin/env python

# search for interesting KP vs. K endgames

import sys
import random

import chess
import chess.engine

TIME = .5

#------------------------------------------------------------------------------
# HELPERS
#------------------------------------------------------------------------------

engine = None
def get_evaluation(board):
    global engine
    if not engine:
        engine = chess.engine.SimpleEngine.popen_uci("/usr/local/bin/stockfish")
    info = engine.analyse(board, chess.engine.Limit(time=TIME))

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

def gen_board(pawn_rank=None):
    sq_symbols = [col+row for col in list('abcdefgh') for row in list('12345678')]

    if pawn_rank == None:
        sq_symbols_P = [col+row for col in list('abcdefh') for row in list('34567')]
    else:
        sq_symbols_P = [col+row for col in list('abcdefh') for row in [str(pawn_rank)]]

    while True:
        sq_K = chess.parse_square(random.choice(sq_symbols))
        sq_k = chess.parse_square(random.choice(sq_symbols))
        sq_P = chess.parse_square(random.choice(sq_symbols_P))

        #if len(set([sq_K, sq_k, sq_P])) == 3:
        #    break

        board = chess.Board()
        board.clear()

        K = chess.Piece.from_symbol('K')
        k = chess.Piece.from_symbol('k')
        P = chess.Piece.from_symbol('P')

        #print(f'K on {sq_K}')
        board.set_piece_at(sq_K, K)
        #print(f'k on {sq_k}')
        board.set_piece_at(sq_k, k)
        #print(f'P on {sq_P}')
        board.set_piece_at(sq_P, P)

        if board.is_valid():
            break

    return board

def is_pawn_move(board, move):
    return board.piece_at(best_move.from_square).piece_type == chess.PAWN

def is_king_move(board, move):
    return board.piece_at(best_move.from_square).piece_type == chess.KING

#------------------------------------------------------------------------------
# MAIN
#------------------------------------------------------------------------------

if __name__ == '__main__':
    board = chess.Board()

    collection = []
    while True:
        board = gen_board(2)

        #board.set_fen('8/8/7K/8/8/4P3/4k3/8 w - - 0 1')
        #board.set_fen('8/8/8/6k1/8/P7/8/1K6 w - - 0 1')
        #board.set_fen('5k2/7P/8/8/8/8/1K6/8 w - - 0 1')
        #board.set_fen('2k5/2P5/8/3K4/8/8/8/8 w - - 0 1')
        #board.set_fen('8/8/8/8/1kP5/8/2K5/8 w - - 0 1')
        (best_move, result) = get_evaluation(board)

        # if we're in a stalemate position or something
        if best_move == None:
            continue

        # is this a winning position?
        if not is_winning(result):
            continue

        # is the winning position just running a pawn to the end?
        if chess.square_rank(best_move.from_square) < 6:
            if board.piece_at(best_move.from_square).piece_type == chess.PAWN:
                continue

        # pawn moves too easy, require king move
        if not is_king_move(board, best_move):
            continue

        print(f'generated candidate board: {board.fen()} with evaluation {result}')
        moves = list(board.legal_moves)
        print(f'there are {len(moves)} legal moves')

        # if there are multiple promotion moves, assume one is a queen move and keep only that one
        if len([m for m in moves if m.promotion != None]):
            assert [m for m in moves if m.promotion == chess.QUEEN]
            moves = [m for m in moves if m.promotion in [None, chess.QUEEN]]

        # if the winning move is simply to promote, skip it
        #if best_move.promotion == chess.QUEEN:
        #    print('trivial promote to queen')
        #    continue

        moves_that_win = 0
        for m in moves:
            board.push(m)
            (_, result) = get_evaluation(board)
            if is_winning(result):
                moves_that_win += 1
                print(f'{m} wins')
            else:
                print(f'{m} doesn\'t win')
            board.pop()

            if moves_that_win >= 2:
                break

        if moves_that_win == 1:
            print('found one! added to collection:')
            print(board)
            collection.append(board.fen())
            print('\n'.join(collection))

    if engine:
        engine.quit()
