# roughly adapted from http://www.yacpdb.org/xfen/index.php.html
import re
from PIL import Image, ImageDraw

RE_TOKEN = re.compile('^(B?)(!?)([kqrbsnpeaofwdx])([1-7])?$', re.IGNORECASE)
baseGlyphs = {\
        'k':((0,0), (0,17)),
        'q':((0,2), (0,18)),
        'r':((0,4), (0,19)),
        'b':((0,6), (0,20)),
        's':((0,8), (0,21)),
        'n':((0,8), (0,21)),
        'p':((0,10), (0,22)),
        'e':((0,14), (0,16)),
        'a':((4,15), (4,15)),
        'o':((0,15), (6,13)),
        'f':((0,12), (0,12)),
        'w':((4,12), (4,12)),
        'd':((0,13), (0,13)),
        'x':((4,13), (4,13))
    }

def token_to_sprite(xfen_token, color): # $color == bg color
    if not xfen_token:
        return [('EQ', False), ('FQ', False)][color]
    sprite = {}
    matches = RE_TOKEN.match(xfen_token)
    if matches:
        sprite = {'glyph':matches.group(3).lower(), 'rot':matches.group(4), 'border':(matches.group(1) != '')}
        if matches.group(2) != '':
            sprite['color'] = 'neutral'
        elif sprite['glyph'] == matches.group(3):
            sprite['color'] = 'black'
        else:
            sprite['color'] = 'white'

        if not sprite['rot']:
            sprite['rot'] = 0
        else:
            sprite['rot'] = int(sprite['rot'])
    else: 
        sprite = {'glyph':'x', 'rot':0, 'color':'white', 'border':False}
        
    if sprite['glyph'] == 'x':
        sprite['color'] = 'white'

    rot4, rot2, rot1, s = 'kqrbsnp', 'e', 'aofwd', 0

    # color modifiers
    if sprite['color'] == 'neutral':
        s = baseGlyphs[sprite['glyph']][1][0] + 8*baseGlyphs[sprite['glyph']][1][1]
    elif sprite['color'] == 'white':
        s = baseGlyphs[sprite['glyph']][0][0] + 8*baseGlyphs[sprite['glyph']][0][1]
    else:
        s = baseGlyphs[sprite['glyph']][0][0] + 8*baseGlyphs[sprite['glyph']][0][1] + 2

    # rotation modifiers
    if sprite['rot'] > 3: # 45 deg are not yet supported
        sprite['rot'] = sprite['rot'] % 4
        if 0 == sprite['rot']: sprite['rot'] = 1
    if sprite['glyph'] in rot4:
        if sprite['color'] == 'neutral':
            s = s + 2*sprite['rot']
        else:
            s = s + 4*sprite['rot']
    elif sprite['glyph'] in rot2:
        if sprite['color'] == 'neutral':
            s = s + 2*(sprite['rot'] % 2)
        else:
            s = s + 4*(sprite['rot'] % 2)
    # and rot1 cant be rotated
    # bg modifier
    s = s + color

    ABC = 'ABCDEFGHIJKLMNOPQRSTUVW'
    coords = ABC[s % 8] + ABC[s >> 3]
    return (coords, sprite['border'])

def parse_xfen(xfen):
    cells = 64*['']
    i, j = 0 , 0
    while (j < 64) and (i < len(xfen)):
        if xfen[i] in '12345678':
            j = j + int(xfen[i])
            i = i + 1
        elif '(' == xfen[i]:
            idx = xfen.find(')', i)
            if idx != -1:
                cells[j] = xfen[i+1:idx]
                j = j + 1
                i = idx + 1
            else:
                i = i + 1
        elif '/' == xfen[i]:
            i = i + 1
        else:
            cells[j] = xfen[i]
            i, j = i + 1, j + 1
    return cells

def convert(xfen, filename):
    cs = 32 # cell size
    bs = 1  # border size
    
    sprites = Image.open('resources/fonts/gc2.gif');
    img = Image.new('RGBA', (8*cs+2*bs, 8*cs+2*bs))
    canvas = ImageDraw.Draw(img)
    canvas.rectangle([0, 0, 8*cs+2*bs, 8*cs+2*bs], fill="#808080", outline="#808080")
    
    cells = parse_xfen(xfen);
    for i in xrange(64):
        coords, with_border = token_to_sprite(cells[i], (i % 2) ^ (i >> 3)%2 )    
        img_x = bs + cs*(i % 8)
        img_y = bs + cs*(i >> 3)
        sprite_x = cs*(ord(coords[0]) - ord('A'))
        sprite_y = cs*(ord(coords[1]) - ord('A'))
        sprite = sprites.crop((sprite_x, sprite_y, sprite_x + cs, sprite_y + cs))
        img.paste(sprite, (img_x, img_y))
        if with_border:
            canvas.rectangle((img_x, img_y, img_x + cs - 1, img_y + cs - 1), outline="#000000");
    img.save(filename)
