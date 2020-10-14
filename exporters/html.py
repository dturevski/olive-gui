# -*- coding: utf-8 -*-

# standard
import re

# local
from model import Board
import exporters.pdf as pdf

# todo: use chevron/mustache templating (someday)


def render(entry, settings):

    board = Board()
    board.fromAlgebraic(entry["algebraic"])

    html = pdf.ExportDocument.header(entry, settings['lang']) + "<br/>\n"
    html += board_to_html(board, settings['diagram_font'])
    html += entry['stipulation'] + ' ' + board.getPiecesCount() + "<br/>\n"
    html += pdf.ExportDocument.solver(entry, settings['lang']) + "<br/>\n"
    html += pdf.ExportDocument.legend(board) + "<br/><br/>\n"
    if 'solution' in entry:
        html += solution_to_html(entry['solution'], settings['inline_font'])
    if 'keywords' in entry:
        html += "<br/>\n" + ', '.join(entry['keywords']) + "<br/>\n"
    if 'comments' in entry:
        html += "<br/>\n" + "<br/>\n".join(entry['comments']) + "<br/>\n"
    html += "<br/><br/>\n"

    return html


def render_many(entries, settings):
    return """<!doctype html>
        <html lang="en">
          <head>
            <meta charset="utf-8">
            <title>exported</title>
          </head>
          <body>%s</body>
        </html>""" % "".join([render(e, settings) for e in entries])


def board_to_html(board, config):
    """mostly copy paste from pdf.py  :( real clumsy
    important assumption: empty squares and board edges reside in one font file/face
    (poorly designated 'aux-postfix') in case of most chess fonts there's only one file/face
    and there's nothing to worry about, in case of GC2004 this is true (they are in GC2004d)
    in other fonts - who knows"""
    spans, fonts, font_ = [], [], config['prefix'] + config['aux-postfix']
    # top edge
    fonts.append(font_)
    spans.append([chr(int(config['edges']['NW'])) +
                  8 * chr(int(config['edges']['N'])) +
                  chr(int(config['edges']['NE'])) +
                  "<br/>"])
    for i in range(64):
        # left edge
        if i % 8 == 0:
            font = config['prefix'] + config['aux-postfix']
            char = chr(int(config['edges']['W']))
            if font != font_:
                fonts.append(font)
                spans.append([char])
                font_ = font
            else:
                spans[-1].append(char)
        # board square
        font = config['prefix'] + config['aux-postfix']
        char = [chr(int(config['empty-squares']['light'])),
                chr(int(config['empty-squares']['dark']))][((i >> 3) + (i % 8)) % 2]
        if not board.board[i] is None:
            glyph = board.board[i].toFen()
            if len(glyph) > 1:  # removing brackets
                glyph = glyph[1:-1]
            if glyph in config['fontinfo']:
                font = config['prefix'] + \
                       config['fontinfo'][glyph]['postfix']
                char = config['fontinfo'][glyph][
                    'chars'][((i >> 3) + (i % 8)) % 2]
        if font != font_:
            fonts.append(font)
            spans.append([char])
            font_ = font
        else:
            spans[-1].append(char)
        # right edge
        if i % 8 == 7:
            font = config['prefix'] + config['aux-postfix']
            char = chr(int(config['edges']['E']))
            if font != font_:
                fonts.append(font)
                spans.append([char])
                font_ = font
            else:
                spans[-1].append(char)
            spans[-1].append("<br/>")
    # bottom edge
    font = config['prefix'] + config['aux-postfix']
    edge = chr(int(config['edges']['SW'])) + 8 * chr(int(config['edges']
                                                         ['S'])) + chr(int(config['edges']['SE'])) + "<br/>"
    if font != font_:
        fonts.append(font)
        spans.append(edge)
    else:
        spans[-1].append(edge)
    html = ''.join([
        '<font face="%s">%s</font>' % (fonts[i], ''.join(spans[i]))
        for i in range(len(fonts))
    ])
    return '<font size="%s">%s</font>' % (config['size'], html)


def solution_to_html(s, config):
    s = s.replace("\n", "<br/>")
    if 'kqrbsp' in config:
        s = s.replace("x", ":")
        s = s.replace("*", ":")
        # so both pieces match RE in eg: '1.a1=Q Be5'
        s = s.replace(" ", "  ")
        pattern = re.compile('([ .(=\a-z18])([KQRBSP])([^)\\]A-Z])')
        s = re.sub(pattern, lambda m: replace_solution_chars(config, m), s)
        s = s.replace("  ", " ")
    return '<b>' + s + '</b>'


def replace_solution_chars(config, m):
    return m.group(1) + '</b><font face="' + config['prefix'] + '">' + str(chr(
        config['kqrbsp']['kqrbsp'.index(m.group(2).lower())])) + '</font><b>' + m.group(3)