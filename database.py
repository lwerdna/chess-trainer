import re
import time

def read(path='database.txt'):
    state = 'WAITING'
    entry = {}
    result = []
    lineNum = 0
    for line in open('database.txt', 'r').readlines():
        lineNum += 1
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
                entry = {   'TYPE': 'untyped',
                            'FEN': '',
                            'FRONT': '(blank)',
                            'BACK': '(blank)',
                            'LEITNER': (0, int(time.time())),
                            'lineNum': lineNum
                        }
                state = 'BUSY'
            # override defaults
            name, value = m.group(1, 2)
            if name == 'LEITNER':
                box, due_str = value.split(', ')
                struct_time = time.strptime(due_str, '%Y-%m-%d %H:%M:%S')
                epoch = int(time.mktime(struct_time))
                value = int(box), epoch
            entry[name] = value

    if state != 'WAITING':
        result.append(entry)

    return result

def write(dbinfo, path='database.txt'):
    with open(path, 'w') as fp:
        for entry in dbinfo:
            for key in ['TYPE', 'FEN', 'LINE', 'FRONT', 'BACK', 'LEITNER']:
                if not key in entry:
                    continue

                value = entry[key]
                if key == 'LEITNER':
                    box, epoch = value
                    struct_time = time.localtime(epoch)
                    due_str = time.strftime('%Y-%m-%d %H:%M:%S', struct_time)
                    fp.write('LEITNER: %s, %s\n' % (box, due_str))
                else:
                    fp.write(f'{key}: {value}\n')
            fp.write('\n')
    fp.close()

if __name__ == '__main__':
    import json
    info = read()
    print(json.dumps(info, indent=4))
