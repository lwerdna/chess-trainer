#!/usr/bin/env python

# search for interesting KP vs. K endgames

import sys
import random

import chess
import chess.engine

sys.path.append('..')
import evaluation

TIME = .5
ROOK_PAWNS_ONLY = True

#------------------------------------------------------------------------------
# HELPERS
#------------------------------------------------------------------------------

def gen_board(pawn_rank=None):
    sq_symbols = [col+row for col in list('abcdefgh') for row in list('12345678')]

    if pawn_rank == None:
        sq_symbols_P = [col+row for col in list('abcdefh') for row in list('34567')]
    elif ROOK_PAWNS_ONLY:
        sq_symbols_P = ['a2', 'a3', 'a4', 'a5', 'a6', 'a7', 'h2', 'h3', 'h4', 'h5', 'h6', 'h7']
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

        board.turn = chess.BLACK

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
    evaluation.init()

    collection = []
    while True:
        board = gen_board(2)
        board.set_fen('8/7K/5k2/8/8/8/7P/8 b - - 0 1')

        print(board.fen())
        print(board)

        move = evaluation.does_only_one_move_draw(board)
        if not move:
            continue

        print('only one move draws: ' + str(move))
        # is the winning position just running a pawn to the end?
        #if chess.square_rank(move.from_square) < 6:
        #    if board.piece_at(move.from_square).piece_type == chess.PAWN:
        #        continue

        # pawn moves too easy, require king move
        #if not is_king_move(board, move):
        #    continue


        # if there are multiple promotion moves, assume one is a queen move and keep only that one
        #if len([m for m in moves if m.promotion != None]):
        #    assert [m for m in moves if m.promotion == chess.QUEEN]
        #    moves = [m for m in moves if m.promotion in [None, chess.QUEEN]]

        # if the winning move is simply to promote, skip it
        #if move.promotion == chess.QUEEN:
        #    print('trivial promote to queen')
        #    continue

        print('found one! added to collection:')
        print(board)
        collection.append(board.fen())
        print('\n'.join(collection))
        break

    evaluation.exit()
