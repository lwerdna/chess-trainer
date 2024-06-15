#!/usr/bin/env python

import os

from common import *

def get_problems_from_game(game):
    nodes = collect_nodes(game)

    # collect all problem start nodes
    problem_nodes = {}
    problem_questions = {}
    for node in nodes:
        for m in re.finditer(r'<(\d+)(?: Q="(.*)")?>', node.comment):
            problem_index, question = m.group(1, 2)
            problem_index = int(problem_index)

            if problem_index in problem_nodes:
                raise Exception(f'problem {problem_index} start tag appears twice in tree')

            problem_nodes[problem_index] = node
            problem_questions[problem_index] = question

    problems = []

    for problem_index, ancestor in problem_nodes.items():
        entry = {}
        if problem_index in problem_questions:
            entry['question'] = problem_questions[problem_index]

        entry['fen'] = ancestor.board().fen()

        # find end nodes
        end_nodes = []
        for node in collect_nodes(ancestor):
            if m := re.search(r'</(\d+)>', node.comment):
                if int(m.group(1)) == problem_index:
                    end_nodes.append(node)

        # no end tag?
        #   then all leaves from start tag are end tag
        if not end_nodes:
            end_nodes = [n for n in collect_nodes(ancestor) if n.is_end()]

        # collect all nodes involved from ancestor to end nodes
        whitelist = set()
        for b in end_nodes:
            path = search_path(ancestor, b)
            whitelist.update(path)

        entry['line'] = tree_to_san_line(ancestor, whitelist)

        problems.append(entry)

    return problems

def get_pgns(path='./pgns'):
    result = []
    for root, dirs, fnames in os.walk(path):
        for dir in dirs:
            #print os.path.join(path, dir)
            pass
        for fname in fnames:
            fpath = os.path.join(path, fname)
            result.append(fpath)
    return result

def get_problems():
    problems = []

    #for fpath in get_pgns():
    #for fpath in ['./misc/two-rook-mate-with-variations.pgn']:
    for fpath in ['./pgns/all-openings.pgn']:
        with open(fpath) as fp:
            game = chess.pgn.read_game(fp)

        for problem in get_problems_from_game(game):
            problems.append(problem)

    return problems

if __name__ == '__main__':
    print('\n'.join(get_pgns()))

    problems = get_problems()
    
    import pprint
    pprint.pprint(problems)
