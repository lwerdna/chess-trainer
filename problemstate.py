import chess

from common import *
import evaluation
import debug

class ProblemState():
    def __init__(self):
        self.correct = True

    def initialize_chessboard(self):
        pass

    def test_move(self):
        pass
    def update_move(self):
        pass

    def is_done(self):
        pass

class CheckmateOrPromoteToQueenProblemState(ProblemState):
    def __init__(self, dbentry):
        self.dbentry = dbentry
        self.board = chess.Board(dbentry['FEN'])
        self.player_color = self.board.turn

    def initialize_chessboard(self, cboard):
        cboard.set_fen(self.dbentry['FEN'])
        cboard.setPerspective(self.board.turn)
        cboard.update_view()

    # test if a player move is correct
    def test_move(self, move):
        result = True

        self.board.push_san(move)

        outcome = self.board.outcome()
        if outcome and outcome.termination != chess.Termination.CHECKMATE:
            result = False

        self.board.pop()
        return result

    # enter player move (assuming it's tested as correct)
    def update_move(self, move, cboard):
        assert self.test_move(move)

        self.board.push_san(move)

        if not self.is_done():
            reply_move = evaluation.bestmove(self.board)
            reply_san = move_as_san(self.board, reply_move)
            print(f'evaluation.evaluate() returned {reply_san}')

            # update our model
            self.board.push_san(reply_san)
            # update UI
            cboard.move_glide(reply_san)

    def is_done(self):
        # did we checkmate him?
        outcome = self.board.outcome()
        if outcome and outcome.termination == chess.Termination.CHECKMATE:
            if outcome.winner == self.player_color:
                return True

        # did we promote to queen?
        if self.board.turn != self.player_color:
            move = self.board.peek()
            if move.promotion == chess.QUEEN:
                return True

        # neither? not done
        return False

class FollowVariationsProblemState(ProblemState):
    def __init__(self, dbentry):
        self.dbentry = dbentry
        self.line = split_line_string(dbentry['LINE'])
        self.board = chess.Board(dbentry['FEN'])
        self.halfmove_index = 0

    def initialize_chessboard(self, cboard):
        cboard.set_fen(self.dbentry['FEN'])
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

        # the line isn't ended, execute the reply
        if self.halfmove_index+1 < len(self.line):
            reply = self.line[self.halfmove_index]

            # update our state with the reply
            self.board.push_san(reply)

            # update the UI state with the reply
            cboard.move_glide(reply)
            self.halfmove_index += 1

    def is_done(self):
        return self.halfmove_index >= len(self.line)

def create_problem_state_from_db_data(entry):
    match entry['TYPE']:
        case 'follow_variations':
            return FollowVariationsProblemState(entry)
        case 'checkmate_or_promote_to_queen':
            return CheckmateOrPromoteToQueenProblemState(entry)
        case _:
            raise Exception('unknown problem type: ' + entry['TYPE'])
