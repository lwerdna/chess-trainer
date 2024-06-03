# class ChessBoard is for the board
# class PieceLabel is for the pieces
# class Widget     is for the squares

# The ChessBoard's grid layout contains the squares (Widget) and pieces (PieceLabel).
# Resolution of pieces to square is done by coordinates of the grid layout

import copy

from PyQt5.QtCore import pyqtSignal, QPropertyAnimation, QEventLoop, QRegExp, Qt, QThread
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QApplication, QFrame, QGridLayout, QLabel, QMessageBox, QSizePolicy, QWidget

import common
import debug

#from position import Position
import chess

SQR_SIZE = 100

class ChessBoard(QFrame):
    # parent is TestFrame
    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent

        #self.square_colors = ['#B58863', '#F0D9B5']
        self.square_colors = ['#F0D9B5', '#B58863']
        #self.highlight_colors = ['#DAC34B', '#F7EC74']
        self.highlight_colors = ['#F7EC74', '#DAC34B']

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setContentsMargins(0, 0, 0, 0)

        self.layout = QGridLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # QT grid layout uses row,col with 0,0 in top left
        # we lay it out in the order convention by chess module (0 at bottom left) (and append to self.squares)
        self.squares = []
        for qt_row in [7,6,5,4,3,2,1,0]:
            for qt_col in [0,1,2,3,4,5,6,7]:
                square = QWidget(self)
                square.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                self.layout.addWidget(square, qt_row, qt_col)
                #print(f'square[{len(self.squares)}] is at qt row={qt_row}, col={qt_col}')
                self.squares.append(square) # important ordering

        self.setPerspective(chess.WHITE)

        self.setLayout(self.layout)

        #self.model = chess.Board()
        self.model = chess.BaseBoard()

        #self.search = Search(self.model)
        #self.search_thread = SearchThread(self)
        self.self_play = True
        self.difficulty = None
        self.autosave = None
        self.saved = True
        self.auto_promote_to = None # chess.QUEEN, etc.

        self.move_request_callback = None
        self.move_complete_callback = None

        self.undone_stack = []

        self.sqr_size = SQR_SIZE

        self.update()

    def setPerspective(self, perspective):
        self.perspective = perspective

        for i in range(64):
            if perspective == chess.WHITE:
                self.squares[i].setObjectName(str(i))
            else:
                self.squares[i].setObjectName(str(63-i))

            color = self.square_colors[self.indexToLightDark(i)]
            self.squares[i].setStyleSheet('background-color: ' + color)

    def sanToIndex(self, san):
        index = {   'a8': 56, 'b8': 57, 'c8': 58, 'd8': 59, 'e8': 60, 'f8': 61, 'g8': 62, 'h8': 63,
                    'a7': 48, 'b7': 49, 'c7': 50, 'd7': 51, 'e7': 52, 'f7': 53, 'g7': 54, 'h7': 55,
                    'a6': 40, 'b6': 41, 'c6': 42, 'd6': 43, 'e6': 44, 'f6': 45, 'g6': 46, 'h6': 47,
                    'a5': 32, 'b5': 33, 'c5': 34, 'd5': 35, 'e5': 36, 'f5': 37, 'g5': 38, 'h5': 39,
                    'a4': 24, 'b4': 25, 'c4': 26, 'd4': 27, 'e4': 28, 'f4': 29, 'g4': 30, 'h4': 31,
                    'a3': 16, 'b3': 17, 'c3': 18, 'd3': 19, 'e3': 20, 'f3': 21, 'g3': 22, 'h3': 23,
                    'a2':  8, 'b2':  9, 'c2': 10, 'd2': 11, 'e2': 12, 'f2': 13, 'g2': 14, 'h2': 15,
                    'a1':  0, 'b1':  1, 'c1':  2, 'd1':  3, 'e1':  4, 'f1':  5, 'g1':  6, 'h1':  7 }[san]

        if self.perspective == chess.WHITE:
            return index
        else:
            return 63-index

    # 0
    def indexToLightDark(self, i):
        lookup   = {56:0, 57:1, 58:0, 59:1, 60:0, 61:1, 62:0, 63:1,
                    48:1, 49:0, 50:1, 51:0, 52:1, 53:0, 54:1, 55:0,
                    40:0, 41:1, 42:0, 43:1, 44:0, 45:1, 46:0, 47:1,
                    32:1, 33:0, 34:1, 35:0, 36:1, 37:0, 38:1, 39:0,
                    24:0, 25:1, 26:0, 27:1, 28:0, 29:1, 30:0, 31:1,
                    16:1, 17:0, 18:1, 19:0, 20:1, 21:0, 22:1, 23:0,
                    8: 0,  9:1, 10:0, 11:1, 12:0, 13:1, 14:0, 15:1,
                    0: 1,  1:0,  2:1,  3:0,  4:1,  5:0,  6:1,  7:0 }

        if self.perspective == chess.WHITE:
            return lookup[i]
        else:
            return lookup[63-i]

    def indexToSquareWidget(self, i):
        if self.perspective == chess.WHITE:
            return self.squares[i]
        else:
            return self.squares[63-i]

    # converts a (module chess) index 0..63 to the row,col coordinate of the widget in the QGridLayout
    def indexToQtCoords(self, i):
        lookup   = {56:(0,0), 57:(0,1), 58:(0,2), 59:(0,3), 60:(0,4), 61:(0,5), 62:(0,6), 63: (0,7),
                    48:(1,0), 49:(1,1), 50:(1,2), 51:(1,3), 52:(1,4), 53:(1,5), 54:(1,6), 55: (1,7),
                    40:(2,0), 41:(2,1), 42:(2,2), 43:(2,3), 44:(2,4), 45:(2,5), 46:(2,6), 47: (2,7),
                    32:(3,0), 33:(3,1), 34:(3,2), 35:(3,3), 36:(3,4), 37:(3,5), 38:(3,6), 39: (3,7),
                    24:(4,0), 25:(4,1), 26:(4,2), 27:(4,3), 28:(4,4), 29:(4,5), 30:(4,6), 31: (4,7),
                    16:(5,0), 17:(5,1), 18:(5,2), 19:(5,3), 20:(5,4), 21:(5,5), 22:(5,6), 23: (5,7),
                    8: (6,0),  9:(6,1), 10:(6,2), 11:(6,3), 12:(6,4), 13:(6,5), 14:(6,6), 15: (6,7),
                    0: (7,0),  1:(7,1),  2:(7,2),  3:(7,3),  4:(7,4),  5:(7,5),  6:(7,6),  7: (7,7) }

        if self.perspective == chess.WHITE:
            return lookup[i]
        else:
            return lookup[63-i]

    def set_move_request_callback(self, func):
        self.move_request_callback = func

    def set_move_complete_callback(self, func):
        self.move_complete_callback = func

    def resizeEvent(self, event):
        if event.size().width() > event.size().height():
            self.resize(event.size().height(), event.size().height())
            self.sqr_size = int(event.size().height() / 8)
        else:
            self.resize(event.size().width(), event.size().width())
            self.sqr_size = int(event.size().width() / 8)

    # symbol:       str like 'R'
    def place_piece(self, sqr_index, symbol):
        row, col = self.indexToQtCoords(sqr_index)
        piece_label = PieceLabel(self, symbol)
        self.layout.addWidget(piece_label, row, col)

    # NB: square index changes!
    # 0 can be bottom left widget in layout
    # 0 can be top right widget in layout
    def get_piece_widget_by_square_index(self, sqr_index):
        square = self.indexToSquareWidget(sqr_index)
        square_pos = self.layout.getItemPosition(self.layout.indexOf(square))

        for piece in self.findChildren(QLabel):
            piece_pos = self.layout.getItemPosition(self.layout.indexOf(piece))
            if square_pos == piece_pos:
                return piece

    # NB: square san changes!
    # a1 can be bottom left widget
    # a1 can be top right widget
    def get_piece_widget_by_square_san(self, square):
        index = self.sanToIndex(square)
        return self.get_piece_widget_by_square_index(index)

    #--------------------------------------------------------------------------
    # get/set fen
    #--------------------------------------------------------------------------

    def set_fen(self, fen):
        if self.get_mode() == 'free':
            if ' ' in fen:
                fen = fen.split(' ')[0]
            self.model.set_board_fen(fen)

        else:
            self.model.set_fen(fen)

    def get_fen(self):
        if self.get_mode() == 'free':
            return self.model.board_fen()
        else:
            return self.model.fen()

    # draw the board based on FEN
    def update_view(self):
        # destroy all labels
        for piece in self.findChildren(QLabel):
            piece.setParent(None)

        # create new labels
        pmap = self.model.piece_map()
        for square_idx, piece_obj in pmap.items():
            self.place_piece(square_idx, piece_obj.symbol())

        self.set_pickup_model()

    def reset(self):
        self.set_fen(common.starting_fen)
        self.update_view()

    def highlight(self, idx):
        square = self.indexToSquareWidget(idx)
        color = self.highlight_colors[self.indexToLightDark(idx)]
        square.setStyleSheet('background-color: ' + color)

    def unhighlight(self, idx):
        square = self.indexToSquareWidget(idx)
        color = self.square_colors[self.indexToLightDark(idx)]
        square.setStyleSheet('background-color: ' + color)

    def unhighlight_all(self):
        for sqr_index in range(64):
            self.unhighlight(sqr_index)

    def moves_from_square(self, sqr_index):
        result = []
        if type(self.model) == chess.Board:
            result = []
            for move in self.model.generate_pseudo_legal_moves():
                if move.from_square == sqr_index:
                    result.append(move.to_square)

            return result

    #--------------------------------------------------------------------------
    # set pickup (which pieces the user can interact with)
    #--------------------------------------------------------------------------

    def set_pickup_none(self):
        for piece in self.findChildren(PieceLabel):
            piece.enabled = False

    def set_pickup_all(self):
        for piece in self.findChildren(PieceLabel):
            piece.enabled = True

    def set_pickup_white(self):
        for piece in self.findChildren(PieceLabel):
            if piece.is_white:
                piece.enabled = True
            else:
                piece.enabled = False

    def set_pickup_black(self):
        for piece in self.findChildren(PieceLabel):
            if piece.is_white:
                piece.enabled = False
            else:
                piece.enabled = True

    def set_pickup(self, pickup_str):
        match pickup_str:
            case 'all': self.set_pickup_all()
            case 'none': self.set_pickup_none()
            case 'white': self.set_pickup_white()
            case 'black': self.set_pickup_black()

    # pickup mode based on model state
    def set_pickup_model(self):
        if self.get_mode() == 'game':
            match self.model.turn:
                case chess.WHITE: self.set_pickup_white()
                case chess.BLACK: self.set_pickup_black()
                case _: set_pickup_all()

    #--------------------------------------------------------------------------
    # set mode (free or game (rules enforced))
    #--------------------------------------------------------------------------

    # change to free mode
    def set_mode_free(self):
        if type(self.model) == chess.Board:
            fen = self.model.fen()
            bfen = fen.split(' ')[0] if ' ' in fen else fen
            self.model = chess.BaseBoard(bfen)

    # change to game mode
    def set_mode_game(self):
        # if in free mode, convert
        if self.get_mode() == 'free':
            bfen = self.model.board_fen()
            self.model = chess.Board()
            self.model.set_board_fen(bfen)

        # set pickup mode based on model
        self.set_pickup_model()

    def set_mode(self, mode_str):
        match mode_str:
            case 'free': self.set_mode_free()
            case 'game': self.set_mode_game()

    def get_mode(self):
        match type(self.model):
            case chess.BaseBoard: return 'free'
            case chess.Board: return 'game'

    #

    def do_rook_castle(self, king_dst, is_undo):
        if king_dst == 2:
            rook_src = 0
            rook_dst = 3
        elif king_dst == 6:
            rook_src = 7
            rook_dst = 5
        elif king_dst == 58:
            rook_src = 56
            rook_dst = 59
        elif king_dst == 62:
            rook_src = 63
            rook_dst = 61

        if is_undo:
            rook = self.get_piece_widget_by_square_index(rook_dst)
            self.piece_glide(rook, rook_src)
        else:
            rook = self.get_piece_widget_by_square_index(rook_src)
            self.piece_glide(rook, rook_dst)

    def piece_glide(self, piece, sqr_index):
        piece.raise_()
        square = self.indexToSquareWidget(sqr_index)

        self.glide = QPropertyAnimation(piece, b'pos')
        self.glide.setDuration(100)
        self.glide.setEndValue(square.pos())
        self.glide.start()

        # Start local event loop, so program waits until glide is completed
        loop = QEventLoop()
        self.glide.finished.connect(loop.quit)
        loop.exec()

    def move_glide(self, move_san):
        move = self.model.parse_san(move_san)
        piece = self.get_piece_widget_by_square_index(move.from_square)
        print(f'{piece} .x={piece.x()} .y={piece.y()}')
        print(f'{move} {move.from_square} -> {move.to_square}')
        self.piece_glide(piece, move.to_square)
        self.model.push_san(move_san)
        self.update_view()

        # TODO: handle castling, see do_rook_castle

    def undo_glide(self):
        move = self.model.peek()
        piece = self.get_piece_widget_by_square_index(move.to_square)
        print(f'{piece} .x={piece.x()} .y={piece.y()}')
        print(f'{move} {move.from_square} -> {move.to_square}')
        self.piece_glide(piece, move.from_square)
        self.model.pop()
        self.update_view()

    # the PieceLabel class calls us
    # a PieceLabel has been dropped resulting in a valid move
    def move_inputted(self, move):
        # in game mode, ignore illegal moves
        if self.get_mode() == 'game':
            if not self.model.is_legal(move):
                return

        # inform user
        allowed = True
        if self.move_request_callback:
            allowed = self.move_request_callback(self, move)

        if not allowed:
            return

        # update model, UI
        match self.get_mode():
            case 'free':
                piece = self.model.piece_at(move.from_square)
                self.model.remove_piece_at(move.from_square)
                self.model.set_piece_at(move.to_square, piece)
            case 'game':
                self.model.push(move)

        self.update_view()
        print('view is updated!')

        # inform user
        if self.move_complete_callback:
            move_san = common.last_move_as_san(self.model)
            self.move_complete_callback(self, move_san)

    def game_over(self):
        legal_moves = list(filter(self.model.is_legal,
                                  self.model.get_pseudo_legal_moves()))

        if not legal_moves:
            # Checkmate
            if self.model.is_in_check():
                text = "{} wins by checkmate".format("White" if self.model.colour else "Black")
                #if user:
                #    user.add_win() if self.user_is_white == bool(self.model.colour) else user.add_loss()
            # Stalemate
            else:
                text = "Draw by stalemate"
                if user:
                    user.add_draw()
        # Fifty-move rule
        elif self.model.halfmove_clock >= 100:
            text = "Draw by fifty-move rule"
            if user:
                user.add_draw()
        # Threefold repetition
        elif self.model.is_threefold_repetition():
            text = "Draw by threefold repetition"
            if user:
                user.add_draw()
        elif self.model.is_insufficient_material():
            text = "Draw by insufficient material"
            if user:
                user.add_draw()

        msg_box = QMessageBox()
        msg_box.setWindowIcon(QIcon('./assets/icons/pawn_icon.png'))
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle("Chess")
        msg_box.setText(text)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()

        self.saved = True

class PieceLabel(QLabel):
    def __init__(self, parent, symbol):
        super().__init__(parent)

        self.symbol = symbol # str representing the piece PNBRQKpnbrqk

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(1, 1)

        # Make label transparent, so square behind piece is visible
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.board = parent
        self.is_white = self.symbol in list('PNBRQK')
        self.enabled = True

        self.src_pos = None
        self.mouse_pos = None
        self.src_square = None
        self.dst_square = None
        self.legal_moves = None
        self.legal_dst_squares = None

        # Store original piece image
        lookup = {
            'p': 'bp', 'n': 'bn', 'b': 'bb', 'r': 'br', 'q': 'bq', 'k': 'bk',
            'P': 'wp', 'N': 'wn', 'B': 'wb', 'R': 'wr', 'Q': 'wq', 'K': 'wk'
        }
        pixmap = QPixmap(f'./assets/pieces/{lookup[self.symbol]}.png')
        self.setPixmap(pixmap)

        # When label is scaled, also scale image inside the label
        self.setScaledContents(True)

        self.setMouseTracking(True)

        self.show()

    def resizeEvent(self, event):
        if event.size().width() > event.size().height():
            self.resize(event.size().height(), event.size().height())
        else:
            self.resize(event.size().width(), event.size().width())

    def enterEvent(self, event):
        if self.enabled:
            QApplication.setOverrideCursor(Qt.OpenHandCursor)

    def leaveEvent(self, event):
        # Set arrow cursor while not hovering over a piece
        QApplication.setOverrideCursor(Qt.ArrowCursor)

    def mousePressEvent(self, event):
        if not self.enabled:
            return

        if event.buttons() == Qt.LeftButton:
            # Set closed hand cursor while dragging a piece
            QApplication.setOverrideCursor(Qt.ClosedHandCursor)

            # Raise piece to the front
            self.raise_()

            # Store mouse position and square position, relative to the chessboard
            self.mouse_pos = self.mapToParent(self.mapFromGlobal(event.globalPos()))
            self.src_pos = self.mapToParent(self.rect().topLeft())

            # Snap to cursor
            offset = self.rect().topLeft() - self.rect().center()
            self.move(self.mouse_pos + offset)

            # Identify origin square by comparing Qt position of PieceLabel to Square (QWidget)
            for square in self.board.squares:
                if square.pos() == self.src_pos:
                    self.src_square = square
                    print(f'origin square: {square.objectName()}')
                    break

            # Identify legal moves
            sqr_index = int(self.src_square.objectName())

            # Highlight origin and destination squares
            self.legal_dst_squares = []
            self.board.highlight(sqr_index)
            for dst_square in self.board.moves_from_square(sqr_index):
                self.board.highlight(dst_square)
                self.legal_dst_squares.append(dst_square)

    def mouseMoveEvent(self, event):
        if not self.enabled:
            return

        if event.buttons() == Qt.LeftButton:
            # Update mouse position, relative to the chess board
            self.mouse_pos = self.mapToParent(self.mapFromGlobal(event.globalPos()))

            # Calculate offset from centre to top-left of square
            offset = self.rect().topLeft() - self.rect().center()

            # Calculate new x position, not allowing the piece to go outside the board
            if self.mouse_pos.x() < self.board.rect().left():
                new_pos_x = self.board.rect().left() + offset.x()
            elif self.mouse_pos.x() > self.board.rect().right():
                new_pos_x = self.board.rect().right() + offset.x()
            else:
                new_pos_x = self.mouse_pos.x() + offset.x()

            # Calculate new y position, not allowing the piece to go outside the board
            if self.mouse_pos.y() < self.board.rect().top():
                new_pos_y = self.board.rect().top() + offset.y()
            elif self.mouse_pos.y() > self.board.rect().bottom():
                new_pos_y = self.board.rect().right() + offset.y()
            else:
                new_pos_y = self.mouse_pos.y() + offset.y()

            # Move piece to new position
            print(f'moving myself {self} ({self.symbol}) to {new_pos_x}, {new_pos_y}')
            self.move(new_pos_x, new_pos_y)

    # self: board.PieceLabel
    def mouseReleaseEvent(self, event):
        if not self.enabled:
            return

        # Set open hand cursor when piece is released
        QApplication.setOverrideCursor(Qt.OpenHandCursor)

        self.board.unhighlight_all()

        # abort if mouse not on on board
        if not self.board.rect().contains(self.board.mapFromGlobal(event.globalPos())):
            return

        # locate destination square, abort if not found
        for square in self.board.squares:
            if square.rect().contains(square.mapFromGlobal(event.globalPos())):
                self.dst_square = square
                break
        else:
            #print(f'destination square not found, sending back')
            #self.move(self.src_pos)
            return

        sqr_src = int(self.src_square.objectName())
        sqr_dst = int(self.dst_square.objectName())
        print(f'{sqr_src} -> {sqr_dst}')

        # is the move legal?
        if not sqr_dst in self.legal_dst_squares:
            #print(f'is illegal')
            return

        # is it a non-move?
        if sqr_src == sqr_dst:
            return

#                    elif move_type == CASTLING:
#                        self.board.do_rook_castle(move_made & 0x3F, False)
#
#                    self.board.move_inputted(move_made)
#                else:
#                    # Snap back to origin square
#                    self.move(self.src_pos)

        piece = self.board.model.piece_at(sqr_src)

        promotion = False

        if piece.piece_type == chess.PAWN:
            if piece.color == chess.WHITE and chess.square_rank(sqr_dst)+1 == 8:
                promotion = True
            elif piece.color == chess.BLACK and chess.square_rank(sqr_dst)+1 == 1:
                promotion = True

        prom_piece = None
        if promotion:
            if self.board.auto_promote_to != None:
                prom_piece = self.board.auto_promote_to
            else:
                # prompt for the promotion piece
                promotion_prompt = QMessageBox()
                promotion_prompt.setWindowIcon(QIcon('./assets/icons/pawn_icon.png'))
                promotion_prompt.setIcon(QMessageBox.Question)
                promotion_prompt.setWindowTitle("Chess")
                promotion_prompt.setText("Choose promotion piece.")
                knight_btn = promotion_prompt.addButton("Knight", QMessageBox.AcceptRole)
                bishop_btn = promotion_prompt.addButton("Bishop", QMessageBox.AcceptRole)
                rook_btn = promotion_prompt.addButton("Rook", QMessageBox.AcceptRole)
                queen_btn = promotion_prompt.addButton("Queen", QMessageBox.AcceptRole)
                promotion_prompt.exec()

                cb = promotion_prompt.clickedButton()
                if cb == knight_btn:
                    prom_piece = chess.KNIGHT
                elif cb == bishop_btn:
                    prom_piece = chess.BISHOP
                elif cb == rook_btn:
                    prom_piece = chess.ROOK
                elif cb == queen_btn:
                    prom_piece = chess.QUEEN

        move = chess.Move(sqr_src, sqr_dst, promotion=prom_piece)
        print(f'calling move_inputted({move})')
        self.board.move_inputted(move)

        return

#        if self.dst_square.objectName() in self.legal_dst_squares:  # If legal move
            # Snap to destination square
#            self.board.layout.removeWidget(self)
#            row = self.dst_square.y() / self.board.sqr_size
#            col = self.dst_square.x() / self.board.sqr_size
#            self.board.layout.addWidget(self, round(row), round(col))



#                    elif move_type == CASTLING:
#                        self.board.do_rook_castle(move_made & 0x3F, False)
#
#                    self.board.move_inputted(move_made)
#                else:
#                    # Snap back to origin square
#                    self.move(self.src_pos)
