#!/usr/bin/env python

import sys

import chess

import debug

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, QMainWindow, QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QWidget

import board

#------------------------------------------------------------------------------
# LOGIC
#------------------------------------------------------------------------------

def on_move_request(board, move):
    print(f'MOVE REQUEST: {move} board state: {board.get_fen()}')
    return True

def on_move_complete(board, move):
    print(f'MOVE COMPLETE: {move} board state: {board.get_fen()}')
    return True

def on_click_mode(board):
    global mode
    mode = {'free':'game', 'game':'free'}[mode]
    print(f'setting board mode to: {mode}')
    board.set_mode(mode)

def on_click_pickup(board):
    global pickup
    pickup = {'white':'black', 'black':'all', 'all':'none', 'none':'white'}[pickup]
    print(f'setting board mode to: {pickup}')
    board.set_pickup(pickup)

pickup = ''
mode = ''
def on_board_init(board):
    global mode, pickup
    mode = 'game'
    pickup = 'white'
    board.set_mode(mode)
    board.set_fen(chess.STARTING_BOARD_FEN)
    board.set_fen('8/PK5k/8/8/8/8/8/8 w - - 0 1')
    board.update_view()
        
    board.set_move_request_callback(on_move_request)
    board.set_move_complete_callback(on_move_complete)

#------------------------------------------------------------------------------
# GUI
#------------------------------------------------------------------------------

class TestFrame(QFrame):
    def __init__(self, parent):
        super().__init__()

        self.parent = parent

        self.setStyleSheet('background-color: #4B4945')

        buttons_widget = QWidget()
        l = QHBoxLayout()
        self.btn_mode = QPushButton('MODE')
        l.addWidget(self.btn_mode)
        self.btn_pickup = QPushButton('PICKUP')
        l.addWidget(self.btn_pickup)
        buttons_widget.setLayout(l)

        l = QVBoxLayout()
        self.board = board.ChessBoard(self)
        l.addWidget(buttons_widget)
        l.addWidget(self.board)
        self.setLayout(l)

        # setup board
        self.board.set_mode_free()

        # setup buttons
        self.btn_mode.clicked.connect(lambda: on_click_mode(self.board))
        self.btn_pickup.clicked.connect(lambda: on_click_pickup(self.board))

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
