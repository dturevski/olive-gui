import datetime
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import logging
import traceback

import model

GATEWAY = "http://88.119.26.162/helpman/HelpmAn.exe/"

class Analyzer:

    def __init__(self):
        self.version = datetime.datetime(2018, 3, 14)

    # must be helpmate w/o fairy elements
    def isApplicable(self, entry):
        matches = model.RE_COMMON_STIPULATION.match(entry['stipulation'])
        if not (matches and matches.group("aim") == "#" and matches.group("play").lower() == "h"):
            return False # not a helpmate
        return not model.hasFairyElements(entry)


    def analyze(self, entry, solution, board, acc):
        if not self.isApplicable(entry):
            return
        try:
            params = { "a": "3", "fen": board.toFen(), "stip": entry["stipulation"], "sol": entry["solution"] }
            if 'twins' in entry:
                params['twins'] = " ".join(["%s) %s" % (k, entry['twins'][k]) for k in sorted(entry['twins'].keys())])
            for predicate in urllib.request.urlopen(urllib.request.Request(GATEWAY, urllib.parse.urlencode(params))).read().split("\n"):
                #todo xN modifiers & syntax differencies
                acc.push(predicate)
        except Exception as ex:
            logging.warn(traceback.format_exc(ex))
