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
	
        diagrams = Section()
	diagrams.Header.append('Problems')
        
        solutions = Section()
        solutions.Header.append('Solutions')
        
        for i, problem in enumerate(self.records):
            p_diag = Paragraph()
            p_diag.append(str(i+1) + str('. '))
            p_diag.append(self.prepare_diagram(problem))
            diagrams.append(p_diag)
            
            p_sol = Paragraph()
            p_sol.append(str(i+1) + str('. '))
            p_sol.append(self.prepare_solution(problem))
            solutions.append(p_sol)
        
#        print str(self.records[0]['solution'])
        
        doc.Sections.append(diagrams)        
        doc.Sections.append(solutions)        
        Renderer().Write(doc, file('%s' % filename, 'w'))
        
    def prepare_diagram(self, problem):
        return 'diagram'
    
    def prepare_solution(self, problem):
        if 'solution' in problem:
            return str(problem['solution'])
        return ''
            
