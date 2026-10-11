"""Olive collection state; shared entry helpers live in yacpdb.model."""
from yacpdb.model import *
from base import get_write_dir


class Model:
    file = get_write_dir() + '/conf/default-entry.yaml'

    def __init__(self):
        f = open(Model.file, 'r', encoding="utf8")
        try:
            self.defaultEntry = yaml.safe_load(f)
        finally:
            f.close()
        self.current, self.entries, self.dirty_flags, self.board = -1, [], [], Board()
        self.pieces_counts = []
        self.add(copy.deepcopy(self.defaultEntry), False)
        self.is_dirty = False
        self.filename = ''

    def cur(self):
        return self.entries[self.current]

    def overridden_glyphs(self):
        return self.cur().get('glyphs', {})

    def setNewCurrent(self, idx):
        self.current = idx
        if 'algebraic' in self.entries[idx]:
            self.board.fromAlgebraic(self.entries[idx]['algebraic'])
        else:
            self.board.clear()

    def insert(self, data, dirty, idx):
        self.entries.insert(idx, data)
        self.dirty_flags.insert(idx, dirty)
        if 'algebraic' in data:
            self.board.fromAlgebraic(data['algebraic'])
        else:
            self.board.clear()
        self.pieces_counts.insert(idx, self.board.getPiecesCount())
        self.current = idx
        if(dirty):
            self.is_dirty = True

    def onBoardChanged(self):
        self.pieces_counts[self.current] = self.board.getPiecesCount()
        self.dirty_flags[self.current] = True
        self.is_dirty = True
        self.entries[self.current]['algebraic'] = self.board.toAlgebraic()

    def markDirty(self):
        self.dirty_flags[self.current] = True
        self.is_dirty = True

    def add(self, data, dirty):
        self.insert(data, dirty, self.current + 1)

    def delete(self, idx):
        self.entries.pop(idx)
        self.dirty_flags.pop(idx)
        self.pieces_counts.pop(idx)
        self.is_dirty = True
        if(len(self.entries) > 0):
            if(idx < len(self.entries)):
                self.setNewCurrent(idx)
            else:
                self.setNewCurrent(idx - 1)
        else:
            self.current = -1

    def parseDate(self):
        y, m, d = '', 0, 0
        if 'date' not in self.entries[self.current]:
            return y, m, d
        parts = str(self.entries[self.current]['date']).split("-")
        if len(parts) > 0:
            y = parts[0]
        if len(parts) > 1:
            m = myint(parts[1])
        if len(parts) > 2:
            d = myint(parts[2])
        return y, m, d

    def twinsAsText(self):
        if 'twins' not in self.entries[self.current]:
            return ''
        return "\n".join([k + ': ' + self.entries[self.current]['twins'][k]
                          for k in sorted(self.entries[self.current]['twins'].keys())])

    def saveDefaultEntry(self):
        f = open(Model.file, 'wb')
        try:
            f.write(yaml.dump(self.defaultEntry, encoding='utf8', allow_unicode=True))
        finally:
            f.close()

    def toggleOption(self, option):
        if 'options' not in self.entries[self.current]:
            self.entries[self.current]['options'] = []
        if option in self.entries[self.current]['options']:
            self.entries[self.current]['options'].remove(option)
        else:
            self.entries[self.current]['options'].append(option)
        self.markDirty()
