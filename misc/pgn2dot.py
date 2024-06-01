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

if __name__ == '__main__':
    fpath = sys.argv[1] if sys.argv[1:] else 'two-rook-mate-with-variations.pgn'

    print(f'// opening {fpath}')
    game = chess.pgn.read_game(open(fpath))
    assign_fullmove(game, 1)

    #print('mainline moves')
    #for move in game.mainline_moves():
    #    print(move)

    # root node is type: Game (extends GameNode)
    # child nodes are type: ChildNode (extends GameNode)
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

