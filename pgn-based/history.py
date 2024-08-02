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
    key = re.match(r'^.*problems/(.*)$', pgn_path).group(1)
    if not key in database:
        database[key] = {}
        database[key]['due'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()-1))

def update_pgn(pgn_path, due_epoch):
    key = re.match(r'^.*problems/(.*)$', pgn_path).group(1)
    global database
    database[key]['due'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(due_epoch))

def is_due(pgn_path):
    global database
    key = re.match(r'^.*problems/(.*)$', pgn_path).group(1)
    entry = database[key]
    struct_time = time.strptime(entry['due'], '%Y-%m-%d %H:%M:%S')
    now = int(time.time())
    return now > int(time.mktime(struct_time))

