import time

def is_due(leitner_entry):
    box, due = leitner_entry
    now = int(time.time())
    return now >= due

def calc_due_time(box):
    now = int(time.time())
    return now + 24*60*60 * (.8 * box)**2

def calc_due_times(current_box):
    now = int(time.time())
    result = []

    box_bottom = max(current_box - 2, 0)
    for box in range(box_bottom, box_bottom+5):
        result.append(calc_due_time(box))

    return result

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

