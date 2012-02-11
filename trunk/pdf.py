# -*- coding: utf-8 -*-

# 3rd party
import reportlab.rl_config
reportlab.rl_config.warnOnMissingFontGlyphs = 0
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import reportlab.platypus
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors

# local
import model

A4_LANDSCAPE_H, A4_LANDSCAPE_W = A4
A5_MARGIN_X, A5_MARGIN_Y = 24, 16
AUX_X_MARGIN = 12

FONT_FAMILY = 'DejaVu Serif Condensed'
FONT_SIZE = {'header':10, 'chess':18, 'subscript':8, 'footer':8, 'rightpane': 8}
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
    def __init__(self, records, Lang):
        self.records, self.Lang = records, Lang
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', wordWrap=True))       
        styles.add(ParagraphStyle(name='Pre', wordWrap=True, fontName=FONT_FAMILY, fontSize=FONT_SIZE['rightpane'], spaceAfter=FONT_SIZE['rightpane']))       
        self.style = styles['Justify']
        self.style_pre = styles['Pre']
    def doExport(self, filename):
        frameTemplate = reportlab.platypus.Frame(\
            0, 0, A4_LANDSCAPE_W, A4_LANDSCAPE_H,
            leftPadding=A5_MARGIN_X, bottomPadding=A5_MARGIN_Y,
            rightPadding=A5_MARGIN_X, topPadding=A5_MARGIN_Y
            )
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
      
        story = []
        for i in xrange(0, len(self.records), 2):
            e = None
            if i + 1 < len(self.records): e = self.records[i + 1]
            story.append(self.mainTable(self.records[i], e))
            story.append(reportlab.platypus.PageBreak())

        docTemplate.build(story)
        
    def subscript(self,  left,  right):
        t = reportlab.platypus.Table([[left, right]],\
            colWidths=[4*FONT_SIZE['chess'],  4*FONT_SIZE['chess']],
            rowHeights=[None]
)
        t.setStyle(reportlab.platypus.TableStyle([\
            ('LEFTPADDING',(0,0), (1,0), 0),
            ('RIGHTPADDING',(0,0),(1,0), 0),
            ('TOPPADDING',(0,0),(1,0), FONT_SIZE['subscript']),
            ('ALIGN', (0,0), (0,0), 'LEFT'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'), 
            ('FACE', (0,0), (1,0), FONT_FAMILY),
            ('SIZE', (0,0), (1,0), FONT_SIZE['subscript'])
             ]))
        return t
    
    def mainTable(self, e1, e2):
        w_left = 8*FONT_SIZE['chess']
        w_right = (A4_LANDSCAPE_W - 4*A5_MARGIN_X - 2*w_left - 2*AUX_X_MARGIN)/2
        t = reportlab.platypus.Table(
            [[self.leftTop(e1), '', '', '', self.leftTop(e2), '',  ''],
            [self.leftBottom(e1), '', self.rightBottom(e1), '', self.leftBottom(e2), '', self.rightBottom(e2)]],
            colWidths=[w_left, AUX_X_MARGIN, w_right, 2*A5_MARGIN_X, w_left, AUX_X_MARGIN, w_right],
            rowHeights=[None, None]
            )
        t.setStyle(reportlab.platypus.TableStyle([\
            ('VALIGN', (0,0), (-1,0), 'BOTTOM'),
            ('VALIGN', (0,1), (-1,1), 'TOP')
             ]))
        return t
        
    def leftTop(self, e):
        if e is None:
            return ''
        return reportlab.platypus.Paragraph(\
            '<font face="%s" size=%d>%s</font><br/>' %
                (FONT_FAMILY, FONT_SIZE['header'], ExportDocument.header(e)),
                self.style
            )
    def leftBottom(self, e):
        story = []
        if e is None:
            return story
        b = model.Board()
        if e.has_key('algebraic'):
            b.fromAlgebraic(e['algebraic'])
        x = unicode(self.board2Html(b).decode("ISO-8859-1"))
        story.append(reportlab.platypus.Paragraph('<para autoLeading="max">'+x+'</para>', self.style))
        s_left = ''
        if e.has_key('stipulation'):
            s_left = e['stipulation']
        story.append(self.subscript(s_left, b.getPiecesCount()))
        story.append(reportlab.platypus.Paragraph(\
            '<font face="%s" size=%d>%s</font>' % (
                FONT_FAMILY,
                FONT_SIZE['footer'],
                ExportDocument.solver(e, self.Lang) + '<br/>' + ExportDocument.legend(b)
                ), self.style
            ))
        return story
        
    def rightBottom(self, e):
        story = []
        if e is None:
            return story
        parts = []
        if e.has_key('solution'):
            story.append(reportlab.platypus.Preformatted(wrapParagraph(e['solution'],  50), self.style_pre))
        if e.has_key('keywords'):
            parts.append('<i>' + ', '.join(e['keywords']) + '</i>')
        if e.has_key('comments'):
            parts.append('<br/>'.join(e['comments']))
        story.append(reportlab.platypus.Paragraph(\
            '<font face="%s" size=%d>%s</font>' % (
                FONT_FAMILY,
                FONT_SIZE['rightpane'],
                '<br/><br/>'.join(parts)
                ), self.style
            ))
        return story
        
    def header(e): 
        parts = []
        if(e.has_key('authors')):
            parts.append("<b>" + "<br/>".join(e['authors']) + "</b>")
        if(model.notEmpty(e, 'source')):
            s = "<i>" + e['source'] + "</i>"
            if(model.notEmpty(e, 'source-id')):
                s = s + "<i> (" + e['source-id'] + ")</i>"
            if(model.notEmpty(e, 'date')):
                s = s + "<i>, " + e['date'] + "</i>"
            parts.append(s)
        if(model.notEmpty(e, 'distinction')):
            parts.append(e['distinction'])
        return "<br/>".join(parts)
    header = staticmethod(header)
    
    def solver(e, Lang):
        parts = []
        if(model.notEmpty(e, 'intended-solutions')):
            if '.' in e['intended-solutions']:
                parts.append(e['intended-solutions'])
            else:
                parts.append(e['intended-solutions'] + " " + Lang.value('EP_Intended_solutions_shortened'))
        if(e.has_key('options')):
            parts.append("<b>" + "<br/>".join(e['options']) + "</b>")
        if(e.has_key('twins')):
            parts.append("<br/>".join([k + ') ' + e['twins'][k] for k in sorted(e['twins'].keys())]))
        return "<br/>".join(parts)
    solver = staticmethod(solver)
    
    def legend(board):
        legend = board.getLegend()
        if len(legend) == 0:
            return ''
        return "<br/>".join([", ".join(legend[k]) + ': ' + k for k in legend.keys()])
    legend = staticmethod(legend)
        
    def board2Html(self,  board):
        lines = []
        spans, fonts, prevfont = [], [], 'z'
        for i in xrange(64):
            font, char = 'd', ["\xA3", "\xA4"][((i>>3) + (i%8))%2]
            if not board.board[i] is None:
                glyph = board.board[i].toFen()
                if len(glyph) > 1:
                    glyph = glyph[1:-1]
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

def wrapParagraph(str,  w):
    lines = []
    for line in str.split("\n"):
        lines.extend(wrapNice(removeInlineIdents(line), w))
    return "\n".join(lines)
    
def wrapNice(line, w):
    if len(line) < w:
        return [line]
    words = line.split(' ')
    cur_line_words = []
    total = 0
    for i in xrange(len(words)):
        if total == 0:
            new_total = len(words[i])
        else:
            new_total = total + 1 + len(words[i])
        if new_total > w:
            if len(words[i]) <= w:
                retval = [' '.join(cur_line_words)]
                retval.extend(wrapNice(' '.join(words[i:]), w))
                return retval
            else: # rough wrap
                slice_size = w - total - 1
                cur_line_words.append(words[i][0:slice_size])
                retval = [' '.join(cur_line_words)]
                tail = ' '.join([words[i][slice_size:]]+words[i+1:])
                retval.extend(wrapNice(tail, w))
                return retval
        elif new_total == w:
            cur_line_words.append(words[i])
            retval = [' '.join(cur_line_words)]
            if i == len(words) - 1:
                return retval
            else:
                retval.extend(wrapNice(' '.join(words[i+1:]), w))
                return retval
        else:
            cur_line_words.append(words[i])
            total = new_total
    return [' '.join(cur_line_words)]
        
def removeInlineIdents(line):
    outer = 0
    while outer < len(line) and line[outer] == ' ':
        outer = outer + 1
    return line[0:outer] + ' '.join([x for x in line.strip().split(' ') if x != ''])
