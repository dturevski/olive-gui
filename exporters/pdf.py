# -*- coding: utf-8 -*-

# local
import model

# 3rd party
import reportlab.rl_config
reportlab.rl_config.warnOnMissingFontGlyphs = 0
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import reportlab.platypus
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from PyQt5 import QtGui

# local
import model


FONT_FAMILY = 'Roboto Condensed'
FONT_SIZE = {
    'header': 12,
    'chess': 18,
    'subscript': 10,
    'footer': 10,
    'rightpane': 12}
FONT_DIR = 'resources/fonts/roboto/'
FONT_INFO = {
    'normal': (
        FONT_FAMILY + '',
        'RobotoCondensed-Regular.ttf'),
    'bold': (
        FONT_FAMILY + ' Bold',
        'RobotoCondensed-Bold.ttf'),
    'italic': (
        FONT_FAMILY + ' Italic',
        'RobotoCondensed-Italic.ttf'),
    'boldItalic': (
        FONT_FAMILY + ' Bold Italic',
        'RobotoCondensed-BoldItalic.ttf')}
CHESS_FONTS = {
    'd': ('GC2004D', 'resources/fonts/gc2004d_.ttf'),
    'x': ('GC2004X', 'resources/fonts/gc2004x_.ttf'),
    'y': ('GC2004Y', 'resources/fonts/gc2004y_.ttf')
}
CHESS_FONT_RENDERING_OFFSET = 0.25
MARGIN_X, MARGIN_Y = 72 - FONT_SIZE['chess'], 72
AUX_X_MARGIN = 36

CHESS_FONT_STYLES = {}

def register_fonts():

    for variation in list(FONT_INFO.keys()):
        pdfmetrics.registerFont(TTFont(FONT_INFO[variation][0], FONT_DIR+FONT_INFO[variation][1]))

    pdfmetrics.registerFontFamily(
        FONT_FAMILY,
        normal=FONT_INFO['normal'][0],
        bold=FONT_INFO['bold'][0],
        italic=FONT_INFO['italic'][0],
        boldItalic=FONT_INFO['boldItalic'][0])


    for key in list(CHESS_FONTS.keys()):
        pdfmetrics.registerFont(TTFont(CHESS_FONTS[key][0], CHESS_FONTS[key][1]))
        pdfmetrics.registerFontFamily(key, normal=key, bold=key, italic=key, boldItalic=key)
        styles = getSampleStyleSheet()
        styles.add(
            ParagraphStyle(
                name='chess'+key,
                wordWrap=False,
                fontName=CHESS_FONTS[key][0],
                fontSize=FONT_SIZE['chess'],
                spaceAfter=0))
        CHESS_FONT_STYLES[key] = styles['chess'+key]


def getPieceParagraph(font, char):
    return reportlab.platypus.Paragraph(
        '<para autoLeading="max">%s</para>' % char,
        CHESS_FONT_STYLES[font]
    )


class ExportDocument:

    def __init__(self, records, Lang):
        ExportDocument.startFonts()
        self.records, self.Lang = records, Lang
        register_fonts()
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='Justify', wordWrap=True))
        styles.add(ParagraphStyle(name='Center', alignment=reportlab.lib.enums.TA_CENTER))
        styles.add(
            ParagraphStyle(
                name='Pre',
                wordWrap=True,
                fontName=FONT_FAMILY,
                fontSize=FONT_SIZE['rightpane'],
                spaceAfter=FONT_SIZE['rightpane']))
        self.style = styles['Justify']
        self.style_pre = styles['Pre']
        self.style_center = styles['Center']

    def doExport(self, filename):
        frameTemplate = reportlab.platypus.Frame(
            0, 0, A4[0], A4[1],
            leftPadding=MARGIN_X, bottomPadding=MARGIN_Y,
            rightPadding=MARGIN_X, topPadding=MARGIN_Y
        )
        pageTemplate = reportlab.platypus.PageTemplate(frames=[frameTemplate])
        docTemplate = reportlab.platypus.BaseDocTemplate(
            filename,
            pagesize=A4,
            pageTemplates=[pageTemplate],
            showBoundary=1,
            leftMargin=0,
            rightMargin=0,
            topMargin=0,
            bottomMargin=0,
            allowSplitting=1,
            _pageBreakQuick=1)

        story = []
        for i in range(0, len(self.records)):
            story.append(self.mainTable(self.records[i]))
            story.append(reportlab.platypus.PageBreak())

        docTemplate.build(story)

    def subscript(self, left, middle, right):
        fs = FONT_SIZE['chess']
        t = reportlab.platypus.Table([['', left, middle, right]],
                                     colWidths=[fs*(1+CHESS_FONT_RENDERING_OFFSET), 2 * fs, 4 * fs, 2 * fs],
                                     rowHeights=[None]
                                     )
        t.setStyle(reportlab.platypus.TableStyle([
            ('LEFTPADDING', (1, 0), (1, 0), 0),
            ('RIGHTPADDING', (3, 0), (3, 0), 0),
            ('TOPPADDING', (0, 0), (-1, 0), FONT_SIZE['subscript']),
            ('VALIGN', (0, 0), (-1, 0), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'LEFT'),
            ('ALIGN', (2, 0), (2, 0), 'CENTER'),
            ('ALIGN', (3, 0), (3, 0), 'RIGHT'),
            ('FACE', (0, 0), (-1, 0), FONT_FAMILY),
            ('SIZE', (0, 0), (-1, 0), FONT_SIZE['subscript'])
        ]))
        return t

    def mainTable(self, entry):
        w_left = 10 * FONT_SIZE['chess']
        w_right = A4[0] - 2 * MARGIN_X - w_left - AUX_X_MARGIN
        t = reportlab.platypus.Table(
            [[self.leftTop(entry), '', ''],
             [self.leftBottom(entry), '', self.rightBottom(entry)]],
            colWidths=[w_left, AUX_X_MARGIN, w_right],
            rowHeights=[None, None]
        )
        t.setStyle(reportlab.platypus.TableStyle([
            ('VALIGN', (0, 0), (-1, 0), 'BOTTOM'),
            ('VALIGN', (0, 1), (-1, 1), 'TOP')
        ]))
        return t

    def leftTop(self, e):
        if e is None:
            return ''
        header = reportlab.platypus.Paragraph(
            '<font face="%s" size=%d>%s</font><br/>' % (FONT_FAMILY, FONT_SIZE['header'],
             ExportDocument.header(e, self.Lang)), self.style
        )
        return reportlab.platypus.Table(
            [['', header]],
            colWidths=[FONT_SIZE['chess'], 9*FONT_SIZE['chess']]
        )


    def leftBottom(self, e):
        story = []
        if e is None:
            return story
        b = model.Board()
        if 'algebraic' in e:
            b.fromAlgebraic(e['algebraic'])
        story.append(self.getBoardTable(b))
        s_left = ''
        if 'stipulation' in e:
            s_left = e['stipulation']
        s_middle = reportlab.platypus.Paragraph(
            '<font face="%s" size=%d>%s</font>' %
            (FONT_FAMILY,
             FONT_SIZE['footer'],
             ExportDocument.solver(
                 e,
                 self.Lang) +
             '<br/>' +
             ExportDocument.legend(b)),
            self.style_center)
        story.append(self.subscript(s_left, s_middle, b.getPiecesCount()))
        return story


    def fenLine(self, b):
        t = reportlab.platypus.Table([[b.toFen()]])
        t.setStyle(reportlab.platypus.TableStyle([
            ('TEXTCOLOR', (0, 0), (-1, -1), (0.75, 0.75, 0.75)),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), FONT_SIZE['rightpane']),
        ]))
        return t

    def rightBottom(self, e):
        story = []
        if e is None:
            return story
        parts = []
        if 'solution' in e:
            story.append(
                reportlab.platypus.Preformatted(
                    wrapParagraph(
                        e['solution'],
                        50),
                    self.style_pre))
        if 'keywords' in e:
            parts.append('<i>' + ', '.join(e['keywords']) + '</i>')
        if 'comments' in e:
            parts.append('<br/>'.join(e['comments']))
        story.append(reportlab.platypus.Paragraph(
            '<font face="%s" size=%d>%s</font>' % (
                FONT_FAMILY,
                FONT_SIZE['rightpane'],
                '<br/><br/>'.join(parts)
            ), self.style
        ))
        if 'algebraic' in e:
            b = model.Board()
            b.fromAlgebraic(e['algebraic'])
            story.append(self.fenLine(b))
        return story

    def header(e, Lang):
        parts = []
        if'authors' in e:
            parts.append("<b>" + "<br/>".join(e['authors']) + "</b>")
        if 'source' in e and 'name' in e['source']:
            s = "<i>" + e['source']['name'] + "</i>"
            sourceid = model.formatIssueAndProblemId(e['source'])
            if sourceid != '':
                s = s + "<i> (" + sourceid + ")</i>"
            if 'date' in e['source']:
                s = s + "<i>, " + model.formatDate(e['source']['date']) + "</i>"
            parts.append(s)
        if 'award' in e:
            tourney = e.get('award', {}).get('tourney', {}).get('name', '')
            source = e.get('source', {}).get('name', '')
            if tourney != '' and tourney != source:
                parts.append(tourney)
            if 'distinction' in e['award']:
                d = model.Distinction.fromString(e['award']['distinction'])
                parts.append(d.toStringInLang(Lang))
        return ExportDocument.escapeHtml("<br/>".join(parts))
    header = staticmethod(header)

    def solver(e, Lang):
        parts = []
        if(model.notEmpty(e, 'intended-solutions')):
            if '.' in e['intended-solutions']:
                parts.append(e['intended-solutions'])
            else:
                parts.append(
                    e['intended-solutions'] +
                    " " +
                    Lang.value('EP_Intended_solutions_shortened'))
        if('options' in e):
            parts.append("<b>" + "<br/>".join(e['options']) + "</b>")
        if('twins' in e):
            parts.append(model.createPrettyTwinsText(e))
        return ExportDocument.escapeHtml("<br/>".join(parts))
    solver = staticmethod(solver)

    def legend(board):
        legend = board.getLegend()
        if len(legend) == 0:
            return ''
        return ExportDocument.escapeHtml(
            "<br/>".join([", ".join(legend[k]) + ': ' + k for k in list(legend.keys())]))
    legend = staticmethod(legend)

    def escapeHtml(str):
        str = str.replace('&', '&amp;')
        # todo: more replacements
        return str
    escapeHtml = staticmethod(escapeHtml)

    fontsStarted = False
    def startFonts():
        if ExportDocument.fontsStarted:
            return
        register_fonts()
        ExportDocument.topBorder = [getPieceParagraph('y', char) for char in "KLLLLLLLLM"]
        ExportDocument.bottomBorder = [getPieceParagraph('y', char) for char in "RSSSSSSSST"]
        ExportDocument.leftBorder = getPieceParagraph('y', "N")
        ExportDocument.rightBorder = getPieceParagraph('y', "Q")
        ExportDocument.fontsStarted = True
    startFonts = staticmethod(startFonts)

    def board2Table(self, board):
        rows, row = [ExportDocument.topBorder], None
        for i in range(64):
            if i % 8 == 0:
                row = [ExportDocument.leftBorder]
                rows.append(row)
            font, char = 'd', ["\xA3", "\xA4"][((i >> 3) + (i % 8)) % 2]
            if not board.board[i] is None:
                glyph = board.board[i].toFen()
                if len(glyph) > 1:
                    glyph = glyph[1:-1]
                font = model.FairyHelper.fontinfo[glyph]['family']
                char = model.FairyHelper.to_html(glyph, i, board.board[i].specs)
            row.append(getPieceParagraph(font, char))
            if i % 8 == 7:
                row.append(ExportDocument.rightBorder)

        rows.append(ExportDocument.bottomBorder)
        return rows

    def board2Html(self, board):
        lines = []
        spans, fonts, prevfont = [], [], 'z'
        for i in range(64):
            font, char = 'd', ["\xA3", "\xA4"][((i >> 3) + (i % 8)) % 2]
            if not board.board[i] is None:
                glyph = board.board[i].toFen()
                if len(glyph) > 1:
                    glyph = glyph[1:-1]
                font = model.FairyHelper.fontinfo[glyph]['family']
                char = model.FairyHelper.fontinfo[glyph][
                    'chars'][((i >> 3) + (i % 8)) % 2]
            if font != prevfont:
                fonts.append(font)
                spans.append([char])
                prevfont = font
            else:
                spans[-1].append(char)
            if i != 63 and i % 8 == 7:
                spans[-1].append("<br/>")
        return ''.join(
            [
                '<font face="%s" size=%d>%s</font>' %
                (CHESS_FONTS[
                     fonts[i]][0],
                 FONT_SIZE['chess'],
                 ''.join(
                     spans[i])) for i in range(
                len(fonts))])

    def getBoardTable(self, b):
        t = reportlab.platypus.Table(
            self.board2Table(b),
            colWidths = [FONT_SIZE['chess'] for _ in range(10)],
            rowHeights = [FONT_SIZE['chess'] for _ in range(10)]
        )
        t.setStyle(reportlab.platypus.TableStyle([
            #('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
            #('BOX', (0,0), (-1,-1), 0.25, colors.black),
        ]))
        return t


def wrapParagraph(str, w):
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
    for i in range(len(words)):
        if total == 0:
            new_total = len(words[i])
        else:
            new_total = total + 1 + len(words[i])
        if new_total > w:
            if len(words[i]) <= w:
                retval = [' '.join(cur_line_words)]
                retval.extend(wrapNice(' '.join(words[i:]), w))
                return retval
            else:  # rough wrap
                slice_size = w - total - 1
                cur_line_words.append(words[i][0:slice_size])
                retval = [' '.join(cur_line_words)]
                tail = ' '.join([words[i][slice_size:]] + words[i + 1:])
                retval.extend(wrapNice(tail, w))
                return retval
        elif new_total == w:
            cur_line_words.append(words[i])
            retval = [' '.join(cur_line_words)]
            if i == len(words) - 1:
                return retval
            else:
                retval.extend(wrapNice(' '.join(words[i + 1:]), w))
                return retval
        else:
            cur_line_words.append(words[i])
            total = new_total
    return [' '.join(cur_line_words)]


def removeInlineIdents(line):
    outer = 0
    while outer < len(line) and line[outer] == ' ':
        outer = outer + 1
    return line[0:outer] + \
        ' '.join([x for x in line.strip().split(' ') if x != ''])
