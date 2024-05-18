import re
import time

def read(path='database.txt'):
    state = 'WAITING'
    entry = {}
    result = []
    for line in open('database.txt', 'r').readlines():
        line = line.strip()
        if line=='' or line.isspace():
            if state == 'WAITING':
                pass
            else:
                result.append(entry)
                state = 'WAITING'
        elif line.startswith('#'):
            continue
        elif m := re.match(r'^([A-Z]+):\s*(.*)$', line):
            if state == 'WAITING':
                # default values
                entry = {   'TYPE': 'PlayBest2',
                            'FEN': '',
                            'FRONT': '',
                            'BACK': '',
                            'LEITNER_BOX': 0,
                            'LEITNER_DUE': int(time.time())
                        }
                state = 'BUSY'
            # override defaults
            name, value = m.group(1, 2)
            entry[name] = value
    if entry:
        result.append(entry)
    return result

if __name__ == '__main__':
    import json
    info = read()
    print(json.dumps(info, indent=4))
