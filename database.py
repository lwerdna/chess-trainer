import re
import time

def special_handle_defaults(entry):
    # convert text Leitner data to epoch for easy comparison by higher logic
    if value := entry.get('LEITNER'):
        box, due_str = value.split(', ')
        struct_time = time.strptime(due_str, '%Y-%m-%d %H:%M:%S')
        epoch = int(time.mktime(struct_time))
        value = int(box), epoch
        entry['LEITNER'] = value

    # if no type is given, but a correct line is given, then type is halfmoves
    if entry.get('TYPE')=='untyped' and entry.get('LINE'):
        entry['TYPE'] = 'halfmoves'

def read(path):
    state = 'WAITING'
    entry = {}
    result = []
    lineNum = 0
    for line in open(path, 'r').readlines():
        lineNum += 1
        line = line.strip()
        if line=='' or line.isspace():
            if state == 'WAITING':
                pass
            else:
                special_handle_defaults(entry)
                result.append(entry)
                state = 'WAITING'
        elif line.startswith('#'):
            continue
        elif m := re.match(r'^([A-Z]+):\s*(.*)$', line):
            name, value = m.group(1, 2)

            if state == 'WAITING':
                # default values
                entry = {   'TYPE': 'untyped',
                            'FEN': '',
                            'FRONT': '(blank)',
                            'BACK': '(blank)',
                            'LEITNER': '0, ' + time.strftime('%Y-%m-%d %H:%M:%S', time.localtime()),
                            'lineNum': lineNum
                        }
                state = 'BUSY'

            entry[name] = value

    if state != 'WAITING':
        special_handle_defaults(entry)
        result.append(entry)

    return result

def write(dbinfo, path):
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
