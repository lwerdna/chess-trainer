#!/usr/bin/env python

import sys
import time
import random

import chess
import chess.engine

import debug
import database
import evaluation

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QLineEdit, QDialog, QDialogButtonBox, QLabel, QPlainTextEdit, QSizePolicy, QTextEdit

from board import ChessBoard

import pgnfile
from common import *

#------------------------------------------------------------------------------
# LOGIC
#------------------------------------------------------------------------------

window = None
dbinfo = None

problem_index = None

solution_state = {
    'type': None,
    'stage': 'INIT', # INIT, SUCCESS, FAILURE, PLAYING
    'halfmove_index': 0,
    'player_color': None
}

def select_problem(replay=False):
    global window
    global problem_index
    global solution_state

    # collect problems that are due
    due_indices = []
    now = int(time.time())
    for i, entry in enumerate(dbinfo):
        due = entry['LEITNER'][1]
        #print(f'comparing {now} >= {due} for entry at line {entry["lineNum"]}')
        if now >= due:
            #print('DUE!')
            due_indices.append(i)
        else:
            print('NOT!')
    due_indices = [i for i, entry in enumerate(dbinfo) if entry['LEITNER'][1] < int(time.time())]

    print(due_indices)
    if not due_indices:
        return False

    # grab one at random
    problem_index = random.choice(due_indices)
    problem = dbinfo[problem_index]

    #print(f'selected problem from line number: {problem["lineNum"]}')
    window.frame.frontText.setText(problem['FRONT'])

    board = window.frame.board

    board.set_fen(problem['FEN'])
    board.setPerspective(board.model.turn)
    board.update_view()

    solution_state = {
        'stage': 'PLAYING',
        'type': problem['TYPE'],
        'problem': problem,
        'player_color': board.model.turn,
        'halfmove_index': 0
    }

    #if 'AUTO_PROMOTE' in problem.headers:
    #    board.auto_promote_to = chess.Piece.from_symbol(problem.headers['AUTO_PROMOTE']).piece_type
    #else:
    #    board.auto_promote_to = None

    #board.set_fen(problem.headers['FEN'])
    #board.update_view()

    return True

def post_problem_interaction(board):
    global dbinfo
    global problem_index

    problem = dbinfo[problem_index]

    # restore the board to the original problem state
    board.set_fen(problem['FEN'])
    board.update_view()

    # pop up dialog
    dlg = DoneDialog(board)
    dlg.setWindowTitle('DoneDialog')

    text = problem['BACK']
    text = text.replace('\\n', '\n')

    dlg.textEdit.setPlainText(text)
    dlg.exec()

    result = dlg.result
    print(f'got click result: {result}')

    # save any edited text
    text = dlg.textEdit.toPlainText()
    text = text.replace('\n', '\\n') # actual newline to '\', 'n'
    dbinfo[problem_index]['BACK'] = text

# callbacks
def on_move_request(board, move):
    global problem_index
    #print(f'MOVE REQUEST: {move} board state: {board.get_fen()}')
    return True

def on_move_complete(board, move):
    global problem_index
    global solution_state

    #print(f'MOVE COMPLETE: {move} board state: {board.get_fen()}')

    problem_type = solution_state['type']

    # GAME ENDED!
    outcome = board.model.outcome()
    if outcome == None:
        pass
    elif outcome.termination == chess.Termination.CHECKMATE:
        # in all problem types, achieving checkmate is considered success
        if outcome.winner == player_color:
            print('SUCCESS: checkmate detected')
            solution_state['stage'] = 'SUCCESS'
    else:
        if problem_type == 'checkmate_or_promote_to_queen':
            print('FAILURE: non-checkmate outcome detected')
            board.model.pop()
            return

    # EVALUATION-INDEPENDENT WIN CONDITIONS

    # did the player promote to queen?
    if problem_type == 'checkmate_or_promote_to_queen':
        if move.promotion == chess.QUEEN:
            print('SUCCESS:: queen promotion detected')
            solution_state['stage'] = 'SUCCESS'

    # EVALUATION-DEPENDENT WIN/LOSS CONDITIONS
#    bcopy = board.model.copy()
#    debug.breakpoint()
#    bcopy.pop() # undo user move
#    reply, score = evaluation.best_reply_to(bcopy, move)
#

    # user has to make one side's halfmoves
    if problem_type == 'halfmoves':
        # did he make the last
        lastmove = last_move_as_san(board.model)
        print(f'last move: {lastmove}')

        line_moves = line_to_moves(dbinfo[problem_index]['LINE'])
        expect_move = line_moves[solution_state['halfmove_index']]

        #print(f'line moves: {line_moves}')
        #print(f'halfmove_index: {solution_state["halfmove_index"]}')
        #print(f'expect move: {expect_move}')

        if lastmove != expect_move:
            #solution_state['stage'] = 'FAILURE'
            board.model.pop()
        elif solution_state['halfmove_index'] == len(line_moves)-1:
            solution_state['stage'] = 'SUCCESS'
        else:
            solution_state['halfmove_index'] += 1
            board.model.push_san(line_moves[solution_state['halfmove_index']])
            solution_state['halfmove_index'] += 1
    elif problem_type == 'checkmate_or_promote_to_queen':
        # select opponent reply
        reply = evaluation.bestmove(board.model)
        print(f'evaluation.evaluate() returned {reply}')

        #print(f'found opponent reply: {reply}')
        board.model.push(reply)
        board.update_view()

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
    if solution_state['stage'] == 'SUCCESS':
        post_problem_interaction(board)
        select_problem()

def on_board_init(board):
    global dbinfo

    evaluation.init()

    dbinfo = database.read()

    board.set_mode('game')
    board.set_move_request_callback(on_move_request)
    board.set_move_complete_callback(on_move_complete)


def on_exit():
    global dbinfo
    print('on_exit')
    database.write(dbinfo)
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
        self.board.set_mode_free()

        # initiate logic
        on_board_init(self.board)

class Window(QMainWindow):
    def __init__(self):
        super().__init__()

        self.frame = TestFrame(self)

        # Set window details
        self.setCentralWidget(self.frame)
        self.setWindowTitle("Chess")
        self.setWindowIcon(QIcon('./assets/icons/pawn_icon.png'))
        self.setMinimumSize(900, 900)
        self.show()

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
    window = Window()

    select_problem()

    sys.exit(app.exec_())  # Start main event loop


