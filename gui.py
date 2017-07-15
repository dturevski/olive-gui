# -*- coding: utf-8 -*-

# standard
import os
import tempfile
import copy
import string
import re
import struct
import ctypes
import urllib

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
import fancy
import chest


class SigWrapper(QtCore.QObject):
    sigLangChanged = QtCore.pyqtSignal()
    sigModelChanged = QtCore.pyqtSignal()
    sigFocusOnPieces = QtCore.pyqtSignal()
    sigFocusOnPopeye = QtCore.pyqtSignal()
    sigFocusOnStipulation = QtCore.pyqtSignal()
    sigFocusOnSolution = QtCore.pyqtSignal()
    sigNewVersion = QtCore.pyqtSignal()


class Commonframe(QtGui.QMainWindow):

    def __init__(self):
        super(Commonframe, self).__init__()

    def openCollection(self, fileName):

        try:
            f = open(unicode(fileName), 'r')
            Mainframe.model = model.Model()
            Mainframe.model.delete(0)
            for data in yaml.load_all(f):
                Mainframe.model.add(model.makeSafe(data), False)
            f.close()
            Mainframe.model.is_dirty = False
        except IOError:
            msgBox(Lang.value('MSG_IO_failed'))
            Mainframe.model = model.Model()
        except yaml.YAMLError as e:
            msgBox(Lang.value('MSG_YAML_failed') % e)
            Mainframe.model = model.Model()
        else:
            if len(Mainframe.model.entries) == 0:
                Mainframe.model = model.Model()
            Mainframe.model.filename = unicode(fileName)
        finally:
            Mainframe.sigWrapper.sigModelChanged.emit()


class Mainframe(Commonframe):
    sigWrapper = SigWrapper()
    fontSize = 24
    fonts = {
        'd': QtGui.QFont(
            'GC2004D', fontSize), 'y': QtGui.QFont(
            'GC2004Y', fontSize), 'x': QtGui.QFont(
                'GC2004X', fontSize)}
    currentlyDragged = None
    transform_names = [
        'Shift_up',
        'Shift_down',
        'Shift_left',
        'Shift_right',
        'Rotate_CW',
        'Rotate_CCW',
        'Mirror_vertical',
        'Mirror_horizontal',
        'Invert_colors',
        'Clear']
    transform_icons = ['up', 'down', 'left',
                       'right', 'rotate-clockwise', 'rotate-anticlockwise',
                       'left-right', 'up-down', 'switch', 'out']
    selectedPiece = None

    class CheckNewVersion(QtCore.QThread):

        def __init__(self, parent):
            QtCore.QThread.__init__(self)
            self.parent = parent

        def run(self):
            try:
                info = yaml.load(
                    urllib.urlopen(
                        Conf.value('latest-binary-version-info-url')))
                if cmp(info['version'], Conf.value('version')) > 0:
                    self.parent.infoNewVersion = info
                    # All GUI must be in the main thread
                    Mainframe.sigWrapper.sigNewVersion.emit()
            except:
                pass

            self.terminate()

    def onNewVersion(self):
        dialog = YesNoDialog(
            Lang.value('MSG_New_version') %
            self.infoNewVersion['version'])
        if dialog.exec_():
            QtGui.QDesktopServices.openUrl(
                QtCore.QUrl(self.infoNewVersion['details']))

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

        if Conf.value('check-for-latest-binary'):
            self.checkNewVersion = Mainframe.CheckNewVersion(self)
            self.checkNewVersion.start()

    def initLayout(self):
        # widgets
        hbox = QtGui.QHBoxLayout()

        # left pane
        widgetLeftPane = QtGui.QWidget()
        vboxLeftPane = QtGui.QVBoxLayout()
        vboxLeftPane.setSpacing(0)
        vboxLeftPane.setContentsMargins(0, 0, 0, 0)
        self.fenView = FenView(self)
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
        self.publishingView = PublishingView()
        self.chestView = chest.ChestView(Conf, Lang, Mainframe)
        self.tabBar2 = QtGui.QTabWidget()
        self.tabBar2.addTab(self.popeyeView, Lang.value('TC_Popeye'))
        self.tabBar2.addTab(self.solutionView, Lang.value('TC_Solution'))
        self.tabBar2.addTab(self.easyEditView, Lang.value('TC_Edit'))
        self.tabBar2.addTab(self.yamlView, Lang.value('TC_YAML'))
        self.tabBar2.addTab(self.publishingView, Lang.value('TC_Publishing'))
        self.tabBar2.addTab(self.chestView, Lang.value('TC_Chest'))
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
        self.newAction = QtGui.QAction(
            QtGui.QIcon('resources/icons/page-white.png'),
            Lang.value('MI_New'),
            self)
        self.newAction.setShortcut('Ctrl+N')
        self.newAction.triggered.connect(self.onNewFile)

        self.openAction = QtGui.QAction(
            QtGui.QIcon('resources/icons/folder.png'),
            Lang.value('MI_Open'),
            self)
        self.openAction.setShortcut('Ctrl+O')
        self.openAction.triggered.connect(self.onOpenFile)

        self.saveAction = QtGui.QAction(
            QtGui.QIcon('resources/icons/disk.png'),
            Lang.value('MI_Save'),
            self)
        self.saveAction.setShortcut('Ctrl+S')
        self.saveAction.triggered.connect(self.onSaveFile)

        self.saveAsAction = QtGui.QAction(
            QtGui.QIcon('resources/icons/page-white-save.png'),
            Lang.value('MI_Save_as'),
            self)
        self.saveAsAction.triggered.connect(self.onSaveFileAs)

        self.saveTemplateAction = QtGui.QAction(
            Lang.value('MI_Save_template'), self)
        self.saveTemplateAction.triggered.connect(self.onSaveTemplate)

        self.importPbmAction = QtGui.QAction(Lang.value('MI_Import_PBM'), self)
        self.importPbmAction.triggered.connect(self.onImportPbm)

        self.importCcvAction = QtGui.QAction(Lang.value('MI_Import_CCV'), self)
        self.importCcvAction.triggered.connect(self.onImportCcv)

        self.exportHtmlAction = QtGui.QAction(
            Lang.value('MI_Export_HTML'), self)
        self.exportHtmlAction.triggered.connect(self.onExportHtml)
        self.exportPdfAction = QtGui.QAction(
            QtGui.QIcon('resources/icons/printer.png'),
            Lang.value('MI_Export_PDF'),
            self)
        self.exportPdfAction.triggered.connect(self.onExportPdf)
        self.exportImgAction = QtGui.QAction(
            Lang.value('MI_Export_Image'), self)
        self.exportImgAction.triggered.connect(self.onExportImg)
        self.exportHtmlAction.setEnabled(False)

        self.addEntryAction = QtGui.QAction(
            QtGui.QIcon('resources/icons/add.png'),
            Lang.value('MI_Add_entry'),
            self)
        self.addEntryAction.triggered.connect(self.onAddEntry)

        self.deleteEntryAction = QtGui.QAction(
            QtGui.QIcon('resources/icons/delete.png'),
            Lang.value('MI_Delete_entry'),
            self)
        self.deleteEntryAction.triggered.connect(self.onDeleteEntry)

        self.exitAction = QtGui.QAction(
            QtGui.QIcon('resources/icons/exit.png'),
            Lang.value('MI_Exit'),
            self)
        self.exitAction.setShortcut('Ctrl+Q')
        self.exitAction.triggered.connect(self.close)

        self.startPopeyeAction = QtGui.QAction(
            QtGui.QIcon('resources/icons/key.png'),
            Lang.value('MI_Run_Popeye'),
            self)
        self.startPopeyeAction = QtGui.QAction(
            QtGui.QIcon('resources/icons/key.png'),
            Lang.value('MI_Run_Popeye'),
            self)
        self.startPopeyeAction.setShortcut('F7')
        self.startPopeyeAction.triggered.connect(self.popeyeView.startPopeye)
        self.stopPopeyeAction = QtGui.QAction(
            QtGui.QIcon('resources/icons/stop.png'),
            Lang.value('MI_Stop_Popeye'),
            self)
        self.stopPopeyeAction.triggered.connect(self.popeyeView.stopPopeye)
        self.listLegalBlackMoves = QtGui.QAction(
            QtGui.QIcon('resources/icons/anyblack.png'),
            Lang.value('MI_Legal_black_moves'),
            self)
        self.listLegalBlackMoves.triggered.connect(
            self.popeyeView.makeListLegal('black'))
        self.listLegalWhiteMoves = QtGui.QAction(
            QtGui.QIcon('resources/icons/anywhite.png'),
            Lang.value('MI_Legal_white_moves'),
            self)
        self.listLegalWhiteMoves.triggered.connect(
            self.popeyeView.makeListLegal('white'))
        self.optionsAction = QtGui.QAction(
            QtGui.QIcon('resources/icons/cog-key.png'),
            Lang.value('MI_Options'),
            self)
        self.optionsAction.triggered.connect(self.popeyeView.onOptions)
        self.twinsAction = QtGui.QAction(
            QtGui.QIcon('resources/icons/gemini.png'),
            Lang.value('MI_Twins'),
            self)
        self.twinsAction.triggered.connect(self.popeyeView.onTwins)

        self.popeyeView.setActions(
            {
                'start': self.startPopeyeAction,
                'stop': self.stopPopeyeAction,
                'legalb': self.listLegalBlackMoves,
                'legalw': self.listLegalWhiteMoves,
                'options': self.optionsAction,
                'twins': self.twinsAction})

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
        map(self.fileMenu.addAction,
            [self.newAction,
             self.openAction,
             self.saveAction,
             self.saveAsAction,
             self.saveTemplateAction])
        self.fileMenu.addSeparator()
        self.langMenu = self.fileMenu.addMenu(Lang.value('MI_Language'))
        map(self.langMenu.addAction, self.langActions)
        self.fileMenu.addSeparator()
        self.importMenu = self.fileMenu.addMenu(Lang.value('MI_Import'))
        self.importMenu.addAction(self.importPbmAction)
        self.importMenu.addAction(self.importCcvAction)
        self.exportMenu = self.fileMenu.addMenu(Lang.value('MI_Export'))
        # self.exportMenu.addAction(self.exportHtmlAction)
        self.exportMenu.addAction(self.exportPdfAction)
        self.exportMenu.addAction(self.exportImgAction)
        self.fileMenu.addSeparator()
        self.fileMenu.addAction(self.exitAction)

        # Entry menu
        self.editMenu = menubar.addMenu(Lang.value('MI_Edit'))
        map(self.editMenu.addAction, [
            self.addEntryAction, self.deleteEntryAction])
        self.editMenu.addSeparator()

        # Popeye menu
        self.popeyeMenu = menubar.addMenu(Lang.value('MI_Popeye'))
        map(self.popeyeMenu.addAction,
            [self.startPopeyeAction,
             self.stopPopeyeAction,
             self.listLegalBlackMoves,
             self.listLegalWhiteMoves,
             self.optionsAction,
             self.twinsAction])

        # help menu
        menubar.addSeparator()
        self.helpMenu = menubar.addMenu(Lang.value('MI_Help'))
        self.aboutAction = QtGui.QAction(
            QtGui.QIcon('resources/icons/information.png'),
            Lang.value('MI_About'),
            self)
        self.aboutAction.triggered.connect(self.onAbout)
        self.helpMenu.addAction(self.aboutAction)

    def initToolbar(self):
        self.toolbar = self.addToolBar('')
        self.toolbar.setObjectName('thetoolbar')
        map(self.toolbar.addAction, [
            self.newAction, self.openAction, self.saveAction])
        self.toolbar.addSeparator()
        map(self.toolbar.addAction, [
            self.addEntryAction, self.deleteEntryAction])
        self.toolbar.addSeparator()
        map(self.toolbar.addAction,
            [self.startPopeyeAction,
             self.stopPopeyeAction,
             self.listLegalBlackMoves,
             self.listLegalWhiteMoves,
             self.optionsAction,
             self.twinsAction])
        self.toolbar.addSeparator()
        self.quickOptionsView = QuickOptionsView(self)
        self.quickOptionsView.embedTo(self.toolbar)
        self.toolbar.addSeparator()
        self.createTransformActions()

    def initSignals(self):
        Mainframe.sigWrapper.sigLangChanged.connect(self.onLangChanged)
        Mainframe.sigWrapper.sigModelChanged.connect(self.onModelChanged)
        Mainframe.sigWrapper.sigFocusOnPieces.connect(self.onFocusOnPieces)
        Mainframe.sigWrapper.sigFocusOnStipulation.connect(
            self.onFocusOnStipulation)
        Mainframe.sigWrapper.sigFocusOnPopeye.connect(self.onFocusOnPopeye)
        Mainframe.sigWrapper.sigFocusOnSolution.connect(self.onFocusOnSolution)
        Mainframe.sigWrapper.sigNewVersion.connect(self.onNewVersion)

    def initFrame(self):
        # window banner
        self.setWindowIcon(
            QtGui.QIcon(
                QtGui.QPixmap('resources/icons/olive.png')))



        # restoring windows and toolbars geometry
        settings = QtCore.QSettings()
        if len(settings.value("overviewColumnWidths").toString()) > 0:
            self.restoreGeometry(settings.value("geometry").toByteArray())
            self.restoreState(settings.value("windowState").toByteArray())
            self.overview.setColumnWidthsFromString(
                settings.value("overviewColumnWidths").toString())
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
            self.langActions[
                sorted(
                    Conf.value('languages').keys()).index(
                    Lang.current)].setChecked(False)
            self.langActions[sorted(Conf.value('languages').keys()).index(
                newlang)].setChecked(True)
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
        self.tabBar2.setTabText(4, Lang.value('TC_Publishing'))
        self.tabBar2.setTabText(5, Lang.value('TC_Chest'))

        # actions
        self.exitAction.setText(Lang.value('MI_Exit'))
        self.newAction.setText(Lang.value('MI_New'))
        self.openAction.setText(Lang.value('MI_Open'))
        self.saveAction.setText(Lang.value('MI_Save'))
        self.saveAsAction.setText(Lang.value('MI_Save_as'))
        self.saveTemplateAction.setText(Lang.value('MI_Save_template'))
        self.addEntryAction.setText(Lang.value('MI_Add_entry'))
        self.deleteEntryAction.setText(Lang.value('MI_Delete_entry'))
        self.startPopeyeAction.setText(Lang.value('MI_Run_Popeye'))
        self.stopPopeyeAction.setText(Lang.value('MI_Stop_Popeye'))
        self.listLegalWhiteMoves.setText(Lang.value('MI_Legal_white_moves'))
        self.listLegalBlackMoves.setText(Lang.value('MI_Legal_black_moves'))
        self.optionsAction.setText(Lang.value('MI_Options'))
        self.twinsAction.setText(Lang.value('MI_Twins'))
        self.aboutAction.setText(Lang.value('MI_About'))
        self.importPbmAction.setText(Lang.value('MI_Import_PBM'))
        self.importCcvAction.setText(Lang.value('MI_Import_CCV'))
        self.exportHtmlAction.setText(Lang.value('MI_Export_HTML'))
        self.exportPdfAction.setText(Lang.value('MI_Export_PDF'))
        self.exportImgAction.setText(Lang.value('MI_Export_Image'))

        for i, k in enumerate(Mainframe.transform_names):
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
        fileName = QtGui.QFileDialog.getOpenFileName(
            self, Lang.value('MI_Open'), default_dir, "(*.olv)")
        if not fileName:
            return
        self.openCollection(fileName)

    def openCollection(self, fileName):
        super(Mainframe, self).openCollection(fileName)
        self.overview.rebuild()

    def onSaveFile(self):
        if Mainframe.model.filename != '':
            f = open(Mainframe.model.filename, 'w')
            try:
                for i in xrange(len(Mainframe.model.entries)):
                    f.write("---\n")
                    f.write(
                        unicode(
                            yaml.dump(
                                Mainframe.model.entries[i],
                                encoding=None,
                                allow_unicode=True)).encode('utf8'))
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
        fileName = QtGui.QFileDialog.getSaveFileName(
            self, Lang.value('MI_Save_as'), default_dir, "(*.olv)")
        if not fileName:
            return
        Mainframe.model.filename = unicode(fileName)
        self.onSaveFile()

    def onSaveTemplate(self):
        Mainframe.model.defaultEntry = copy.deepcopy(Mainframe.model.cur())
        try:
            Mainframe.model.saveDefaultEntry()
        except IOError:
            msgBox(Lang.value('MSG_IO_failed'))

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
            return False  # ie cancel the caller
        else:
            return False
        return False

    def getOpenFileNameAndEncoding(self, title, dir, filter):
        dialog = QtGui.QFileDialog()
        dialog.setOption(QtGui.QFileDialog.DontUseNativeDialog, True)
        dialog.setFilter(filter)
        dialog.setWindowTitle(title)

        encodings = Conf.value('import-post-decode')
        keys = sorted(encodings.keys())
        combo = QtGui.QComboBox()
        combo.addItems(["%s (%s)" % (k, encodings[k]) for k in keys])
        combo.setCurrentIndex(
            keys.index(
                Conf.value('import-post-decode-default')))

        grid = dialog.layout()
        grid.addWidget(QtGui.QLabel(Lang.value('MISC_Encoding')), 4, 0)
        grid.addWidget(combo, 4, 1)

        fileName = False
        if dialog.exec_() and len(dialog.selectedFiles()):
            fileName = dialog.selectedFiles()[0]
        return fileName, keys[combo.currentIndex()]

    def onImportPbm(self):
        if not self.doDirtyCheck():
            return
        default_dir = './collections/'
        if Mainframe.model.filename != '':
            default_dir, tail = os.path.split(Mainframe.model.filename)
        #fileName = QtGui.QFileDialog.getOpenFileName(self, Lang.value('MI_Import_PBM'), default_dir, "(*.pbm)")
        fileName, encoding = self.getOpenFileNameAndEncoding(
            Lang.value('MI_Import_PBM'), default_dir, "(*.pbm)")
        if not fileName:
            return
        try:
            Mainframe.model = model.Model()
            Mainframe.model.delete(0)
            file = open(unicode(fileName))
            pbm.PBM_ENCODING = encoding
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

    def onImportCcv(self):
        if not self.doDirtyCheck():
            return
        default_dir = './collections/'
        if Mainframe.model.filename != '':
            default_dir, tail = os.path.split(Mainframe.model.filename)
        fileName, encoding = self.getOpenFileNameAndEncoding(
            Lang.value('MI_Import_CCV'), default_dir, "(*.ccv)")
        if not fileName:
            return
        try:
            Mainframe.model = model.Model()
            Mainframe.model.delete(0)
            for data in fancy.readCvv(fileName, encoding):
                Mainframe.model.add(model.makeSafe(data), False)
            Mainframe.model.is_dirty = False
        except IOError:
            msgBox(Lang.value('MSG_IO_failed'))
        except:
            msgBox(Lang.value('MSG_CCV_import_failed'))
        finally:
            if len(Mainframe.model.entries) == 0:
                Mainframe.model = model.Model()
            self.overview.rebuild()
            Mainframe.sigWrapper.sigModelChanged.emit()

    def onExportHtml(self):
        pass

    def onExportPdf(self):
        default_dir = './collections/'
        fileName = QtGui.QFileDialog.getSaveFileName(
            self,
            Lang.value('MI_Export') +
            ' ' +
            Lang.value('MI_Export_PDF'),
            default_dir,
            "(*.pdf)")
        if not fileName:
            return
        try:
            ed = pdf.ExportDocument(Mainframe.model.entries, Lang)
            ed.doExport(unicode(fileName))
        except IOError:
            msgBox(Lang.value('MSG_IO_failed'))
        except:
            msgBox(Lang.value('MSG_PDF_export_failed'))

    def onExportImg(self):
        fileName = QtGui.QFileDialog.getSaveFileName(self, Lang.value(
            'MI_Export') + ' / ' + Lang.value('MI_Export_Image'), '', "(*.png)")
        if not fileName:
            return
        try:
            xfen2img.convert(Mainframe.model.board.toFen(), unicode(fileName))
        except IOError:
            msgBox(Lang.value('MSG_IO_failed'))
        except:
            msgBox(Lang.value('MSG_Image_export_failed'))

    def onAddEntry(self):
        idx = Mainframe.model.current + 1
        Mainframe.model.insert(
            copy.deepcopy(
                Mainframe.model.defaultEntry),
            True,
            idx)
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
            Mainframe.model.insert(
                copy.deepcopy(
                    Mainframe.model.defaultEntry), True, 0)
            self.overview.insertItem(idx)
        else:
            self.overview.setCurrentItem(
                self.overview.topLevelItem(
                    Mainframe.model.current))
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
            self.transforms.append(
                QtGui.QAction(
                    QtGui.QIcon(
                        'resources/icons/arrow-' +
                        Mainframe.transform_icons[i] +
                        '.png'),
                    Lang.value(
                        'MI_' +
                        k),
                    self))
            self.transforms[-1].triggered.connect(
                self.createTransformsCallable(k))
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
            elif command == 'Invert_colors':
                Mainframe.model.board.invertColors()
            else:
                pass
            Mainframe.model.onBoardChanged()
            Mainframe.sigWrapper.sigModelChanged.emit()
        return callable

    def closeEvent(self, event):
        if not self.doDirtyCheck():
            event.ignore()
            return
        settings = QtCore.QSettings()
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        settings.setValue(
            "overviewColumnWidths",
            self.overview.getColumnWidths())

        self.chessBox.sync()
        Conf.write()
        event.accept()


class ClickableLabel(QtGui.QLabel):

    def __init__(self, str):
        super(ClickableLabel, self).__init__(str)
        self.setOpenExternalLinks(True)


class QuickOptionsView():  # for clarity this View is not a widget

    def __init__(self, mainframeInstance):
        self.quickies = [
            {'option': 'SetPlay', 'icon': 'setplay.png', 'lang': 'QO_SetPlay'},
            {'option': 'Defence 1', 'icon': 'tries.png', 'lang': 'QO_Tries'},
            {'option': 'PostKeyPlay', 'icon': 'postkeyplay.png', 'lang': 'QO_PostKeyPlay'},
            {'option': 'Intelligent', 'icon': 'intelligent.png', 'lang': 'QO_IntelligentMode'}
        ]
        self.actions = []
        for q in self.quickies:
            action = QtGui.QAction(
                QtGui.QIcon(
                    'resources/icons/' +
                    q['icon']),
                Lang.value(
                    q['lang']),
                mainframeInstance)
            action.setCheckable(True)
            action.triggered.connect(self.makeToggleOption(q['option']))
            self.actions.append(action)

        Mainframe.sigWrapper.sigModelChanged.connect(self.onModelChanged)
        Mainframe.sigWrapper.sigLangChanged.connect(self.onLangChanged)

        self.skip_model_changed = False

    def makeToggleOption(self, option):
        def toggleOption():
            Mainframe.model.toggleOption(option)
            self.skip_model_changed = True
            Mainframe.sigWrapper.sigModelChanged.emit()
            self.skip_model_changed = False
        return toggleOption

    def embedTo(self, toolbar):
        for action in self.actions:
            toolbar.addAction(action)

    def onModelChanged(self):
        if self.skip_model_changed:
            return
        for i in xrange(len(self.quickies)):
            self.actions[i].setChecked('options' in Mainframe.model.cur() and self.quickies[
                                       i]['option'] in Mainframe.model.cur()['options'])

    def onLangChanged(self):
        for i in xrange(len(self.quickies)):
            self.actions[i].setText(Lang.value(self.quickies[i]['lang']))


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
        vbox.addWidget(
            ClickableLabel(
                'olive v' +
                Conf.value('version') +
                ' is free software licensed under GNU GPL'))
        vbox.addWidget(ClickableLabel(u'© 2011-2016'))
        vbox.addWidget(ClickableLabel(u'Project contributors:'))
        vbox.addWidget(ClickableLabel(u'<b>Mihail Croitor (MDA), Борислав Гађански (SRB)</b>'))
        vbox.addWidget(ClickableLabel(u'<b>Torsten Linß (GER), Thomas Maeder (CHE)</b>'))
        vbox.addWidget(ClickableLabel(u'<b>Phil Sphicas (USA), Дмитрий Туревский (RUS)</b>'))
        vbox.addWidget(ClickableLabel(
            'For more information please visit <a href="http://www.yacpdb.org/#static/olive">http://www.yacpdb.org/#static/olive</a>'))

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

    def __init__(self, mainframe):
        super(FenView, self).__init__()
        self.parent = mainframe
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
        self.parent.chessBox.updateXFenOverrides()
        Mainframe.model.board.fromFen(text)
        self.skip_model_changed = True
        Mainframe.model.onBoardChanged()
        Mainframe.sigWrapper.sigModelChanged.emit()
        self.skip_model_changed = False


class OverviewList(QtGui.QTreeWidget):

    def __init__(self):
        super(OverviewList, self).__init__()
        self.setAlternatingRowColors(True)

        self.clipboard = QtGui.QApplication.clipboard()

        Mainframe.sigWrapper.sigLangChanged.connect(self.onLangChanged)
        Mainframe.sigWrapper.sigModelChanged.connect(self.onModelChanged)
        self.currentItemChanged.connect(self.onCurrentItemChanged)

        # self.setSelectionMode(QtGui.QAbstractItemView.MultiSelection)
        self.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)

        self.skip_model_changed = False
        self.skip_current_item_changed = False

    def mousePressEvent(self, e):
        if e.buttons() != QtCore.Qt.RightButton:
            return QtGui.QTreeWidget.mousePressEvent(self, e)

        hasSelection = len(self.selectionModel().selectedRows()) > 0

        menu = QtGui.QMenu('')

        copyAction = QtGui.QAction(Lang.value('MI_Copy'), self)
        copyAction.triggered.connect(self.onCopy)
        copyAction.setEnabled(hasSelection)
        menu.addAction(copyAction)

        cutAction = QtGui.QAction(Lang.value('MI_Cut'), self)
        cutAction.triggered.connect(self.onCut)
        cutAction.setEnabled(hasSelection)
        menu.addAction(cutAction)

        pasteAction = QtGui.QAction(Lang.value('MI_Paste'), self)
        pasteAction.triggered.connect(self.onPaste)
        pasteAction.setEnabled(len(self.clipboard.text()) > 0)
        menu.addAction(pasteAction)

        saveSelection = QtGui.QAction(Lang.value('MI_Save_selection_as'), self)
        saveSelection.triggered.connect(self.onSaveSelectionAs)
        saveSelection.setEnabled(hasSelection)
        menu.addAction(saveSelection)

        menu.exec_(e.globalPos())

    def keyPressEvent(self,event):
        if event.key()==(QtCore.Qt.Key_Control and QtCore.Qt.Key_C):
            self.onCopy()
        if event.key()==(QtCore.Qt.Key_Control and QtCore.Qt.Key_V):
            self.onPaste()
        if event.key()==(QtCore.Qt.Key_Control and QtCore.Qt.Key_X):
            self.onCut()

    def getSelectionAsYaml(self):
        text = u''
        for idx in sorted([x.row()
                           for x in self.selectionModel().selectedRows()]):
            text = text + "---\n"
            text = text + yaml.dump(
                Mainframe.model.entries[idx], encoding=None, allow_unicode=True
            )
        return text

    def onCopy(self):
        self.clipboard.setText(self.getSelectionAsYaml())

    def onCut(self):
        self.onCopy()
        selection = sorted([x.row()
                            for x in self.selectionModel().selectedRows()])
        selection.reverse()
        for idx in selection:
            Mainframe.model.delete(idx)
        if len(Mainframe.model.entries) == 0:
            Mainframe.model = model.Model()
        self.rebuild()
        Mainframe.sigWrapper.sigModelChanged.emit()

    def onPaste(self):
        try:
            data = yaml.load_all(unicode(self.clipboard.text()))
            if isinstance(data, dict):
                data = [data]
        except yaml.YAMLError as e:
            msgBox(Lang.value('MSG_YAML_failed') % e)
            return
        for entry in data:
            entry = model.makeSafe(entry)
            Mainframe.model.insert(entry, True, Mainframe.model.current + 1)
        self.rebuild()
        Mainframe.sigWrapper.sigModelChanged.emit()

    def onSaveSelectionAs(self):
        default_dir = './collections/'
        if Mainframe.model.filename != '':
            default_dir, tail = os.path.split(Mainframe.model.filename)
        fileName = QtGui.QFileDialog.getSaveFileName(
            self, Lang.value('MI_Save_selection_as'), default_dir, "(*.olv)")
        if not fileName:
            return

        f = open(unicode(fileName), 'w')
        try:
            f.write(self.getSelectionAsYaml().encode('utf8'))
        except IOError:
            msgBox(Lang.value('MSG_IO_failed'))
        finally:
            f.close()

    def init(self):
        self.setColumnCount(6)
        self.onLangChanged()

    def getColumnWidths(self):
        return ";".join([str(self.columnWidth(i)) for i in xrange(self.columnCount())])

    def setColumnWidthsFromString(self, widths):
        try:
            intList = [int(s) for s in widths.split(";")]
            for i, w in enumerate(intList):
                self.setColumnWidth(i, w)
        except :
            pass

    def onLangChanged(self):
        self.setHeaderLabels(['',
                              Lang.value('EP_Authors'),
                              Lang.value('EP_Source'),
                              Lang.value('EP_Date'),
                              Lang.value('EP_Distinction'),
                              Lang.value('EP_Stipulation'),
                              Lang.value('EP_Pieces_count')])
        for i in xrange(len(Mainframe.model.entries)):
            if 'distinction' in Mainframe.model.entries[i]:
                d = model.Distinction.fromString(
                    Mainframe.model.entries[i]['distinction'])
                # 4 is the index of the distinction column
                self.topLevelItem(i).setText(4, d.toStringInLang(Lang))

    def removeDirtyMarks(self):
        for i in xrange(len(Mainframe.model.entries)):
            self.topLevelItem(i).setText(0, str(i + 1))

    def rebuild(self):
        self.clear()
        for i in xrange(len(Mainframe.model.entries)):
            newItem = QtGui.QTreeWidgetItem()
            for j, text in enumerate(self.createItem(i)):
                newItem.setText(j, text)
            self.addTopLevelItem(newItem)
        self.skip_model_changed = True
        self.setCurrentItem(self.topLevelItem(Mainframe.model.current))

    def insertItem(self, idx):
        newItem = QtGui.QTreeWidgetItem()
        for j, text in enumerate(self.createItem(idx)):
            newItem.setText(j, text)
        self.insertTopLevelItem(idx, newItem)

        for j in xrange(idx + 1, len(Mainframe.model.entries)):
            self.topLevelItem(j).setText(
                0, str(j + 1) + ['', '*'][Mainframe.model.dirty_flags[j]])
        self.skip_model_changed = True
        self.setCurrentItem(self.topLevelItem(Mainframe.model.current))

    def deleteItem(self, idx):
        self.takeTopLevelItem(idx)
        for j in xrange(idx, len(Mainframe.model.entries)):
            self.topLevelItem(j).setText(
                0, str(j + 1) + ['', '*'][Mainframe.model.dirty_flags[j]])
        # which item is current now depends and handled by the caller
        # (Mainframe)

    def createItem(self, idx):
        item = []
        item.append(str(idx + 1) + ['', '*'][Mainframe.model.dirty_flags[idx]])

        authorsTxt = ''
        if 'authors' in Mainframe.model.entries[idx]:
            authorsTxt = '; '.join(Mainframe.model.entries[idx]['authors'])
        item.append(authorsTxt)

        for key in ['source', 'date', 'distinction', 'stipulation']:
            if key in Mainframe.model.entries[idx]:
                if key == 'distinction':
                    d = model.Distinction.fromString(
                        Mainframe.model.entries[idx][key])
                    item.append(d.toStringInLang(Lang))
                else:
                    item.append(unicode(Mainframe.model.entries[idx][key]))
            else:
                item.append('')

        item.append(Mainframe.model.pieces_counts[idx])

        return item

    def onModelChanged(self):
        if self.skip_model_changed:
            self.skip_model_changed = False
            return

        for i, text in enumerate(self.createItem(Mainframe.model.current)):
            self.topLevelItem(Mainframe.model.current).setText(i, text)

    def onCurrentItemChanged(self, current, prev):
        if current is None:  # happens when deleting
            return
        if self.skip_current_item_changed:
            return

        # stupid hack:
        text = current.text(0)
        if(text[-1] == '*'):
            text = text[:-1]
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

    # mouseMoveEvent works as well but with slightly different mechanics
    def mousePressEvent(self, e):
        Mainframe.sigWrapper.sigFocusOnPieces.emit()
        if e.buttons() != QtCore.Qt.LeftButton:
            # On right click
            # if the square is empty, add the selected piece
            # if the square is non-empty, remove it
            if Mainframe.model.board.board[self.id] is None:
                if Mainframe.selectedPiece is not None:
                    Mainframe.model.board.add(model.Piece(Mainframe.selectedPiece.name,
                                                          Mainframe.selectedPiece.color,
                                                          Mainframe.selectedPiece.specs),
                                              self.id)
                else:
                    return
            else:
                Mainframe.selectedPiece = Mainframe.model.board.board[self.id]
                Mainframe.model.board.drop(self.id)
            Mainframe.model.onBoardChanged()
            Mainframe.sigWrapper.sigModelChanged.emit()
            return
        if Mainframe.model.board.board[self.id] is None:
            return

        # ctrl-drag copies existing piece
        modifiers = QtGui.QApplication.keyboardModifiers()
        Mainframe.currentlyDragged = Mainframe.model.board.board[self.id]
        if not (modifiers & QtCore.Qt.ControlModifier):
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
        Mainframe.model.board.add(
            model.Piece(
                Mainframe.currentlyDragged.name,
                Mainframe.currentlyDragged.color,
                Mainframe.currentlyDragged.specs),
            self.id)
        Mainframe.model.onBoardChanged()
        Mainframe.sigWrapper.sigModelChanged.emit()


class ChessBoxItem(QtGui.QLabel):

    def __init__(self, piece):
        super(ChessBoxItem, self).__init__()
        self.changePiece(piece)

    def getShortGlyph(piece):
        glyph = piece.toFen()
        if len(glyph) > 1:
            glyph = glyph[1:-1]
        return glyph
    getShortGlyph = staticmethod(getShortGlyph)

    def changePiece(self, piece):
        if piece is None:
            self.setFont(Mainframe.fonts['d'])
            self.setText("\xA3")
            self.setToolTip('')
        else:
            glyph = ChessBoxItem.getShortGlyph(piece)
            self.setFont(
                Mainframe.fonts[
                    model.FairyHelper.fontinfo[glyph]['family']])
            self.setText(model.FairyHelper.fontinfo[glyph]['chars'][0])
            self.setToolTip(str(piece))

        self.piece = piece

    # mouseMoveEvent works as well but with slightly different mechanics
    def mousePressEvent(self, e):
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

        populateFromCurrent = QtGui.QAction(
            Lang.value('MI_Populate_from_current'), self)
        populateFromCurrent.triggered.connect(self.manager.populateFromCurrent)
        menu.addAction(populateFromCurrent)
        menu.addSeparator()

        if self.piece is None:
            addNewAction = QtGui.QAction(Lang.value('MI_Add_piece'), self)
            addNewAction.triggered.connect(self.choose)
            menu.addAction(addNewAction)
        else:
            deleteAction = QtGui.QAction(Lang.value('MI_Delete_piece'), self)
            deleteAction.triggered.connect(self.remove)
            menu.addAction(deleteAction)
        deleteAllAction = QtGui.QAction(
            Lang.value('MI_Delete_all_pieces'), self)
        deleteAllAction.triggered.connect(self.manager.deleteAll)
        menu.addAction(deleteAllAction)

        menu.addSeparator()
        for i in xrange(len(Conf.zoos)):
            action = QtGui.QAction(Conf.zoos[i]['name'], self)
            action.triggered.connect(self.manager.makeChangeZooCallable(i))
            menu.addAction(action)

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

        labelBottom = QtGui.QLabel(
            "\x4F\xA7\xA8\xA9\xAA\xAB\xAC\xAD\xAE\xAF\x4F")
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
                lbl = DraggableLabel(j + i * 8)
                lbl.setTextAndFont(["\xA3", "\xA4"][(i + j) % 2], 'd')
                # lbl.setDragEnabled(True)
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

        # hbox.addLayout(vboxEdgeLeft)
        hbox.addWidget(centerWidget)
        hbox.addStretch(1)
        # hbox.addLayout(vboxEdgeRight)

        hboxExtra = QtGui.QHBoxLayout()
        spacer = QtGui.QLabel("\xA3")
        spacer.setFont(Mainframe.fonts['d'])
        self.labelStipulation = QtGui.QLabel("")
        self.labelPiecesCount = QtGui.QLabel("")
        # hboxExtra.addWidget(spacer)
        hboxExtra.addWidget(self.labelStipulation)
        hboxExtra.addStretch(1)
        hboxExtra.addWidget(self.labelPiecesCount)
        # hboxExtra.addWidget(spacer)

        # vbox.addWidget(labelTop)
        vbox.addLayout(hbox)
        # vbox.addWidget(labelBottom)
        vbox.addLayout(hboxExtra)

        self.setLayout(vbox)

    def onModelChanged(self):
        if self.skip_model_changed:
            self.skip_model_changed = False
            return

        for i, lbl in enumerate(self.labels):
            if Mainframe.model.board.board[i] is None:
                lbl.setFont(Mainframe.fonts['d'])
                lbl.setText(["\xA3", "\xA4"][((i >> 3) + (i % 8)) % 2])
            else:
                glyph = Mainframe.model.board.board[i].toFen()
                if len(glyph) > 1:
                    glyph = glyph[1:-1]
                lbl.setFont(
                    Mainframe.fonts[
                        model.FairyHelper.fontinfo[glyph]['family']])
                lbl.setText(model.FairyHelper.fontinfo[glyph][
                            'chars'][((i >> 3) + (i % 8)) % 2])
        if('stipulation' in Mainframe.model.cur()):
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
        return pdf.ExportDocument.header(Mainframe.model.cur(), Lang)

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
                x = i * ChessBox.cols + j
                item = ChessBoxItemManagable(None, i * ChessBox.cols + j, self)
                if '' != Conf.value('fairy-zoo')[i][j]:
                    item.changePiece(
                        model.Piece.fromAlgebraic(
                            Conf.value('fairy-zoo')[i][j]))
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

    def updateXFenOverrides(self):
        model.FairyHelper.overrides = {}
        for item in self.items:
            if not item.piece is None:
                glyph = ChessBoxItem.getShortGlyph(item.piece).lower()
                model.FairyHelper.overrides[glyph] = {
                    'name': item.piece.name, 'specs': item.piece.specs}

    def makeChangeZooCallable(self, zoo_idx):
        def callable():
            self.changeZoo(Conf.zoos[zoo_idx]['pieces'])
        return callable

    def changeZoo(self, zoo):
        for i in xrange(ChessBox.rows):
            for j in xrange(ChessBox.cols):
                piece = None
                if zoo[i][j] != '':
                    piece = model.Piece.fromAlgebraic(zoo[i][j])
                self.items[i * ChessBox.cols + j].changePiece(piece)

    def sync(self):
        zoo = Conf.value('fairy-zoo')
        for i in xrange(ChessBox.rows):
            for j in xrange(ChessBox.cols):
                if not self.items[i * ChessBox.cols + j].piece is None:
                    zoo[i][j] = self.items[
                        i * ChessBox.cols + j].piece.serialize()
                else:
                    zoo[i][j] = ''

    def populateFromCurrent(self):
        self.deleteAll()
        i, unique = 0, {}
        for piece in model.getFairyPieces(Mainframe.model.cur()):
            k = str(piece)
            if (len(self.items) > i) and k not in unique:
                unique[k] = True
                self.items[i].changePiece(piece)
                i += 1


class AddFairyPieceDialog(options.OkCancelDialog):

    def __init__(self, Lang):
        form = QtGui.QFormLayout()
        self.comboColor = QtGui.QComboBox()
        self.comboColor.addItems(model.COLORS)
        form.addRow(Lang.value('PP_Color'), self.comboColor)

        self.piece_types = sorted(model.FairyHelper.glyphs.iterkeys())
        self.comboType = QtGui.QComboBox()
        self.comboType.addItems(
            [x + ' (' + model.FairyHelper.glyphs[x]['name'] + ')' for x in self.piece_types])
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
        specs = [
            x for i, x in enumerate(
                model.FAIRYSPECS) if self.checkboxes[i].isChecked()]
        return model.Piece(type, color, specs)


class EasyEditView(QtGui.QWidget):

    def __init__(self):
        super(EasyEditView, self).__init__()
        grid = QtGui.QGridLayout()
        # authors
        self.labelAuthors = QtGui.QLabel(
            Lang.value('EP_Authors') +
            ':<br/><br/>' +
            Lang.value('EE_Authors_memo'))
        self.inputAuthors = QtGui.QTextEdit()
        grid.addWidget(self.labelAuthors, 0, 0)
        grid.addWidget(self.inputAuthors, 0, 1)

        self.labelSource = QtGui.QLabel(Lang.value('EP_Source') + ':')
        self.memoSource = QtGui.QLabel(Lang.value('EE_Source_memo'))
        self.inputSource = QtGui.QLineEdit()
        self.inputIssueId = QtGui.QLineEdit()
        self.inputIssueId.setFixedWidth(
            self.inputIssueId.minimumSizeHint().width())
        self.inputSourceId = QtGui.QLineEdit()
        self.inputSourceId.setFixedWidth(
            self.inputSourceId.minimumSizeHint().width())
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
        self.inputDateYear.setFixedWidth(
            self.inputDateYear.minimumSizeHint().width())
        self.inputDateMonth = QtGui.QComboBox()
        self.inputDateMonth.addItems([''])
        self.inputDateMonth.addItems([str(x) for x in xrange(1, 13)])
        self.inputDateDay = QtGui.QComboBox()
        self.inputDateDay.addItems([''])
        self.inputDateDay.addItems(["%02d" % x for x in xrange(1, 32)])
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

        self.labelDistinction = QtGui.QLabel(
            Lang.value('EP_Distinction') + ':')
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

        if 'authors' in Mainframe.model.cur():
            self.inputAuthors.setText(
                "\n".join(Mainframe.model.cur()['authors']))
        else:
            self.inputAuthors.setText("")

        if 'source' in Mainframe.model.cur():
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

        Mainframe.model.cur()['authors'] = [x.strip() for x in unicode(
            self.inputAuthors.toPlainText()).split("\n") if x.strip() != '']
        Mainframe.model.cur()['source'] = unicode(
            self.inputSource.text()).strip()
        i_id, s_id = unicode(
            self.inputIssueId.text()).strip(), unicode(
            self.inputSourceId.text()).strip()
        is_id = '/'.join([i_id, s_id])
        if is_id.startswith('/'):
            is_id = is_id[1:]
        Mainframe.model.cur()['source-id'] = is_id

        date = model.myint(
            unicode(
                self.inputDateYear.text()).encode(
                'ascii',
                'replace'))
        if date != 0:
            date = str(date)
            if self.inputDateMonth.currentIndex() != 0:
                date = date + '-' + ("%02d" %
                                     self.inputDateMonth.currentIndex())
                if self.inputDateDay.currentIndex() != 0:
                    date = date + '-' + ("%02d" %
                                         self.inputDateDay.currentIndex())
            Mainframe.model.cur()['date'] = date
        elif 'date' in Mainframe.model.cur():
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
        self.labelAuthors.setText(
            Lang.value('EP_Authors') +
            ':<br/><br/>' +
            Lang.value('EE_Authors_memo'))
        self.labelAuthors.setToolTip(Lang.value('EE_Authors_memo'))
        self.labelSource.setText(Lang.value('EP_Source') + ':')
        self.memoSource.setText(Lang.value('EE_Source_memo'))
        self.labelDate.setText(Lang.value('EP_Date') + ':')
        self.memoDate.setText(Lang.value('EE_Date_memo'))
        self.labelDistinction.setText(Lang.value('EP_Distinction') + ':')


class DistinctionWidget(QtGui.QWidget):
    names = ['', 'Place', 'Prize', 'HM', 'Comm.']
    lang_entries = ['', 'DSTN_Place', 'DSTN_Prize', 'DSTN_HM', 'DSTN_Comm']

    def __init__(self):
        super(DistinctionWidget, self).__init__()
        hbox = QtGui.QHBoxLayout()
        self.special = QtGui.QCheckBox(Lang.value('DSTN_Special'))
        hbox.addWidget(self.special)
        self.lo = QtGui.QSpinBox()
        hbox.addWidget(self.lo)
        self.hi = QtGui.QSpinBox()
        hbox.addWidget(self.hi)
        self.name = QtGui.QComboBox()
        self.name.addItems(
            ['X' * 15 for i in DistinctionWidget.names])  # spacers
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
        Mainframe.sigWrapper.sigLangChanged.connect(self.onLangChanged)
        self.skip_model_changed = False
        self.onLangChanged()

    def onChanged(self):
        if self.skip_model_changed:
            return
        distinction = self.get()
        if 'distinction' in Mainframe.model.cur():
            if distinction == Mainframe.model.cur()['distinction']:
                return
        else:
            if distinction == '':
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
        self.name.setCurrentIndex(
            DistinctionWidget.names.index(
                distinction.name))
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
        if 'distinction' in Mainframe.model.cur():
            distinction = model.Distinction.fromString(
                Mainframe.model.cur()['distinction'])
        self.skip_model_changed = True
        self.set(distinction)
        self.skip_model_changed = False

    def onLangChanged(self):
        self.special.setText(Lang.value('DSTN_Special'))
        for i, le in enumerate(DistinctionWidget.lang_entries):
            if le != '':
                self.name.setItemText(i, Lang.value(le))
            else:
                self.name.setItemText(i, '')


class KeywordsInputWidget(QtGui.QTextEdit):

    def __init__(self):
        super(KeywordsInputWidget, self).__init__()
        self.kwdMenu = QtGui.QMenu(Lang.value('MI_Add_keyword'))
        # for section in sorted(Conf.keywords.keys()):
        for section in Conf.keywords.keys():
            submenu = self.kwdMenu.addMenu(section)
            for keyword in sorted(Conf.keywords[section]):
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
            keywords = [
                x.strip() for x in unicode(
                    self.toPlainText()).split("\n") if x.strip() != '']
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
        Mainframe.model.cur()['solution'] = unicode(
            self.solution.toPlainText()).strip()
        Mainframe.model.cur()['keywords'] = [x.strip() for x in unicode(
            self.keywords.toPlainText()).split("\n") if x.strip() != '']
        Mainframe.model.cur()['comments'] = [x.strip() for x in unicode(
            self.comments.toPlainText()).split("\n\n") if x.strip() != '']

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

        if 'solution' in Mainframe.model.cur():
            self.solution.setText(Mainframe.model.cur()['solution'])
        else:
            self.solution.setText("")
        if 'keywords' in Mainframe.model.cur():
            self.keywords.setText("\n".join(Mainframe.model.cur()['keywords']))
        else:
            self.keywords.setText("")
        if 'comments' in Mainframe.model.cur():
            self.comments.setText(
                "\n\n".join(
                    Mainframe.model.cur()['comments']))
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
        for k in ['start', 'stop', 'legalb', 'legalw', 'options', 'twins']:
            menu.addAction(self.actions[k])
        menu.exec_(e.globalPos())


class PopeyeView(QtGui.QSplitter):
    stipulations = [
        '',
        '#2',
        '#3',
        '#4',
        'h#2',
        'h#3',
        'h#',
        's#2',
        's#',
        'hs#',
        'Ser-h#']

    def makeListLegal(self, color):
        def callable():
            entry = copy.deepcopy(Mainframe.model.cur())

            entry['stipulation'] = '~1'
            if 'twins' in entry:
                del entry['twins']
            if 'options' not in entry:
                entry['options'] = []
            entry['options'] = [
                x for x in entry['options'] if x not in [
                    'SetPlay', 'WhiteToPlay', 'Duplex', 'HalfDuplex']]
            if 'black' == color:
                entry['options'].append('HalfDuplex')

            input = legacy.popeye.create_input(
                entry,
                False,
                copy.deepcopy(Conf.popeye['sticky-options']),
                Mainframe.model.board.toPopeyePiecesClause())
            self.runPopeyeInGui(input)

        return callable

    def setActions(self, actions):
        self.actions = actions
        self.setActionEnabled(True)
        self.input.setActions(actions)

    def __init__(self):
        super(PopeyeView, self).__init__(QtCore.Qt.Horizontal)

        self.input = PopeyeInputWidget()
        self.output = PopeyeOutputWidget(self)
        self.output.setReadOnly(True)

        self.sstip = QtGui.QCheckBox(Lang.value('PS_SStipulation'))
        self.btnEdit = QtGui.QPushButton(Lang.value('PS_Edit'))
        self.btnEdit.clicked.connect(self.onEdit)
        w = QtGui.QWidget()

        row = 0
        grid = QtGui.QGridLayout()

        self.labelPopeye = QtGui.QLabel(Lang.value('TC_Popeye') + ':')
        grid.addWidget(self.labelPopeye, row, 0)
        row +=1

        self.inputPyPath = options.SelectFileWidget(Lang.value('TC_Popeye'), Conf.popeye['path'], self.onPopeyePathChanged)
        grid.addWidget(self.inputPyPath, row, 0, 1, 2)
        row += 1

        self.labelMemory = QtGui.QLabel(Lang.value('PS_Hashtables') + ':')
        grid.addWidget(self.labelMemory, row, 0)
        self.inputMemory = QtGui.QLineEdit()
        self.inputMemory.setText(str(Conf.popeye['memory']))
        self.inputMemory.setValidator(QtGui.QIntValidator(1, 1000000))
        self.inputMemory.textChanged.connect(self.onMemoryChanged)
        grid.addWidget(self.inputMemory, row, 1)
        row += 1

        grid.addWidget(self.input, row, 0, 1, 2)
        row += 1

        self.labelStipulation = QtGui.QLabel(
            Lang.value('EP_Stipulation') + ':')
        grid.addWidget(self.labelStipulation, row, 0)
        self.labelIntended = QtGui.QLabel(
                Lang.value('EP_Intended_solutions') + ':')
        grid.addWidget(self.labelIntended, row, 1)
        row += 1

        self.inputStipulation = QtGui.QComboBox()
        self.inputStipulation.setEditable(True)
        self.inputStipulation.addItems(PopeyeView.stipulations)
        grid.addWidget(self.inputStipulation, row, 0)
        self.inputIntended = QtGui.QLineEdit()
        grid.addWidget(self.inputIntended, row, 1)
        row += 1

        grid.addWidget(self.btnEdit, row, 0)
        row += 1

        # stretcher
        grid.addWidget(QtGui.QWidget(), row, 2)
        grid.setRowStretch(row, 1)
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
        Mainframe.model.cur()['stipulation'] = unicode(
            self.inputStipulation.currentText()).encode(
            'ascii', 'ignore').strip()
        Mainframe.model.cur()['intended-solutions'] = unicode(
            self.inputIntended.text()).encode(
            'ascii', 'ignore').strip()
        for k in ['stipulation', 'intended-solutions']:
            if Mainframe.model.cur()[k] == '':
                del Mainframe.model.cur()[k]
        self.skip_model_changed = True
        Mainframe.model.markDirty()
        Mainframe.sigWrapper.sigModelChanged.emit()
        self.skip_model_changed = False

    def onMemoryChanged(self):
        try: Conf.popeye['memory'] = int(str(self.inputMemory.text()))
        except: pass

    def onPopeyePathChanged(self, newPath):
        Conf.popeye['path'] = newPath

    def onOptions(self):
        entry_options = []
        if 'options' in Mainframe.model.cur():
            entry_options = Mainframe.model.cur()['options']
        dialog = options.OptionsDialog(model.FairyHelper.options, sorted(
            model.FairyHelper.conditions), 14, 3, entry_options, Lang)
        if(dialog.exec_()):
            Mainframe.model.cur()['options'] = dialog.getOptions()
            self.skip_model_changed = True
            Mainframe.model.markDirty()
            Mainframe.sigWrapper.sigModelChanged.emit()
            self.skip_model_changed = False

    def onTwins(self):
        twins = {}
        if 'twins' in Mainframe.model.cur():
            twins = Mainframe.model.cur()['twins']
        dialog = options.TwinsDialog(Mainframe.model.twinsAsText(), Lang)
        if(dialog.exec_()):
            new_twins = dialog.getTwins()
            if len(new_twins):
                Mainframe.model.cur()['twins'] = new_twins
            elif 'twins' in Mainframe.model.cur():
                del Mainframe.model.cur()['twins']
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
            Mainframe.model.cur()['solution'] = PopeyeView.trimIndented("\n".join(lines[1:-2]))
        else:
            Mainframe.model.cur()['solution'] = self.solutionOutput.solution

        Mainframe.model.markDirty()
        Mainframe.sigWrapper.sigModelChanged.emit()
        Mainframe.sigWrapper.sigFocusOnSolution.emit()

    def stopPopeye(self):
        self.stop_requested = True
        self.process.kill()
        self.output.insertPlainText(QtCore.QString(
            "\n" + Lang.value('MSG_Terminated')))

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
        self.output.setText([self.solutionOutput.solution,
                             self.raw_output][self.raw_mode])

    def runPopeyeInGui(self, input):
        self.setActionEnabled(False)

        self.reset()
        self.entry_copy = copy.deepcopy(Mainframe.model.cur())

        Mainframe.sigWrapper.sigFocusOnPopeye.emit()

        # writing input to temporary file
        handle, self.temp_filename = tempfile.mkstemp()
        os.write(handle, input)
        os.close(handle)

        self.process = QtCore.QProcess()
        self.process.readyReadStandardOutput.connect(self.onOut)
        self.process.readyReadStandardError.connect(self.onError)
        self.process.finished.connect(self.onFinished)
        # self.process.closeWriteChannel()
        py_exe = Conf.popeye['path']
        params = ['-maxmem', str(Conf.popeye['memory']) + 'M']
        params.append(self.temp_filename)
        #print py_exe, params
        self.process.error.connect(self.onFailed)
        self.process.start(py_exe, params)

    def startPopeye(self):
        self.runPopeyeInGui(str(self.input.toPlainText()))

    def onFailed(self):
        try:
            os.unlink(self.temp_filename)
        except:
            pass
        self.setActionEnabled(True)
        if not self.stop_requested:
            msgBox(Lang.value('MSG_Popeye_failed') % Conf.popeye['path'])

    def onOut(self):
        data = self.process.readAllStandardOutput()
        self.raw_output = self.raw_output + str(data)
        self.output.insertPlainText(QtCore.QString(data))
        if len(self.raw_output) > int(Conf.popeye['stop-max-bytes']):
            self.stopPopeye()

    def onError(self):
        self.output.setTextColor(QtGui.QColor(255, 0, 0))
        self.output.insertPlainText(QtCore.QString(
            self.process.readAllStandardError()))
        self.output.setTextColor(QtGui.QColor(0, 0, 0))

    def onFinished(self):
        try:
            os.unlink(self.temp_filename)
        except:
            pass
        self.setActionEnabled(True)

        if Conf.value('auto-compactify'):
            self.onCompact()

        try:
            self.compact_possible = True
        except (legacy.popeye.ParseError, legacy.chess.UnsupportedError) as e:
            self.compact_possible = False

    def setActionEnabled(self, status):
        self.actions['stop'].setEnabled(not status)
        self.actions['start'].setEnabled(status)
        self.actions['legalb'].setEnabled(status)
        self.actions['legalw'].setEnabled(status)

    def setLegacyNotation(self, notation):
        legacy_notation = {}
        notations = Conf.value('notations')
        for a, b in zip(notations['en'], notations[notation]):
            legacy_notation[a] = b
        legacy.chess.NOTATION = legacy_notation

    def onCompact(self):
        try:
            self.setLegacyNotation(Conf.value('default-notation'))
            self.solution = legacy.popeye.parse_output(
                self.entry_copy, self.raw_output)
            self.solutionOutput = legacy.chess.SolutionOutput(False)
            b = legacy.chess.Board()
            b.from_algebraic(self.entry_copy['algebraic'])
            self.solutionOutput.create_output(self.solution, b)
            self.solutionOutput.solution = PopeyeView.trimIndented(self.solutionOutput.solution)
            self.toggleCompact()
        except (legacy.popeye.ParseError, legacy.chess.UnsupportedError) as e:
            msgBox(Lang.value('MSG_Not_supported') % str(e))
            self.compact_possible = False


    def trimIndented(text):

        def countLeadingSpaces(line):
            r = 0
            for c in line:
                if c != " ":
                    return r
                r += 1
            return len(line)

        lines, minIndent = text.splitlines(False), 1024
        for line in lines:
            if line.strip() == "":
                continue
            ls = countLeadingSpaces(line)
            if ls < minIndent:
                minIndent = ls

        return ("\n".join([line[minIndent:] if line.strip() != "" else "" for line in lines])).strip()


    trimIndented = staticmethod(trimIndented)

    def onModelChanged(self):
        self.input.setText(
            legacy.popeye.create_input(
                Mainframe.model.cur(),
                self.sstip.isChecked(),
                copy.deepcopy(Conf.popeye['sticky-options']),
                Mainframe.model.board.toPopeyePiecesClause()))
        if self.skip_model_changed:
            return

        if self.current_index != Mainframe.model.current:
            self.reset()

        self.skip_model_changed = True

        if 'stipulation' in Mainframe.model.cur():
            stipulation = Mainframe.model.cur()['stipulation']
            if stipulation in PopeyeView.stipulations:
                self.inputStipulation.setCurrentIndex(
                    PopeyeView.stipulations.index(stipulation))
            self.inputStipulation.setEditText(stipulation)
        else:
            self.inputStipulation.setCurrentIndex(0)

        if 'intended-solutions' in Mainframe.model.cur():
            self.inputIntended.setText(
                str(Mainframe.model.cur()['intended-solutions']))
        else:
            self.inputIntended.setText("")

        self.skip_model_changed = False

    def onLangChanged(self):
        self.labelPopeye.setText(Lang.value('TC_Popeye') + ':')
        self.labelMemory.setText(Lang.value('PS_Hashtables') + ':')
        self.labelStipulation.setText(Lang.value('EP_Stipulation') + ':')
        self.labelIntended.setText(Lang.value('EP_Intended_solutions') + ':')
        self.btnEdit.setText(Lang.value('PS_Edit'))

    def createChangeNotationCallable(self, notation):
        def callable():
            self.solutionOutput = legacy.chess.SolutionOutput(False)
            self.setLegacyNotation(notation)
            b = legacy.chess.Board()
            b.from_algebraic(self.entry_copy['algebraic'])
            self.solutionOutput.create_output(self.solution, b)
            self.output.setText(self.solutionOutput.solution)
        return callable


class PublishingView(QtGui.QSplitter):

    def loadFontInfo(self, filename):
        fontinfo = {}
        f = open(filename)
        for entry in map(lambda x: x.strip().split("\t"), f.readlines()):
            fontinfo[entry[0]] = {'postfix': entry[1], 'chars': [
                chr(int(entry[2])), chr(int(entry[3]))]}
        f.close()
        return fontinfo

    def solution2Html(self, s, config):
        s = string.replace(s, "\n", "<br/>")
        if 'kqrbsp' in config:
            s = string.replace(s, "x", ":")
            s = string.replace(s, "*", ":")
            # so both pieces match RE in eg: '1.a1=Q Be5'
            s = string.replace(s, " ", "  ")
            pattern = re.compile('([ \.\(\=\a-z18])([KQRBSP])([^\)\]A-Z])')
            s = re.sub(
                pattern,
                lambda m: self.replaceSolutionChars(
                    config,
                    m),
                s)
            s = string.replace(s, "  ", " ")
        return '<b>' + s + '</b>'

    def replaceSolutionChars(self, config, m):
        return m.group(1) + '</b><font face="' + config['prefix'] + '">' + str(chr(
            config['kqrbsp']['kqrbsp'.index(m.group(2).lower())])) + '</font><b>' + m.group(3)

    def board2Html(self, board, config):  # mostly copypaste from pdf.py  :( real clumsy
        # important assumption: empty squares and board edges reside in one font file/face
        # (poorly designated 'aux-postfix') in case of most chess fonts there's only one file/face
        # and there's nothing to worry about, in case of GC2004 this is true (they are in GC2004d)
        # in other fonts - who knows
        lines = []
        spans, fonts, prevfont = [], [], config['prefix'] + config['aux-postfix']
        # top edge
        fonts.append(prevfont)
        spans.append([chr(int(config['edges']['NW'])) +
                      8 * chr(int(config['edges']['N'])) +
                      chr(int(config['edges']['NE'])) +
                      "<br/>"])
        for i in xrange(64):
            # left edge
            if i % 8 == 0:
                font = config['prefix'] + config['aux-postfix']
                char = chr(int(config['edges']['W']))
                if font != prevfont:
                    fonts.append(font)
                    spans.append([char])
                    prevfont = font
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
            if font != prevfont:
                fonts.append(font)
                spans.append([char])
                prevfont = font
            else:
                spans[-1].append(char)
            # right edge
            if i % 8 == 7:
                font = config['prefix'] + config['aux-postfix']
                char = chr(int(config['edges']['E']))
                if font != prevfont:
                    fonts.append(font)
                    spans.append([char])
                    prevfont = font
                else:
                    spans[-1].append(char)
                spans[-1].append("<br/>")
        # bottom edge
        font = config['prefix'] + config['aux-postfix']
        edge = chr(int(config['edges']['SW'])) + 8 * chr(int(config['edges']
                                                             ['S'])) + chr(int(config['edges']['SE'])) + "<br/>"
        if font != prevfont:
            fonts.append(font)
            spans.append(edge)
        else:
            spans[-1].append(edge)
        html = ''.join([
            '<font face="%s">%s</font>' % (fonts[i], ''.join(spans[i]))
            for i in xrange(len(fonts))
        ])
        return ('<font size="%s">%s</font>') % (config['size'], html)
        # return html

    def __init__(self):
        super(PublishingView, self).__init__(QtCore.Qt.Horizontal)

        f = open('conf/chessfonts.yaml', 'r')
        self.config = yaml.load(f)
        f.close()
        for family in self.config['diagram-fonts']:
            self.config['config'][family]['fontinfo'] = self.loadFontInfo(
                self.config['config'][family]['glyphs-tab'])

        self.richText = QtGui.QTextEdit()
        self.richText.setReadOnly(True)

        w = QtGui.QWidget()
        vbox = QtGui.QVBoxLayout()

        self.labelDiaFont = QtGui.QLabel()
        vbox.addWidget(self.labelDiaFont)
        self.diaFontSelect = QtGui.QComboBox()
        self.diaFontSelect.addItems(
            [self.config['config'][x]['display-name'] for x in self.config['diagram-fonts']])
        self.diaFontSelect.setCurrentIndex(
            self.config['diagram-fonts'].index(self.config['defaults']['diagram']))
        vbox.addWidget(self.diaFontSelect)
        self.labelSolFont = QtGui.QLabel()
        vbox.addWidget(self.labelSolFont)
        self.solFontSelect = QtGui.QComboBox()
        self.solFontSelect.addItems(
            [self.config['config'][x]['display-name'] for x in self.config['inline-fonts']])
        self.solFontSelect.setCurrentIndex(
            self.config['inline-fonts'].index(self.config['defaults']['inline']))
        vbox.addWidget(self.solFontSelect)
        self.labelMemo = QtGui.QLabel()
        vbox.addWidget(self.labelMemo)
        vbox.addStretch(1)

        w.setLayout(vbox)
        self.addWidget(self.richText)
        self.addWidget(w)
        self.setStretchFactor(0, 1)

        self.diaFontSelect.currentIndexChanged.connect(self.onModelChanged)
        self.solFontSelect.currentIndexChanged.connect(self.onModelChanged)
        Mainframe.sigWrapper.sigModelChanged.connect(self.onModelChanged)
        Mainframe.sigWrapper.sigLangChanged.connect(self.onLangChanged)

        self.onLangChanged()

    def onModelChanged(self):
        self.richText.setText("")
        self.richText.setFontPointSize(12)

        self.richText.insertHtml(
            pdf.ExportDocument.header(
                Mainframe.model.cur(),
                Lang) + "<br/>\n")

        inline_font = self.config[
            'inline-fonts'][self.solFontSelect.currentIndex()]
        diagram_font = self.config[
            'diagram-fonts'][self.diaFontSelect.currentIndex()]

        self.richText.insertHtml(
            self.board2Html(
                Mainframe.model.board,
                self.config['config'][diagram_font]))
        self.richText.insertHtml(
            Mainframe.model.cur()['stipulation'] +
            ' ' +
            Mainframe.model.board.getPiecesCount() +
            "<br/>\n")

        self.richText.insertHtml(
            pdf.ExportDocument.solver(
                Mainframe.model.cur(),
                Lang) + "<br/>\n")
        self.richText.insertHtml(
            pdf.ExportDocument.legend(
                Mainframe.model.board) +
            "<br/><br/>\n")

        if 'solution' in Mainframe.model.cur():
            self.richText.insertHtml(
                self.solution2Html(
                    Mainframe.model.cur()['solution'],
                    self.config['config'][inline_font]))

        if('keywords' in Mainframe.model.cur()):
            self.richText.insertHtml(
                "<br/>\n" +
                ', '.join(
                    Mainframe.model.cur()['keywords']) +
                "<br/>\n")

        if('comments' in Mainframe.model.cur()):
            self.richText.insertHtml(
                "<br/>\n" + "<br/>\n".join(Mainframe.model.cur()['comments']) + "<br/>\n")

    def onLangChanged(self):
        self.labelDiaFont.setText(Lang.value('PU_Diagram_font') + ':')
        self.labelSolFont.setText(Lang.value('PU_Inline_font') + ':')
        self.labelMemo.setText(Lang.value('PU_Memo'))
        self.onModelChanged()


class PopeyeOutputWidget(QtGui.QTextEdit):

    def __init__(self, parentView):
        self.parentView = parentView
        super(PopeyeOutputWidget, self).__init__()

    def contextMenuEvent(self, e):
        menu = self.createStandardContextMenu()
        if self.parentView.compact_possible:
            menu.addSeparator()
            if self.parentView.solutionOutput is None:
                menu.addAction(
                    Lang.value('PS_Compact'),
                    self.parentView.onCompact)
            else:
                submenu = menu.addMenu(Lang.value('PS_Notation'))
                submenu.addAction(
                    Lang.value('PS_Original_output'),
                    self.parentView.toggleCompact)
                notations = Conf.value('notations')
                for notation in notations.keys():
                    submenu.addAction(
                        ''.join(
                            notations[notation]),
                        self.parentView.createChangeNotationCallable(notation))
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
        self.setText(
            yaml.dump(
                Mainframe.model.cur(),
                encoding=None,
                allow_unicode=True))


class Conf:
    file = 'conf/main.yaml'
    keywords_file = 'conf/keywords.yaml'
    zoo_file = 'conf/zoos.yaml'
    popeye_file = 'conf/popeye.yaml'
    chest_file = 'conf/chest.yaml'

    def read():

        with open(Conf.file, 'r') as f:
            Conf.values = yaml.load(f)

        Conf.zoos = []
        with open(Conf.zoo_file, 'r') as f:
            for zoo in yaml.load_all(f):
                Conf.zoos.append(zoo)

        with open(Conf.keywords_file, 'r') as f:
            Conf.keywords = yaml.load(f)

        with open(Conf.popeye_file, 'r') as f:
            Conf.popeye = yaml.load(f)

        with open(Conf.chest_file, 'r') as f:
            Conf.chest = yaml.load(f)

    read = staticmethod(read)

    def write():
        with open(Conf.file, 'w') as f:
            f.write(Conf.dump(Conf.values))
        with open(Conf.popeye_file, 'w') as f:
            f.write(Conf.dump(Conf.popeye))
        with open(Conf.chest_file, 'w') as f:
            f.write(Conf.dump(Conf.chest))
    write = staticmethod(write)

    def value(v):
        return Conf.values[v]
    value = staticmethod(value)

    def dump(object):
        return unicode(
                yaml.dump(
                        object,
                        encoding=None,
                        allow_unicode=True)).encode('utf8')
    dump = staticmethod(dump)


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
