#!/usr/bin/env python

import sys
import time
import random

import chess
import chess.engine

import debug
import history

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

    # pop up dialog
    dlg = DoneDialog(cboard)

    dlg.exec()

    result = dlg.result
    print(f'got result: {result}')

    now = int(time.time())
    if result != None:
        match result:
            case 'minute':
                due_epoch = now + 60
            case 'day':
                due_epoch = now + 24*60*60
            case 'week':
                due_epoch = now + 7*24*60*60
            case 'month':
                due_epoch = now + 4*7*24*60*60
            case 'year':
                due_epoch = now + 365*24*60*60

        time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(due_epoch))
        print(f'next due date: {time_str}')

        history.update_problem(problem_state.problem, due_epoch)

    # now filter the problems that are due (possibly getting rid of this current one)
    problems = [p for p in problems if history.is_due(p)]

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
    history.store()
    evaluation.exit()

#------------------------------------------------------------------------------
# GUI
#------------------------------------------------------------------------------

class DoneDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)

        self.setWindowTitle("Review")

        vLayout = QVBoxLayout()

        # text edit
        #self.textEdit = QTextEdit(self)
        #vLayout.addWidget(self.textEdit)

        # the buttons
        hLayout = QHBoxLayout()

        b = QPushButton(f'1 minute', self)
        b.clicked.connect(self.clickedMinute)
        hLayout.addWidget(b)
        b = QPushButton(f'1 day', self)
        b.clicked.connect(self.clickedDay)
        hLayout.addWidget(b)
        b = QPushButton(f'1 week', self)
        b.clicked.connect(self.clickedWeek)
        hLayout.addWidget(b)
        b = QPushButton(f'1 month', self)
        b.clicked.connect(self.clickedMonth)
        hLayout.addWidget(b)
        b = QPushButton(f'1 year', self)
        b.clicked.connect(self.clickedYear)
        hLayout.addWidget(b)

        vLayout.addLayout(hLayout)

        # done
        self.setLayout(vLayout)

        #
        self.result = None

    def clickedMinute(self, text):
        self.result = 'minute'
        self.close()

    def clickedDay(self, text):
        self.result = 'day'
        self.close()

    def clickedWeek(self, text):
        self.result = 'week'
        self.close()

    def clickedMonth(self, text):
        self.result = 'month'
        self.close()

    def clickedYear(self, text):
        self.result = 'year'
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
    history.load()

    # load all problems
    problems = problem_finder.get_problems()

    # ensure they're all tracked in our SRS
    for problem in problems:
        history.add_problem(problem)

    # now filter the problems that are due
    problems = [p for p in problems if history.is_due(p)]

    sys.excepthook = except_hook
    app = QApplication(sys.argv)
    window = MyWindow()

    select_problem()

    sys.exit(app.exec_())  # Start main event loop

