#!/usr/bin/env python

import sys

import chess
import chess.pgn

def assign_fullmove(node, current):
    node.fullmove = current
    for child in node.variations:
        assign_fullmove(child, current if node.turn() == chess.WHITE else current+1)

def collect_nodes(node):
    result = [node]
    for child in node.variations:
        result.extend(collect_nodes(child))
    return result

# get branch nodes
def get_branch_nodes(node):
    result = []
    if type(node) == chess.pgn.Game or len(node.variations)>1:
        result.append(node)
    for child in node.variations:
        result.extend(get_branch_nodes(child))
    return result

def descend_left(node):
    result = [node]
    if node.variations:
        child = node.variations[0]
        result.extend(descend_left(child))
    return result

def cool(node, line):
    result = []
    if node.is_end():
        result.append(line + [node])
    else:
        for i, child in enumerate(node.variations):
            if i==0:
                result.extend(cool(child, line+[node])) # left descent continues current line
            else:
                result.extend(cool(child, [node])) # non-left descent starts new
    return result

if __name__ == '__main__':
    fpath = sys.argv[1] if sys.argv[1:] else 'two-rook-mate-with-variations.pgn'

    print(f'// opening {fpath}')
    game = chess.pgn.read_game(open(fpath))
    assign_fullmove(game, 1)

    for line in cool(game, []):
        root_node = line[0]
        b = root_node.board()
        print(f'from position: ' + b.fen())

        for n in line[1:]:
            print(n.san())

