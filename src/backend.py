from pathlib import Path
from abc import ABC, abstractmethod
import pickle

from game_state import GameState
from board import Side, Board


class Backend(ABC):

    def __init__(self, size):
        self._size = size

    @abstractmethod
    def get_all_possible_boards_numbers(self):
        pass

    @abstractmethod
    def get_moves(self, board, turn):
        pass

    @abstractmethod
    def make_move(self, board, turn, move):
        pass

    def _generate_all_possible_boards(self):
        boards = set()
        game_states = {GameState.create_initial(self._size, LiveBackend(self._size))}

        while game_states:
            game_state = game_states.pop()

            if game_state in game_states:
                continue

            if game_state.is_finished():
                boards.update([game_state.board_view, game_state.opposite_board_view])
            else:
                boards.add(game_state.board_view)

            for move in game_state.get_moves():
                next_game_state = game_state.copy().make_move(move)
                game_states.add(next_game_state)

        return boards


class LiveBackend(Backend):

    def __init__(self, size):
        super().__init__(size)
        self.__boards_numbers = None

    def get_all_possible_boards_numbers(self):
        if self.__boards_numbers is None:
            self.__boards_numbers = tuple(board.number for board in self._generate_all_possible_boards())
        return self.__boards_numbers

    def get_moves(self, board, turn):
        moves_array = board.get_legal_moves(turn)
        return tuple(map(tuple, moves_array))

    def make_move(self, board, turn, move):
        new_board = board.make_move(move, turn)
        new_turn = -turn if board.has_any_moves(-turn) else turn
        return new_board, new_turn


class PreparedBackend(Backend):

    def __init__(self, size):
        super().__init__(size)
        self.__transitions = self.__load_or_generate_transitions()

    def get_all_possible_boards_numbers(self):
        return tuple(self.__transitions.keys())

    def get_moves(self, board, turn):
        relative_board = board.to_relative(turn)
        return tuple(self.__transitions[relative_board.number].keys())

    def make_move(self, board, turn, move):
        relative_board = board.to_relative(turn)
        is_turn_change, next_relative_board_number = self.__transitions[relative_board.number][move]
        next_board = Board.create_from_number(next_relative_board_number, self._size).to_absolute(turn)
        next_turn = -turn if is_turn_change else turn
        return next_board, next_turn

    def __get_file_location(self):
        root_path = Path(__file__).parent.parent
        filename = f'{self._size[0]}x{self._size[1]}_transitions.pickle'
        return root_path / 'res' / filename

    def __load_or_generate_transitions(self):
        if self.__transitions_file_exists():
            print('Loading prepared transitions...')
            return self.__load_transitions()
        else:
            print('Preparing transitions transitions...')
            transitions = self.__generate_transitions()
            self.__save_transitions(transitions)
            return transitions

    def __transitions_file_exists(self):
        return self.__get_file_location().exists()

    def __load_transitions(self):
        with open(self.__get_file_location(), 'rb') as f:
            return pickle.load(f)

    def __save_transitions(self, transitions):
        with open(self.__get_file_location(), 'wb') as f:
            pickle.dump(transitions, f)

    def __generate_transitions(self):
        transitions = {}

        for board in self._generate_all_possible_boards():
            game_state = GameState(board, Side.ME, LiveBackend(self._size))
            moves = game_state.get_moves()
            moves_dict = {move: self.__get_move_result(game_state, move) for move in moves}
            transitions[board.number] = moves_dict

        return transitions

    def __get_move_result(self, game_state, move):
        next_game_state = game_state.copy().make_move(move)
        is_turn_change = next_game_state.turn == Side.OPPONENT
        next_board = next_game_state.board.to_relative(Side.ME)
        return is_turn_change, next_board.number
