import unittest

from board import Board, Piece, algebraicToIdx


class TestBoardSerialization(unittest.TestCase):

    def test_to_algebraic_sorts_pieces_within_color(self):
        board = Board()
        board.add(Piece('P', 'black', []), algebraicToIdx('c3'))
        board.add(Piece('P', 'black', []), algebraicToIdx('a3'))

        self.assertEqual(['Pa3', 'Pc3'], board.toAlgebraic()['black'])

        board.drop(algebraicToIdx('a3'))
        board.add(Piece('P', 'black', []), algebraicToIdx('a3'))

        self.assertEqual(['Pa3', 'Pc3'], board.toAlgebraic()['black'])


if __name__ == '__main__':
    unittest.main()
