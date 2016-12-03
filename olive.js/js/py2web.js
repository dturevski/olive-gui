var Py2Web = function() {

    var pieces = {K:"king", Q:"queen", R:"rook", B:"bishop", S:"knight", P:"pawn"};
    var colorNames = {w: "white", b: "black", n: "neutral" };

    function parseSquare(str) {
        return str.charCodeAt(0) - "a".charCodeAt(0) + 8*(7 - str.charCodeAt(1) + "1".charCodeAt(0))
    }

    function algebraic(square) {
        return "abcdefgh".charAt(square % 8) + "87654321".charAt(square >> 3)
    }

    function to_xy(i) {
        return {x: i % 8, y: i >> 3}
    }

    function from_xy(x, y) {
        return y*8 + x
    }

    function __setv(k, v) {
        this[k] = v
        return this
    }

    function Piece(n, c, s) {

        this.name = n
        this.color = c
        this.specs = s

        this.setv = __setv

        this.xfen = function () {
            var glyph = this.name.toLowerCase() in __fairyHelper.override?
                __fairyHelper.override[this.name.toLowerCase()]:
                __fairyHelper.glyphs[this.name.toLowerCase()]

            if (this.color == 'w') {
                glyph = glyph.toUpperCase()
            } else {
                glyph = glyph.toLowerCase()
            }

            if (this.color == 'n') {
                glyph = '!' + glyph
            }

            if (this.specs != '') {
                glyph = 'b' + glyph
            }

            if (glyph.length > 1) {
                glyph = '(' + glyph + ')'
            }

            return glyph
        }

        this.inverseColor = function() {
            if(this.color == 'w')
                this.color = 'b'
            else if(this.color == 'b')
                this.color = 'w'
        }

        this.asText = function() {
            var name = this.name;
            if(__fairyHelper.notation[name]) {
                name = __fairyHelper.notation[name];
            }
            return (this.color == 'n'? 'n': '') + this.specs + name;
        }

        this.toClass = function() {
            return colorNames[this.color] + "-" + pieces[this.name];
        }

        this.equalsIgnoreSpecs = function(piece) {
            return this.name == piece.name && this.color == piece.color;
        }

    }

    function Board() {

        this.add = function(piece, at) {
            if( (at > 63) || (at < 0) ) {
                return;
            }
            this.board[at] = piece
        }

        this.drop = function(at) {
            this.add(null, at)
        }

        this.clear = function() {
            this.board = new Array(64);
            this.imitators = []

            for(i = 0; i < 64; i++) {
                this.drop(i);
            }
        }

        this.move = function(from, to) {
            this.add(this.board[from], to)
            this.drop(from)
        }

        this.transform = function(method) {
            var tmp = new Board()
            for(var i = 0; i < 64; i++) {
                if(this.board[i] != null) {
                    p = to_xy(i)
                    tmp.add(this.board[i], method(p.x, p.y))
                }
            }
            this.board = tmp.board
        }

        // :)
        this.rotate = function(angle) {
            switch(angle) {
                case 270:
                    this.rotate(90)
                case 180:
                    this.rotate(90)
                case 90:
                    this.transform( function(x, y) { return from_xy(y, 7 - x) } )
            }
        }

        this.shift = function(a, b) {
            pa = to_xy(a)
            pb = to_xy(b)
            this.transform( function(x, y) { return from_xy(x + pb.x - pa.x, y + pb.y - pa.y) })
        }

        this.mirror = function(a, b) {
            if(a == 56) { // a1 <--
                if(b == 63) // --> h1
                    this.transform( function(x, y) { return from_xy(7 - x, y) })
                else if (b == 7) // --> h8
                    this.transform( function(x, y) { return from_xy(y, x) })
                else if (b == 0) // --> a8
                    this.transform( function(x, y) { return from_xy(x, 7 - y) })
            } else if ( (a == 63) && (b == 0)) { // h1 <--> a8
                this.transform( function(x, y) { return from_xy(7 - y, 7 - x) })
            }
        }

        this.polishTwin = function(method) {
            for(var i = 0; i < 64; i++) {
                if(this.board[i] != null) {
                    this.board[i].inverseColor()
                }
            }
        }

        this.toFen = function() {
            var fen = ''; var blanks = 0;
            for(var i = 0; i < 64; i++) {
                if( (i > 0) && (i % 8 == 0) ) {
                    if(blanks > 0)
                        fen += blanks;
                    fen += '/';
                    blanks = 0;
                }

                var f = '';
                if(this.board[i] != null) f = this.board[i].xfen();
                if(this.imitators.indexOf(i) != -1) f = '(!o)';

                if(f != '') {
                    if(blanks > 0)
                        fen += blanks;
                    fen += f;
                    blanks = 0;
                } else {
                    blanks++;
                }
            }
            if(blanks > 0)
                fen += blanks;
            return fen;
        }

        this.fromFen = function(fen) {
            this.clear()
            var i = 0;
            var j = 0;
            while((j < 64) && (i < fen.length)) {
                if("12345678".indexOf(fen.charAt(i)) != -1) {
                    j = j + parseInt(fen.charAt(i))
                    i = i + 1
                } else if('(' == fen.charAt(i)) {
                    idx = fen.indexOf(')', i);
                    if(idx != -1) {
                        this.add(ParsePiece(fen.substring(i+1, idx)), j)
                        j = j + 1
                        i = idx + 1
                    } else {
                        i = i + 1
                    }
                } else if('/' == fen.charAt(i)) {
                    i = i + 1
                } else {
                    this.add(ParsePiece(fen.charAt(i)), j)
                    j = j + 1;
                    i = i + 1;
                }
            }
        }

        this.toAlgebraic = function() {
            var retval = {white: [], black: [], neutral: []}
            var cs = {w:"white", b:"black", n:"neutral"}
            for(var i = 0; i < 64; i++) {
                if(this.board[i] != null) {
                    retval[cs[this.board[i].color]].push(this.board[i].name + algebraic(i))
                }
            }
            return retval
        }

        this.fromPiecesClause = function(p) {
            this.clear()
            var lines = p.trim().toLowerCase().split("\n")
            for(var i = 0; i < lines.length; i++) {
                var words = lines[i].trim().split(/\s+/)
                if (['white', 'black', 'neutral'].indexOf(words[0]) == -1) {
                    continue
                }
                var color = words[0][0]
                var specs = ''
                var j = 1
                while((j < words.length) && (__fairyHelper.pprops.indexOf(words[j]) != -1)) {
                    specs += words[j][0]
                    j = j + 1
                }

                var matches
                while((j < words.length) && (matches = words[j].match(/([a-z][0-9a-z]?)([a-h][1-8])+/))) {
                    name = matches[1].toUpperCase()
                    for(var k = 0; k < (words[j].length - name.length)/2; k++) {
                        var square = parseSquare(words[j].substr(name.length + k*2, 2))
                        if('i' == name.toLowerCase()) {
                            this.imitators.push(square)
                        } else {
                            this.add(new Piece(name, color, specs), square)
                        }
                    }
                    j = j + 1
                }
            }
        }

        this.fromAlgebraic = function(algebraic) {
            for(color in algebraic) {
                if (['white', 'black', 'neutral'].indexOf(color) == -1) {
                    continue;
                }
                for(var i = 0; i < algebraic[color].length; i++) {
                    var words = algebraic[color][i].split(/\s+/);
                    var specs = '';
                    for(var j = 0; j < words.length - 2; j++) {
                        if(__fairyHelper.pprops.indexOf(words[j]) != -1) {
                            specs += words[j][0];
                        }
                    }
                    if(matches = words[words.length - 1].toLowerCase().match(/([a-z][0-9a-z]?)([a-h][1-8])+/)) {
                        var name = matches[1].toUpperCase();
                        var square = parseSquare(matches[2]);
                        this.add(new Piece(name, color[0], specs), square)
                    }

                }
            }
        }

        this.toPiecesClause = function() {
            var c = {};
            for(var i = 0; i < 64; i++) {
                var p = this.board[i];
                if(p == null) continue;
                if(!(p.color in c)) {
                    c[p.color] = {};
                }
                var specs = p.specs.join(" ");
                if(!(specs in c[p.color])) {
                    c[p.color][specs] = {};
                }
                if(!(p.name in c[p.color][specs])) {
                    c[p.color][specs][p.name] = [];
                }
                c[p.color][specs][p.name].push(algebraic(i));
            }

            var lines = [];
            for(var color in c) for(var specs in c[color]) {
                var gs = [];
                for(var name in c[color][specs]) {
                    gs.push(name + c[color][specs][name].join(""));
                }
                lines.push("  " + (colorNames[color] + " " + specs).trim() + " " + gs.join(" "));
            }
            return lines.join("\n");
        }

        this.xfen2Html = function(fen) {

            var b = new Array(64);
            for(var i = 0; i < 64; i++) {
                b[i] = '';
            }

            var i = 0;
            var j = 0;
            while((j < 64) && (i < fen.length)) {
                if("12345678".indexOf(fen.charAt(i)) != -1) {
                    j = j + parseInt(fen.charAt(i))
                    i = i + 1
                } else if('(' == fen.charAt(i)) {
                    idx = fen.indexOf(')', i);
                    if(idx != -1) {
                        b[j] = fen.substring(i+1, idx)
                        j = j + 1
                        i = idx + 1
                    } else {
                        i = i + 1
                    }
                } else if('/' == fen.charAt(i)) {
                    i = i + 1
                } else {
                    b[j] = fen.charAt(i)
                    j = j + 1;
                    i = i + 1;
                }
            }

            var retval = '';
            for(var i = 0; i < 8; i++) {
                for(var j = 0; j < 8; j++) {
                    retval += '<a class="cp' + xfen2spritedecl(b[i*8+j], (i+j)%2) +'"></a>'
                }
            }
            return retval;


        }

        this.toHtml = function() {
            var retval = '';
            for(var i = 0; i < 8; i++) {
                for(var j = 0; j < 8; j++) {
                    var xfen = this.board[i*8+j] == null? '': this.board[i*8+j].xfen()
                    retval += '<a class="cp' + xfen2spritedecl(xfen, (i+j)%2) +'"></a>'
                }
            }
            return retval;
        }

        this.btm = true  // black to move

        this.flip = function() {
            this.btm = !this.btm
        }

        this.getStm = function() {
            return this.btm? 'b': 'w'
        }

        this.setStm = function(c) {
            this.btm = (c == 'b')
        }

        this.serialize = function() {
            return JSON.stringify(this)
        }

        this.unserialize = function(s) {
            o = JSON.parse(s)
            for(var i = 0; i < 64; i++) {
                if(o.board[i] != null) {
                    this.board[i] = new Piece(o.board[i].name, o.board[i].color, o.board[i].specs)
                } else {
                    this.board[i] = null
                }
            }
            this.btm = o.btm
            this.imitators = o.imitators
        }

        this.piecesCount = function() {
            var cnt = {w: 0, b: 0, n: 0};
            for(var i = 0; i < 64; i++) {
                if(this.board[i] != null) {
                    cnt[this.board[i].color]++;
                }
            }
            var pcs =  cnt.w + '+' + cnt.b
            if(cnt.n > 0) pcs = pcs + '+' + cnt.n
            return pcs
        }


        this.clear();
    }

    return {
        Board: Board,
        Piece: Piece,
        pieces: pieces
    }
}();