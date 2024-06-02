import chess

from common import *
import debug

class ProblemState():
    def __init__(self):
        self.correct = True

class FollowVariationsProblemState(ProblemState):
    def __init__(self, dbentry):
        self.dbentry = dbentry
        self.line = split_line_string(dbentry['LINE'])
        self.board = chess.Board(dbentry['FEN'])
        self.halfmove_index = 0

    def initialize_chessboard(self, cboard):
        cboard.set_fen(self.board.fen())
        cboard.setPerspective(self.board.turn)
        cboard.update_view()

    # test if a player move is correct
    def test_move(self, move):
        expect_move = self.line[self.halfmove_index]

        #print(f'line moves: {line_moves}')
        #print(f'halfmove_index: {problem_state["halfmove_index"]}')
        #print(f'expect move: {expect_move}')

        if move == expect_move:
            return True
        else:
            print(f'{move} was wrong, expected {expect_move}')
            self.correct = False
            return False

    # enter player move (assuming it's tested as correct)
    def update_move(self, move, cboard):
        assert self.test_move(move)

        self.halfmove_index += 1
        self.board.push_san(move)

        # the line isn't ended, animate the reply
        if self.halfmove_index+1 < len(self.line):
            reply = self.line[self.halfmove_index]

            # update our state with the reply
            self.board.push_san(reply)

            # update the UI state with the reply
            cboard.move_glide(reply, False)
            self.halfmove_index += 1

    def is_done(self):
        return self.halfmove_index >= len(self.line)

def create_problem_state_from_db_data(entry):
    if entry['TYPE'] == 'follow_variations':
        return FollowVariationsProblemState(entry)
    else:
        debug.breakpoint()
