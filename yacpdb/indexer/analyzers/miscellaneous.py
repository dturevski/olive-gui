import copy
import p2w.nodes, model

# Phases+Twins+Zilahi


class Analyzer:

    def __init__(self): pass

    def analyze(self, entry, solution, board, acc):
        parity = 1 \
            if board.getSideToCompleteLineByStipulation(entry["stipulation"]) != \
                    board.getStmByStipulation(entry["stipulation"]) \
            else 0
        visitor = ZilahiTraverser(parity)
        visitor.visit(solution, board, {}, frozenset())
        for _ in xrange(visitor.phases):
            acc.push("Phases")
        for _ in xrange(visitor.twins):
            acc.push("Twins")

        non_cyclical_zp = False
        matches = model.RE_COMMON_STIPULATION.match(entry["stipulation"])
        if matches and matches.group("play").lower() in ["h", "hs", "ser-h"]:
            non_cyclical_zp = True

        visitor.zilahi(acc, non_cyclical_zp)


class ZilahiTraverser:

    class ZInfo:
        def __init__(self, moved, captured, finalizer):
            self.captured, self.finalizer = {}, finalizer
            for origin in captured:
                self.captured[origin] = (captured[origin], origin not in moved)

    def __init__(self, parity):
        self.parity = parity
        self.twins, self.phases, self.zinfo = 0, 0, []

    def visit(self, node, board, captured, moved):
        if node.depth == 1:
            self.twins += 1
        if node.depth == 2:
            self.phases += 1

        m = moved | set([board.board[node.departure].origin] if hasattr(node, "departure") else [])
        c = copy.copy(captured)
        if hasattr(node, "capture") and node.capture != -1:
            c[board.board[node.capture].origin] = board.board[node.capture].toPredicatePieceDomain()

        if len(node.children) == 0 and node.depth % 2 == self.parity and hasattr(node, "departure"): # if parity mismatch, it's a refutation
            self.zinfo.append(ZilahiTraverser.ZInfo(m, c, board.board[node.departure]))
        else:
            node.make(board)
            for ch in node.children:
                self.visit(ch, board, c, m)
            node.unmake(board)

    def zilahi(self, acc, non_cyclical_zp):
        accounted, self.cycles, incycles = frozenset(), set(), set()
        # if we start from all phases, we will count each cycle as many times as there are phases in the cycle
        for i, info in enumerate(self.zinfo):
            self.recurse(i, accounted | set([info.finalizer.origin]), info.finalizer, [])
        for cycle in self.cycles:
            #print cycle
            acc.push("Zilahi(%d)" % len(cycle))
            for origin, piece, passive, phaseno in cycle:
                incycles.add(origin)
                acc.push("ZilahiPiece(%s, %s)" % (piece, str(passive).lower()))

        # and now zpieces, that are not part of cycles
        if not non_cyclical_zp:
            return
        accounted2 = set()
        for i, info in enumerate(self.zinfo):
            o = info.finalizer.origin
            if o not in incycles:
                for j, info2 in enumerate(self.zinfo):
                    if j != i and o in info2.captured and o not in accounted2:
                        acc.push("ZilahiPiece(%s, %s)" % (
                            info2.captured[info.finalizer.origin][0],
                            str(info2.captured[info.finalizer.origin][1]).lower()
                        ))
                        accounted2.add(o)



    def recurse(self, cycle_completes_at, accounted_origins, finalizer, cycle):
        for i, info in enumerate(self.zinfo):
            if finalizer.origin in info.captured:
                c = cycle + [(finalizer.origin, info.captured[finalizer.origin][0], info.captured[finalizer.origin][1], i)]
                if i == cycle_completes_at:
                    if len(c) > 1:
                        self.cycles.add(self.normalizeCycle(c))
                elif i > cycle_completes_at and not info.finalizer.origin in accounted_origins:
                    self.recurse(cycle_completes_at, accounted_origins | set([info.finalizer.origin]),  info.finalizer, c)


    def normalizeCycle(self, cycle): # make it start from alphanumerically first origin
        o, ix, c = cycle[0][0], 0, []
        for i, t in enumerate(cycle):
            if t[0] < o:
                o = t[0]
                ix = i
        for i in xrange(len(cycle)):
            c.append(cycle[(ix+i)%len(cycle)])
        return tuple(c) # tuple() because list is unhashable type, can't be added to set