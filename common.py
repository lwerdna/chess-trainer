import os
import re
import io
import operator

import chess
import chess.engine

import debug

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


# Used for converting squares from index notation to algebraic notation
index_to_san = {56: 'a8', 57: 'b8', 58: 'c8', 59: 'd8', 60: 'e8', 61: 'f8', 62: 'g8', 63: 'h8',
                48: 'a7', 49: 'b7', 50: 'c7', 51: 'd7', 52: 'e7', 53: 'f7', 54: 'g7', 55: 'h7',
                40: 'a6', 41: 'b6', 42: 'c6', 43: 'd6', 44: 'e6', 45: 'f6', 46: 'g6', 47: 'h6',
                32: 'a5', 33: 'b5', 34: 'c5', 35: 'd5', 36: 'e5', 37: 'f5', 38: 'g5', 39: 'h5',
                24: 'a4', 25: 'b4', 26: 'c4', 27: 'd4', 28: 'e4', 29: 'f4', 30: 'g4', 31: 'h4',
                16: 'a3', 17: 'b3', 18: 'c3', 19: 'd3', 20: 'e3', 21: 'f3', 22: 'g3', 23: 'h3',
                8:  'a2', 9:  'b2', 10: 'c2', 11: 'd2', 12: 'e2', 13: 'f2', 14: 'g2', 15: 'h2',
                0:  'a1', 1:  'b1', 2:  'c1', 3:  'd1', 4:  'e1', 5:  'f1', 6:  'g1', 7:  'h1' }

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

def get_stockfish_path():
    paths = [   '/usr/local/bin/stockfish', # Linux
                '/usr/games/stockfish', # Linux
                '/opt/homebrew/bin/stockfish' # MacOS
            ]

    for path in paths:
        if os.path.exists(path):
            return path

    raise Exception('Can\'t find stockfish!')

def get_engine():
    path = get_stockfish_path()
    return chess.engine.SimpleEngine.popen_uci(path)

def only_kings(board):
    return all(p.symbol() in 'Kk' for p in board.piece_map().values())

def is_winning(score):
    match type(score):
        case chess.engine.Mate: return True
        case chess.engine.Cp: return score.score() > 10
        case _: assert False

# "1. e6 Qd6 2. Bxe8 Bg5 3. Ng2 Re4 4. Qf3 Qxe6 5. Rf1"
# ->
# ['e6', 'Qd6', 'Bxe8', 'Bg5', 'Ng2', 'Re4', 'Qf3', 'Qxe6', 'Rf1']
def split_line_string(line):
    # get rid of possible "1..."
    if m := re.match(r'^\d\.+(.*)$', line):
        line = m.group(1)
    # get rid of game result strings
    if line.endswith(' *'):
        line = line[0:-2]
    if line.endswith(' 1/2-1/2'):
        line = line[0:-8]
    if line.endswith(' 1-0'):
        line = line[0:-4]
    if line.endswith(' 0-1'):
        line = line[0:-4]
    # remove move numbers
    line = re.sub(r'\d+\.', '', line)
    # remove leading and trailing spaces
    line = line.strip()
    # split on spaces
    return re.split(r'\s+', line)

def last_move_as_san(board):
    bcopy = board.copy()
    move = bcopy.pop()
    return bcopy.san(move)

def move_as_san(board, move):
    return board.san(move)

# assign a fullmove number to nodes in a variation tree
def assign_fullmove(node, current):
    node.fullmove = current
    for child in node.variations:
        assign_fullmove(child, current if node.turn() == chess.WHITE else current+1)

# collect all nodes in a variation tree
def collect_nodes(node):
    result = [node]
    for child in node.variations:
        result.extend(collect_nodes(child))
    return result

# get all nodes in a variation tree where branching occurs (and root)
def get_branch_nodes(node):
    result = []
    if type(node) == chess.pgn.Game or len(node.variations)>1:
        result.append(node)
    for child in node.variations:
        result.extend(get_branch_nodes(child))
    return result

# get all nodes in a depth search to the bottom, always going left (main variation)
def descend_left(node):
    result = [node]
    if node.variations:
        child = node.variations[0]
        result.extend(descend_left(child))
    return result

# convert a GameNode/ChildNode "chain" (a tree with always only one child except leaf)
# to a string like "1.Rd8+ Kf7 2.R1d7+ Kf6 3.Rf8+ Ke5 4.Re8+ Kf4 5.Rd4+ Kg3 6.Re3#"
def node_chain_to_san(node):
    tokens = []

    first = True
    while not node.is_end():
        if node.turn() == chess.WHITE:
            tokens.append(f'{node.fullmove}.')
        elif first:
            tokens.append(f'{node.fullmove}...')

        tokens.append(node.variations[0].san())

        first = False

        node = node.variations[0]
        if not node.is_end():
            tokens.append(' ')

    return ''.join(tokens)

# convert a list of GameNode/ChildNode
# to a string like "1.Rd8+ Kf7 2.R1d7+ Kf6 3.Rf8+ Ke5 4.Re8+ Kf4 5.Rd4+ Kg3 6.Re3#"
#
# ignore children (held in .variations) and instead use the list as ancestry
def node_list_to_san(nodes):
    tokens = []

    for i, node in enumerate(nodes):
        first = (i == 0)
        last = (i == len(nodes)-1)

        if first:
            tokens.append(f'{node.fullmove}' + ('.' if node.turn() == chess.WHITE else '...'))
        elif node.turn() == chess.WHITE and not last:
            tokens.append(f'{node.fullmove}.')

        if i < len(nodes)-1:
            tokens.append(nodes[i+1].san())
        if i < len(nodes)-2:
            tokens.append(' ')

        first = False

    return ''.join(tokens)

def generate_variation_exercises_worker(node, line):
    result = []
    if node.is_end():
        result.append(line + [node])
    else:
        for i, child in enumerate(node.variations):
            if i==0:
                result.extend(generate_variation_exercises_worker(child, line+[node])) # left descent continues current line
            else:
                result.extend(generate_variation_exercises_worker(child, [node])) # non-left descent starts new
    return result

# fen:        starting board state
# variations: text describes lines
def generate_variation_exercises(fen, variations):
    result = []

    # have chess parse it
    pgn = io.StringIO(f'[FEN "{fen}"]\n{variations}')
    game = chess.pgn.read_game(pgn)
    assign_fullmove(game, 1)

    temp = generate_variation_exercises_worker(game, [])

    for nodes in generate_variation_exercises_worker(game, []):
        fen = nodes[0].board().fen()
        line_str = node_list_to_san(nodes)
        result.append({'FEN':fen, 'LINE':line_str})

    return result

def moves_to_dot(fen, variations):
    pgn = io.StringIO(f'[FEN "{fen}"]\n{variations}')
    game = chess.pgn.read_game(pgn)
    assign_fullmove(game, 1)

    print('digraph g {')

    print('\t//nodes')
    nodes = collect_nodes(game)
    for node in nodes:
        print(f'\t{id(node)} [label=""]')

    print('\t//edges')
    for src in nodes:
        for dst in src.variations:
            # X.turn is the color *TO* move at state X
            if src.turn() == chess.WHITE:
                move_label = f'{dst.fullmove}.{dst.san()}'
            else:
                move_label = f'{dst.fullmove}...{dst.san()}'
            print(f'\t{id(src)} -> {id(dst)} [label="{move_label}"]')

    print('}')

