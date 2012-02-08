# -*- coding: utf-8 -*-
from reportlab.pdfgen import canvas
import reportlab.rl_config
reportlab.rl_config.warnOnMissingFontGlyphs = 0
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import platypus 

from reportlab.lib.pagesizes import letter, A4
A4_LANDSCAPE_H, A4_LANDSCAPE_W = A4
A5_MARGIN_X, A5_MARGIN_Y = 10, 10

FONT_FAMILY = 'DejaVu Serif Condensed'
FONT_DIR = 'resources/fonts/dejavu/'
FONT_INFO = \
    {'normal':(FONT_FAMILY+'', 'DejaVuSerifCondensed.ttf'),\
    'bold':(FONT_FAMILY+' Bold', 'DejaVuSerifCondensed-Bold.ttf'),\
    'italic':(FONT_FAMILY+' Italic', 'DejaVuSerifCondensed-Italic.ttf'),\
    'boldItalic':(FONT_FAMILY+' Bold Italic', 'DejaVuSerifCondensed-BoldItalic.ttf')\
    }
for variation in FONT_INFO.keys():
    pdfmetrics.registerFont(TTFont(FONT_INFO[variation][0], FONT_DIR+FONT_INFO[variation][1]))
pdfmetrics.registerFontFamily(FONT_FAMILY,\
    normal=FONT_INFO['normal'][0], bold=FONT_INFO['bold'][0],\
    italic=FONT_INFO['italic'][0], boldItalic=FONT_INFO['boldItalic'][0])

    
mainTable = platypus.Table()
    

def hello(c):
    c.drawString(100, 500, u"Хэлло World")
    
c = canvas.Canvas("hello.pdf", pagesize=(A4_LANDSCAPE_W, A4_LANDSCAPE_H))




c.showPage()
c.save()