#!/usr/bin/env python

import os
import sys

import database
import problemstate

path = sys.argv[1] if sys.argv[1:] else 'database.txt'
dbinfo = database.read(path)

for i, entry in enumerate(dbinfo):
    print(f'the {i}\'th problem from {path}:{entry["lineNum"]}')

    problem_state = problemstate.create_problem_state_from_db_data(entry)

