#!/usr/bin/env python

import sys
import time
import random

import chess
import chess.engine

import debug
import database

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QLineEdit, QDialog, QDialogButtonBox, QLabel, QPlainTextEdit, QSizePolicy, QTextEdit

from cboard import ChessBoard

import pgnfile
from problemstate import *
from common import *

#------------------------------------------------------------------------------
# LOGIC
#------------------------------------------------------------------------------

window = None
dbinfo = None

problem_index = None
problem_state = None

def select_problem(replay=False):
    global window
    global problem_index
    global problem_state

    # collect problems that are ue
    due_indices = []
    now = int(time.time())
    for i, entry in enumerate(dbinfo):
        box, due = entry['LEITNER']
        print(f'comparing {now} >= {due} for entry at line {entry["lineNum"]}')
        if now >= due:
            due_indices.append(i)

    print(f'due indices: {due_indices}')
    if not due_indices:
        return False

    # grab one at random
    problem_index = random.choice(due_indices)
    problem = dbinfo[problem_index]

    #print(f'selected problem from line number: {problem["lineNum"]}')
    window.frame.frontText.setText(problem['FRONT'])

    problem_state = create_problem_state_from_db_data(problem)

    cboard = window.frame.board

    problem_state.initialize_chessboard(cboard)

    #if 'AUTO_PROMOTE' in problem.headers:
    #    board.auto_promote_to = chess.Piece.from_symbol(problem.headers['AUTO_PROMOTE']).piece_type
    #else:
    #    board.auto_promote_to = None

    #board.set_fen(problem.headers['FEN'])
    #board.update_view()

    return True

def post_problem_interaction(cboard):
    global dbinfo
    global problem_index

    problem = dbinfo[problem_index]

    # restore the cboard to the original problem state
    cboard.set_fen(problem['FEN'])
    cboard.update_view()

    # pop up dialog
    dlg = DoneDialog(cboard)
    dlg.setWindowTitle('DoneDialog')

    text = problem['BACK']
    text = text.replace('\\n', '\n')

    dlg.textEdit.setPlainText(text)
    dlg.exec()

    result = dlg.result
    print(f'got click result: {result}')

    box, due = problem['LEITNER']
    match result:
        case 'terrible':
            box = 0
        case 'bad':
            box = box-1
        case 'ok':
            box = max(box, 1)
        case 'good':
            box = box+1
        case 'easy':
            box = box+2

    now_epoch = int(time.time())
    due_epoch = now_epoch + 10*60 * 5**(box)

    time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(due_epoch))
    print(f'next due date: {time_str}')

    problem['LEITNER'] = box, due_epoch

    # save any edited text
    text = dlg.textEdit.toPlainText()
    text = text.replace('\n', '\\n') # actual newline to '\', 'n'
    dbinfo[problem_index]['BACK'] = text

# callbacks
def on_move_request(board, move):
    global problem_index
    #print(f'MOVE REQUEST: {move} board st ate: {board.get_fen()}')
    return True

def on_move_complete(cboard, move):
    global problem_index
    global problem_state

    # consume move
    if problem_state.test_move(move):
        problem_state.update_move(move, cboard)
    else:
        cboard.undo_glide()

    # is problem finished?
    if problem_state.is_done():
        post_problem_interaction(cboard)
        problems_remaining = select_problem()
        if not problems_remaining:
            print(f'TODO: close app, problems done!')

def on_move_complete2(board, move):
    global problem_index
    global problem_state

    #print(f'MOVE COMPLETE: {move} board state: {board.get_fen()}')

    problem_type = problem_state['type']

    # GAME ENDED!
    outcome = board.model.outcome()
    if outcome == None:
        pass
    elif outcome.termination == chess.Termination.CHECKMATE:
        # in all problem types, achieving checkmate is considered success
        if outcome.winner == problem_state['player_color']:
            print('SUCCESS: checkmate detected')
            problem_state['stage'] = 'SUCCESS'
    else:
        if problem_type == 'checkmate_or_promote_to_queen':
            print('FAILURE: non-checkmate outcome detected')
            board.model.pop()
            return



    # EVALUATION-DEPENDENT WIN/LOSS CONDITIONS
#    bcopy = board.model.copy()
#    debug.breakpoint()
#    bcopy.pop() # undo user move
#    reply, score = evaluation.best_reply_to(bcopy, move)
#

    if problem_type == 'checkmate_or_promote_to_queen':
        # select opponent reply
        reply_move = evaluation.bestmove(board.model)
        reply_san = move_as_san(board.model, reply_move)
        print(f'evaluation.evaluate() returned {reply_san}')
        board.move_glide(reply_san)

#    if problem_type == 'draw_kk_or_repetition':
#        if not evaluation.is_even(score):
#            print('FAILURE: non-drawing board detected')
#            print(f'{board.get_fen()} has evaluation {score} after {reply}')
#            #debug.breakpoint()
#            state = 'FAILURE'
#        elif only_kings(board.model):
#            print('SUCCESS: draw with only kings')
#            state = 'SUCCESS'
#        elif board.model.can_claim_threefold_repetition():
#            print(f'SUCCESS: draw by threefold repetition')
#            state = 'SUCCESS'
#        else:
#            # player continues
#            pass
#    elif problem_type == 'checkmate_or_promote_to_queen':
#        if not is_winning(score):
#            print('FAILURE: non-winning board detected')
#    elif m := re.match(r'^PlayBest(\d+)$', problem_type):
#        moves_needed = int(m.group(1))
#    else:
#        debug.breakpoint()

    #print(f'logic state: {state}')
    if problem_state['stage'] == 'SUCCESS':
        post_problem_interaction(board)
        problems_remaining = select_problem()
        if not problems_remaining:
            print(f'TODO: close app, problems done!')

def on_board_init(board):
    global dbinfo

    evaluation.init()

    path = sys.argv[1] if sys.argv[1:] else 'database.txt'
    dbinfo = database.read(path)

    board.set_mode('game')
    board.set_move_request_callback(on_move_request)
    board.set_move_complete_callback(on_move_complete)


def on_exit():
    global dbinfo
    print('on_exit')
    path = sys.argv[1] if sys.argv[1:] else 'database.txt'
    database.write(dbinfo, path)
    evaluation.exit()

#------------------------------------------------------------------------------
# GUI
#------------------------------------------------------------------------------

class DoneDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Review")

        vLayout = QVBoxLayout()

        # text edit
        self.textEdit = QTextEdit(self)
        vLayout.addWidget(self.textEdit)

        # the buttons
        hLayout = QHBoxLayout()
        b = QPushButton('terrible', self)
        b.clicked.connect(self.clickedTerrible)
        hLayout.addWidget(b)
        b = QPushButton('bad', self)
        b.clicked.connect(self.clickedBad)
        hLayout.addWidget(b)
        b = QPushButton('ok', self)
        b.clicked.connect(self.clickedOk)
        hLayout.addWidget(b)
        b = QPushButton('good', self)
        b.clicked.connect(self.clickedGood)
        hLayout.addWidget(b)
        b = QPushButton('easy', self)
        b.clicked.connect(self.clickedEasy)
        hLayout.addWidget(b)

        vLayout.addLayout(hLayout)

        # done
        self.setLayout(vLayout)

        #
        self.result = None

    def clickedTerrible(self, text):
        self.result = 'terrible'
        self.close()

    def clickedBad(self, text):
        self.result = 'bad'
        self.close()

    def clickedOk(self, text):
        self.result = 'ok'
        self.close()

    def clickedGood(self, text):
        self.result = 'good'
        self.close()

    def clickedEasy(self, text):
        self.result = 'easy'
        self.close()

class TestFrame(QFrame):
    def __init__(self, parent):
        super().__init__()

        self.parent = parent

        #self.setStyleSheet('background-color: #4B4945')

        l = QVBoxLayout()

        self.frontText = QLineEdit()
        l.addWidget(self.frontText)

        self.board = ChessBoard(self)
        l.addWidget(self.board)

        self.setLayout(l)

        # setup board
        #self.board.set_mode_free()

class MyWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.board_init_called = False

        self.frame = TestFrame(self)

        # Set window details
        self.setCentralWidget(self.frame)
        self.setWindowTitle("Chess")
        self.setWindowIcon(QIcon('./assets/icons/pawn_icon.png'))
        self.setMinimumSize(900, 900)
        self.show()

    def event(self, event):
        #print(event.type())
        if self.board_init_called == False:
            on_board_init(self.frame.board)
            self.board_init_called = True

        return super(MyWindow, self).event(event)

    def closeEvent(self, event):
        print('CLOSING!')
        on_exit()

def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)

#------------------------------------------------------------------------------
# MAIN
#------------------------------------------------------------------------------

if __name__ == '__main__':
    sys.excepthook = except_hook
    app = QApplication(sys.argv)
    window = MyWindow()

    select_problem()

    sys.exit(app.exec_())  # Start main event loop


