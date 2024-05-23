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
from PyQt5.QtWidgets import QApplication, QMainWindow, QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QLineEdit

from board import ChessBoard

import pgnfile
from common import *

#------------------------------------------------------------------------------
# LOGIC
#------------------------------------------------------------------------------

window = None
dbinfo = None

problem_context = {
    'problem': None,
    'type': None,
    'state': 'INIT', # INIT, SUCCESS, FAILURE, PLAYING
    'halfmove_index': 0,
    'player_color': None
}

def select_problem(replay=False):
    global window
    global problem_context

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
    problem = dbinfo[random.choice(due_indices)]
    #problem = dbinfo[3]

    print(f'selected problem from line number: {problem["lineNum"]}')

    window.frame.frontText.setText(problem['FRONT'])
    window.frame.backText.setText(problem['BACK'])

    board = window.frame.board

    board.set_fen(problem['FEN'])
    board.setPerspective(board.model.turn)
    board.update_view()

    problem_context = {
        'state': 'PLAYING',
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

# callbacks
state = 'ONE'
def on_move_request(board, move):
    #print(f'MOVE REQUEST: {move} board state: {board.get_fen()}')
    return True

def on_move_complete(board, move):
    global problem_context

    #print(f'MOVE COMPLETE: {move} board state: {board.get_fen()}')

    problem_type = problem_context['type']

    # did player win?
#    outcome = board.model.outcome()
#    if outcome == None:
#        pass
#    elif outcome.termination == chess.Termination.CHECKMATE:
#        if outcome.winner == player_color:
#            print('SUCCESS: checkmate detected')
#            state = 'SUCCESS'
#    else:
#        if problem_type == 'checkmate_or_promote_to_queen':
#            print('FAILURE: non-checkmate outcome detected')
#            state = 'FAILURE'

    # EVALUATION-INDEPENDENT WIN CONDITIONS

    # did the player promote to queen?
#    if problem_type == 'checkmate_or_promote_to_queen':
#        if move.promotion == chess.QUEEN:
#            print('SUCCESS:: queen promotion detected')
#            state = 'SUCCESS'

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

        line_moves = line_to_moves(problem_context['problem']['LINE'])
        expect_move = line_moves[problem_context['halfmove_index']]

        print(f'line moves: {line_moves}')
        print(f'halfmove_index: {problem_context["halfmove_index"]}')

        print(f'expect move: {expect_move}')

        if lastmove != expect_move:
            #problem_context['state'] = 'FAILURE'
            board.model.pop()
        elif problem_context['halfmove_index'] == len(line_moves)-1:
            problem_context['state'] = 'SUCCESS'
        else:
            problem_context['halfmove_index'] += 1
            board.model.push_san(line_moves[problem_context['halfmove_index']])
            problem_context['halfmove_index'] += 1

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
    ok = True
    match problem_context['state']:
        case 'FAILURE':
            # update PGN
            #problem.headers['RECORD'] = problem.headers.get('RECORD', '') + 'L'
            print('FAILURE')
            ok = select_problem()
        case 'SUCCESS':
            # update PGN
            #problem.headers['RECORD'] = problem.headers.get('RECORD', '') + 'W'
            print('SUCCESS')
            ok = select_problem()
        case 'PLAYING':
            # select opponent reply
            #print(f'evaluation.evaluate() returned {reply0}')
            #reply1 = evaluation.bestmove(board.model)

            #print(f'found opponent reply: {reply}')
            #board.model.push(reply)
            #board.update_view()
            #moves += 1
            print('PLAYING')

        case _:
            debug.breakpoint()

    if not ok:
        print('NOT OK!')

def on_board_init(board):
    global dbinfo

    evaluation.init()

    dbinfo = database.read()

    board.set_mode('game')
    board.set_move_request_callback(on_move_request)
    board.set_move_complete_callback(on_move_complete)


def on_exit():
    #database.write(dbinfo)
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

        self.frontText = QLineEdit()
        l.addWidget(self.frontText)

        self.board = ChessBoard(self)
        l.addWidget(self.board)

        self.backText = QLineEdit()
        l.addWidget(self.backText)

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


