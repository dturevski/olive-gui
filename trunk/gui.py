# -*- coding: utf-8 -*-

# standard
import os
import tempfile
import copy

# 3rd party
import yaml
from PyQt4 import QtGui, QtCore

# local
import legacy.popeye
import legacy.chess
import options
import model
import pbm
import pdf
import xfen2img


class SigWrapper(QtCore.QObject):
    sigLangChanged = QtCore.pyqtSignal() 
    sigModelChanged = QtCore.pyqtSignal() 
    sigFocusOnPieces = QtCore.pyqtSignal() 
    sigFocusOnPopeye = QtCore.pyqtSignal() 
    sigFocusOnStipulation = QtCore.pyqtSignal() 
    sigFocusOnSolution = QtCore.pyqtSignal() 


class Mainframe(QtGui.QMainWindow):
    sigWrapper = SigWrapper()
    fontSize = 24
    fonts = {'d':QtGui.QFont('GC2004D', fontSize), 'y': QtGui.QFont('GC2004Y', fontSize), 'x':QtGui.QFont('GC2004X', fontSize)}
    currentlyDragged = None
    transform_names = ['Shift_up','Shift_down','Shift_left',\
        'Shift_right','Rotate_CW','Rotate_CCW',\
        'Mirror_vertical','Mirror_horizontal','Clear']
    transform_icons = ['up','down','left',\
        'right','rotate-clockwise','rotate-anticlockwise',\
        'left-right','up-down','out']

    def __init__(self):
        super(Mainframe, self).__init__()

        Mainframe.model = model.Model()

        self.initLayout()
        self.initActions()
        self.initMenus()
        self.initToolbar()        
        self.initSignals()
        self.initFrame()

        self.updateTitle()
        self.overview.rebuild()
        self.show()

    def initLayout(self):
        # widgets
        hbox = QtGui.QHBoxLayout()
        
        # left pane
        widgetLeftPane = QtGui.QWidget()
        vboxLeftPane = QtGui.QVBoxLayout()
        vboxLeftPane.setSpacing(0)
        vboxLeftPane.setContentsMargins(0, 0, 0, 0)
        self.fenView = FenView()
        self.boardView = BoardView()
        self.infoView = InfoView()
        self.chessBox = ChessBox()

        vboxLeftPane.addWidget(self.fenView)
        vboxLeftPane.addWidget(self.boardView)
        
        self.tabBar1 = QtGui.QTabWidget()
        self.tabBar1.setTabPosition(1)
        self.tabBar1.addTab(self.infoView, Lang.value('TC_Info'))
        self.tabBar1.addTab(self.chessBox, Lang.value('TC_Pieces'))

        vboxLeftPane.addWidget(self.tabBar1, 1)
        widgetLeftPane.setLayout(vboxLeftPane)
        
        # right pane
        self.easyEditView = EasyEditView()
        self.solutionView = SolutionView()
        self.popeyeView = PopeyeView()
        self.yamlView = YamlView()
        self.tabBar2 = QtGui.QTabWidget()
        self.tabBar2.addTab(self.popeyeView, Lang.value('TC_Popeye'))
        self.tabBar2.addTab(self.solutionView, Lang.value('TC_Solution'))
        self.tabBar2.addTab(self.easyEditView, Lang.value('TC_Edit'))
        self.tabBar2.addTab(self.yamlView, Lang.value('TC_YAML'))
        splitter = QtGui.QSplitter(QtCore.Qt.Vertical)
        self.overview = OverviewList()
        self.overview.init()
        
        splitter.addWidget(self.tabBar2)
        splitter.addWidget(self.overview)
        
        # putting panes together
        hbox.addWidget(widgetLeftPane)
        hbox.addWidget(splitter, 1)
        
        cw = QtGui.QWidget()
        self.setCentralWidget(cw)
        self.centralWidget().setLayout(hbox)
        
    def initActions(self):
        self.newAction = QtGui.QAction(QtGui.QIcon('resources/icons/page-white.png'), Lang.value('MI_New'), self)        
        self.newAction.setShortcut('Ctrl+N')
        self.newAction.triggered.connect(self.onNewFile)

        self.openAction = QtGui.QAction(QtGui.QIcon('resources/icons/folder.png'), Lang.value('MI_Open'), self)        
        self.openAction.setShortcut('Ctrl+O')
        self.openAction.triggered.connect(self.onOpenFile)

        self.saveAction = QtGui.QAction(QtGui.QIcon('resources/icons/disk.png'), Lang.value('MI_Save'), self)        
        self.saveAction.setShortcut('Ctrl+S')
        self.saveAction.triggered.connect(self.onSaveFile)

        self.saveAsAction = QtGui.QAction(QtGui.QIcon('resources/icons/page-white-save.png'), Lang.value('MI_Save_as'), self)        
        self.saveAsAction.triggered.connect(self.onSaveFileAs)

        self.importPbmAction = QtGui.QAction(Lang.value('MI_Import_PBM'), self)        
        self.importPbmAction.triggered.connect(self.onImportPbm)

        self.exportHtmlAction = QtGui.QAction(Lang.value('MI_Export_HTML'), self)        
        self.exportHtmlAction.triggered.connect(self.onExportHtml)
        self.exportPdfAction = QtGui.QAction(QtGui.QIcon('resources/icons/printer.png'), Lang.value('MI_Export_PDF'), self)        
        self.exportPdfAction.triggered.connect(self.onExportPdf)
        self.exportImgAction = QtGui.QAction(Lang.value('MI_Export_Image'), self)        
        self.exportImgAction.triggered.connect(self.onExportImg)
        self.exportHtmlAction.setEnabled(False)

        self.addEntryAction = QtGui.QAction(QtGui.QIcon('resources/icons/add.png'), Lang.value('MI_Add_entry'), self)        
        self.addEntryAction.triggered.connect(self.onAddEntry)

        self.deleteEntryAction = QtGui.QAction(QtGui.QIcon('resources/icons/delete.png'), Lang.value('MI_Delete_entry'), self)        
        self.deleteEntryAction.triggered.connect(self.onDeleteEntry)

        self.exitAction = QtGui.QAction(QtGui.QIcon('resources/icons/exit.png'), Lang.value('MI_Exit'), self)        
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.triggered.connect(self.close)

        self.startPopeyeAction = QtGui.QAction(QtGui.QIcon('resources/icons/key.png'), Lang.value('MI_Run_Popeye'), self)        
        self.startPopeyeAction.setShortcut('F7')
        self.startPopeyeAction.triggered.connect(self.popeyeView.startPopeye)
        self.stopPopeyeAction = QtGui.QAction(QtGui.QIcon('resources/icons/stop.png'), Lang.value('MI_Stop_Popeye'), self)        
        self.stopPopeyeAction.triggered.connect(self.popeyeView.stopPopeye)
        self.optionsAction = QtGui.QAction(QtGui.QIcon('resources/icons/cog-key.png'), Lang.value('MI_Options'), self)        
        self.optionsAction.triggered.connect(self.popeyeView.onOptions)
        self.twinsAction = QtGui.QAction(QtGui.QIcon('resources/icons/gemini.png'), Lang.value('MI_Twins'), self)        
        self.twinsAction.triggered.connect(self.popeyeView.onTwins)

        self.popeyeView.setActions({'start':self.startPopeyeAction, 'stop':self.stopPopeyeAction,\
            'options':self.optionsAction, 'twins':self.twinsAction})
        
        langs = Conf.value('languages')    
        self.langActions = []
        for key in sorted(langs.keys()):
            self.langActions.append(QtGui.QAction(langs[key], self))
            self.langActions[-1].triggered.connect(self.makeSetNewLang(key))
            self.langActions[-1].setCheckable(True)
            self.langActions[-1].setChecked(key == Lang.current)

    def initMenus(self):
        # Menus
        menubar = self.menuBar()
        # File menu
        self.fileMenu = menubar.addMenu(Lang.value('MI_File'))
        map(self.fileMenu.addAction, [self.newAction, self.openAction, self.saveAction, self.saveAsAction])
        self.fileMenu.addSeparator()
        self.langMenu = self.fileMenu.addMenu(Lang.value('MI_Language'))
        map(self.langMenu.addAction, self.langActions)
        self.fileMenu.addSeparator()
        self.importMenu = self.fileMenu.addMenu(Lang.value('MI_Import'))
        self.importMenu.addAction(self.importPbmAction)
        self.exportMenu = self.fileMenu.addMenu(Lang.value('MI_Export'))
        #self.exportMenu.addAction(self.exportHtmlAction)
        self.exportMenu.addAction(self.exportPdfAction)
        self.exportMenu.addAction(self.exportImgAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAction)

        # Entry menu
        self.editMenu = menubar.addMenu(Lang.value('MI_Edit'))
        map(self.editMenu.addAction, [self.addEntryAction, self.deleteEntryAction])
        self.editMenu.addSeparator()

        # Popeye menu
        self.popeyeMenu = menubar.addMenu(Lang.value('MI_Popeye'))
        map(self.popeyeMenu.addAction, [self.startPopeyeAction, self.stopPopeyeAction,\
            self.optionsAction, self.twinsAction])
        
        # help menu
        menubar.addSeparator()
        self.helpMenu = menubar.addMenu(Lang.value('MI_Help'))
        self.aboutAction = QtGui.QAction(QtGui.QIcon('resources/icons/information.png'), Lang.value('MI_About'), self)        
        self.aboutAction.triggered.connect(self.onAbout)
        self.helpMenu.addAction(self.aboutAction)

    def initToolbar(self):
        self.toolbar = self.addToolBar('')
        self.toolbar.setObjectName('thetoolbar')
        map(self.toolbar.addAction, [self.newAction, self.openAction, self.saveAction])
        self.toolbar.addSeparator()
        map(self.toolbar.addAction, [self.addEntryAction, self.deleteEntryAction])
        self.toolbar.addSeparator()
        map(self.toolbar.addAction, [self.startPopeyeAction, self.stopPopeyeAction,\
            self.optionsAction, self.twinsAction])
        self.toolbar.addSeparator()        
        self.createTransformActions()

    def initSignals(self):
        Mainframe.sigWrapper.sigLangChanged.connect(self.onLangChanged)
        Mainframe.sigWrapper.sigModelChanged.connect(self.onModelChanged)
        Mainframe.sigWrapper.sigFocusOnPieces.connect(self.onFocusOnPieces)
        Mainframe.sigWrapper.sigFocusOnStipulation.connect(self.onFocusOnStipulation)
        Mainframe.sigWrapper.sigFocusOnPopeye.connect(self.onFocusOnPopeye)
        Mainframe.sigWrapper.sigFocusOnSolution.connect(self.onFocusOnSolution)

    def initFrame(self):
        # window banner
        self.setWindowIcon(QtGui.QIcon(QtGui.QPixmap('resources/icons/olive.png')))
        
        # restoring windows and toolbars geometry 
        settings = QtCore.QSettings()
        if len(settings.value("geometry").toByteArray()):
            self.restoreGeometry(settings.value("geometry").toByteArray());
            self.restoreState(settings.value("windowState").toByteArray());
        else:
            # first run
            self.setGeometry(32, 32, 32, 32)

        
    def updateTitle(self): 
        docname = Lang.value('WT_New_Collection')
        if Mainframe.model.filename != '':
            head, tail = os.path.split(Mainframe.model.filename)
            docname = tail + ' (' + head + ')'
        title = docname +\
            ' [' + [Lang.value('WT_Saved'), Lang.value('WT_Not_saved')][Mainframe.model.is_dirty] + \
            '] - olive ' + Conf.value('version')
        self.setWindowTitle(title)    
    
    def makeSetNewLang(self, newlang): 
        def setNewLang():
            self.langActions[sorted(Conf.value('languages').keys()).index(Lang.current)].setChecked(False)
            self.langActions[sorted(Conf.value('languages').keys()).index(newlang)].setChecked(True)
            Lang.current = newlang
            Mainframe.sigWrapper.sigLangChanged.emit()
        return setNewLang
    
    def onModelChanged(self):
        self.updateTitle()    

    def onAbout(self):
        dialog = AboutDialog()
        dialog.exec_()
    
    def onLangChanged(self):
        # tab captions
        self.tabBar1.setTabText(0, Lang.value('TC_Info'))
        self.tabBar1.setTabText(1, Lang.value('TC_Pieces'))
        self.tabBar2.setTabText(0, Lang.value('TC_Popeye'))
        self.tabBar2.setTabText(1, Lang.value('TC_Solution'))
        self.tabBar2.setTabText(2, Lang.value('TC_Edit'))
        self.tabBar2.setTabText(3, Lang.value('TC_YAML'))
        
        #actions
        self.exitAction.setText(Lang.value('MI_Exit'))
        self.newAction.setText(Lang.value('MI_New'))
        self.openAction.setText(Lang.value('MI_Open'))
        self.saveAction.setText(Lang.value('MI_Save'))
        self.saveAsAction.setText(Lang.value('MI_Save_as'))
        self.addEntryAction.setText(Lang.value('MI_Add_entry'))
        self.deleteEntryAction.setText(Lang.value('MI_Delete_entry'))
        self.startPopeyeAction.setText(Lang.value('MI_Run_Popeye'))
        self.stopPopeyeAction.setText(Lang.value('MI_Stop_Popeye'))
        self.optionsAction.setText(Lang.value('MI_Options'))
        self.twinsAction.setText(Lang.value('MI_Twins'))
        self.aboutAction.setText(Lang.value('MI_About'))
        self.importPbmAction.setText(Lang.value('MI_Import_PBM'))
        self.exportHtmlAction.setText(Lang.value('MI_Export_HTML'))
        self.exportPdfAction.setText(Lang.value('MI_Export_PDF'))
        self.exportImgAction.setText(Lang.value('MI_Export_Image'))
        
        for i, k in enumerate(Mainframe.transform_names)  :
            self.transforms[i].setText(Lang.value('MI_' + k))
        
        # menus
        self.fileMenu.setTitle(Lang.value('MI_File'))
        self.langMenu.setTitle(Lang.value('MI_Language'))
        self.editMenu.setTitle(Lang.value('MI_Edit'))
        self.popeyeMenu.setTitle(Lang.value('MI_Popeye'))
        self.helpMenu.setTitle(Lang.value('MI_Help'))
        self.importMenu.setTitle(Lang.value('MI_Import'))
        self.exportMenu.setTitle(Lang.value('MI_Export'))
        
        # window title
        self.updateTitle()
        Conf.values['default-lang'] = Lang.current
        
    def onNewFile(self):
        if not self.doDirtyCheck():
            return
        Mainframe.model = model.Model()
        self.overview.rebuild()
        Mainframe.sigWrapper.sigModelChanged.emit()
        
    def onOpenFile(self):
        if not self.doDirtyCheck():
            return
        default_dir = './collections/'
        if Mainframe.model.filename != '':
            default_dir, tail = os.path.split(Mainframe.model.filename)
        fileName = QtGui.QFileDialog.getOpenFileName(self, Lang.value('MI_Open'), default_dir, "(*.olv)")
        if not fileName:
            return
        self.openCollection(fileName)

    def openCollection(self,  fileName):
        try:
            f = open(fileName, 'r')
            Mainframe.model = model.Model()
            Mainframe.model.delete(0)
            for data in yaml.load_all(f):
                Mainframe.model.add(model.makeSafe(data), False)
            f.close()
            Mainframe.model.is_dirty = False
            self.overview.rebuild()
        except IOError:
            msgBox(Lang.value('MSG_IO_failed'))
            Mainframe.model = model.Model()
        except yaml.YAMLError, e:
            msgBox(Lang.value('MSG_YAML_failed') % e)
            Mainframe.model = model.Model()
        else:
            if len(Mainframe.model.entries) == 0:
                Mainframe.model = model.Model()
            Mainframe.model.filename = unicode(fileName)
        finally:
            self.overview.rebuild()
            Mainframe.sigWrapper.sigModelChanged.emit()
        
    def onSaveFile(self):
        if Mainframe.model.filename != '':
            f = open(Mainframe.model.filename, 'w')
            try:
                for i in xrange(len(Mainframe.model.entries)):
                    f.write("---\n")
                    f.write(unicode(yaml.dump(Mainframe.model.entries[i], encoding=None, allow_unicode=True)).encode('utf8'))
                    Mainframe.model.dirty_flags[i] = False
                Mainframe.model.is_dirty = False
                self.overview.removeDirtyMarks()
            finally:
                f.close()
                Mainframe.sigWrapper.sigModelChanged.emit()
        else:
            self.onSaveFileAs()

    def onSaveFileAs(self):
        default_dir = './collections/'
        if Mainframe.model.filename != '':
            default_dir, tail = os.path.split(Mainframe.model.filename)
        fileName = QtGui.QFileDialog.getSaveFileName(self, Lang.value('MI_Save_as'), default_dir, "(*.olv)")
        if not fileName:
            return
        Mainframe.model.filename = str(fileName)
        self.onSaveFile()
        
    def doDirtyCheck(self):
        if not Mainframe.model.is_dirty:
            return True
        dialog = YesNoCancelDialog(Lang.value('MSG_Not_saved'))
        if(dialog.exec_()):
            if 'Yes' == dialog.outcome:
                self.onSaveFile()
                return True
            if 'No' == dialog.outcome:
                return True
            return False # ie cancel the caller
        else:
            return False
        return False
        
    def onImportPbm(self):
        if not self.doDirtyCheck():
            return
        default_dir = './collections/'
        if Mainframe.model.filename != '':
            default_dir, tail = os.path.split(Mainframe.model.filename)
        fileName = QtGui.QFileDialog.getOpenFileName(self, Lang.value('MI_Import_PBM'), default_dir, "(*.pbm)")
        if not fileName:
            return
        try:
            Mainframe.model = model.Model()
            Mainframe.model.delete(0)
            file = open(fileName)
            for data in pbm.PbmEntries(file):
                Mainframe.model.add(model.makeSafe(data), False)
            file.close()
            Mainframe.model.is_dirty = False
        except IOError:
            msgBox(Lang.value('MSG_IO_failed'))
        except:
            msgBox(Lang.value('MSG_PBM_import_failed'))
        finally:
            if len(Mainframe.model.entries) == 0:
                Mainframe.model = model.Model()
            self.overview.rebuild()
            Mainframe.sigWrapper.sigModelChanged.emit()
        
    def onExportHtml(self):
        pass

    def onExportPdf(self):
        default_dir = './collections/'
        fileName = QtGui.QFileDialog.getSaveFileName(self,\
            Lang.value('MI_Export') + ' ' + Lang.value('MI_Export_PDF'), default_dir, "(*.pdf)")
        if not fileName:
            return
        try:
            ed = pdf.ExportDocument(Mainframe.model.entries, Lang)
            ed.doExport(fileName)
        except IOError:
            msgBox(Lang.value('MSG_IO_failed'))
        except:
            msgBox(Lang.value('MSG_PDF_export_failed'))
    def onExportImg(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self,\
            Lang.value('MI_Export') + ' / ' + Lang.value('MI_Export_Image'), '', "(*.png)")
        if not fileName:
            return
        try:
            print Mainframe.model.board.toFen(), fileName 
            xfen2img.convert(Mainframe.model.board.toFen(), str(fileName))
        except IOError:
            msgBox(Lang.value('MSG_IO_failed'))
        except:
            msgBox(Lang.value('MSG_Image_export_failed'))
        
    def onAddEntry(self):
        idx = Mainframe.model.current + 1
        Mainframe.model.insert(copy.deepcopy(Mainframe.model.defaultEntry), True, idx)
        self.overview.insertItem(idx)
        
    def onDeleteEntry(self):
        dialog = YesNoDialog(Lang.value('MSG_Confirm_delete_entry'))
        if not dialog.exec_():
            return
        self.overview.skip_current_item_changed = True
        idx = Mainframe.model.current
        Mainframe.model.delete(idx)
        self.overview.deleteItem(idx)
        self.overview.skip_current_item_changed = False
        if len(Mainframe.model.entries) == 0:
            Mainframe.model.insert(copy.deepcopy(Mainframe.model.defaultEntry), True, 0)
            self.overview.insertItem(idx)
        else:
            self.overview.setCurrentItem(self.overview.topLevelItem(Mainframe.model.current))
        Mainframe.sigWrapper.sigModelChanged.emit()
    def onFocusOnPieces(self):
        self.tabBar1.setCurrentWidget(self.chessBox)
    def onFocusOnStipulation(self):
        self.tabBar2.setCurrentWidget(self.popeyeView)
    def onFocusOnPopeye(self):
        self.tabBar2.setCurrentWidget(self.popeyeView)
    def onFocusOnSolution(self):
        self.tabBar2.setCurrentWidget(self.solutionView)
    
    def createTransformActions(self):
        self.transforms = []
        for i, k in enumerate(Mainframe.transform_names):
            self.transforms.append(QtGui.QAction(QtGui.QIcon('resources/icons/arrow-' +\
                Mainframe.transform_icons[i] + '.png'), Lang.value('MI_'+k), self))
            self.transforms[-1].triggered.connect(self.createTransformsCallable(k))
            self.toolbar.addAction(self.transforms[-1])
            self.editMenu.addAction(self.transforms[-1])
        
    def createTransformsCallable(self, command):
        def callable():
            if command == 'Shift_up':
                Mainframe.model.board.shift(0, -1)
            elif command == 'Shift_down':
                Mainframe.model.board.shift(0, 1)
            elif command == 'Shift_left':
                Mainframe.model.board.shift(-1, 0)
            elif command == 'Shift_right':
                Mainframe.model.board.shift(1, 0)
            elif command == 'Rotate_CW':
                Mainframe.model.board.rotate('270')
            elif command == 'Rotate_CCW':
                Mainframe.model.board.rotate('90')
            elif command == 'Mirror_horizontal':
                Mainframe.model.board.mirror('a1<-->a8')
            elif command == 'Mirror_vertical':
                Mainframe.model.board.mirror('a1<-->h1')
            elif command == 'Clear':
                Mainframe.model.board.clear()
            else:
                pass
            Mainframe.model.onBoardChanged()
            Mainframe.sigWrapper.sigModelChanged.emit()
        return callable
        
    def closeEvent(self, event):
        if not self.doDirtyCheck():
            event.ignore()
        settings = QtCore.QSettings();
        settings.setValue("geometry", self.saveGeometry());
        settings.setValue("windowState", self.saveState());

        self.chessBox.sync()
        Conf.write()
        event.accept()            

class ClickableLabel(QtGui.QLabel):
    def __init__(self, str):
        super(ClickableLabel, self).__init__(str)
        self.setOpenExternalLinks(True)
        
class AboutDialog(QtGui.QDialog):                
    def __init__(self):
        super(AboutDialog, self).__init__()
        self.setAutoFillBackground(True)
        self.setBackgroundRole(QtGui.QPalette.Light)
        vbox = QtGui.QVBoxLayout()
        lblLogo = QtGui.QLabel()
        iconLogo = QtGui.QIcon('resources/icons/olive-logo.png')
        lblLogo.setPixmap(iconLogo.pixmap(331, 139))
        vbox.addWidget(lblLogo, QtCore.Qt.AlignCenter)
        vbox.addWidget(ClickableLabel('olive v'+Conf.value('version') + ' is free software licensed under GNU GPL'))
        vbox.addWidget(ClickableLabel('&copy; 2011-2012 Dmitri Turevski &lt;<a href="mailto:dmitri.turevski@gmail.com">dmitri.turevski@gmail.com</a>&gt;'))
        vbox.addWidget(ClickableLabel('For more information please visit <a href="http://code.google.com/p/olive-gui/">http://code.google.com/p/olive-gui/</a>'))

        vbox.addStretch(1)
        buttonOk = QtGui.QPushButton(Lang.value('CO_OK'), self)
        buttonOk.clicked.connect(self.accept)
        vbox.addWidget(buttonOk)

        self.setLayout(vbox)
        self.setWindowTitle(Lang.value('MI_About'))

class YesNoDialog(QtGui.QDialog):                
    def __init__(self, msg):
        super(YesNoDialog, self).__init__()
        
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(QtGui.QLabel(msg))
        vbox.addStretch(1)
        
        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        buttonYes = QtGui.QPushButton(Lang.value('CO_Yes'), self)
        buttonYes.clicked.connect(self.accept)
        buttonNo = QtGui.QPushButton(Lang.value('CO_No'), self)
        buttonNo.clicked.connect(self.reject)
        
        hbox.addWidget(buttonYes)
        hbox.addWidget(buttonNo)
        vbox.addLayout(hbox)
        self.setLayout(vbox)

class YesNoCancelDialog(QtGui.QDialog):                
    def __init__(self, msg):
        super(YesNoCancelDialog, self).__init__()
        
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(QtGui.QLabel(msg))
        vbox.addStretch(1)
        
        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        buttonYes = QtGui.QPushButton(Lang.value('CO_Yes'), self)
        buttonYes.clicked.connect(self.yes)
        buttonNo = QtGui.QPushButton(Lang.value('CO_No'), self)
        buttonNo.clicked.connect(self.no)
        buttonCancel = QtGui.QPushButton(Lang.value('CO_Cancel'), self)
        buttonCancel.clicked.connect(self.cancel)
        
        hbox.addWidget(buttonYes)
        hbox.addWidget(buttonNo)
        hbox.addWidget(buttonCancel)
        vbox.addLayout(hbox)
        self.setLayout(vbox)
        
        self.choice = 'Yes'
    def yes(self):
        self.outcome = 'Yes'
        self.accept()
    def no(self):
        self.outcome = 'No'
        self.accept()
    def cancel(self):
        self.outcome = 'Cancel'
        self.reject()
        
        
class FenView(QtGui.QLineEdit):
    def __init__(self):
        super(FenView, self).__init__()
        self.skip_model_changed = False
        Mainframe.sigWrapper.sigModelChanged.connect(self.onModelChanged)
        self.textChanged.connect(self.onTextChanged)
        
    def onModelChanged(self):
        if self.skip_model_changed:
            return
        self.skip_model_changed = True
        fen = Mainframe.model.board.toFen()
        fen = fen.replace('S', Conf.value('horsehead-glyph').upper()).\
            replace('s', Conf.value('horsehead-glyph').lower())
        self.setText(fen)
        self.skip_model_changed = False

    def onTextChanged(self, text):
        if self.skip_model_changed:
            return
        Mainframe.model.board.fromFen(text)
        self.skip_model_changed = True
        Mainframe.model.onBoardChanged()
        Mainframe.sigWrapper.sigModelChanged.emit()
        self.skip_model_changed = False
        
class OverviewList(QtGui.QTreeWidget):

    def __init__(self):
        super(OverviewList, self).__init__()
        self.setAlternatingRowColors(True)
        
        Mainframe.sigWrapper.sigLangChanged.connect(self.onLangChanged)
        Mainframe.sigWrapper.sigModelChanged.connect(self.onModelChanged)
        self.currentItemChanged.connect(self.onCurrentItemChanged)
        self.skip_model_changed = False
        self.skip_current_item_changed = False
        
    def init(self):
        self.setColumnCount(6)
        self.onLangChanged()
    
    def onLangChanged(self):
        self.setHeaderLabels(['', Lang.value('EP_Authors'), \
            Lang.value('EP_Source'), Lang.value('EP_Date'), \
            Lang.value('EP_Distinction'), Lang.value('EP_Stipulation'), \
            Lang.value('EP_Pieces_count')])
    
    def removeDirtyMarks(self):
        for i in xrange(len(Mainframe.model.entries)):
            self.topLevelItem(i).setText(0, str(i+1))

    def rebuild(self):
        self.clear()
        for i in xrange(len(Mainframe.model.entries)):
            newItem = QtGui.QTreeWidgetItem()
            for j,  text in enumerate(self.createItem(i)):
                newItem.setText(j,  text)
            self.addTopLevelItem(newItem)
        self.skip_model_changed = True
        self.setCurrentItem(self.topLevelItem(Mainframe.model.current))
        
    def insertItem(self, idx):
        newItem = QtGui.QTreeWidgetItem()
        for j,  text in enumerate(self.createItem(idx)):
            newItem.setText(j,  text)
        self.insertTopLevelItem(idx, newItem)
        
        for j in xrange(idx + 1, len(Mainframe.model.entries)):
            self.topLevelItem(j).setText(0, str(j+1)+['', '*'][Mainframe.model.dirty_flags[j]])
        self.skip_model_changed = True
        self.setCurrentItem(self.topLevelItem(Mainframe.model.current))

    def deleteItem(self, idx):
        self.takeTopLevelItem(idx)
        for j in xrange(idx, len(Mainframe.model.entries)):
            self.topLevelItem(j).setText(0, str(j+1)+['', '*'][Mainframe.model.dirty_flags[j]])
        # which item is current now depends and handled by the caller (Mainframe)
        
    def createItem(self, idx):
        item = []
        item.append(str(idx+1)+['', '*'][Mainframe.model.dirty_flags[idx]])
        
        authorsTxt = ''
        if Mainframe.model.entries[idx].has_key('authors'):
            authorsTxt = '; '.join(Mainframe.model.entries[idx]['authors'])
        item.append(authorsTxt)
        
        for key in ['source',  'date',  'distinction',  'stipulation']:
            if Mainframe.model.entries[idx].has_key(key):
                item.append(unicode(Mainframe.model.entries[idx][key]))
            else:
                item.append('')
        
        item.append(Mainframe.model.pieces_counts[idx])
        
        return item
    
    def onModelChanged(self):
        if self.skip_model_changed:
            self.skip_model_changed = False
            return
        
        for i,  text in enumerate(self.createItem(Mainframe.model.current)):
            self.topLevelItem(Mainframe.model.current).setText(i,  text)

    def onCurrentItemChanged(self, current, prev):
        if current is None: # happens when deleting
            return
        if self.skip_current_item_changed:
            return
        
        # stupid hack:
        text = current.text(0)
        if(text[-1] == '*'): text = text[:-1]
        Mainframe.model.setNewCurrent(int(text) - 1)
        
        self.skip_model_changed = True
        Mainframe.sigWrapper.sigModelChanged.emit()

class DraggableLabel(QtGui.QLabel):
    def __init__(self, id):
        super(DraggableLabel, self).__init__()
        self.id = id
    def setTextAndFont(self, text, font):
        self.setText(text)
        self.setFont(Mainframe.fonts[font])

    def mousePressEvent(self, e): # mouseMoveEvent works as well but with slightly different mechanics
        Mainframe.sigWrapper.sigFocusOnPieces.emit()
    
        if e.buttons() != QtCore.Qt.LeftButton:
            return
        if Mainframe.model.board.board[self.id] is None:
            return

        Mainframe.currentlyDragged = Mainframe.model.board.board[self.id]
        Mainframe.model.board.drop(self.id)
        Mainframe.model.onBoardChanged()
        Mainframe.sigWrapper.sigModelChanged.emit()
        
        mimeData = QtCore.QMimeData()
        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)
        drag.setHotSpot(e.pos() - self.rect().topLeft())
        dropAction = drag.start(QtCore.Qt.MoveAction)
        Mainframe.currentlyDragged = None

    def dragEnterEvent(self, e):
        e.accept()

    def dropEvent(self, e):
        e.setDropAction(QtCore.Qt.MoveAction)
        e.accept()

        if Mainframe.currentlyDragged is None:
            return
        Mainframe.model.board.add(model.Piece(Mainframe.currentlyDragged.name, Mainframe.currentlyDragged.color, Mainframe.currentlyDragged.specs), self.id)
        Mainframe.model.onBoardChanged()
        Mainframe.sigWrapper.sigModelChanged.emit()

class ChessBoxItem(QtGui.QLabel):
    def __init__(self, piece):
        super(ChessBoxItem, self).__init__()
        self.changePiece(piece)
        
    def changePiece(self, piece):
        self.piece = piece
        if self.piece is None:
            self.setFont(Mainframe.fonts['d'])
            self.setText("\xA3")
            self.setToolTip(str(self.piece))
        else:
            glyph = piece.toFen()
            if len(glyph) > 1:
                glyph = glyph[1:-1]
            self.setFont(Mainframe.fonts[model.FairyHelper.fontinfo[glyph]['family']])
            self.setText(model.FairyHelper.fontinfo[glyph]['chars'][0])
            self.setToolTip(str(self.piece))

    def mousePressEvent(self, e): # mouseMoveEvent works as well but with slightly different mechanics
        if self.piece is None:
            return
        if e.buttons() != QtCore.Qt.LeftButton:
            return

        Mainframe.currentlyDragged = self.piece        
        mimeData = QtCore.QMimeData()
        drag = QtGui.QDrag(self)
        drag.setMimeData(mimeData)
        drag.setHotSpot(e.pos() - self.rect().topLeft())
        dropAction = drag.start(QtCore.Qt.MoveAction)
        Mainframe.currentlyDragged = None

class ChessBoxItemManagable(ChessBoxItem):        
    def __init__(self, piece, id, manager):
        self.id, self.manager = id, manager
        super(ChessBoxItemManagable, self).__init__(piece)

    def mousePressEvent(self, e):
        if not self.piece is None:
            super(ChessBoxItemManagable, self).mousePressEvent(e)
        if e.buttons() != QtCore.Qt.RightButton:
            return
        
        menu = QtGui.QMenu(Lang.value('MI_Fairy_pieces'))
        if self.piece is None:
            addNewAction = QtGui.QAction(Lang.value('MI_Add_piece'), self)
            addNewAction.triggered.connect(self.choose)
            menu.addAction(addNewAction)
        else:
            deleteAction = QtGui.QAction(Lang.value('MI_Delete_piece'), self)
            deleteAction.triggered.connect(self.remove)
            menu.addAction(deleteAction)
        deleteAllAction = QtGui.QAction(Lang.value('MI_Delete_all_pieces'), self)
        deleteAllAction.triggered.connect(self.manager.deleteAll)
        menu.addAction(deleteAllAction)
        
        menu.exec_(e.globalPos())
        
    def remove(self):
        self.changePiece(None)
        
    def choose(self):
        dialog = AddFairyPieceDialog(Lang)
        if(dialog.exec_()):
            self.changePiece(dialog.getPiece())

class BoardView(QtGui.QWidget):
    def __init__(self):
        super(BoardView, self).__init__()
        Mainframe.sigWrapper.sigModelChanged.connect(self.onModelChanged)
        self.skip_model_changed = False
        
        vbox = QtGui.QVBoxLayout()
        vbox.setSpacing(0)
        
        labelTop = QtGui.QLabel("\xA3\xA6\xA6\xA6\xA6\xA6\xA6\xA6\xA6\xA3")
        labelTop.setFont(Mainframe.fonts['d'])

        labelBottom = QtGui.QLabel("\x4F\xA7\xA8\xA9\xAA\xAB\xAC\xAD\xAE\xAF\x4F")
        labelBottom.setFont(Mainframe.fonts['y'])

        hbox = QtGui.QHBoxLayout()
        hbox.setSpacing(0)
        
        vboxEdgeLeft = QtGui.QVBoxLayout()
        vboxEdgeLeft.setSpacing(0)
        centerWidget = QtGui.QWidget()
        centerWidget.setBackgroundRole(QtGui.QPalette.Light)
        centerWidget.setAutoFillBackground(True)
        centerGrid = QtGui.QGridLayout()
        centerGrid.setVerticalSpacing(0)
        centerGrid.setHorizontalSpacing(0)  
        centerGrid.setContentsMargins(0, 0, 0, 0)
        centerWidget.setLayout(centerGrid)
        self.labels = []
        for i in xrange(8):
            for j in xrange(8):
                lbl = DraggableLabel(j+i*8)
                lbl.setTextAndFont(["\xA3", "\xA4"][(i+j)%2], 'd')
                #lbl.setDragEnabled(True)
                lbl.setAcceptDrops(True)
                centerGrid.addWidget(lbl, i, j)
                self.labels.append(lbl)
        
        vboxEdgeRight = QtGui.QVBoxLayout()
        vboxEdgeRight.setSpacing(0)
        for i in xrange(8):
            labelLeft = QtGui.QLabel(chr(110 - i))
            labelLeft.setFont(Mainframe.fonts['y'])
            vboxEdgeLeft.addWidget(labelLeft)
            labelRight = QtGui.QLabel("\xA5")
            labelRight.setFont(Mainframe.fonts['d'])
            vboxEdgeRight.addWidget(labelRight)
        
        #hbox.addLayout(vboxEdgeLeft)
        hbox.addWidget(centerWidget)
        hbox.addStretch(1)
        #hbox.addLayout(vboxEdgeRight)
        
        
        hboxExtra = QtGui.QHBoxLayout()
        spacer = QtGui.QLabel("\xA3")
        spacer.setFont(Mainframe.fonts['d'])
        self.labelStipulation = QtGui.QLabel("")
        self.labelPiecesCount = QtGui.QLabel("")
        #hboxExtra.addWidget(spacer)
        hboxExtra.addWidget(self.labelStipulation)
        hboxExtra.addStretch(1)
        hboxExtra.addWidget(self.labelPiecesCount)
        #hboxExtra.addWidget(spacer)
        
        #vbox.addWidget(labelTop)
        vbox.addLayout(hbox)
        #vbox.addWidget(labelBottom)
        vbox.addLayout(hboxExtra)
        
        self.setLayout(vbox)

    def onModelChanged(self):
        if self.skip_model_changed:
            self.skip_model_changed = False
            return
            
        for i, lbl in enumerate(self.labels):
            if Mainframe.model.board.board[i] is None:
                lbl.setFont(Mainframe.fonts['d'])
                lbl.setText(["\xA3", "\xA4"][((i>>3) + (i%8))%2])
            else:
                glyph = Mainframe.model.board.board[i].toFen()
                if len(glyph) > 1:
                    glyph = glyph[1:-1]
                lbl.setFont(Mainframe.fonts[model.FairyHelper.fontinfo[glyph]['family']])
                lbl.setText(model.FairyHelper.fontinfo[glyph]['chars'][((i>>3) + (i%8))%2])
        if(Mainframe.model.cur().has_key('stipulation')):
            self.labelStipulation.setText(Mainframe.model.cur()['stipulation'])
        else:
            self.labelStipulation.setText("")
        self.labelPiecesCount.setText(Mainframe.model.board.getPiecesCount())


class InfoView(QtGui.QTextEdit):
    def __init__(self):
        super(InfoView, self).__init__()
        self.setReadOnly(True)
        Mainframe.sigWrapper.sigModelChanged.connect(self.onModelChanged)
        Mainframe.sigWrapper.sigLangChanged.connect(self.onModelChanged)

    def onModelChanged(self):
        chunks = [self.meta(), self.solver(), self.legend()]
        self.setText("<br/><br/>".join([x for x in chunks if x != '']))
        
    def meta(self):
        return pdf.ExportDocument.header(Mainframe.model.cur())
        
    def solver(self):
        return pdf.ExportDocument.solver(Mainframe.model.cur(), Lang)

    def legend(self):
        return pdf.ExportDocument.legend(Mainframe.model.board)
     
        
class ChessBox(QtGui.QWidget):
    rows, cols = 3, 7
    
    def __init__(self):
        super(ChessBox, self).__init__()
        self.gboxOrtho = QtGui.QGroupBox(Lang.value('TC_Pieces_Ortho'))
        self.gboxFairy = QtGui.QGroupBox(Lang.value('TC_Pieces_Fairy'))
        self.gridOrtho = QtGui.QGridLayout()
        self.gridFairy = QtGui.QGridLayout()
        self.gridFairy.setVerticalSpacing(0)
        self.gridFairy.setHorizontalSpacing(0)
        Mainframe.sigWrapper.sigLangChanged.connect(self.onLangChanged)
 
        self.items = []
        
        for i, color in enumerate(['white', 'black']):
            for j, name in enumerate('KQRBSP'):
                item = ChessBoxItem(model.Piece(name, color, []))
                self.gridOrtho.addWidget(item, i, j)
        for i in xrange(ChessBox.rows):
            for j in xrange(ChessBox.cols):
                x = i*ChessBox.cols + j
                item = ChessBoxItemManagable(None, i*ChessBox.cols + j, self)
                if '' != Conf.value('fairy-zoo')[i][j]:
                    item.changePiece(model.Piece.fromAlgebraic(Conf.value('fairy-zoo')[i][j]))
                self.items.append(item)
                self.gridFairy.addWidget(item, i, j)

        # a stretcher
        self.gridFairy.addWidget(QtGui.QWidget(), ChessBox.rows, ChessBox.cols)
        self.gridFairy.setRowStretch(ChessBox.rows, 1)
        self.gridFairy.setColumnStretch(ChessBox.cols, 1)
        
        self.gboxFairy.setLayout(self.gridFairy)
        self.gboxOrtho.setLayout(self.gridOrtho)
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.gboxOrtho)
        vbox.addWidget(self.gboxFairy)
        vbox.addStretch(10)
        self.setLayout(vbox)                  
                
    def onLangChanged(self):
        self.gboxOrtho.setTitle(Lang.value('TC_Pieces_Ortho'))
        self.gboxFairy.setTitle(Lang.value('TC_Pieces_Fairy'))
        
    def deleteAll(self):
        for item in self.items:
            if not item.piece is None:
                item.changePiece(None)
                
    def sync(self):
        zoo = Conf.value('fairy-zoo')
        for i in xrange(ChessBox.rows):
            for j in xrange(ChessBox.cols):
                if not self.items[i*ChessBox.cols + j].piece is None:
                    zoo[i][j] = self.items[i*ChessBox.cols + j].piece.serialize()
                else:
                    zoo[i][j] = ''
        
                
class AddFairyPieceDialog(options.OkCancelDialog):
    def __init__(self, Lang):
        form = QtGui.QFormLayout()
        self.comboColor = QtGui.QComboBox()
        self.comboColor.addItems(model.COLORS)
        form.addRow(Lang.value('PP_Color'), self.comboColor)
        
        self.piece_types = sorted(model.FairyHelper.glyphs.iterkeys())
        self.comboType = QtGui.QComboBox()
        self.comboType.addItems([x + ' (' + model.FairyHelper.glyphs[x]['name'] + ')' for x in self.piece_types])
        form.addRow(Lang.value('PP_Type'), self.comboType)
                
        vbox = QtGui.QVBoxLayout()
        vbox.addLayout(form, 1)
        vbox.addWidget(QtGui.QLabel(Lang.value('PP_Fairy_properties')))
        
        self.checkboxes = [QtGui.QCheckBox(x) for x in model.FAIRYSPECS]
        for box in self.checkboxes:
            vbox.addWidget(box)
            
        self.mainWidget = QtGui.QWidget()
        self.mainWidget.setLayout(vbox)
        super(AddFairyPieceDialog, self).__init__(Lang)
        
        self.setWindowTitle(Lang.value('MI_Add_piece'))
        
    def getPiece(self):
        color = str(self.comboColor.currentText())
        type = str(self.piece_types[self.comboType.currentIndex()])
        specs = [x for i, x in enumerate(model.FAIRYSPECS) if self.checkboxes[i].isChecked()]
        return model.Piece(type, color, specs)
        
class EasyEditView(QtGui.QWidget):

    def __init__(self):
        super(EasyEditView, self).__init__()
        grid = QtGui.QGridLayout()
        # authors
        self.labelAuthors = QtGui.QLabel(Lang.value('EP_Authors')+':<br/><br/>'+ Lang.value('EE_Authors_memo'))
        self.inputAuthors = QtGui.QTextEdit()
        grid.addWidget(self.labelAuthors, 0, 0)
        grid.addWidget(self.inputAuthors, 0, 1)

        self.labelSource = QtGui.QLabel(Lang.value('EP_Source') + ':')
        self.memoSource = QtGui.QLabel(Lang.value('EE_Source_memo'))
        self.inputSource = QtGui.QLineEdit()
        self.inputIssueId = QtGui.QLineEdit()
        self.inputIssueId.setFixedWidth(self.inputIssueId.minimumSizeHint().width())
        self.inputSourceId = QtGui.QLineEdit()
        self.inputSourceId.setFixedWidth(self.inputSourceId.minimumSizeHint().width())
        tmpWidget = QtGui.QWidget()
        hbox = QtGui.QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(self.inputSource)
        hbox.addWidget(self.inputIssueId)
        hbox.addWidget(self.inputSourceId)
        hbox.addWidget(self.memoSource)
        tmpWidget.setLayout(hbox)
        grid.addWidget(self.labelSource, 1, 0)
        grid.addWidget(tmpWidget, 1, 1)

        self.labelDate = QtGui.QLabel(Lang.value('EP_Date') + ':')
        self.memoDate = QtGui.QLabel(Lang.value('EE_Date_memo'))
        self.inputDateYear = QtGui.QLineEdit()
        self.inputDateYear.setMaxLength(4)
        self.inputDateYear.setValidator(QtGui.QIntValidator())
        self.inputDateYear.setFixedWidth(self.inputDateYear.minimumSizeHint().width())
        self.inputDateMonth = QtGui.QComboBox()
        self.inputDateMonth.addItems([''])
        self.inputDateMonth.addItems([str(x) for x in xrange(1, 13)])
        self.inputDateDay = QtGui.QComboBox()
        self.inputDateDay.addItems([''])
        self.inputDateDay.addItems(["%02d"%x for x in xrange(1, 32)])
        tmpWidget = QtGui.QWidget()
        hbox = QtGui.QHBoxLayout()
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.addWidget(self.inputDateYear, 1)
        hbox.addWidget(self.inputDateMonth)
        hbox.addWidget(self.inputDateDay)
        hbox.addWidget(self.memoDate)
        hbox.addStretch(1)
        tmpWidget.setLayout(hbox)
        grid.addWidget(self.labelDate, 2, 0)
        grid.addWidget(tmpWidget, 2, 1)

        self.labelDistinction = QtGui.QLabel(Lang.value('EP_Distinction') + ':')
        self.inputDistinction = DistinctionWidget()
        grid.addWidget(self.labelDistinction, 3, 0)
        grid.addWidget(self.inputDistinction, 3, 1)
        
        # stretcher
        grid.addWidget(QtGui.QWidget(), 4, 1)
        grid.setRowStretch(4, 1)
        
        self.setLayout(grid)
        
        self.skip_model_changed = False
        Mainframe.sigWrapper.sigModelChanged.connect(self.onModelChanged)
        Mainframe.sigWrapper.sigLangChanged.connect(self.onLangChanged)
        
        self.inputAuthors.textChanged.connect(self.onChanged)
        self.inputSource.textChanged.connect(self.onChanged)
        self.inputIssueId.textChanged.connect(self.onChanged)
        self.inputSourceId.textChanged.connect(self.onChanged)
        self.inputDateYear.textChanged.connect(self.onChanged)
        self.inputDateMonth.currentIndexChanged.connect(self.onChanged)
        self.inputDateDay.currentIndexChanged.connect(self.onChanged)
        
        
    def onModelChanged(self):
        if self.skip_model_changed:
            return

        self.skip_model_changed = True

        if Mainframe.model.cur().has_key('authors'):
            self.inputAuthors.setText("\n".join(Mainframe.model.cur()['authors']))
        else:
            self.inputAuthors.setText("")

        if Mainframe.model.cur().has_key('source'):
            self.inputSource.setText(Mainframe.model.cur()['source'])
        else:
            self.inputSource.setText("")
        
        issue_id, source_id = Mainframe.model.parseSourceId()
        self.inputIssueId.setText(issue_id)
        self.inputSourceId.setText(source_id)

        y, m, d = Mainframe.model.parseDate()
        self.inputDateYear.setText(y)
        self.inputDateMonth.setCurrentIndex(m)
        self.inputDateDay.setCurrentIndex(d)
        
        self.skip_model_changed = False
        
    def onChanged(self):
        if self.skip_model_changed:
            return
        
        Mainframe.model.cur()['authors'] = [x.strip() for x in unicode(self.inputAuthors.toPlainText()).split("\n") if x.strip() != '']
        Mainframe.model.cur()['source'] = unicode(self.inputSource.text()).strip()
        i_id, s_id = unicode(self.inputIssueId.text()).strip(), unicode(self.inputSourceId.text()).strip()
        is_id = '/'.join([i_id,  s_id])
        if is_id.startswith('/'):
            is_id = is_id[1:]
        Mainframe.model.cur()['source-id'] = is_id

        date = model.myint(unicode(self.inputDateYear.text()).encode('ascii', 'replace'))
        if date != 0:
            date = str(date)
            if self.inputDateMonth.currentIndex() != 0:
                date = date + '-' + ("%02d" % self.inputDateMonth.currentIndex())
                if self.inputDateDay.currentIndex() != 0:
                    date = date + '-' + ("%02d" % self.inputDateDay.currentIndex())
            Mainframe.model.cur()['date'] = date
        elif Mainframe.model.cur().has_key('date'):
            del Mainframe.model.cur()['date']

        for k in ['source', 'source-id']:
            if Mainframe.model.cur()[k] == '':
                del Mainframe.model.cur()[k]
        for k in ['authors']:
            if len(Mainframe.model.cur()[k]) == 0:
                del Mainframe.model.cur()[k]
        
        
        self.skip_model_changed = True
        Mainframe.model.markDirty()
        Mainframe.sigWrapper.sigModelChanged.emit()
        self.skip_model_changed = False
        
    def onLangChanged(self):
        self.labelAuthors.setText(Lang.value('EP_Authors')+':<br/><br/>'+ Lang.value('EE_Authors_memo'))
        self.labelAuthors.setToolTip(Lang.value('EE_Authors_memo'))
        self.labelSource.setText(Lang.value('EP_Source') + ':')
        self.memoSource.setText(Lang.value('EE_Source_memo'))
        self.labelDate.setText(Lang.value('EP_Date') + ':')
        self.memoDate.setText(Lang.value('EE_Date_memo'))
        self.labelDistinction.setText(Lang.value('EP_Distinction') + ':')
        
class DistinctionWidget(QtGui.QWidget):
    names = ['', 'Place', 'Prize', 'HM', 'Comm.']
    def __init__(self):
        super(DistinctionWidget, self).__init__()
        hbox = QtGui.QHBoxLayout()
        self.special = QtGui.QCheckBox("Special")
        hbox.addWidget(self.special)
        self.lo = QtGui.QSpinBox()
        hbox.addWidget(self.lo)
        self.hi = QtGui.QSpinBox()
        hbox.addWidget(self.hi)
        self.name = QtGui.QComboBox()
        self.name.addItems(DistinctionWidget.names)
        hbox.addWidget(self.name)
        self.comment = QtGui.QLineEdit()
        hbox.addWidget(self.comment)
        hbox.addStretch(1)
        self.setLayout(hbox)
     
        self.special.stateChanged.connect(self.onChanged)
        self.name.currentIndexChanged.connect(self.onChanged)
        self.lo.valueChanged.connect(self.onChanged)
        self.hi.valueChanged.connect(self.onChanged)
        self.comment.textChanged.connect(self.onChanged)
        
        Mainframe.sigWrapper.sigModelChanged.connect(self.onModelChanged)
        self.skip_model_changed = False
    
    def onChanged(self):
        if self.skip_model_changed:
            return
        distinction = self.get()
        if Mainframe.model.cur().has_key('distinction'):
            if distinction == Mainframe.model.cur()['distinction']:
                return
        else:
            if distinction =='':
                return
        self.skip_model_changed = True
        Mainframe.model.cur()['distinction'] = distinction
        Mainframe.model.markDirty()
        Mainframe.sigWrapper.sigModelChanged.emit()
        self.skip_model_changed = False

    def set(self, distinction):
        self.special.setChecked(distinction.special)
        self.lo.setValue(distinction.lo)
        self.hi.setValue(distinction.hi)
        self.name.setCurrentIndex(DistinctionWidget.names.index(distinction.name))
        self.comment.setText(distinction.comment)
        
    def get(self):
        distinction = model.Distinction()
        distinction.special = self.special.isChecked()
        distinction.name = DistinctionWidget.names[self.name.currentIndex()]
        distinction.lo = self.lo.value()
        distinction.hi = self.hi.value()
        distinction.comment = unicode(self.comment.text())
        return unicode(distinction)
        
    def onModelChanged(self):
        if self.skip_model_changed:
            return
        distinction = model.Distinction()
        if Mainframe.model.cur().has_key('distinction'):
            distinction = model.Distinction.fromString(Mainframe.model.cur()['distinction'])
        self.skip_model_changed = True
        self.set(distinction)
        self.skip_model_changed = False

class KeywordsInputWidget(QtGui.QTextEdit):
    def __init__(self):
        super(KeywordsInputWidget, self).__init__()
        self.kwdMenu = QtGui.QMenu(Lang.value('MI_Add_keyword'))
        for section in sorted(Conf.keywords.keys()):
            submenu = self.kwdMenu.addMenu(section)
            for keyword in Conf.keywords[section]:
                action = QtGui.QAction(keyword, self)        
                action.triggered.connect(self.createCallable(keyword))
                submenu.addAction(action)
        
    def contextMenuEvent(self, e):
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        self.kwdMenu.setTitle(Lang.value('MI_Add_keyword'))
        menu.addMenu(self.kwdMenu)
        menu.exec_(e.globalPos())
    def createCallable(self, keyword):
        def callable():
            keywords = [x.strip() for x in unicode(self.toPlainText()).split("\n") if x.strip() != '']
            keywords.append(keyword)
            self.setText("\n".join(keywords))
        return callable
        
class SolutionView(QtGui.QWidget):
    def __init__(self):
        super(SolutionView, self).__init__()
        grid = QtGui.QGridLayout()
        self.solution = QtGui.QTextEdit()
        self.solutionLabel = QtGui.QLabel(Lang.value('SS_Solution'))
        self.keywords = KeywordsInputWidget()
        self.keywordsLabel = QtGui.QLabel(Lang.value('SS_Keywords'))
        self.comments = QtGui.QTextEdit()
        self.commentsLabel = QtGui.QLabel(Lang.value('SS_Comments'))
        
        grid.addWidget(self.solutionLabel, 0, 0)
        grid.addWidget(self.solution, 1, 0, 3, 1)
        grid.addWidget(self.keywordsLabel, 0, 1)
        grid.addWidget(self.keywords, 1, 1)
        grid.addWidget(self.commentsLabel, 2, 1)
        grid.addWidget(self.comments, 3, 1)
        
        self.setLayout(grid)
        
        Mainframe.sigWrapper.sigModelChanged.connect(self.onModelChanged)
        Mainframe.sigWrapper.sigLangChanged.connect(self.onLangChanged)
        
        self.solution.textChanged.connect(self.onChanged)
        self.keywords.textChanged.connect(self.onChanged)
        self.comments.textChanged.connect(self.onChanged)

        self.skip_model_changed = False
    def onChanged(self):
        if self.skip_model_changed:
            return
        Mainframe.model.cur()['solution'] = unicode(self.solution.toPlainText()).strip()        
        Mainframe.model.cur()['keywords'] = [x.strip() for x in unicode(self.keywords.toPlainText()).split("\n") if x.strip() != '']
        Mainframe.model.cur()['comments'] = [x.strip() for x in unicode(self.comments.toPlainText()).split("\n\n") if x.strip() != '']

        for k in ['solution']:
            if Mainframe.model.cur()[k] == '':
                del Mainframe.model.cur()[k]
        for k in ['keywords', 'comments']:
            if len(Mainframe.model.cur()[k]) == 0:
                del Mainframe.model.cur()[k]
        
        
        self.skip_model_changed = True
        Mainframe.model.markDirty()
        Mainframe.sigWrapper.sigModelChanged.emit()
        self.skip_model_changed = False
        
    def onModelChanged(self):
        if self.skip_model_changed:
            return
        
        self.skip_model_changed = True

        if Mainframe.model.cur().has_key('solution'):
            self.solution.setText(Mainframe.model.cur()['solution'])
        else:
            self.solution.setText("")
        if Mainframe.model.cur().has_key('keywords'):
            self.keywords.setText("\n".join(Mainframe.model.cur()['keywords']))
        else:
            self.keywords.setText("")
        if Mainframe.model.cur().has_key('comments'):
            self.comments.setText("\n\n".join(Mainframe.model.cur()['comments']))
        else:
            self.comments.setText("")
            
        self.skip_model_changed = False
            
    def onLangChanged(self):
        self.solutionLabel.setText(Lang.value('SS_Solution'))
        self.keywordsLabel.setText(Lang.value('SS_Keywords'))
        self.commentsLabel.setText(Lang.value('SS_Comments'))

class PopeyeInputWidget(QtGui.QTextEdit):
    def __init__(self):
        super(PopeyeInputWidget, self).__init__()
    def setActions(self, actions):
        self.actions = actions
    def contextMenuEvent(self, e):
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        for k in ['start', 'stop', 'options', 'twins']:
            menu.addAction(self.actions[k])
        menu.exec_(e.globalPos())
        
class PopeyeView(QtGui.QSplitter):
    stipulations = ['', '#2', '#3', '#4', 'h#2', 'h#3', 'h#', 's#2', 's#', 'hs#', 'Ser-h#']

    def setActions(self, actions):
        self.actions = actions
        self.actions['stop'].setEnabled(False)
        self.actions['start'].setEnabled(True)
        self.input.setActions(actions)

    def __init__(self):
        super(PopeyeView, self).__init__(QtCore.Qt.Horizontal)
        
        self.input = PopeyeInputWidget()
        self.input.setReadOnly(True)
        self.output = PopeyeOutputWidget(self)
        self.output.setReadOnly(True)
        #self.output.setTextColor(QtGui.QColor(255,255,255))
        #self.output.setTextBackgroundColor(QtGui.QColor(255, 0, 0))
        
        self.sstip = QtGui.QCheckBox(Lang.value('PS_SStipulation'))
        self.btnEdit = QtGui.QPushButton(Lang.value('PS_Edit'))
        self.btnEdit.clicked.connect(self.onEdit)
        w = QtGui.QWidget()
        
        grid = QtGui.QGridLayout()
        grid.addWidget(self.input, 0, 0, 1, 2)
        
        self.labelStipulation = QtGui.QLabel(Lang.value('EP_Stipulation') + ':')
        grid.addWidget(self.labelStipulation, 1, 0)
        
        self.inputStipulation = QtGui.QComboBox()
        self.inputStipulation.setEditable(True)
        self.inputStipulation.addItems(PopeyeView.stipulations)
        grid.addWidget(self.inputStipulation, 2, 0)

        self.labelIntended = QtGui.QLabel(Lang.value('EP_Intended_solutions') + ':')
        grid.addWidget(self.labelIntended, 1, 1)
        self.inputIntended = QtGui.QLineEdit()
        grid.addWidget(self.inputIntended, 2, 1)
        

        grid.addWidget(self.btnEdit, 3, 0)
        
        # stretcher
        grid.addWidget(QtGui.QWidget(), 4, 2)
        grid.setRowStretch(4, 1)
        grid.setColumnStretch(2, 1)

        w.setLayout(grid)
        self.addWidget(self.output)
        self.addWidget(w)
        self.setStretchFactor(0, 1)
        
        self.reset()
        
        self.sstip.stateChanged.connect(self.onModelChanged)
        Mainframe.sigWrapper.sigModelChanged.connect(self.onModelChanged)
        Mainframe.sigWrapper.sigLangChanged.connect(self.onLangChanged)
        
        self.inputIntended.textChanged.connect(self.onChanged)
        self.inputStipulation.editTextChanged.connect(self.onChanged)
        
        self.skip_model_changed = False
    
    def onChanged(self):
        if self.skip_model_changed:
                return
        Mainframe.model.cur()['stipulation'] = unicode(self.inputStipulation.currentText()).encode('ascii', 'ignore').strip()
        Mainframe.model.cur()['intended-solutions'] = unicode(self.inputIntended.text()).encode('ascii', 'ignore').strip()
        for k in ['stipulation', 'intended-solutions']:
            if Mainframe.model.cur()[k] == '':
                del Mainframe.model.cur()[k]
        self.skip_model_changed = True
        Mainframe.model.markDirty()
        Mainframe.sigWrapper.sigModelChanged.emit()
        self.skip_model_changed = False
        
    def onOptions(self):
        entry_options = []
        if Mainframe.model.cur().has_key('options'):
            entry_options = Mainframe.model.cur()['options']
        dialog = options.OptionsDialog(model.FairyHelper.options, sorted(model.FairyHelper.conditions),\
            14, 3, entry_options, Lang)
        if(dialog.exec_()):
            Mainframe.model.cur()['options'] = dialog.getOptions()
            self.skip_model_changed = True
            Mainframe.model.markDirty()
            Mainframe.sigWrapper.sigModelChanged.emit()
            self.skip_model_changed = False
    def onTwins(self):
        twins = {}
        if Mainframe.model.cur().has_key('twins'):
            twins = Mainframe.model.cur()['twins']
        dialog = options.TwinsDialog(Mainframe.model.twinsAsText(), Lang)
        if(dialog.exec_()):
            Mainframe.model.cur()['twins'] = dialog.getTwins()
            self.skip_model_changed = True
            Mainframe.model.markDirty()
            Mainframe.sigWrapper.sigModelChanged.emit()
            self.skip_model_changed = False
    def onTchSettings(self):
        pass
    def onEdit(self):
        if self.raw_mode:
            lines = self.raw_output.strip().split("\n")
            if len(lines) < 2:
                return
            Mainframe.model.cur()['solution'] = ("\n".join(lines[1:-2])).strip()
        else:
            Mainframe.model.cur()['solution'] = self.solutionOutput.solution
        
        Mainframe.model.markDirty()
        Mainframe.sigWrapper.sigModelChanged.emit()
        Mainframe.sigWrapper.sigFocusOnSolution.emit()
    def stopPopeye(self):
        self.stop_requested = True
        self.process.kill()
        self.output.insertPlainText(QtCore.QString("\n" + Lang.value('MSG_Terminated')))
        
    def reset(self):
        self.stop_requested = False
        self.output.setText("")
        self.raw_output = ''
        self.raw_mode = True
        self.compact_possible = False
        self.solutionOutput = None
        self.current_index = Mainframe.model.current
        
    def toggleCompact(self):
        self.raw_mode = not self.raw_mode
        self.output.setText([self.solutionOutput.solution, self.raw_output][self.raw_mode])
        
    def startPopeye(self):
        
        self.actions['stop'].setEnabled(True)
        self.actions['start'].setEnabled(False)        

        self.reset()
        self.entry_copy = copy.deepcopy(Mainframe.model.cur())
                
        Mainframe.sigWrapper.sigFocusOnPopeye.emit()
        
        # writing input to temporary file
        handle, self.temp_filename = tempfile.mkstemp()
        os.write(handle, str(self.input.toPlainText()))
        os.close(handle)
        
        self.process = QtCore.QProcess()
        self.process.readyReadStandardOutput.connect(self.onOut)
        self.process.readyReadStandardError.connect(self.onError)
        self.process.finished.connect(self.onFinished)
        #self.process.closeWriteChannel()
        py_exe = Conf.value('popeye-executable')[os.name].split(" ")
        params = py_exe[1:]
        params.append(self.temp_filename)
        #print py_exe[0], params
        self.process.error.connect(self.onFailed)
        self.process.start(py_exe[0], params)
    
    def onFailed(self):
        try:
            os.unlink(self.temp_filename)
        except:
            pass
        self.actions['stop'].setEnabled(False)
        self.actions['start'].setEnabled(True)
        if not self.stop_requested:
            msgBox(Lang.value('MSG_Popeye_failed') % Conf.value('popeye-executable')[os.name])
        
    def onOut(self):
        data = self.process.readAllStandardOutput()
        self.raw_output = self.raw_output + str(data)
        self.output.insertPlainText(QtCore.QString(data))
        if len(self.raw_output) > int(Conf.value('popeye-stop-max-bytes')):
            self.stopPopeye()
        
    def onError(self):
        self.output.setTextColor(QtGui.QColor(255,0,0))
        self.output.insertPlainText(QtCore.QString(self.process.readAllStandardError()))
        self.output.setTextColor(QtGui.QColor(0,0,0))

    def onFinished(self):
        try:
            os.unlink(self.temp_filename)
        except:
            pass
        self.actions['stop'].setEnabled(False)
        self.actions['start'].setEnabled(True)
        try:
            """solution = legacy.popeye.parse_output(self.entry_copy, self.raw_output)
            self.solutionOutput = legacy.chess.SolutionOutput(False)
            b = legacy.chess.Board()
            b.from_algebraic(self.entry_copy['algebraic'])
            self.solutionOutput.create_output(solution, b)
            if Conf.value('auto-compactify'):
                self.toggleCompact()
            self.btnCompact.setEnabled(True)"""
            self.compact_possible = True
        except (legacy.popeye.ParseError, legacy.chess.UnsupportedError) as e:
            self.compact_possible = False

    def onCompact(self):
        try:
            solution = legacy.popeye.parse_output(self.entry_copy, self.raw_output)
            self.solutionOutput = legacy.chess.SolutionOutput(False)
            b = legacy.chess.Board()
            b.from_algebraic(self.entry_copy['algebraic'])
            self.solutionOutput.create_output(solution, b)
            self.toggleCompact()
        except (legacy.popeye.ParseError, legacy.chess.UnsupportedError) as e:
            msgBox(Lang.value('MSG_Not_supported') % str(e))
            self.compact_possible = False

    def onModelChanged(self):
        self.input.setText(legacy.popeye.create_input(Mainframe.model.cur(),\
            self.sstip.isChecked(), copy.deepcopy(Conf.value('popeye-sticky-options')),\
            Mainframe.model.board.toPopeyePiecesClause()))
        if self.skip_model_changed:
            return

        if self.current_index != Mainframe.model.current:
            self.reset()
            
        self.skip_model_changed = True

        if Mainframe.model.cur().has_key('stipulation'):
            stipulation = Mainframe.model.cur()['stipulation']
            if stipulation in PopeyeView.stipulations:
                self.inputStipulation.setCurrentIndex(PopeyeView.stipulations.index(stipulation))
            self.inputStipulation.setEditText(stipulation)
        else:
            self.inputStipulation.setCurrentIndex(0)
            
        if Mainframe.model.cur().has_key('intended-solutions'):
            self.inputIntended.setText(str(Mainframe.model.cur()['intended-solutions']))
        else:
            self.inputIntended.setText("")
        
        self.skip_model_changed = False
    def onLangChanged(self):
        self.labelStipulation.setText(Lang.value('EP_Stipulation') + ':')
        self.labelIntended.setText(Lang.value('EP_Intended_solutions') + ':')
        self.btnEdit.setText(Lang.value('PS_Edit'))

class PopeyeOutputWidget(QtGui.QTextEdit):
    def __init__(self,  parentView):
        self.parentView = parentView
        super(PopeyeOutputWidget, self).__init__()
    def contextMenuEvent(self, e):
        menu = self.createStandardContextMenu()
        if self.parentView.compact_possible:
            menu.addSeparator()
            if self.parentView.solutionOutput is None:
                menu.addAction(Lang.value('PS_Compact'), self.parentView.onCompact)
            else:
                menu.addAction(
                               [Lang.value('PS_Original_output'),
                                Lang.value('PS_Compact')][self.parentView.raw_mode], 
                                self.parentView.toggleCompact)
        menu.exec_(e.globalPos())

def msgBox(msg):    
    box = QtGui.QMessageBox() 
    box.setText(msg)
    box.exec_()

class YamlView(QtGui.QTextEdit):
    def __init__(self):
        super(YamlView, self).__init__()
        self.setReadOnly(True)
        Mainframe.sigWrapper.sigModelChanged.connect(self.onModelChanged)

    def onModelChanged(self):
        self.setText(yaml.dump(Mainframe.model.cur(), encoding=None, allow_unicode=True))
class Conf:
    file = 'conf/main.yaml'
    keywords_file = 'conf/keywords.yaml'
    
    def read():
        f = open(Conf.file, 'r')
        try:
            Conf.values = yaml.load(f)
        finally:
            f.close()

        f = open(Conf.keywords_file, 'r')
        try:
            Conf.keywords = yaml.load(f)
        finally:
            f.close()
    read = staticmethod(read)

    def write():
        f = open(Conf.file, 'w')
        try:
            f.write(unicode(yaml.dump(Conf.values, encoding=None, allow_unicode=True)).encode('utf8'))
        finally:
            f.close()
    write = staticmethod(write)

    
    def value(v):
        return Conf.values[v]
    value = staticmethod(value)

class Lang:
    file = 'conf/lang.yaml'
    
    def read():
        f = open(Lang.file, 'r')
        try:
            Lang.values = yaml.load(f)
        finally:
            f.close()
        Lang.current = Conf.value('default-lang')
    read = staticmethod(read)

    def value(v):
        return Lang.values[v][Lang.current]
    value = staticmethod(value)
    


