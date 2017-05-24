from gui import *

class Demoframe(QtGui.QMainWindow):


    def __init__(self, app):
        super(Demoframe, self).__init__()
        Mainframe.model = model.Model()

        fontSize = (app.desktop().screenGeometry().height() - 400) >> 3

        Mainframe.fonts = { 'd': QtGui.QFont(
                'GC2004D', fontSize), 'y': QtGui.QFont(
                'GC2004Y', fontSize), 'x': QtGui.QFont(
                'GC2004X', fontSize)}

        self.initLayout()
        self.initFrame()
        self.showFullScreen()

    def initLayout(self):

        # left pane
        widgetLeftPane = QtGui.QWidget()
        vboxLeftPane = QtGui.QVBoxLayout()
        vboxLeftPane.setSpacing(0)
        vboxLeftPane.setContentsMargins(0, 0, 0, 0)
        self.fenView = FenView(self)
        self.boardView = BoardView()

        vboxLeftPane.addWidget(self.fenView)
        vboxLeftPane.addWidget(self.boardView)
        widgetLeftPane.setLayout(vboxLeftPane)

        # right pane
        self.chessBox = ChessBox()

        # putting panes together
        hbox = QtGui.QHBoxLayout()
        hbox.addWidget(widgetLeftPane)
        hbox.addWidget(self.chessBox)

        cw = QtGui.QWidget()
        self.setCentralWidget(cw)
        self.centralWidget().setLayout(hbox)

    def initFrame(self):
        self.setWindowIcon(QtGui.QIcon(QtGui.QPixmap('resources/icons/olive.png')))
        self.setWindowTitle("Demo board")
