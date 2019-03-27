from . import common
from . import chess
import copy

# patterns/cycles/pw


def check(problem, board, solution):
    retval = {}

    # patterns/cycles
    tb = TrajectoriesBuilder()
    tb.visit(solution, [])
    traverse_trajectories([], tb.result, retval)

    # pw
    traverse_for_platzwechsel([], solution.siblings, retval)

    return retval


def traverse_for_platzwechsel(head, tail, retval):
    if len(head) > 2:
        # upon each move in the solution tree:
        # 1) trace piece route to the arrival square (route)
        # 2) find all who left from the arrival square (candidates)
        # 3) for each of them check if they crossed the route
        route, candidates = [], []
        for i in range(len(head) - 1):
            if head[i].departing_piece_id == head[-1].departing_piece_id:
                route.append(head[i].dep[1])
            if head[i].dep[
                    1] == head[-1].arr[1] and head[i].departing_piece_id != head[-1].departing_piece_id:
                candidates.append(head[i].departing_piece_id)
            if head[i].departing_piece_id in candidates and head[
                    i].arr[1] in route:
                retval['Platzwechsel'] = True
                retval['Platzwechsel(' + get_piece_name(head[-1].dep[0]) +
                       '/' + get_piece_name(head[i].dep[0]) + ')'] = True

    for node in tail:
        new_head = copy.copy(head)
        if isinstance(
                node,
                chess.MoveNode) and not isinstance(
                node.move,
                chess.NullMove):
            new_head.append(node.move)
        traverse_for_platzwechsel(new_head, node.siblings, retval)

# rundlauf: cycle of length > 3 w/o repeated squares, all squares are not on a single line
# switchback: any other cycle


def traverse_trajectories(head, tail, retval):
    # patterns
    if len(head) > 0:
        if len(head[-1].branches) > 3:
            patterns = get_patterns(head[-1].square)
            for (name, squares) in list(patterns.items()):
                if len(squares) == len([y for y in squares if y in [
                        x.square for x in head[-1].branches]]):
                    retval[name] = True
                    # todo albino/p-ny
                    retval[
                        name + '(' + get_piece_name(head[-1].piece) + ')'] = True
    # cycles
    if len(head) > 2:
        # search the head backwards to find its last element
        prev = -1
        for i in range(len(head) - 2, -1, -1):
            if head[i].square == head[-1].square:
                rl = len(head) - 1 - i > 1  # cycle length > 2
                if rl:  # all cycle elements are different
                    rl = common.all_different(
                        [x.square for x in head[i + 1:len(head) - 2]])
                if rl:  # all cycle elements are not on the same line
                    for j in range(i + 1, len(head) - 2):
                        if not chess.LUT.att['q'][
                                head[i].square][
                                head[j].square]:
                            break
                    else:
                        rl = False
                if rl:
                    retval['Rundlauf'] = True
                    retval[
                        'Rundlauf(' + get_piece_name(head[-1].piece) + ')'] = True
                else:
                    retval['Switchback'] = True
                    retval[
                        'Switchback(' + get_piece_name(head[-1].piece) + ')'] = True

    for tnode in tail:
        new_head = copy.copy(head)
        new_head.append(tnode)
        traverse_trajectories(new_head, tnode.branches, retval)


class TNode:

    def __init__(self, square, id, piece):
        self.square, self.id, self.piece, self.branches = square, id, piece, []

    def dump(self, level):
        for i in range(level):
            print(" ", end=' ')
        print('->', self.piece + chess.to_xy(self.square))
        for tn in self.branches:
            tn.dump(level + 1)


class TrajectoriesBuilder():

    def __init__(self):
        self.result = []

    def visit(self, solution_node, level):
        if isinstance(
                solution_node,
                chess.MoveNode) and not isinstance(
                solution_node.move,
                chess.NullMove):
            # looking for the piece in the result
            for tnode in self.result:
                if tnode.id == solution_node.move.departing_piece_id and tnode.piece == solution_node.move.dep[0]:
                    # if it is not in level
                    for tnode2 in level:
                        if tnode2.id == tnode.id and tnode2.piece == tnode.piece:
                            pass
                    else:
                        level.append(tnode)
                    break  # ok, it's there
            else:
                new_tnode = TNode(
                    solution_node.move.dep[1],
                    solution_node.move.departing_piece_id,
                    solution_node.move.dep[0])
                self.result.append(new_tnode)
                level.append(new_tnode)
            # looking for the piece in the level
            for i in range(len(level)):
                if level[i].id == solution_node.move.departing_piece_id and level[i].piece == solution_node.move.dep[0]:
                    new_tnode = TNode(
                        solution_node.move.arr[1],
                        level[i].id,
                        level[i].piece)
                    level[i].branches.append(new_tnode)
                    new_level = []
                    for j in range(len(level)):
                        if i != j:
                            new_level.append(level[j])
                        else:
                            new_level.append(new_tnode)
                    level = new_level
                    break
        for node in solution_node.siblings:
            self.visit(node, level)


def get_patterns(square):
    patterns = {
        'Star': [(1, 1), (1, -1), (-1, 1), (-1, -1)],
        'Big star': [(2, 2), (2, -2), (-2, 2), (-2, -2)],
        'Cross': [(0, 1), (0, -1), (-1, 0), (1, 0)],
        'Big cross': [(0, 2), (0, -2), (-2, 0), (2, 0)],
        'Wheel': [(1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2)],
        'Albino': [(-1, -1), (1, -1), (0, -1), (0, -2)],
        'Pickaninny': [(-1, 1), (1, 1), (0, 1), (0, 2)],
    }
    retval = {}
    x, y = chess.LUT.to_xy(square)
    for (name, vecs) in list(patterns.items()):
        tmp = []
        for (a, b) in vecs:
            x_, y_ = x + a, y + b
            if chess.LUT.oob(x_, y_):
                break
            tmp.append(chess.LUT.from_xy(x_, y_))
        else:
            retval[name] = tmp
    return retval


def get_piece_name(piece):
    return "WB"[piece == piece.lower()] + piece.upper()
