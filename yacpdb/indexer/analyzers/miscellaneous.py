import p2w.nodes

# Phases+Twins+Zilahi


class Analyzer:

    def __init__(self): pass

    def analyze(self, entry, solution, board, acc):
        parity = 1 \
            if board.getSideToCompleteLineByStipulation(entry["stipulation"]) != \
                    board.getStmByStipulation(entry["stipulation"]) \
            else 0
        visitor = ZilahiTraverser(parity)
        visitor.visit(solution, board, frozenset(), frozenset())
        for _ in xrange(visitor.phases):
            acc.push("Phases")
        for _ in xrange(visitor.twins):
            acc.push("Twins")
        visitor.zilahi(acc)


class ZilahiTraverser:

    class ZInfo:
        def __init__(self, moved, captured, finalizer):
            self.captured, self.finalizer = {}, finalizer
            for origin in captured:
                self.captured[origin] = origin not in moved

    def __init__(self, parity):
        self.parity = parity
        self.twins, self.phases, self.zinfo = 0, 0, []

    def visit(self, node, board, captured, moved):
        if node.depth == 1:
            self.twins += 1
        if node.depth == 2:
            self.phases += 1

        m = moved | set([board.board[node.departure].origin] if hasattr(node, "departure") else [])
        c = captured | set([board.board[node.capture].origin]if hasattr(node, "capture") and node.capture != -1 else [])

        if len(node.children) == 0 and node.depth % 2 == self.parity: # if parity mismatch, it's a refutation
            self.zinfo.append(ZilahiTraverser.ZInfo(m, c, board.board[node.departure]))
        else:
            node.make(board)
            for ch in node.children:
                self.visit(ch, board, c, m)
            node.unmake(board)

    def zilahi(self, acc):
        accounted, visited, self.cycles, incycles = frozenset(), frozenset(), set(), set()
        # if we start from all phases, we will count each cycle as many times as there are phases in the cycle
        for i, info in enumerate(self.zinfo):
            self.recurse(i, visited | set([i]), accounted | set([info.finalizer.origin]), info.finalizer, [])
        for cycle in self.cycles:
            #print cycle
            acc.push("Zilahi(%d)" % len(cycle))
            for origin, piece, passive in cycle:
                incycles.add(origin)
                acc.push("ZilahiPiece(%s, %s)" % (piece, str(passive).lower()))

        # and now zpieces, that are not part of cycles
        for i, info in enumerate(self.zinfo):
            if info.finalizer.origin not in incycles:
                for j, info2 in enumerate(self.zinfo):
                    if j != i and info.finalizer.origin in info2.captured:
                        acc.push("ZilahiPiece(%s, %s)" % (
                            info.finalizer.toPredicatePieceDomain(),
                            str(info2.captured[info.finalizer.origin]).lower()
                        ))



    def recurse(self, cycle_completes_at, visited_phases, accounted_origins, finalizer, cycle):
        for i, info in enumerate(self.zinfo):
            if finalizer.origin in info.captured:
                c = cycle + [(finalizer.origin, finalizer.toPredicatePieceDomain(), info.captured[finalizer.origin])]
                if i == cycle_completes_at:
                    self.cycles.add(self.normalizeCycle(c))
                elif not i in visited_phases and not info.finalizer.origin in accounted_origins:
                    self.recurse(cycle_completes_at, visited_phases | set([i]),
                                 accounted_origins | set([info.finalizer.origin]),  info.finalizer, c)


    def normalizeCycle(self, cycle): # make it start from alphanumerically first origin
        o, ix, c = cycle[0][0], 0, []
        for i, t in enumerate(cycle):
            if t[0] < o:
                o = t[0]
                ix = i
        for i in xrange(len(cycle)):
            c.append(cycle[(ix+i)%len(cycle)])
        return tuple(c) # tuple() because list is unhashable type, can't be added to set