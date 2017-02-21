# -*- coding: utf-8 -*-

from PyRTF import *
import model

columns = 2
rows = 3

class ExportDocument:
    
    def __init__(self, records, Lang):
        self.records, self.Lang = records, Lang
        
    def do_export(self, filename):
        doc = Document()
	section = Section()
	doc.Sections.append(section)
        
        solutions = Section()
        p = Paragraph()
        p.append(str(self.records[0]['solution']))
        solutions.append(p)
        
        print str(self.records[0]['solution'])
        
        doc.Sections.append(solutions)        
        Renderer().Write(doc, file('%s' % filename, 'w'))
