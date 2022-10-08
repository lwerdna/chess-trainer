# class ChessBoard
# class PieceLabel

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
    def __init__(self, parent):
        super().__init__(parent)

        self.parent = parent

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setContentsMargins(0, 0, 0, 0)

        self.layout = QGridLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.draw_squares()
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

    def draw_squares(self):
        for row, rank in enumerate('87654321'):
            for col, file in enumerate('abcdefgh'):
                square = QWidget(self)
                square.setObjectName(file + rank)
                square.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
                if row % 2 == col % 2:
                    square.setStyleSheet('background-color: #F0D9B5')
                else:
                    square.setStyleSheet('background-color: #B58863')
                self.layout.addWidget(square, row, col)

    # square_name: str like 'a7'
    # piece: str       like 'R'
    def place_piece(self, sqr_name, piece):
        #print(f'place_piece(sqr_name={sqr_name}, piece={piece})')
        col, row = common.square_to_coords[sqr_name]
        piece_label = PieceLabel(self, piece)
        self.layout.addWidget(piece_label, row, col)

    def view_piece_at_square(self, sqr_index):
        square = self.findChild(QWidget, common.index_to_san[sqr_index])
        square_pos = self.layout.getItemPosition(self.layout.indexOf(square))
        for piece in self.findChildren(QLabel):
            piece_pos = self.layout.getItemPosition(self.layout.indexOf(piece))
            if square_pos == piece_pos:
                return piece

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
        # UPDATE PIECE DISPLAY
        pmap = self.model.piece_map()
        for i in range(64):
            square_sym = common.index_to_san[i]

            # get the (view) piece on this square
            vpiece = self.view_piece_at_square(i)

            # is there a (model) piece on this square?
            if i in pmap:
                mpiece = pmap[i]

                # if (view) piece matches (model) piece, done!
                if vpiece:
                    if vpiece.piece_sym == mpiece.symbol():
                        pass
                    else:
                        vpiece.setParent(None)
                        self.place_piece(square_sym, mpiece.symbol())
                else:
                    self.place_piece(square_sym, mpiece.symbol())

            else:
                if vpiece:
                    vpiece.setParent(None)

        # UPDATE PICKUP-ABILITY
        self.set_pickup_model()

    def reset(self):
        self.set_fen(common.starting_fen)
        self.update_view()

    def highlight(self, sq):
        # If square index given, convert to SAN
        if not common.regex_square.match(str(sq)):
            sq = common.index_to_san[sq]

        square = self.findChild(QWidget, sq)

        col, row = common.square_to_coords[sq]

        if row % 2 == col % 2:  # light square
            square.setStyleSheet('background-color: #F7EC74')
        else:  # dark square
            square.setStyleSheet('background-color: #DAC34B')

    def unhighlight(self, sq):
        # If square index given, convert to SAN
        if not common.regex_square.match(str(sq)):
            sq = common.index_to_san[sq]

        square = self.findChild(QWidget, sq)

        col, row = common.square_to_coords[sq]

        if row % 2 == col % 2:  # light square
            square.setStyleSheet('background-color: #F0D9B5')
        else:  # dark square
            square.setStyleSheet('background-color: #B58863')

    def unhighlight_all(self):
        for sqr_index in range(64):
            self.unhighlight(sqr_index)

    def moves_from_square(self, sqr_index):
        if type(self.model) == chess.BaseBoard:
            return []
        elif type(self.model) == chess.Board:
            moves = list(self.model.generate_pseudo_legal_moves())
            #print(moves)

            # convert moves to internal representation
            moves = [(m.from_square << 6) | m.to_square for m in moves]

            # filter moves involving this source square
            moves = [m for m in moves if (m >> 6) & 0x3F == sqr_index]

            # Filter out illegal moves
            #moves = list(filter(self.model.is_legal, moves))

            return moves

    #--------------------------------------------------------------------------
    # set pickup (which pieces the user can interact with)
    #--------------------------------------------------------------------------

    def set_pickup_none(self):
        for piece in self.findChildren(QLabel):
            piece.enabled = False

    def set_pickup_all(self):
        for piece in self.findChildren(QLabel):
            piece.enabled = True

    def set_pickup_white(self):
        for piece in self.findChildren(QLabel):
            if piece.is_white:
                piece.enabled = True
            else:
                piece.enabled = False

    def set_pickup_black(self):
        for piece in self.findChildren(QLabel):
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

    def piece_glide(self, piece, dst_index):
        piece.raise_()
        dst_square = self.findChild(QWidget, common.index_to_san[dst_index])
        self.glide = QPropertyAnimation(piece, b'pos')
        self.glide.setDuration(500)
        self.glide.setEndValue(dst_square.pos())
        self.glide.start()

        # Start local event loop, so program waits until glide is completed
        loop = QEventLoop()
        self.glide.finished.connect(loop.quit)
        loop.exec()

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
            rook = self.view_piece_at_square(rook_dst)
            self.piece_glide(rook, rook_src)
        else:
            rook = self.view_piece_at_square(rook_src)
            self.piece_glide(rook, rook_dst)

    def move_glide(self, move, is_undo):
        src_index = (move >> 6) & 0x3F
        dst_index = move & 0x3F

        if not is_undo:
            piece = self.view_piece_at_square(src_index)
        else:
            piece = self.view_piece_at_square(dst_index)

        self.piece_glide(piece, src_index if is_undo else dst_index)

        #if move & (0x3 << 14) == CASTLING:
        #    self.do_rook_castle(dst_index, is_undo)

    def move_inputted(self, move):
        #print(f'move_inputted({move.from_square} -> {move.to_square})')

        # ignore moves to same square
        if move.from_square == move.to_square:
            return

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

        # inform user
        if self.move_complete_callback:
            self.move_complete_callback(self, move)

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

# Search algorithm must be run in a separate thread to the main event loop, to prevent the GUI from freezing
class SearchThread(QThread):
    move_signal = pyqtSignal(int)

    def __init__(self, board):
        super().__init__()

        self.board = board
        self.move_signal.connect(self.board.computer_move)

    def run(self):
        self.board.set_pickup_none()

        if self.board.difficulty == 1:
            move = self.board.search.iter_search(max_depth=1)  # Depth 1 search
        elif self.board.difficulty == 2:
            move = self.board.search.iter_search(max_depth=2)  # Depth 2 search
        elif self.board.difficulty == 3:
            move = self.board.search.iter_search(time_limit=0.1)  # 0.1 second search
        elif self.board.difficulty == 4:
            move = self.board.search.iter_search(time_limit=1)  # 1 second search
        elif self.board.difficulty == 5:
            move = self.board.search.iter_search(time_limit=5)  # 5 second search

        self.board.position = self.board.search.position

        self.move_signal.emit(move)


class PieceLabel(QLabel):
    def __init__(self, parent, piece):
        super().__init__(parent)

        self.piece_sym = piece # str representing the piece PNBRQKpnbrqk

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(1, 1)

        # Make label transparent, so square behind piece is visible
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.board = parent
        self.is_white = self.piece_sym in list('PNBRQK')
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
        pixmap = QPixmap(f'./assets/pieces/{lookup[self.piece_sym]}.png')
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

            # Identify origin square
            all_squares = self.board.findChildren(QWidget, QRegExp(r'[a-h][1-8]'))
            for square in all_squares:
                if square.pos() == self.src_pos:
                    self.src_square = square
                    break

            # Identify legal moves
            sqr_index = common.san_to_index[self.src_square.objectName()]
            self.legal_moves = self.board.moves_from_square(sqr_index)

            # Only need destination square for each move
            self.legal_dst_squares = list(map(lambda move: common.index_to_san[move & 0x3F], self.legal_moves))

            # Highlight origin and destination squares
            self.board.highlight(sqr_index)
            for dst_square in self.legal_dst_squares:
                self.board.highlight(dst_square)

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
            self.move(new_pos_x, new_pos_y)

    # self: board.PieceLabel
    def mouseReleaseEvent(self, event):
        if not self.enabled:
            return

        # Set open hand cursor when piece is released
        QApplication.setOverrideCursor(Qt.OpenHandCursor)

        self.board.unhighlight_all()

        # If mouse not released on board, move piece back to origin square, and return
        if not self.board.rect().contains(self.board.mapFromGlobal(event.globalPos())):
            self.move(self.src_pos)
            return

        # Identify destination square
        all_squares = self.board.findChildren(QWidget, QRegExp(r'[a-h][1-8]'))
        for square in all_squares:
            if square.rect().contains(square.mapFromGlobal(event.globalPos())):
                self.dst_square = square
                break


        # get name like 'a7' or 'g8'
        sqr_src = chess.parse_square(self.src_square.objectName())
        sqr_dst = chess.parse_square(self.dst_square.objectName())

        if sqr_src == sqr_dst:
            return

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
                print(f'HERP: {self.board.auto_promote_to}')
                print(f'HERP: {type(self.board.auto_promote_to)}')
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

        print(f'sqr_src: {sqr_src}')
        print(f'sqr_dst: {sqr_dst}')
        print(f'prom_piece: {prom_piece}')
        move = chess.Move(sqr_src, sqr_dst, promotion=prom_piece)
        print(f'move: {move}')
        self.board.move_inputted(move)
        self.board.update_view()

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
