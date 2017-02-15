# -*- coding: utf-8 -*-

import model

from PyRTF import *

columns = 2
rows = 3

class ExportDocument:
    
    def __init__(self, records, Lang):
        self.records, self.Lang = records, Lang
        f = open('conf/chessfonts.yaml', 'r')
        self.config = yaml.load(f)
        f.close()
        for family in self.config['diagram-fonts']:
            self.config['config'][family]['fontinfo'] = self.loadFontInfo(
                self.config['config'][family]['glyphs-tab'])
        
    def do_export(self, filename):
        doc = Document()
        ss = doc.StyleSheet
	section = Section()
	doc.Sections.append( section )
        
        diagrams = ""
        solutions = ""
        

        inline_font = self.config[
            'inline-fonts'][self.solFontSelect.currentIndex()]
        diagram_font = self.config[
            'diagram-fonts'][self.diaFontSelect.currentIndex()]
        
        for record in self.records:
            # populate all diagrams
            diagrams += self.build_diagram(record)
            # populate all solutions
            solutions += self.build_solution(record)
        # concat diagrams with solutions
        section.append(diagrams + solutions)
        
        Renderer().Write(doc, file( '%s' % filename, 'w' ))
        
    def build_diagram(self, problem):
        return problem.toAlgebraic()
    
    def build_solution(self, problem):
        result = ""
        if "solution" in problem.entries:
            result = problem.entries["solution"]
        return result