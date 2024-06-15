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

# return a string that uniquely identifies a problem
def problem_to_key(problem):
    return problem['fen'] + ' ' + problem['line']

# key: problem key consisting of the start fen, space, then san line
def add_problem(problem):
    global database
    key = problem_to_key(problem)
    if not key in database:
        database[key] = {}
        database[key]['due'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()-1))

def update_problem(problem, due_epoch):
    global database
    key = problem_to_key(problem)
    database[key]['due'] = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(due_epoch))

def is_due(problem):
    global database
    key = problem_to_key(problem)
    entry = database[key]
    struct_time = time.strptime(entry['due'], '%Y-%m-%d %H:%M:%S')
    now = int(time.time())
    return now > int(time.mktime(struct_time))

