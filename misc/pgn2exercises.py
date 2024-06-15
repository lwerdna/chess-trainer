#!/usr/bin/env python

import re
import sys

import chess
import chess.pgn

sys.path.append('..')
from common import *

if __name__ == '__main__':
    fpath = sys.argv[1] if sys.argv[1:] else 'two-rook-mate-with-variations.pgn'

    print(f'// opening {fpath}')
    game = chess.pgn.read_game(open(fpath))

    nodes = collect_nodes(game)

    # collect all problem start nodes
    problem_nodes = {}
    problem_questions = {}
    for node in nodes:
        for m in re.finditer(r'<(\d+)(?: Q="(.*)")?>', node.comment):
            problem_id, question = m.group(1, 2)
            problem_id = int(problem_id)

            if problem_id in problem_nodes:
                raise Exception(f'problem {problem_id} start tag appears twice in tree')

            problem_nodes[problem_id] = node
            problem_questions[problem_id] = question

    # collect corresponding end nodes
    problems = {}
    # entry[x:int] is dict with:
    # {
    # 'start': start node of problem x
    # 'end': [end nodes of problem x]
    # 'question': question text (optional)
    # }
    for problem_id, ancestor in problem_nodes.items():
        problems[problem_id] = { 'start':ancestor, 'end':[], 'question':problem_questions[problem_id] }

        for node in collect_nodes(ancestor):
            if m := re.search(r'</(\d+)>', node.comment):
                if int(m.group(1)) == problem_id:
                    problems[problem_id]['end'].append(node)

    # no end tag?
    #   then all leaves from start tag are end tag
    for problem_id, entry in problems.items():
        if entry['end'] == []:
            entry['end'] = [n for n in collect_nodes(entry['start']) if n.is_end()]

    # print results
    for problem_id, entry in problems.items():
        print(f'problem_id={problem_id}')
        print(f'    start:')
        print(f'        {repr(entry["start"])}')
        print(f'   end(s):')
        for end in entry['end']:
            print(f'        {repr(end)}')
        if entry['question']:
            print(f' question:')
            print(f'        {entry["question"]}')

        print(f'    paths:')

        whitelist = set()

        a = entry['start']
        for b in entry['end']:
            path = search_path(a, b)
            whitelist.update(path)

            line = tree_to_san_line(a, set(path))
            print('        ' + line)

        cool = tree_to_san_line(entry['start'], whitelist)
        print(cool)

