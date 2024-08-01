#!/usr/bin/env python

import sys

import chess
import chess.pgn

sys.path.append('../pgn-based')
import common

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
        cattrs = ' fillcolor=grey50, style=filled' if node.turn() == chess.BLACK else ''
        print(f'\t{id(node)} [label=""{cattrs}]')

    for n in nodes:
        if n.comment:
            comment_label = n.comment.replace('"', '\\"')
            print(f'\t{id(n.comment)} [label="{comment_label}" shape="box"]')

    print('\t//edges')
    for src in nodes:
        if src.comment:
            print(f'\t{id(src.comment)} -> {id(src)} [style="dashed"];')

        for dst in src.variations:
            move_label = common.node_to_san(dst)
            print(f'\t{id(src)} -> {id(dst)} [label="{move_label}"]')

    print('}')

