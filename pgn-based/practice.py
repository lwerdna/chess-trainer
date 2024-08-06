#!/usr/bin/env python

import os
import sys
import time
import random

import chess
import chess.engine

import debug
import history

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QLineEdit, QDialog, QDialogButtonBox, QLabel, QPlainTextEdit, QSizePolicy, QTextEdit

from cboard import ChessBoard

import problem_finder
from problemstate import *
from common import *

#------------------------------------------------------------------------------
# LOGIC
#------------------------------------------------------------------------------

window = None
pgn_paths = None
current_pgn = None
problem_state = None

def select_pgn(replay=False):
    global window
    global pgn_path
    global pgn_paths
    global problem_state

    # grab one at random
    if not pgn_paths:
        print('ERROR: no pgn paths!')
        return;
    else:
        pgn_path = random.choice(pgn_paths)

    # create the problem state
    print(f'loading PGN: {pgn_path}')
    current_pgn = os.path.basename(pgn_path)
    problem_state = VanillaPgnProblemState(pgn_path)

    # update the chessboard on the UI
    cboard = window.frame.board
    problem_state.initialize_chessboard(cboard)

    # update the text
    window.frame.frontText.setText(problem_state.get_message())

    return True

def post_problem_interaction(cboard):
    global window
    global pgn_path
    global pgn_paths
    global problem_state

    # restore the cboard to the original problem state
    cboard = window.frame.board
    problem_state.initialize_chessboard(cboard)

    # pop up dialog
    dlg = DoneDialog(cboard, pgn_path)

    dlg.exec()

    result = dlg.result
    print(f'got result: {result}')

    now = int(time.time())
    if result != None:
        minute = 60
        hour = 60*minute
        day = 24*hour
        week = 7*day
        month = 4*week
        year = 365*day
        match result:
            case 'minute':
                due_epoch = now + minute
            case 'day':
                due_epoch = now + 24*hour + random.randint(-hour, hour)
            case 'week':
                due_epoch = now + 7*day + random.randint(-day, day)
            case 'month':
                due_epoch = now + 4*week + random.randint(-3*day, 3*day)
            case 'year':
                due_epoch = now + year + random.randint(-month, month)

        time_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(due_epoch))
        print(f'next due date: {time_str}')

        history.update_pgn(pgn_path, due_epoch)

    # remove this problem if it's no longer due
    if not history.is_due(pgn_path):
        pgn_paths.remove(pgn_path)

    pgn_path = None
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
        problem_state.update_move(move, cboard, lambda msg: window.frame.frontText.setText(msg))
    else:
        cboard.undo_glide()

    # is problem finished?
    if problem_state.is_done():
        post_problem_interaction(cboard)
        remaining = select_pgn()
        if not remaining:
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
    def __init__(self, parent, pgn_path):
        super().__init__(parent)

        self.setWindowTitle("Review")

        vLayout = QVBoxLayout()

        self.pgn_path = os.path.abspath(pgn_path)

        # path to PGN
        text_pgn_path = QLineEdit(self)
        text_pgn_path.setReadOnly(True);
        text_pgn_path.setText(self.pgn_path)
        #text_pgn_path.setEnabled(False)
        vLayout.addWidget(text_pgn_path)

        text_fen_string = QLineEdit(self)
        text_fen_string.setReadOnly(True)
        game = chess.pgn.read_game(open(self.pgn_path))
        text_fen_string.setText(game.board().fen())
        vLayout.addWidget(text_fen_string)

        #label = QLabel()
        #label.setText(f'<a href="{url}">{url}</a>')
        #label.setTextFormat(Qt.RichText)
        #label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        #label.setOpenExternalLinks(True)

        b = QPushButton('Open in ChessX', self)
        b.clicked.connect(self.clickedChessX)
        vLayout.addWidget(b)

        b = QPushButton('Open in VIM', self)
        b.clicked.connect(self.clickedVim)
        vLayout.addWidget(b)

        # text edit
        self.lastComment = QPlainTextEdit(self)
        #self.lastComment = QTextEdit(self)
        vLayout.addWidget(self.lastComment)

        #
        node = game
        while node.variations:
            node = node.variations[0]
        self.lastComment.setPlainText(node.comment)

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

    def clickedChessX(self, text):
        #os.system('/Applications/chessx.app/Contents/MacOS/chessx ' + self.pgn_path)
        arg0 = '/Applications/chessx.app/Contents/MacOS/chessx'
        arg1 = self.pgn_path
        print(f'launching {arg0} {arg1}')
        os.spawnv(os.P_NOWAIT, arg0, [arg0, arg1])

    def clickedVim(self, text):
        arg0 = '/Applications/MacVim.app/Contents/bin/gvim'
        arg1 = self.pgn_path
        print(f'launching {arg0} {arg1}')
        os.spawnv(os.P_NOWAIT, arg0, [arg0, arg1])

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

    def closeEvent(self, event):
        if self.lastComment.document().isModified():
            print(f'writing to {self.pgn_path}')
            # reopen the PGN
            game = chess.pgn.read_game(open(self.pgn_path))
            # skip to last node
            node = game
            while node.variations:
                node = node.variations[0]
            # set the comment
            node.comment = self.lastComment.toPlainText()
            # write
            print(game, file=open(self.pgn_path, 'w'), end='\n\n')
        else:
            print(f'no changes to {self.pgn_path}')

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

    pgn_path = None
    if sys.argv[1:]:
        if sys.argv[1].endswith('.pgn'):
            pgn_path = sys.argv[1]

    # load pgn's
    if pgn_path:
        pgn_paths = [pgn_path]
    else:
        pgn_paths = []
        for root, dirnames, filenames in os.walk('./problems'):
            for filename in filenames:
                if filename.endswith('.pgn'):
                    fpath = os.path.join(root, filename)
                    pgn_paths.append(fpath)

    print('pgn paths:')
    print('\n'.join(pgn_paths))

    # ensure they're all tracked in our SRS
    for pgn in pgn_paths:
        history.add_pgn(pgn)

    # now filter the pgn_paths that are due
    if '--force' in sys.argv[1:] or (sys.argv[1:] and sys.argv[1].endswith('.pgn')):
        pass
    else:
        pgn_paths = [p for p in pgn_paths if history.is_due(p)]

    sys.excepthook = except_hook
    app = QApplication(sys.argv)
    window = MyWindow()

    select_pgn()

    sys.exit(app.exec_())  # Start main event loop

