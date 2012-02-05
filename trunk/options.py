from PyQt4 import QtGui, QtCore

class ParamInt(QtGui.QSpinBox):
    def __init__(self):
        super(ParamInt, self).__init__()
        self.trigger = self.valueChanged
    def get(self):
        return str(self.value())
    def set(self, v):
        self.setValue(int(v))
 
class ParamStr(QtGui.QLineEdit):
    def __init__(self):
        super(ParamStr, self).__init__()
        self.trigger = self.textChanged
        self.setFixedWidth(50)
    def get(self):
        return str(self.text())
    def set(self, v):
        self.setText(v)

class ParamSelect(QtGui.QComboBox):
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
        
class Option(QtGui.QWidget):
    def __init__(self, pattern):
        super(Option, self).__init__()
        parts = pattern.split(" ")

        self.command = parts[0]
        self.params = []
        hbox = QtGui.QHBoxLayout()
        self.checkbox = QtGui.QCheckBox(self.command) 
        hbox.addWidget(self.checkbox)
        for part in parts[1:]:
            if '<int>' == part:
                self.params.append(ParamInt())
            elif '<str>' == part:
                self.params.append(ParamStr())
            elif '<select{' == part[:len('<select{')]:
                    self.params.append(ParamSelect((part[len('<select{'):-2]).split('|')))
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
        return (self.command + " " + " ".join([x.get() for x in self.params])).strip()

class OkCancelDialog(QtGui.QDialog):                
    def __init__(self, Lang):
        super(OkCancelDialog, self).__init__()
        
        vbox = QtGui.QVBoxLayout()
        vbox.addWidget(self.mainWidget)
        vbox.addStretch(1)
        
        hbox = QtGui.QHBoxLayout()
        hbox.addStretch(1)
        buttonOk = QtGui.QPushButton(Lang.value('CO_OK'), self)
        buttonOk.clicked.connect(self.accept)
        buttonCancel = QtGui.QPushButton(Lang.value('CO_Cancel'), self)
        buttonCancel.clicked.connect(self.reject)
        
        hbox.addWidget(buttonOk)
        hbox.addWidget(buttonCancel)
        vbox.addLayout(hbox)
        
        self.setLayout(vbox)
        
class OptionsDialog(OkCancelDialog):
    def __init__(self, options, conditions, rows, cols, entry_options, Lang):
        self.mainWidget = QtGui.QTabWidget()
        self.options = []
        self.createTabs('Options', options, rows, cols, entry_options)
        self.createTabs('Conditions', conditions, rows, cols, entry_options)
        super(OptionsDialog, self).__init__(Lang)
        self.setWindowTitle(Lang.value('MI_Options'))
    def createTabs(self, caption, options, rows, cols, entry_options):
        count_tabs = len(options)//(rows*cols) + (len(options)%(rows*cols) != 0)
        planted = 0
        for i in xrange(count_tabs):
            w = QtGui.QWidget()
            grid = QtGui.QGridLayout()
            grid.setVerticalSpacing(0)
            grid.setHorizontalSpacing(0)  
            grid.setContentsMargins(0, 0, 0, 0)
            stretcher = QtGui.QWidget()
            grid.addWidget(stretcher, rows, cols)
            grid.setRowStretch(rows, 1)
            grid.setColumnStretch(cols, 1)
            w.setLayout(grid)
            self.mainWidget.addTab(w, caption +  ['', ' ('+str(i+1)+')'][i>0])
            for col in xrange(cols):
                for row in xrange(rows):
                    self.options.append(Option(options[i*rows*cols+col*rows+row]))
                    self.options[-1].set(entry_options)
                    grid.addWidget(self.options[-1], row, col)
                    planted = planted + 1
                    if planted == len(options):
                        return
    def getOptions(self):
        return [x.get() for x in self.options if x.get() != '']

class TwinsInputWidget(QtGui.QTextEdit):
    twinsExamples = [\
        "Stipulation ?",\
        "Condition ?",\
        "Move ? ?",\
        "Exchange ? ?",\
        "Remove ?",\
        "Substitute ? ?",\
        "Add ? ?",\
        "Rotate ?",\
        "Mirror ?<-->?",\
        "Shift ? ?",\
        "PolishType"]

    def __init__(self):
        super(TwinsInputWidget, self).__init__()
    def contextMenuEvent(self, e):
        menu = self.createStandardContextMenu()
        menu.addSeparator()
        twins = self.getTwins()
        next_letter = 'b'
        if len(twins):
            next_letter = chr(ord(sorted(twins.keys())[-1]) + 1)
        for t in TwinsInputWidget.twinsExamples:
            command = next_letter + ': ' + t
            menu.addAction(command, self.createCallable(command))
        menu.exec_(e.globalPos())
    def getTwins(self):
        twins = {}
        for line in [x.strip() for x in unicode(self.toPlainText()).encode('utf-8').split("\n") if x.strip() != '']:
            parts = line.split(":")
            if len(parts) != 2:
                continue
            twins[parts[0].strip()] = parts[1].strip()
        return twins
    def createCallable(self, command):
        def callable():
            twins = [x.strip() for x in unicode(self.toPlainText()).split("\n") if x.strip() != '']
            twins.append(command)
            self.setText("\n".join(twins))

        return callable

class TwinsDialog(OkCancelDialog):
    def __init__(self, twins, Lang):
        self.mainWidget = TwinsInputWidget()
        self.mainWidget.setText(twins)
        super(TwinsDialog, self).__init__(Lang)
        self.setWindowTitle(Lang.value('MI_Twins'))
    def getTwins(self):
        return self.mainWidget.getTwins()
