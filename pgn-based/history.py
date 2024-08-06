#!/usr/bin/env python

import os
import re

import time
import json

import time

database = None

def duration_string(seconds):
    if seconds < 60:
        answer = '%d sec' % seconds
    elif seconds < 3600:
        answer = '%d mins' % (seconds / 60)
    elif seconds < 86400:
        answer = '%d hrs' % (seconds / 3600)
    elif seconds < 2592000:
        answer = '%d days' % (seconds / 86400)
    elif seconds < 31536000:
        answer = '%d mos' % (seconds / 2592000)
    else:
        answer = '%.1f yrs' % (seconds / 31536000.0)

    return answer

def load():
    global database
    with open('history.json') as fp:
        database = json.load(fp)

def store():
    global database
    with open('history.json', 'w') as fp:
        fp.write(json.dumps(database, indent=4))

def add_pgn(pgn_path):
    global database
    key = make_key(pgn_path)
    if not key in database:
        database[key] = {}
        database[key]['due'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()-1))

def update_pgn(pgn_path, due_epoch):
    key = make_key(pgn_path)
    global database
    database[key]['due'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(due_epoch))

def is_due(pgn_path):
    global database
    entry = access(pgn_path)
    struct_time = time.strptime(entry['due'], '%Y-%m-%d %H:%M:%S')
    now = int(time.time())
    return now > int(time.mktime(struct_time))

def make_key(pgn_path):
    return re.match(r'^.*problems/(.*)$', pgn_path).group(1)

def access(pgn_path):
    global database
    key = make_key(pgn_path)
    return database.get(key)

if __name__ == '__main__':
    (RED, GREEN, YELLOW, NORMAL) = ('\x1B[31m', '\x1B[32m', '\x1B[33m', '\x1B[0m')

    load()

    pgn_paths = []
    for root, dirnames, filenames in os.walk('./problems'):
        for filename in filenames:
            if filename.endswith('.pgn'):
                fpath = os.path.join(root, filename)
                # if this file isn't currently in the DB, add it
                if access(fpath) is None:
                    add_pgn(fpath)
                pgn_paths.append(fpath)

    total_ok, total_due = 0, 0
    now = int(time.time())
    for pgn_path in pgn_paths:
        entry = access(pgn_path)
        if not entry:
            continue
        epoch = time.mktime(time.strptime(entry['due'], '%Y-%m-%d %H:%M:%S'))
        if is_due(pgn_path):
            delta = now - epoch
            descr = f'{RED}due {duration_string(delta)} ago{NORMAL}'
            total_due += 1
        else:
            delta = epoch - now
            descr = f'{GREEN}{duration_string(delta)} until due{NORMAL}'
            total_ok += 1
        print(f'{pgn_path} {descr}')

    print(f'total {total_ok} ok, {total_due} due')
