import operator
import re

# FEN string for starting chess position
starting_fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'

# Regular expressions for common chess notation
rank = r'[rnbqkpRNBQKP1-8]{1,8}'
board_fen = rank + '/' + rank + '/' + rank + '/' + rank + '/' + rank + '/' + rank + '/' + rank + '/' + rank
regex_fen = re.compile(r'^' + board_fen + r' [wb] (?:(?:K?Q?k?q?)|-) (?:(?:[a-h][1-8])|-) \d+ \d+$')
regex_square = re.compile(r'[a-h][1-8]')
regex_san = re.compile(r'^(?:(?P<qCastle>O-O-O)|(?P<kCastle>O-O)|(?P<srcPiece>[NbRQK])?'
                       r'(?P<srcHint>[a-h1-8]{1,2})?(?P<action>x)?(?P<dstSquare>[a-h][1-8])'
                       r'(?P<promote>=[NbRQ])?)(?P<check>[+#])?')

# Used for converting files from letters to numbers
notation_to_index = {"a": 1,
                     "b": 2,
                     "c": 3,
                     "d": 4,
                     "e": 5,
                     "f": 6,
                     "g": 7,
                     "h": 8}

# Used for converting files from numbers to letters
index_to_notation = {1: "a",
                     2: "b",
                     3: "c",
                     4: "d",
                     5: "e",
                     6: "f",
                     7: "g",
                     8: "h"}

# Used for converting squares from algebraic notation to index notation
san_to_index = {'a8': 56, 'b8': 57, 'c8': 58, 'd8': 59, 'e8': 60, 'f8': 61, 'g8': 62, 'h8': 63,
                'a7': 48, 'b7': 49, 'c7': 50, 'd7': 51, 'e7': 52, 'f7': 53, 'g7': 54, 'h7': 55,
                'a6': 40, 'b6': 41, 'c6': 42, 'd6': 43, 'e6': 44, 'f6': 45, 'g6': 46, 'h6': 47,
                'a5': 32, 'b5': 33, 'c5': 34, 'd5': 35, 'e5': 36, 'f5': 37, 'g5': 38, 'h5': 39,
                'a4': 24, 'b4': 25, 'c4': 26, 'd4': 27, 'e4': 28, 'f4': 29, 'g4': 30, 'h4': 31,
                'a3': 16, 'b3': 17, 'c3': 18, 'd3': 19, 'e3': 20, 'f3': 21, 'g3': 22, 'h3': 23,
                'a2':  8, 'b2':  9, 'c2': 10, 'd2': 11, 'e2': 12, 'f2': 13, 'g2': 14, 'h2': 15,
                'a1':  0, 'b1':  1, 'c1':  2, 'd1':  3, 'e1':  4, 'f1':  5, 'g1':  6, 'h1':  7}

# Used for converting squares from index notation to algebraic notation
index_to_san = {56: 'a8', 57: 'b8', 58: 'c8', 59: 'd8', 60: 'e8', 61: 'f8', 62: 'g8', 63: 'h8',
                48: 'a7', 49: 'b7', 50: 'c7', 51: 'd7', 52: 'e7', 53: 'f7', 54: 'g7', 55: 'h7',
                40: 'a6', 41: 'b6', 42: 'c6', 43: 'd6', 44: 'e6', 45: 'f6', 46: 'g6', 47: 'h6',
                32: 'a5', 33: 'b5', 34: 'c5', 35: 'd5', 36: 'e5', 37: 'f5', 38: 'g5', 39: 'h5',
                24: 'a4', 25: 'b4', 26: 'c4', 27: 'd4', 28: 'e4', 29: 'f4', 30: 'g4', 31: 'h4',
                16: 'a3', 17: 'b3', 18: 'c3', 19: 'd3', 20: 'e3', 21: 'f3', 22: 'g3', 23: 'h3',
                8:  'a2', 9:  'b2', 10: 'c2', 11: 'd2', 12: 'e2', 13: 'f2', 14: 'g2', 15: 'h2',
                0:  'a1', 1:  'b1', 2:  'c1', 3:  'd1', 4:  'e1', 5:  'f1', 6:  'g1', 7:  'h1', }

# Generate a list of all squares on the board in algebraic notation         
squares_san = []
for rank in '12345678':
    for file in 'abcdefgh':
        squares_san.append(file + rank)

# Used for converting squares from algebraic notation to coordinates
square_to_coords = {}
for row, rank in enumerate('87654321'):
    for col, file in enumerate('abcdefgh'):
        square_to_coords[file + rank] = (col, row)


