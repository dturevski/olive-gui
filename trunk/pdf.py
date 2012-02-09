# -*- coding: utf-8 -*-
from reportlab.pdfgen import canvas
import reportlab.rl_config
reportlab.rl_config.warnOnMissingFontGlyphs = 0
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import reportlab.platypus
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors

import model

A4_LANDSCAPE_H, A4_LANDSCAPE_W = A4
A5_MARGIN_X, A5_MARGIN_Y = 10, 10

FONT_FAMILY = 'DejaVu Serif Condensed'
FONT_SIZE = {'header':12, 'chess':16, 'subscript':8, 'footer':12, 'rightpane': 12}
FONT_DIR = 'resources/fonts/dejavu/'
FONT_INFO = \
    {'normal':(FONT_FAMILY+'', 'DejaVuSerifCondensed.ttf'),
    'bold':(FONT_FAMILY+' Bold', 'DejaVuSerifCondensed-Bold.ttf'),
    'italic':(FONT_FAMILY+' Italic', 'DejaVuSerifCondensed-Italic.ttf'),
    'boldItalic':(FONT_FAMILY+' Bold Italic', 'DejaVuSerifCondensed-BoldItalic.ttf')
    }
CHESS_FONTS = {\
    'd':('GC2004D', 'resources/fonts/gc2004d_.ttf'), 
    'x':('GC2004X', 'resources/fonts/gc2004x_.ttf'), 
    'y':('GC2004Y', 'resources/fonts/gc2004y_.ttf')
    }    
for variation in FONT_INFO.keys():
    pdfmetrics.registerFont(TTFont(FONT_INFO[variation][0], FONT_DIR+FONT_INFO[variation][1]))
pdfmetrics.registerFontFamily(FONT_FAMILY,\
    normal=FONT_INFO['normal'][0], bold=FONT_INFO['bold'][0],\
    italic=FONT_INFO['italic'][0], boldItalic=FONT_INFO['boldItalic'][0])
for key in CHESS_FONTS.keys():
    pdfmetrics.registerFont(TTFont(CHESS_FONTS[key][0], CHESS_FONTS[key][1]))
    pdfmetrics.registerFontFamily(key, normal=key, bold=key, italic=key, boldItalic=key)

    
class ExportDocument:
    def __init__(self, records):
        self.records = records
    def doExport(self, filename):
        frameTemplate = reportlab.platypus.Frame(0, 0, A4_LANDSCAPE_W, A4_LANDSCAPE_H, leftPadding=48, bottomPadding=48, rightPadding=48, topPadding=48, showBoundary=1)
        pageTemplate = reportlab.platypus.PageTemplate(frames=[frameTemplate])
        docTemplate = reportlab.platypus.BaseDocTemplate(filename, pagesize=(A4_LANDSCAPE_W, A4_LANDSCAPE_H),\
            pageTemplates=[pageTemplate],\
            showBoundary=1,\
            leftMargin=0,\
            rightMargin=0,\
            topMargin=0,\
            bottomMargin=0,\
            allowSplitting=1,\
            _pageBreakQuick=1)
        

        styles = getSampleStyleSheet()
        styleN = styles['Normal']
        styleH = styles['Heading1']
        story = []
        #add some flowables
        #story.append(reportlab.platypus.Paragraph("This is a Heading",styleH))
        
        b = model.Board()
        b.fromFen('3K2k1/3Rr1p1/4p1R1/6b1/5P1P/8/4P3/8')
        x = unicode(self.board2Html(b).decode("ISO-8859-1"))
        story.append(reportlab.platypus.Paragraph('<para autoLeading="max">'+x+'</para>', styleN))
        story.append(self.subscript('asdasd', 'aDSASD'))


        docTemplate.build(story)
        
    def subscript(self,  left,  right):
        t = reportlab.platypus.Table([[left,  right]], colWidths=[4*FONT_SIZE['chess'],  4*FONT_SIZE['chess']],  rowHeights=[None]
)
        t.setStyle(reportlab.platypus.TableStyle([\
            ('ALIGN', (0,0), (0,0), 'LEFT'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'), 
            ('FACE', (0,0), (1,0), FONT_FAMILY),
            ('SIZE', (0,0), (1,0), FONT_SIZE['subscript']),
            ('INNERGRID', (0,0), (-1,0), 0.25, colors.black)
             ]))
        return t
    def leftPane(self):
        pass

    def board2Html(self,  board):
        lines = []
        spans, fonts, prevfont = [], [], 'z'
        for i in xrange(64):
            font, char = 'd', ["\xA3", "\xA4"][((i>>3) + (i%8))%2]
            if not board.board[i] is None:
                glyph = board.board[i].toFen()
                font = model.FairyHelper.fontinfo[glyph]['family']
                char = model.FairyHelper.fontinfo[glyph]['chars'][((i>>3) + (i%8))%2]
            if font != prevfont:
                fonts.append(font)
                spans.append([char])
                prevfont = font
            else:
                spans[-1].append(char)
            if i != 63 and i % 8 == 7:
                spans[-1].append("<br/>")
        return ''.join([\
            '<font face="%s" size=%d>%s</font>' % (CHESS_FONTS[fonts[i]][0], FONT_SIZE['chess'], ''.join(spans[i])) 
            for i in xrange(len(fonts))
            ])
        
    

export = ExportDocument([])
export.doExport('hello.pdf')
