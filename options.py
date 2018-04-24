import os

from PyQt5 import QtGui, QtWidgets


class ParamInt(QtWidgets.QSpinBox):

    def __init__(self):
        super(ParamInt, self).__init__()
        self.trigger = self.valueChanged

    def get(self):
        return str(self.value())

    def set(self, v):
        self.setValue(int(v))


class ParamStr(QtWidgets.QLineEdit):

    def __init__(self):
        super(ParamStr, self).__init__()
        self.trigger = self.textChanged
        self.setFixedWidth(50)

    def get(self):
        return self.text()

    def set(self, v):
        self.setText(v)


class ParamSelect(QtWidgets.QComboBox):

    def __init__(self, params):
        super(ParamSelect, self).__init__()
        self.trigger = self.currentIndexChanged
        self.params = params
        self.addItems(self.params)

    def get(self):
        return self.params[self.currentIndex()]

    def set(self, v):
        if v in self.params:
            self.setCurrentIndex(self.params.index(v))
        else:
            self.setCurrentIndex(0)


class Option(QtWidgets.QWidget):

    def __init__(self, pattern):
        super(Option, self).__init__()
        parts = [p.replace('+', ' ') for p in pattern.split(" ")]

        self.command = parts[0]
        self.params = []
        hbox = QtWidgets.QHBoxLayout()
        self.checkbox = QtWidgets.QCheckBox(self.command)
        hbox.addWidget(self.checkbox)
        for part in parts[1:]:
            if '<int>' == part:
                self.params.append(ParamInt())
            elif '<str>' == part:
                self.params.append(ParamStr())
            elif '<select{' == part[:len('<select{')]:
                self.params.append(ParamSelect(
                    (part[len('<select{'):-2]).split('|')))
            else:
                # assert(False)
                break
            hbox.addWidget(self.params[-1])
            self.params[-1].trigger.connect(self.onParamChanged)
        hbox.addStretch(1)
        self.setLayout(hbox)

    def onParamChanged(self):
        self.checkbox.setChecked(True)

    def set(self, options):
        for option in options:
            if option == 'Intelligent':
                option = 'Intelligent 0'
            parts = option.split(" ")
            if parts[0].lower() == self.command.lower():
                for i, param_value in enumerate(parts[1:]):
                    if i < len(self.params):
                        self.params[i].set(param_value)
                self.checkbox.setChecked(True)
                break

    def get(self):
        if not self.checkbox.isChecked():
            return ''
        if self.command == 'Intelligent' and self.params[0].get() == '0':
            return 'Intelligent'
        return (self.command + " " +
                " ".join([x.get() for x in self.params])).strip()


class OkCancelDialog(QtWidgets.QDialog):

    def __init__(self, Lang):
        super(OkCancelDialog, self).__init__()

        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(self.mainWidget)
        vbox.addStretch(1)

        hbox = QtWidgets.QHBoxLayout()
        hbox.addStretch(1)
        buttonOk = QtWidgets.QPushButton(Lang.value('CO_OK'), self)
        buttonOk.clicked.connect(self.accept)
        buttonCancel = QtWidgets.QPushButton(Lang.value('CO_Cancel'), self)
        buttonCancel.clicked.connect(self.reject)

        hbox.addWidget(buttonOk)
        hbox.addWidget(buttonCancel)
        vbox.addLayout(hbox)

        self.setLayout(vbox)


class OptionsDialog(OkCancelDialog):

    def __init__(self, options, conditions, rows, cols, entry_options, Lang):
        self.mainWidget = QtWidgets.QTabWidget()
        self.options = []
        self.createTabs('Options', options, rows, cols, entry_options)
        self.createTabs('Conditions', conditions, rows, cols, entry_options)
        super(OptionsDialog, self).__init__(Lang)
        self.setWindowTitle(Lang.value('MI_Options'))
        self.setWindowIcon(QtGui.QIcon(QtGui.QPixmap('resources/icons/settings.svg')))

    def createTabs(self, caption, options, rows, cols, entry_options):
        count_tabs = len(options) // (rows * cols) + \
            (len(options) % (rows * cols) != 0)
        planted = 0
        for i in range(count_tabs):
            w = QtWidgets.QWidget()
            grid = QtWidgets.QGridLayout()
            grid.setVerticalSpacing(0)
            grid.setHorizontalSpacing(0)
            grid.setContentsMargins(0, 0, 0, 0)
            stretcher = QtWidgets.QWidget()
            grid.addWidget(stretcher, rows, cols)
            grid.setRowStretch(rows, 1)
            grid.setColumnStretch(cols, 1)
            w.setLayout(grid)
            page_first, page_last = '', ''
            for col in range(cols):
                for row in range(rows):
                    if planted == len(options):
                        break
                    optionWidget = Option(
                        options[
                            i *
                            rows *
                            cols +
                            col *
                            rows +
                            row])
                    self.options.append(optionWidget)
                    if page_first == '':
                        page_first = optionWidget.command
                    page_last = optionWidget.command
                    self.options[-1].set(entry_options)
                    grid.addWidget(self.options[-1], row, col)
                    planted = planted + 1
            tab_caption = caption
            if 'Conditions' == tab_caption:
                tab_caption = ['Conditions: ', ''][
                    i != 0] + page_first[0:3].upper() + ' - ' + page_last[0:3].upper()
            self.mainWidget.addTab(w, tab_caption)

    def getOptions(self):
        return [x.get() for x in self.options if x.get() != '']


class TwinsInputWidget(QtWidgets.QTextEdit):
    twinsExamples = [
        "Stipulation ?",
        "Condition ?",
        "Move ? ?",
        "Exchange ? ?",
        "Remove ?",
        "Substitute ? ?",
        "Add ? ?",
        "Rotate ?",
        "Mirror ?<-->?",
        "Shift ? ?",
        "PolishType"]

    def __init__(self):
        super(TwinsInputWidget, self).__init__()

    def contextMenuEvent(self, e):
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        twins = self.getTwins()
        if len(twins):
            next_letter = chr(ord(sorted(twins.keys())[-1]) + 1)
            continuedMenu = menu.addMenu(next_letter + ': Continued')
            for t in TwinsInputWidget.twinsExamples:
                command = next_letter + ': ' + t
                c_command = next_letter + ': Continued ' + t
                menu.addAction(command, self.createCallable(command))
                continuedMenu.addAction(
                    c_command, self.createCallable(c_command))
        else:
            for next_letter in ['a', 'b']:
                submenu = menu.addMenu(next_letter + ': ')
                for t in TwinsInputWidget.twinsExamples:
                    command = next_letter + ': ' + t
                    submenu.addAction(command, self.createCallable(command))
        menu.exec_(e.globalPos())

    def getTwins(self):
        twins = {}
        for line in [
            x.strip() for x in str(
                self.toPlainText()).encode(
                'ascii',
                'replace').split("\n") if x.strip() != '']:
            parts = line.split(":")
            if len(parts) != 2:
                continue
            twins[parts[0].strip()] = parts[1].strip()
        return twins

    def createCallable(self, command):
        def callable():
            twins = [
                x.strip() for x in str(
                    self.toPlainText()).split("\n") if x.strip() != '']
            twins.append(command)
            self.setText("\n".join(twins))

        return callable


class TwinsDialog(OkCancelDialog):

    def __init__(self, twins, Lang):
        self.mainWidget = TwinsInputWidget()
        self.mainWidget.setText(twins)
        super(TwinsDialog, self).__init__(Lang)
        self.setWindowTitle(Lang.value('MI_Twins'))
        self.setWindowIcon(QtGui.QIcon(QtGui.QPixmap('resources/icons/gemini.svg')))

    def getTwins(self):
        return self.mainWidget.getTwins()


class SelectFileWidget(QtWidgets.QLineEdit):

    def __init__(self, title, value, onChanged):
        super(SelectFileWidget, self).__init__()
        self.title = title
        self.value = value;
        self.onChanged = onChanged
        self.setText(value)
        self.setReadOnly(True)

    def mousePressEvent(self, e):
        fileName = QtWidgets.QFileDialog.getOpenFileName(self, self.title, os.path.dirname(self.value))[0]
        if not fileName:
            return
        self.value = str(fileName)
        self.setText(self.value)
        self.onChanged(self.value)

    def setText(self, text):
        halfMaxLen = 20
        if len(text) > 2*halfMaxLen:
            text = text[:halfMaxLen] + ' ... ' + text[-halfMaxLen:]
        return super(SelectFileWidget, self).setText(text)
