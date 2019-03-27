import model

class Analyzer:

    def __init__(self): pass

    def analyze(self, entry, solution, board, acc):
        matches = model.RE_COMMON_STIPULATION.match(entry['stipulation'])
        if not matches or matches.group("aim") not in "#=" or model.hasFairyElements(entry):
            return
        aim = matches.group("aim")
