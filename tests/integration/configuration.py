"""Run with QT_QPA_PLATFORM=offscreen for a headless Qt integration check."""
import copy
import os
from pathlib import Path
import time
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PyQt5 import QtCore, QtGui, QtWidgets

import gui
from conf import Conf, ConfigurationError
from configuration import format_errors
from lang import Lang
from tests.unit.configuration import ConfigurationTest


class LiveConfigurationTest(unittest.TestCase):
    def test_live_reload_and_editor_replacement(self):
        Conf.read()
        Lang.read()
        original_language = Lang.current
        self.addCleanup(setattr, Lang, 'current', original_language)
        ConfigurationTest.setUp(self)
        app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        gui.Mainframe.app = app
        # Keep test geometry/state out of the user's application settings.
        with patch.object(gui.Mainframe, 'initFrame'), patch.object(gui.Mainframe, 'show'):
            window = gui.Mainframe()
        self.addCleanup(window.deleteLater)
        controller = window.configuration
        self.addCleanup(controller.timer.stop)
        errors = []
        import sys
        with patch.object(sys, 'excepthook', lambda *args: errors.append(args)):
            window.validateConfiguration('values', Conf.values)
            original_entry = copy.deepcopy(gui.Mainframe.model.cur())
            original_dirty = gui.Mainframe.model.is_dirty
            window.popeyeView.input.setPlainText('Keep my hand-written input')
            window.popeyeView.output.setPlainText('Keep my solver output')
            original_input = window.popeyeView.input.toPlainText()
            path = Path(Conf.file)
            data = copy.deepcopy(Conf.values)
            data['font-size'] = 30
            data['default-lang'] = 'de'
            data['popeye-toolbar-options'][0]['enabled'] = False
            data['popeye-toolbar-options'][-1]['enabled'] = True
            temporary = path.with_suffix('.tmp')
            temporary.write_bytes(Conf.dump(data))
            os.replace(temporary, path)
            self.wait_for(app, lambda: Conf.values['font-size'] == 30)
            self.assertEqual(30, window.boardView.labels[0].font().pointSize())
            self.assertEqual('de', Lang.current)
            self.assertEqual([o['option'] for o in data['popeye-toolbar-options'] if o['enabled']],
                             [a.text() for a in window.quickOptionsView.actions])
            self.assertIn(str(path), controller.watcher.files())
            data['font-size'] = 32
            path.write_bytes(Conf.dump(data))
            self.wait_for(app, lambda: Conf.values['font-size'] == 32)

            # Reject a partial save, then recover automatically on the next save.
            path.write_text('font-size: [', encoding='utf8')
            self.wait_for(app, lambda: Lang.value('MSG_Configuration_not_loaded')
                          in window.statusBar().currentMessage())
            self.assertEqual(32, Conf.values['font-size'])
            data['font-size'] = 34
            data['popeye-toolbar-options'] = []
            path.write_bytes(Conf.dump(data))
            self.wait_for(app, lambda: Conf.values['font-size'] == 34)
            data['font-size'] = 36
            data['popeye-toolbar-options'] = [
                {'enabled': True, 'icon': 'flash.svg', 'option': 'Intelligent'}]
            path.write_bytes(Conf.dump(data))
            self.wait_for(app, lambda: Conf.values['font-size'] == 36)

            # A missing file must remain watched via its directory and recover.
            path.unlink()
            self.wait_for(app, lambda: Lang.value('MSG_Configuration_not_loaded')
                          in window.statusBar().currentMessage())
            self.assertEqual(36, Conf.values['font-size'])
            data['font-size'] = 38
            path.write_bytes(Conf.dump(data))
            self.wait_for(app, lambda: Conf.values['font-size'] == 38)

            ConfigurationTest.edit(self, 'popeye', memory=4096, path='changed.exe')
            ConfigurationTest.edit(self, 'chest', options='-r', path='changed-chest.exe')
            self.wait_for(app, lambda: window.popeyeView.inputMemory.text() == '4096'
                          and window.chestView.inputOptions.text() == '-r')
            self.assertEqual('changed.exe', window.popeyeView.inputPyPath.value)
            self.assertEqual('changed-chest.exe', window.chestView.inputChestPath.value)
            self.assertEqual(original_entry, gui.Mainframe.model.cur())
            self.assertEqual(original_dirty, gui.Mainframe.model.is_dirty)
            self.assertEqual(original_input, window.popeyeView.input.toPlainText())
            self.assertEqual('Keep my solver output', window.popeyeView.output.toPlainText())
            self.assertEqual([], errors)

            for language in ('en', 'rs', 'ru', 'de', 'ro'):
                Lang.current = language
                gui.Mainframe.sigWrapper.sigLangChanged.emit()
                failures = [(str(path), ConfigurationError('CFG_Changed_during_save'))]
                with patch.object(window, 'doDirtyCheck', return_value=True), \
                        patch.object(window.popeyeView, 'areActionsEnabled', return_value=True), \
                        patch('gui.QtCore.QSettings'), patch.object(Conf, 'write', return_value=failures), \
                        patch('gui.QtWidgets.QMessageBox.warning') as warning:
                    event = QtGui.QCloseEvent()
                    window.closeEvent(event)
                    self.assertEqual((Lang.value('MI_Configuration'),
                                      Lang.value('MSG_Configuration_save_failed') + '\n\n' + format_errors(failures)),
                                     warning.call_args[0][1:])
                    self.assertTrue(event.isAccepted())

            # Every new label, dialog and existing status uses the selected language.
            for language in ('en', 'rs', 'ru', 'de', 'ro'):
                Lang.current = language
                gui.Mainframe.sigWrapper.sigLangChanged.emit()
                self.assertEqual(Lang.value('MI_Configuration'), window.configurationMenu.title())
                self.assertEqual(Lang.value('MI_Configuration_folder'), controller.folder_action.text())
                self.assertEqual(Lang.value('MI_Configuration_reload'), controller.reload_action.text())
                with patch('configuration.QtWidgets.QMessageBox.warning') as warning:
                    controller.reload(manual=True)
                    self.assertEqual(Lang.value('MSG_Configuration_reloaded'),
                                     window.statusBar().currentMessage())
                    with patch('configuration.QtGui.QDesktopServices.openUrl', return_value=False):
                        controller.open(str(path))
                    self.assertEqual((Lang.value('MI_Configuration'),
                                      Lang.value('MSG_Configuration_open_failed') % str(path)),
                                     warning.call_args[0][1:])

            path.write_text('font-size: [', encoding='utf8')
            controller.reload()
            for language in ('en', 'rs', 'ru', 'de', 'ro'):
                Lang.current = language
                gui.Mainframe.sigWrapper.sigLangChanged.emit()
                expected = (Lang.value('MSG_Configuration_not_loaded') + '\n'
                            + format_errors(controller.status_errors))
                self.assertEqual(expected, window.statusBar().currentMessage())
                self.assertIn(Lang.value('CFG_Yaml_location') % (1, 13), expected)
                with patch('configuration.QtWidgets.QMessageBox.warning') as warning:
                    controller.reload(manual=True)
                    self.assertEqual((Lang.value('MI_Configuration'), expected), warning.call_args[0][1:])
            self.assertEqual([], errors)
            with patch('configuration.QtGui.QDesktopServices.openUrl', return_value=True) as opened:
                window.configurationMenu.actions()[0].trigger()
                self.assertEqual(path, Path(opened.call_args[0][0].toLocalFile()))

            window.popeyeView.input.setPlainText(window.popeyeView.generatedInput())
            ConfigurationTest.edit(self, 'popeye', **{'sticky-options': ['NoBoard', 'SetPlay']})
            self.wait_for(app, lambda: 'SetPlay' in window.popeyeView.input.toPlainText())
            # A changed output limit must not stop a solve already in progress.
            window.popeyeView.runConfiguration = copy.deepcopy(Conf.popeye)
            ConfigurationTest.edit(self, 'popeye', **{'stop-max-bytes': 1})
            self.wait_for(app, lambda: Conf.popeye['stop-max-bytes'] == 1)
            with patch.object(window.popeyeView, 'process', create=True) as process, \
                    patch.object(window.popeyeView, 'stopPopeye') as stop:
                process.readAllStandardOutput.return_value = b'solver output'
                window.popeyeView.onOut()
                stop.assert_not_called()
            self.assertEqual([], errors)

    restore = ConfigurationTest.restore

    def wait_for(self, app, condition):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            app.processEvents()
            if condition():
                return
            time.sleep(0.02)
        self.fail('Timed out waiting for configuration reload')


if __name__ == '__main__':
    unittest.main()
