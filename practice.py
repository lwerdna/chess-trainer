#!/usr/bin/env python

import sys
import time
import random

import chess
import chess.engine

import debug
import spaced_repetition

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QLineEdit, QDialog, QDialogButtonBox, QLabel, QPlainTextEdit, QSizePolicy, QTextEdit

from cboard import ChessBoard

import pgnfile

import problem_finder
from problemstate import *
from common import *

#------------------------------------------------------------------------------
# LOGIC
#------------------------------------------------------------------------------

window = None
problems = None
problem_state = None

def select_problem(replay=False):
    global window
    global problems
    global problem_state

    # grab one at random
    problem = random.choice(problems)

    #print(f'selected problem from line number: {problem["lineNum"]}')
    if 'question' in problem:
        window.frame.frontText.setText(problem['question'])

    problem_state = FollowVariationsProblemState(problem)

    cboard = window.frame.board

    problem_state.initialize_chessboard(cboard)

    return True

def post_problem_interaction(cboard):
    global problems
    global problem_state

    # restore the cboard to the original problem state
    cboard.set_fen(problem_state.problem['fen'])
    cboard.update_view()

    # calculate new times

    boxes, due_times = spaced_repetition.calc_due_times(problem)

    # pop up dialog
    dlg = DoneDialog(cboard, due_times)

    dlg.exec()

    result = dlg.result
    print(f'got result: {result}')

    if result != None:
        match result:
            case 'terrible':
                box = boxes[0]
                due_epoch = due_times[0]
            case 'bad':
                box = boxes[1]
                due_epoch = due_times[1]
            case 'ok':
                box = boxes[2]
                due_epoch = due_times[2]
            case 'good':
                box = boxes[3]
                due_epoch = due_times[3]
            case 'easy':
                box = boxes[4]
                due_epoch = due_times[4]

        time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(due_epoch))
        print(f'next due date: {time_str}')

        spaced_repetition.update_problem(problem_state.problem, box, due_epoch)

    # now filter the problems that are due (possibly getting rid of this current one)
    problems = [p for p in problems if spaced_repetition.is_due(p)]

    problem_state = None

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

def on_board_init(board):
    evaluation.init()

    board.set_mode('game')
    board.set_move_request_callback(on_move_request)
    board.set_move_complete_callback(on_move_complete)


def on_exit():
    print('on_exit')
    spaced_repetition.store()
    evaluation.exit()

#------------------------------------------------------------------------------
# GUI
#------------------------------------------------------------------------------

class DoneDialog(QDialog):
    def __init__(self, parent, due_times):
        super().__init__(parent)

        self.setWindowTitle("Review")

        vLayout = QVBoxLayout()

        # text edit
        self.textEdit = QTextEdit(self)
        vLayout.addWidget(self.textEdit)

        # the buttons
        hLayout = QHBoxLayout()

        now = int(time.time())
        durstrs = [spaced_repetition.duration_string(dt - now) for dt in due_times]

        b = QPushButton(f'terrible ({durstrs[0]})', self)
        b.clicked.connect(self.clickedTerrible)
        hLayout.addWidget(b)
        b = QPushButton(f'bad ({durstrs[1]})', self)
        b.clicked.connect(self.clickedBad)
        hLayout.addWidget(b)
        b = QPushButton(f'ok ({durstrs[2]})', self)
        b.clicked.connect(self.clickedOk)
        hLayout.addWidget(b)
        b = QPushButton(f'good ({durstrs[3]})', self)
        b.clicked.connect(self.clickedGood)
        hLayout.addWidget(b)
        b = QPushButton(f'easy ({durstrs[4]})', self)
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
    if 0:
        foo = {'key': {'leitner':'whatever', 'due':'whatever'}}
        import json
        with open('srs.json', 'w') as fp:
            fp.write(json.dumps(foo, indent=4))
        sys.exit(0)

    spaced_repetition.load()

    # load all problems
    problems = problem_finder.get_problems()

    # ensure they're all tracked in our SRS
    for problem in problems:
        spaced_repetition.add_problem(problem)

    # now filter the problems that are due
    problems = [p for p in problems if spaced_repetition.is_due(p)]

    sys.excepthook = except_hook
    app = QApplication(sys.argv)
    window = MyWindow()

    select_problem()

    sys.exit(app.exec_())  # Start main event loop

