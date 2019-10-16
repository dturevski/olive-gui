from . import popeye
from . import finales
from . import chess
from . import soundness
from . import key
from . import trajectories

VERSION = '2010-10-28'


def process(problem):
    retval = {
        'version': VERSION,
        'status': 'unsupported',
        'ash': problem['ash']}

    retval['raw'] = popeye.run(popeye.create_input(problem))  # todo: try/catch
    solution = popeye.parse_output(problem, retval['raw'])  # todo: try/catch

    output = chess.SolutionOutput(True)
    b = chess.Board()
    b.from_algebraic(problem['algebraic'])
    output.create_output(solution, b)
    retval['status'] = 'ok'

    retval['olive'] = {
        'solution': output.solution,
        'boardshots': output.boardshots,
        'keywords': []}
    for module in [finales, soundness, key, trajectories]:
        x = module.check(problem, b, solution)
        for k in x:
            if x[k]:
                retval['olive']['keywords'].append(k)

    return retval
