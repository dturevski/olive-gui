from . import common
from . import chess


def provides():
    return ['Unsound', 'Shortmate', 'Cooked', 'Has duals']


# todo: h#*.5 with setplay
def check(problem, board, solution):
    retval = common.retval(provides)

    for twin in solution.siblings:
        twin.make(board)

        if 'intended-solutions' in problem:
            intended = IntendedSolutions(
                problem['intended-solutions'], twin.stipulation)
        else:
            intended = IntendedSolutions('1', twin.stipulation)

        keyplay = twin.keyplay()

        visitor = MaxPlyVisitor()
        keyplay.traverse(board, visitor)
        if visitor.max_ply < twin.stipulation.ply_count:
            retval['Shortmate'] = True

        iv = IntendedVisitor(intended)
        keyplay.traverse(board, iv)
        for k in iv.retval:
            if k != 'Has duals':
                retval[k] = retval[k] or iv.retval[k]

        # skip duals in threats
        iv = IntendedVisitor(intended)
        keyplay.traverse(board, iv, with_threats=False)
        retval['Has duals'] |= iv.retval['Has duals']

        twin.unmake(board)

    return retval


class IntendedSolutions:

    def __init__(self, str, stipulation):
        branching = [0 for x in range(stipulation.ply_count)]
        if str.find('.') == -1:  # case 'n'
            if stipulation.starts_with_null:
                branching[0] = 0
                branching[1] = int(str)
                for i in range(stipulation.ply_count - 2):
                    cur_ply = i + 2
                    if stipulation.style in ['h', 'hs']:
                        branching[cur_ply] = 1
                    else:
                        branching[cur_ply] = cur_ply % 2
            else:
                branching[0] = int(str)
                for i in range(stipulation.ply_count - 1):
                    cur_ply = i + 1
                    if stipulation.style in ['h', 'hs']:
                        branching[cur_ply] = 1
                    else:
                        branching[cur_ply] = (cur_ply + 1) % 2
        else:
            cur_ply = 0
            parts = str.split('.')
            for part in parts:
                if part == '':
                    break
                branching[cur_ply] = int(part)
                cur_ply = cur_ply + 1
            while cur_ply < stipulation.ply_count:
                branching[cur_ply] = 1
                cur_ply = cur_ply + 1
        self.branching = branching

    def match(ply_count, number_of_branches):
        pass


class IntendedVisitor:

    def __init__(self, intended):
        self.intended = intended
        self.retval = common.retval(provides)

    def visit(self, node, board, side_on_move):
        if len(self.intended.branching) <= node.ply_no:
            return  # terminal node
        if self.intended.branching[node.ply_no] == 0:
            return  # doesn't matter
        if len(node.siblings) < self.intended.branching[node.ply_no]:
            self.retval['Unsound'] = True
        if len(node.siblings) > self.intended.branching[node.ply_no]:
            if node.ply_no == 0:
                self.retval['Cooked'] = True
            elif isinstance(node, chess.MoveNode) and not isinstance(node.move, chess.NullMove):
                self.retval['Has duals'] = True


class MaxPlyVisitor:

    def __init__(self):
        self.max_ply = 0

    def visit(self, node, board, side_on_move):
        if node.ply_no > self.max_ply:
            self.max_ply = node.ply_no
