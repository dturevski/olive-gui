var Module = {};

var oliveJS = function($, Module) {

    var selectedPiece = null;
    var board = new Py2Web.Board();
    var popeyeInputFile = "/test.inp";
    var popeyeMaxMem = "16M"
    var args = ["py", "-maxmem", popeyeMaxMem, popeyeInputFile];



    var initEm = function(Module) {
        Module.print = Module.printErr =  function(text) {
            $(".output").append(text + "\n");
            console.log(text);
        }
        //Module.arguments = args;
        Module.noInitialRun = true;
    }(Module);

    var iteratePieces = function(fn) {
        for(var color in {w:'', b:''}) {
            for(var name in Py2Web.pieces) {
                fn(new Py2Web.Piece(name, color, []))
            }
        }
    };

    $(document).ready(function() {
        initBoard();
        initControls();
        load();
        initTouch();
    });

    var getSquareShade = function(s) {
        return (s + (s >> 3)) % 2 == 0? "light": "dark";
    };

    var initBoard = function() {
        for(var i = 0; i < 64; i++) {
            var e = $("<div index='" + i + "'></div>");
            $(".board").append(e.addClass("square"));
            e.addClass(getSquareShade(i));
            e.click(function() {
                var i = parseInt($(this).attr("index"));
                $(this).removeClass().addClass("square").addClass(getSquareShade(i));
                if(selectedPiece != null) {
                    if(board.board[i] != null) {
                        if(selectedPiece.equalsIgnoreSpecs(board.board[i])) {
                            board.drop(i);
                        } else {
                            board.drop(i);
                            board.add(selectedPiece, i);
                            $(this).addClass(selectedPiece.toClass());
                        }
                    } else {
                        board.add(selectedPiece, i);
                        $(this).addClass(selectedPiece.toClass());
                    }
                } else {
                    board.drop(i);
                }
                updateInput();
            });
        }

        iteratePieces(function(piece) {
            var button = $("<div/>").addClass("square").addClass(piece.toClass());
            $(".pieces").append(button);
            button.click(function() {
                selectedPiece = piece;
                $(".pieces div").removeClass("selected");
                $(this).addClass("selected");
            });
        });

    };

    var repaintBoard = function() {
        $(".board div").each(function() {
            var e = $(this);
            var i = parseInt(e.attr("index"));
            e.removeClass().addClass("square").addClass(getSquareShade(i));
            if(board.board[i] != null) {
                e.addClass(board.board[i].toClass());
            }
        });
    };

    var updateInput = function() {
        var e = $(".input textarea");
        var s = board.toPiecesClause();
        var re = /\npiec[\s\S]*$/ig
        if(s != "") {
            s = "\nPieces\n" + s;
        }
        if(e.val().match(re)) {
            e.val(e.val().replace(re, s));
        } else {
            e.val(e.val().trim() + s);
        }
        save();
    };

    var initControls = function() {

        $(".output").html("");

        $(".clear-board").click(function() {
            board.clear();
            $(".board > div").removeClass().each(function() {
                $(this).addClass("square").addClass(getSquareShade(parseInt($(this).attr("index"))));
            });
        });

        $(".solve").click(function() {
            $(".output").text("");

            openScreen(2, true, function() {
                FS.writeFile(popeyeInputFile, "BeginProblem\n" +  $(".input textarea").val() + "\nEndProblem");

                var argv = new Uint32Array(args.length);
                for(var i = 0; i < args.length; i++) {
                    argv[i] = allocate(intArrayFromString(args[i]), 'i8', ALLOC_NORMAL);
                }
                var bytes = argv.length * argv.BYTES_PER_ELEMENT;
                var ptrArgv = Module._malloc(bytes);
                var pointerHeap = new Uint8Array(Module.HEAPU8.buffer, ptrArgv, bytes);
                pointerHeap.set(new Uint8Array(argv.buffer));

                _main(args.length, pointerHeap.byteOffset);

                for(var i = 0; i < args.length; i++) {
                    _free(argv[i]);
                }
                _free(ptrArgv);
            });
        });

        $(".right").click(function() { board.shift(0, 1); } );
        $(".left").click(function() { board.shift(1, 0); } );
        $(".up").click(function() { board.shift(8, 0); } );
        $(".down").click(function() { board.shift(0, 8); } );
        $(".rotate-90").click(function() { board.rotate(270); } );
        $(".rotate-270").click(function() { board.rotate(90); } );
        $(".mirror-v").click(function() { board.mirror(56, 63); } );
        $(".mirror-h").click(function() { board.mirror(56, 0); } );

        $(".icon").click(function() {
            repaintBoard();
            updateInput();
        });

    };

    function isTouchDevice() {
        //return true;
        return 'ontouchstart' in window        // works on most browsers
            || navigator.maxTouchPoints;       // works on IE10/11 and Surface
    };

    var openScreen = function(screenNo, slideLeft, fn) { fn(); };

    var initTouch = function() {

        if(!isTouchDevice()) {
            $(".screen1").show();
            $(".screen2").show();
            return;
        }

        var curScreen = 0;
        var screenCount = 3;
        for(var i = 0; i < screenCount; i++) {
            var screen = $($(".screen" + i));
            screen.css({ position: "absolute"});
            if(i != curScreen) {
                screen.hide();
            }
        }

        openScreen = function(screenNo, slideLeft, fn) {
            var c = $(".screen" + curScreen);
            var n = $(".screen" + screenNo);
            var w = c.width();
            if(slideLeft) {
                c.animate({ left: -w }, 300, function () { c.hide().css({left: 0}); fn(); } );
                n.css({ left: w, width: 0});
                n.show().animate({ left: 0, width: w }, 300);

            } else {
                c.animate({ left: w, width: 0 }, 300, function () { c.hide().css({left: 0, width: w }); fn(); } );
                n.css({ left: -w });
                n.show().animate({ left: 0 }, 300);
            }
            curScreen = screenNo;
        };

        document.addEventListener('touchstart', handleTouchStart, false);
        document.addEventListener('touchmove', handleTouchMove, false);

        var xDown = null;
        var yDown = null;

        function handleTouchStart(evt) {
            xDown = evt.touches[0].clientX;
            yDown = evt.touches[0].clientY;
        };

        function handleTouchMove(evt) {
            if ( ! xDown || ! yDown ) {
                return;
            }

            var xUp = evt.touches[0].clientX;
            var yUp = evt.touches[0].clientY;

            var xDiff = xDown - xUp;
            var yDiff = yDown - yUp;

            if ( Math.abs( xDiff ) > Math.abs( yDiff ) ) {/*most significant*/
                if ( xDiff > 0 ) {
                    openScreen((curScreen+1) % screenCount, true, function(){});
                } else {
                    openScreen((curScreen+screenCount-1) % screenCount, false, function(){});
                }
            } else {
                if ( yDiff > 0 ) {
                    /* up swipe */
                } else {
                    /* down swipe */
                }
            }
            /* reset values */
            xDown = null;
            yDown = null;
        };


    };

    var save = function() {
        window.localStorage.setItem("ojs_input", $(".input textarea").val());
        window.localStorage.setItem("ojs_board", board.serialize());
    }

    var load = function() {
        var i = window.localStorage.getItem("ojs_input");
        var b = window.localStorage.getItem("ojs_board");
        if(i == null || b == null) return;
        $(".input textarea").val(i);
        board.unserialize(b);
        repaintBoard();
    }

} (jQuery, Module);
