#!/usr/bin/env python

import sys
import random

import chess
import chess.engine

import evaluation
import debug

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QWidget

from board import ChessBoard

import pgnfile

#------------------------------------------------------------------------------
# LOGIC
#------------------------------------------------------------------------------

state = 'INIT' # INIT, WON, LOST, PLAYING
moves = 0
database = None
problem = None
player_color = None

def is_winning(score):
    match type(score):
        case chess.engine.Mate: return True
        case chess.engine.Cp: return score.score() > 10
        case _: assert False

def select_problem(board, replay=False):
    global problem, state, player_color, moves

    if replay:
        pass
    else:
        problem = random.choice(database)

    if 'AUTO_PROMOTE' in problem.headers:
        board.auto_promote_to = chess.Piece.from_symbol(problem.headers['AUTO_PROMOTE']).piece_type
    else:
        board.auto_promote_to = None

    board.set_fen(problem.headers['FEN'])
    board.update_view()

    player_color = board.model.turn
    state = 'PLAYING'
    moves = 0
    #print(f'selected problem: {problem}')

# callbacks
state = 'ONE'
def on_move_request(board, move):
    #print(f'MOVE REQUEST: {move} board state: {board.get_fen()}')
    return True

def on_move_complete(board, move):
    global state, player_color, problem, moves

    #print(f'MOVE COMPLETE: {move} board state: {board.get_fen()}')

    problem_type = problem.headers.get('PROBLEM_TYPE')

    # did player win?
    outcome = board.model.outcome()
    if outcome == None:
        pass
    elif outcome.termination == chess.Termination.CHECKMATE:
        if outcome.winner == player_color:
            print('WON: checkmate detected')
            state = 'WON'
    else:
        if problem_type == 'checkmate_or_promote_to_queen':
            print('LOST: non-checkmate outcome detected')
            state = 'LOST'

    # EVALUATION-INDEPENDENT WIN CONDITIONS

    # did the player promote to queen?
    if problem_type == 'checkmate_or_promote_to_queen':
        if move.promotion == chess.QUEEN:
            print('WON:: queen promotion detected')
            state = 'WON'

    # EVALUATION-DEPENDENT WIN/LOSS CONDITIONS
    bcopy = board.model.copy()
    bcopy.pop()
    (reply, score) = evaluation.best_reply_to(bcopy, move)

    if problem_type == 'draw_for_three_moves':
        if not evaluation.is_even(score):
            print('LOST: non-drawing board detected')
            state = 'LOST'
        else:
            if moves >= 2:
                print('WON: kept drawing evaluation for 3 moves')
                state = 'WON'
            else:
                print(f'keep going')
    elif problem_type == 'checkmate_or_promote_to_queen':
        if not is_winning(score):
            print('LOST: non-winning board detected')
    else:
        debug.breakpoint()


    #print(f'logic state: {state}')

    match state:
        case 'LOST':
            # update PGN
            problem.headers['RECORD'] = problem.headers.get('RECORD', '') + 'L'
            select_problem(board, True)
        case 'WON':
            # update PGN
            problem.headers['RECORD'] = problem.headers.get('RECORD', '') + 'W'
            select_problem(board)
        case 'PLAYING':
            # select opponent reply
            #print(f'evaluation.evaluate() returned {reply0}')
            #reply1 = evaluation.bestmove(board.model)

            #print(f'found opponent reply: {reply}')
            board.model.push(reply)
            board.update_view()
            moves += 1

        case _:
            debug.breakpoint()

def on_board_init(board):
    global database

    evaluation.init()

    database = pgnfile.PgnFile(sys.argv[1])

    board.set_mode('game')
    board.set_move_request_callback(on_move_request)
    board.set_move_complete_callback(on_move_complete)

    select_problem(board)

def on_exit():
    database.write()

    evaluation.exit()

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


