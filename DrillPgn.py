#!/usr/bin/env python

import sys
import random

import chess
import chess.engine

import debug

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QWidget

from board import ChessBoard

import pgnfile

#------------------------------------------------------------------------------
# LOGIC
#------------------------------------------------------------------------------

state = 'INIT' # INIT, WON, LOST, PLAYING
database = None
problem = None
engine = None

def get_evaluation(model):
    global engine
    info = engine.analyse(model, chess.engine.Limit(time=.5))

    best_move = None
    if info.get('pv'):
        best_move = info.get('pv')[0]

    return (best_move, info['score'].white())

def is_winning(model):
    global engine
    (move, result) = get_evaluation(model)
    match type(result):
        case chess.engine.Mate: winning = True
        case chess.engine.Cp: winning = result.score() > 10
        case _: assert False
    return winning

def select_problem(board):
    global problem, state
    problem = random.choice(database)
    problem = database.games[79]
    board.set_fen(problem.headers['FEN'])
    board.update_view()
    state = 'PLAYING'
    print(f'selected problem: {problem}')

# callbacks
state = 'ONE'
def on_move_request(board, move):
    print(f'MOVE REQUEST: {move} board state: {board.get_fen()}')
    return True

def on_move_complete(board, move):
    global state
    global engine

    print(f'MOVE COMPLETE: {move} board state: {board.get_fen()}')
    
    # did player win?
    outcome = board.model.outcome()
    if outcome == None:
        pass
    elif outcome.termination == chess.CHECKMATE:
        if outcome.winner == chess.WHITE:
            print('white checkmate detected')
            state = 'WON'
    else:
        print('non checkmate outcome detected')
        state = 'LOST'
    
    # did the player promote to queen?
    if move.promotion == chess.QUEEN:
        print('queen promotion detected')
        state = 'WON'

    # did the evaluation remain a win?
    if not is_winning(board.model):
        print('non-winning board detected')
        state = 'LOST'

    print(f'logic state: {state}')

    match state:
        case 'LOST':
            # update PGN
            select_problem(board)
        case 'WON':
            # update PGN
            select_problem(board)
        case 'PLAYING':
            result = engine.play(board.model, chess.engine.Limit(time=0.1))
            board.model.push(result.move)
            board.update_view()
        case _:
            breakpoint()

def on_board_init(board):
    global engine
    global database

    engine = chess.engine.SimpleEngine.popen_uci("/usr/local/bin/stockfish")

    database = pgnfile.PgnFile(sys.argv[1])

    board.set_mode('game')
    board.set_move_request_callback(on_move_request)
    board.set_move_complete_callback(on_move_complete)

    select_problem(board)

def on_exit():
    global engine
    engine.quit()

#------------------------------------------------------------------------------
# GUI
#------------------------------------------------------------------------------

class TestFrame(QFrame):
    def __init__(self, parent):
        super().__init__()

        self.parent = parent

        self.setStyleSheet('background-color: #4B4945')

        l = QVBoxLayout()
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

        self.test_frame = TestFrame(self)

        # Set window details
        self.setCentralWidget(self.test_frame)
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
    sys.exit(app.exec_())  # Start main event loop


