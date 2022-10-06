#!/usr/bin/env python

import sys

import chess
import chess.engine

import debug

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QWidget

from board import ChessBoard

#------------------------------------------------------------------------------
# LOGIC
#------------------------------------------------------------------------------

def on_move_request(board, move):
    print(f'MOVE REQUEST: {move} board state: {board.get_fen()}')
    return True

engine = None
def on_move_complete(board, move):
    global engine

    print(f'MOVE COMPLETE: {move} board state: {board.get_fen()}')
    
    if not engine:
        engine = chess.engine.SimpleEngine.popen_uci('/usr/local/bin/stockfish')

    result = engine.play(board.model, chess.engine.Limit(time=0.1))
    board.model.push(result.move)
    board.update_view()

pickup = ''
mode = ''
def on_board_init(board):
    global mode, pickup
    mode = 'game'
    pickup = 'white'
    board.set_mode(mode)
    board.set_fen(chess.STARTING_BOARD_FEN)
    board.update_view()
        
    board.set_move_request_callback(on_move_request)
    board.set_move_complete_callback(on_move_complete)

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


