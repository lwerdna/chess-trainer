import chess

from common import *
import evaluation
import debug

class ProblemState():
    def __init__(self):
        self.correct = True
        self.dbentry['FEN'] = chess.STARTING_FEN

    def initialize_chessboard(self, cboard):
        cboard.set_fen(self.dbentry['FEN'])
        cboard.setPerspective(self.board.turn)
        cboard.update_view()

    def test_move(self, move_san):
        pass
    def update_move(self, move_san, cboard):
        pass

    def is_done(self):
        pass

class PlayBestProblemState(ProblemState):
    def __init__(self, dbentry, moves_required=3):
        self.dbentry = dbentry
        self.board = chess.Board(dbentry['FEN'])
        self.player_color = self.board.turn
        self.moves_required = moves_required
        self.moves_made = 0

    def test_move(self, player_move_san):
        best_move = evaluation.bestmove(self.board)
        best_move_san = move_as_san(self.board, best_move)
        if player_move_san == best_move_san:
            return True
        else:
            print(f'wrong move {player_move_san}, expected: {best_move_san}')

    def update_move(self, move, cboard):
        assert self.test_move(move)

        self.board.push_san(move)
        self.moves_made += 1

        if not self.is_done():
            reply_move = evaluation.bestmove(self.board)
            reply_san = move_as_san(self.board, reply_move)
            print(f'evaluation.evaluate() returned {reply_san}')

            # update our model
            self.board.push_san(reply_san)
            # update UI
            cboard.move_glide(reply_san)

    def is_done(self):
        if self.moves_made >= self.moves_required:
            return True

        outcome = self.board.outcome()
        if outcome and outcome.termination == chess.Termination.CHECKMATE:
            return True

        return False

class CheckmateOrPromoteToQueenProblemState(ProblemState):
    def __init__(self, dbentry):
        self.dbentry = dbentry
        self.board = chess.Board(dbentry['FEN'])
        self.player_color = self.board.turn

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
    def __init__(self, problem):
        self.problem = problem

        # parse problem
        self.fen, line = (problem[k] for k in ['fen', 'line'])
        self.board = chess.Board(self.fen)
        self.player_color = self.board.turn

        # generate the exercises
        self.exercises = generate_variation_exercises(self.fen, line)
        assert len(self.exercises) >= 1
        for i,exercise in enumerate(self.exercises):
            print(f'exercise {i}: FEN: {exercise["FEN"]} LINE: {exercise["LINE"]}')

        # load first exercise
        self.exercise_index = 0
        self.load_current_exercise()

    # we override the parent to set the perspective to the root position
    def initialize_chessboard(self, cboard):
        exercise = self.exercises[self.exercise_index]
        cboard.set_fen(exercise['FEN'])
        cboard.setPerspective(self.player_color)
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
        else:
            # advance, load next exercise
            self.exercise_index += 1
            if self.exercise_index < len(self.exercises):
                self.load_current_exercise()

                self.initialize_chessboard(cboard)

                # play so it's our move
                if self.board.turn != self.player_color:
                    reply = self.line[0]
                    self.board.push_san(reply)
                    cboard.move_glide(reply)
                    self.halfmove_index += 1

    def load_current_exercise(self):
        exercise = self.exercises[self.exercise_index]
        fen = exercise["FEN"]
        self.board = chess.Board(fen)
        self.line = split_line_string(exercise['LINE'])
        self.halfmove_index = 0
        print(f'exercise_index: {self.exercise_index}')
        print(f'   loading fen: {fen}')
        print(f'  loading line: {self.line}')

    def is_done(self):
        return self.exercise_index >= len(self.exercises)

def create_problem_state_from_db_data(entry):
    if entry['TYPE'] == 'follow_variations':
        return FollowVariationsProblemState(entry)
    if entry['TYPE'] == 'checkmate_or_promote_to_queen':
        return CheckmateOrPromoteToQueenProblemState(entry)
    if entry['TYPE'] == 'play_best':
        return PlayBestProblemState(entry)
    if m := re.match(r'^play_best(\d+)$', entry['TYPE']):
        moves = int(m.group(1))
        return PlayBestProblemState(entry, moves)

    raise Exception('unknown problem type: ' + entry['TYPE'])

