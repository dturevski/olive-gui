"""External configuration editing and debounced reloads on the Qt event loop."""
import copy
import os

import yaml
from PyQt5 import QtCore, QtGui, QtWidgets

from conf import Conf, ConfigurationError
from lang import Lang


def format_errors(errors):
    """Keep library/OS diagnostics out of the UI; YAML locations remain useful."""
    lines = []
    for path, error in errors:
        if isinstance(error, ConfigurationError):
            message = Lang.value(error.key) % error.parameters
        elif isinstance(error, yaml.YAMLError):
            mark = getattr(error, 'problem_mark', None)
            message = (Lang.value('CFG_Yaml_location') % (mark.line + 1, mark.column + 1)
                       if mark else Lang.value('CFG_Invalid_yaml'))
        elif isinstance(error, FileNotFoundError):
            message = Lang.value('CFG_File_missing')
        elif isinstance(error, PermissionError):
            message = Lang.value('CFG_Access_denied')
        elif isinstance(error, OSError):
            message = Lang.value('CFG_File_error')
        else:
            message = Lang.value('CFG_Invalid_settings')
        lines.append('%s: %s' % (path, message))
    return '\n'.join(lines)


class ConfigurationController(QtCore.QObject):
    def __init__(self, window):
        super().__init__(window)
        self.window = window
        self.status_errors = []
        self.status_text = None
        self.paths = {name: os.path.abspath(path)
                      for name, path in Conf.editable_files().items()}
        self.watcher = QtCore.QFileSystemWatcher(self)
        self.timer = QtCore.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.setInterval(400)
        self.timer.timeout.connect(self.reload)
        self.watcher.fileChanged.connect(self.schedule)
        self.watcher.directoryChanged.connect(self.schedule)
        self.watcher.addPaths(list(set(os.path.dirname(p) for p in self.paths.values())))
        self.rearm()

    def add_menu(self, file_menu):
        menu = self.menu = file_menu.addMenu(Lang.value('MI_Configuration'))
        for path in self.paths.values():
            menu.addAction(os.path.basename(path), lambda checked=False, p=path: self.open(p))
        menu.addSeparator()
        self.folder_action = menu.addAction(Lang.value('MI_Configuration_folder'),
                       lambda: self.open(os.path.dirname(self.paths['values'])))
        self.reload_action = menu.addAction(Lang.value('MI_Configuration_reload'),
                                            lambda: self.reload(manual=True))
        return menu

    def retranslate(self):
        self.menu.setTitle(Lang.value('MI_Configuration'))
        self.folder_action.setText(Lang.value('MI_Configuration_folder'))
        self.reload_action.setText(Lang.value('MI_Configuration_reload'))
        if self.status_text and self.window.statusBar().currentMessage() == self.status_text:
            self.show_status(self.status_errors)

    def show_status(self, errors):
        self.status_errors = errors
        self.status_text = (Lang.value('MSG_Configuration_not_loaded') + '\n' + format_errors(errors)
                            if errors else Lang.value('MSG_Configuration_reloaded'))
        self.window.statusBar().showMessage(self.status_text, 0 if errors else 5000)

    def open(self, path):
        if not QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path)):
            QtWidgets.QMessageBox.warning(
                self.window, Lang.value('MI_Configuration'),
                Lang.value('MSG_Configuration_open_failed') % path)

    def rearm(self):
        watched = set(self.watcher.files())
        for path in self.paths.values():
            if path not in watched and os.path.isfile(path):
                self.watcher.addPath(path)

    def schedule(self, path):
        self.timer.start()

    def reload(self, manual=False):
        self.timer.stop()
        self.window.chessBox.sync()
        previous = {name: copy.deepcopy(getattr(Conf, name)) for name in self.paths}
        changed, errors = [], []
        for name, path in self.paths.items():
            try:
                updated, _ = Conf.reload(name, self.window.validateConfiguration)
                if updated:
                    changed.append(name)
            except (OSError, ValueError, yaml.YAMLError) as error:
                errors.append((path, error))
        self.rearm()  # Atomic-save editors replace files, removing their watches.
        if changed:
            self.window.applyConfiguration(changed, previous)
        if errors:
            self.show_status(errors)
            if manual:
                QtWidgets.QMessageBox.warning(self.window, Lang.value('MI_Configuration'), self.status_text)
        elif changed or manual:
            self.show_status([])
        else:
            self.window.statusBar().clearMessage()
