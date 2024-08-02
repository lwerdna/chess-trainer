import time
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
    def update_move(self, move_san, cboard, message):
        pass

    def get_message(self):
        return ''

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

    def update_move(self, move, cboard, message):
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
    def update_move(self, move, cboard, message):
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

class NodeAgent():
    def __init__(self, node):
        self.current = node

        # map nodes to the variation indices we've travelled
        self.lookup = {n: set() for n in collect_nodes(node)}

        self.player = node.turn()

    def step(self, move=None):
        if self.exhausted():
            if type(self.current) == chess.pgn.Game:
                return 'DONE'
            self.current = self.current.parent
            return 'ASCENDED'

        # not exhausted
        if self.current.turn() == self.player:
            if move is None:
                return 'WAITING'
            allmoves = self.all_moves()
            vidx = allmoves.index(move)
            self.lookup[self.current].add(vidx)
            self.current = self.current.variations[vidx]
            return 'DESCENDED'
        else:
            visited_idxs = self.lookup[self.current]

            # pick next variation for opponent
            for vidx in range(len(self.current.variations)):
                if not vidx in visited_idxs:
                    self.lookup[self.current].add(vidx)
                    self.current = self.current.variations[vidx]
                    return 'DESCENDED'
            raise Exception('tested descendable, but unable to find unvisited variation')

    def all_moves(self):
        node = self.current
        visited = self.lookup[node]
        board = node.board()
        return [board.san(v.move) for v in node.variations]

    def accepted_moves(self):
        visited = self.lookup[self.current]
        return [m for i,m in enumerate(self.all_moves()) if not i in visited]

    # have we exhausted all paths from this node?
    def exhausted(self):
        if not self.current.variations:
            return True

        if not self.current in self.lookup:
            return False

        visited_idxs = self.lookup[self.current]
        return len(visited_idxs) >= len(self.current.variations)

    def done(self):
        return type(self.current) == chess.pgn.Game and self.exhausted()

    def turn(self):
        return self.current.turn()

class VanillaPgnProblemState(ProblemState):
    def __init__(self, fpath):
        self.pgn_path = fpath
        self.game = chess.pgn.read_game(open(fpath))
        self.user_color = self.game.turn()
        self.agent = NodeAgent(self.game)

    # we override the parent to set the perspective to the root position
    def initialize_chessboard(self, cboard):
        board = self.game.board()
        cboard.set_fen(board.fen())
        cboard.setPerspective(self.user_color)
        cboard.update_view()

    # test if a player move is correct
    # move is san, like "Ke4"
    def test_move(self, move):
        okmoves = self.agent.accepted_moves()
        if move in okmoves:
            print(f'test_move({move}) returns True')
            return True
        print(f'{move} was wrong, expected one of {okmoves}')
        print(f'test_move({move}) returns False')
        return False

    def update_move(self, move, cboard, message):
        print(f'update_move({move})')
        assert self.test_move(move)
        assert self.agent.current.turn() == self.user_color
        assert not self.agent.exhausted()

        assert self.agent.step(move) == 'DESCENDED'
        if comment := self.agent.current.comment:
            message(comment)

        assert self.agent.turn() != self.user_color

        # if an opponent reply is there, move it
        if not self.agent.exhausted():
            preboard = self.agent.current.board()
            assert self.agent.step() == 'DESCENDED'
            if comment := self.agent.current.comment:
                message(comment)
            move = preboard.san(self.agent.current.move)
            print(f'auto-playing move {move}')
            cboard.move_glide(move)

        # if the traversal bottomed out, back it out
        while self.agent.exhausted() and not self.agent.done():
            assert self.agent.step() == 'ASCENDED'
            #time.sleep(.300)
            cboard.undo_glide()

        # if an opponent reply is there, move it
        if self.agent.turn() != self.user_color:
            preboard = self.agent.current.board()
            assert self.agent.step() == 'DESCENDED'
            move = preboard.san(self.agent.current.move)
            print(f'auto-playing move {move}')
            cboard.move_glide(move)
            if comment := self.agent.current.comment:
                message(comment)

    def is_done(self):
        return self.agent.done()

    def get_message(self):
        return self.agent.current.comment

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

