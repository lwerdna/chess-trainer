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

class VanillaPgnProblemState(ProblemState):
    def __init__(self, fpath):

        self.pgn_path = fpath
        self.game = chess.pgn.read_game(open(fpath))
        self.user_color = self.game.turn()

        # stack elements are (GameNode/ChildNode, index) of what we're EXPECTING, what comes NEXT
        # so (Father, 0) means nothing has been expanded yet.
        # changes to (Father, 1) when (Son, 0) is made
        self.stack = [(self.game, 0)]

    # we override the parent to set the perspective to the root position
    def initialize_chessboard(self, cboard):
        node, vidx = self.stack[-1]
        board = node.board()
        cboard.set_fen(board.fen())
        cboard.setPerspective(board.turn)
        cboard.update_view()

    # test if a player move is correct
    # move is san, like "Ke4"
    def test_move(self, move):
        node, vidx = self.stack[-1]
        assert node.board().turn != self.user_color

        nodea = node
        nodeb = node.variations[vidx]

        # TODO: allow multiple user moves
        expect_move = node.board().san(nodeb.move)

        if move == expect_move:
            return True
        else:
            print(f'{move} was wrong, expected {expect_move}')
            self.correct = False
            return False

    def next_variation(self, node, index):
        if not node.variations or index >= len(node.variations):
            return None
        return node.variations[index]

    def backtrack(self):

    # enter player move (assuming it's tested as correct)
    def update_move(self, move, cboard):
        assert self.test_move(move)

        # consume the current move
        parent, vidx = self.stack.pop()

        child = self.next_variation(parent, vidx)
        if not child:
            self.backtrack()
            return

        # append the child
        self.stack.push((parent, vidx+1))
        self.stack.push((child, 0))

        # if the current state has an opponent move, make it
        parent, vidx = self.stack[-1]
        if parent.board.turn() != self.user_color:
            if child := self.next_variation(parent, vidx)
                self.stack.pop()
                reply = parent.board().san(child.move)
                cboard.move_glide(reply)
                self.stack.push((parent, vidx+1))
                self.stack.push((child, 0))

        # 
            child = parent.variations[0]
            self.stack.append((child, 0))
            pushed = True

        parent, vidx = self.stack[-1]
        if not parent.variations:
            while True:
                self.stack.pop()
                parent, vidx = self.stack[-1]
                if parent.board().turn == self.vidx+1 < len(parent.variations):
                    self.stack.pop()
                    self.stack.push((parent, vidx+1))
                    break

        if not parent.variations or vidx + 1

        self.initialize_chessboard(cboard)
        # ascend
        else:
            # are there alternative moves for user?
            if vidx+1 < len(parent.variations):
                self.stack.pop()
                self.stack.append((parent, vidx+1))
            else:
                
            
        debug.breakpoint()

        self.halfmove_index += 1
        self.board.push_san(move)

    def is_node_exhausted(node, index=0):
        l = len(node.variations)
        return l==0 or index>=l

    def is_done(self):
        return len(self.stack) > 0

    def get_message(self):
        node, child_idx = self.stack[-1]
        return node.comment

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

