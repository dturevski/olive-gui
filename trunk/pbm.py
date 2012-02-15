#!/usr/bin/env python
# -*- coding: utf-8 -*-
# pbm2popeye 0.1.0 Copyright 2008 
# Author: Dmitri Turevski <dmitri.turevski@gmail.com>
# 
# This program is distributed under the terms of the GNU General Public License
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#

# standard
import sys
import array
import copy

# local
import model

# may be altered from outside
PBM_ENCODING = "ISO-8859-1"

class PbmEntries:
    def __init__(self, file):
        self.file = file
        self.num_entries = read_int(file, 'H') + 1
        self.entries_read = 0
    def __iter__(self):
        return self
    def next(self):
        if self.num_entries == self.entries_read:
            raise StopIteration
        r = Record(self.file)
        self.entries_read = self.entries_read + 1
        return r.to_yacpdb_struct()

def readPbm(filename): # throws (IOError)
    input = open(filename)
    records = []
    try:
        num_entries = read_int(input, 'H') + 1
        print num_entries
        for i in xrange(num_entries):
            r = Record(input)
            records.append(r.to_yacpdb_struct())
            #r.dump(i != num_entries - 1)
    #except IOError, IndexError:
    except:
        raise
        
    input.close()

def read_int(file, decl):
    v = array.array(decl)
    v.fromfile(file, 1)
    return v[0]

def read_string(file):
    offset = read_int(file, 'L')
    cur_pos = file.tell()
    file.seek(offset)
    string = file.read(read_int(file, 'H'))
    file.seek(cur_pos)
    return unicode(string.decode(PBM_ENCODING))

def byte2piece(byte):
    if byte == 32:
        return ''
    byte = byte - 33
    if (byte < 0) or (byte > 14):
        return '?'
    return 'RQBSPK???kpsbqr'[byte]

def byte2square(byte):
    byte = byte - 32
    return 'abcdefgh'[byte % 8] + '87654321'[byte // 8]

def bytes2stipulation(byte1, byte2):
    #binary = lambda i, c = (lambda i, c: i and (c(i >> 1, c) + str(i & 1)) or ''): c(i, c)
    #print binary(byte1), byte2
    
    type = ['', 'h', 's', 'r'][byte1 % 4]
    type = type + ['#', '='][(byte1 & (1 << 4)) != 0]
    if byte1 & (1 << 3) :
        type = 'Ser-' + type
    num_moves = byte2
    if byte1 & (1 << 6) :
        num_moves = str(num_moves - 1) + '.5'
    
    return type + str(num_moves), byte1 & (1 << 5)

class Record:
    def __init__(self, file):
        read_int(file, 'H') # skip id
        self.stipulation, self.is_maximummer = \
            bytes2stipulation(read_int(file, 'B'), read_int(file, 'B'))
        
        self.info = {}
        for field in ['author', 'source', 'distinction', 'comments', 'text', \
            'twins', 'extra']:
            self.info[field] = read_string(file)
            
        self.comments = []
        for field in ['comments', 'text', 'extra']:
            if self.info[field]:
                for line in self.info[field].split("\n"):
                    self.comments.append(field + ': ' + line.strip())
        
        self.parse_twins()
        
        self.fen, blanks = '', 0
        for i in xrange(64):
            if((i > 0) and (i % 8 == 0)): # new row
                self.fen = self.fen + ['', str(blanks)][blanks > 0]
                self.fen = self.fen + "/"
                blanks = 0
            piece = byte2piece(read_int(file, 'B'))
            if(piece != ''):
                self.fen = self.fen + ['', str(blanks)][blanks > 0]
                self.fen = self.fen + piece
                blanks = 0
            else:
                blanks = blanks + 1
        self.fen = self.fen + ['', str(blanks)][blanks > 0]

    def parse_twins(self):
        self.is_duplex = self.succesive_twining = self.is_zero = False
        self.twins = []
        if self.info['twins'] == '':
            return
        self.succesive_twining = ord(self.info['twins'][0]) == 126
        self.is_zero = True

        twins = []
        for i in xrange(len(self.info['twins']) // 4):
            #for j in xrange(4):
            #    print ord(self.info['twins'][1 + 4*i + j]) - 32,
            #print
            combined = (ord(self.info['twins'][1 + 4*i]) & (1<<6)) != 0

            type, square1, square2, piece  = \
                ord(self.info['twins'][1 + 4*i]) & 31, \
                byte2square(ord(self.info['twins'][1 + 4*i + 1])), \
                byte2square(ord(self.info['twins'][1 + 4*i + 2])), \
                byte2piece(ord(self.info['twins'][1 + 4*i + 3]))
            piece = ['white', 'black'][piece.lower() == piece] + ' ' + piece
            #print type, square1, square2, piece
            if 0 == type:
                self.is_zero = False
            elif 1 == type:
                twins.append('move %s %s' % (square1, square2))
            elif 2 == type:
                twins.append('remove %s' % (square1))
            elif 3 == type:
                twins.append('add %s%s' % (piece, square1))
            elif 4 == type:
                twins.append('remove %s add %s%s' % \
                    (square1, piece, square2))
            elif 5 == type:
                twins.append('exchange %s %s' % (square1, square2))
            elif 6 == type:
                twins.append('rotate 90')
            elif 7 == type:
                twins.append('rotate 180')
            elif 8 == type:
                twins.append('rotate 270')
            elif 9 == type:
                twins.append('shift %s %s' % (square1, square2))
            elif 10 == type:
                self.comments.append('unsupported twin: torus shift %s %s' %\
                    (square1, square2))
            elif 11 == type:
                twins.append('mirror a1<-->a8')
            elif 12 == type:
                twins.append('mirror a1<-->h1')
            elif 13 == type:
                stipulation, is_maximummer = bytes2stipulation(\
                        ord(self.info['twins'][1 + 4*i + 1]) - 32, \
                        ord(self.info['twins'][1 + 4*i + 2]) - 32 )
                twin = []
                if stipulation != self.stipulation:
                    twin.append('stipulation ' + stipulation)
                if is_maximummer and not self.is_maximummer:
                    twin.append('condition maximummer')
                if not is_maximummer and self.is_maximummer:
                    twin.append('condition ')
                twins.append(' '.join(twin))
            elif 14 == type:
                self.comments.append('unsupported twin: after the key')
            elif 15 == type:
                twins.append('PolishType')
            elif 16 == type:
                self.is_duplex = True
            
            if not combined and twins:
                self.twins.append(' '.join(twins))
                twins = []
    def to_yacpdb_struct(self):
        r = {'options':[], 'conditions':[]}
        if self.info['author']:
            r['authors'] = self.info['author'].split(';')
        if self.info['source']:
            r['source'] = self.info['source']
        if self.info['distinction']:
            d = model.Distinction()
            parts = self.info['distinction'].split(u'°')
            d.lo = model.myint(parts[0])
            if len(parts) > 1:
                d.hi = model.myint(parts[1])
            tail = (u'°'.join(parts[1:])).lower()
            if len(parts) == 1:
                tail = self.info['distinction'].lower()
            if 'special' in tail:
                d.special = True
            if 'priz' in tail or 'prix' in tail:
                d.name = 'Prize'
            if 'hono' in tail or 'menti' in tail or 'hm' in tail or 'dicser' in tail:
                d.name = 'HM'
            if 'com' in tail or 'cm' in tail or 'c.' in tail or 'elisme' in tail:
                d.name = 'Comm'
            if 'place' in tail:
                d.name = 'Place'
            r['distinction'] = "%s, (%s)" % (str(d), self.info['distinction'])
        if len(self.comments):
            r['comments'] = self.comments
        if self.is_maximummer:
            r['conditions'].append('BlackMaximummer')
        r['stipulation'] = self.stipulation
        b = model.Board()
        b.fromFen(self.fen)
        r['algebraic'] = b.toAlgebraic()
        if self.is_duplex:
            r['options'].append('Duplex')
        if len(self.twins):
            r['twins'] = {}
            offset = [1, 0][self.is_zero]
            for i, twin in enumerate(self.twins):
                r['twins'][chr(ord('a') + i + offset)] = twin
        return copy.deepcopy(r)
        
    def dump(self, with_separator):
        print
        if self.info['author']:
            print "Author " + self.info['author']
        if self.info['source']:
            print "Origin " + self.info['source']
        if self.info['distinction']:
            print "Title " + self.info['distinction']
        for comment in self.comments:
            print 'Remark', comment
        if self.is_maximummer:
            print "Condition maximummer"
        print "Stipulation " + self.stipulation
        print "Forsyth " + self.fen
        if self.is_duplex:
            print "Option Duplex"
        for index, twin in enumerate(self.twins):
            print ["Twin", "ZeroPosition"][index == 0 and self.is_zero],
            print ["", "continued "][self.succesive_twining] + twin
        print
        if with_separator:
            print "NextProblem"
