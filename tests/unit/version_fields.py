import copy
import os
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

import yaml
from PyQt5 import QtCore, QtWidgets

import gui
import model
import exporters.html
import exporters.latex
import exporters.pdf
from conf import Conf
from lang import Lang


class TestVersionFields(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Conf.read()
        Lang.read()
        cls.app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
        # Register the app's icons when generated resources are available.
        try:
            import resources
        except ImportError:
            pass
        cls.saved_conf = copy.deepcopy(Conf.values)
        cls.frame = gui.Mainframe()
        cls.frame.hide()

    @classmethod
    def tearDownClass(cls):
        Conf.values = cls.saved_conf
        cls.frame.deleteLater()
        cls.app.sendPostedEvents(None, QtCore.QEvent.DeferredDelete)

    def setUp(self):
        Lang.current = 'en'
        self.entry = {'authors': ['Original Author'], 'stipulation': '#2',
                      'algebraic': {'white': ['Ka1'], 'black': ['Kh8']},
                      'solution': '1.Kb1', 'comments': ['Keep this comment']}
        gui.Mainframe.model = model.Model()
        gui.Mainframe.model.entries[0] = copy.deepcopy(self.entry)
        gui.Mainframe.model.setNewCurrent(0)
        self.frame.entryList.rebuild()
        gui.Mainframe.sigWrapper.sigLangChanged.emit()
        gui.Mainframe.sigWrapper.sigModelChanged.emit()
        self.versions = self.frame.versionsView
        self.popeye = self.frame.popeyeView

    def entryWithFields(self):
        return dict(self.entry, **{'version-of': 99999999, 'after': 88888888,
                                  'versionists': ['Jane Doe', 'Иван', 'Last, First'],
                                  'correctors': ['Alex & Sam'],
                                  'non-standard-stipulation': 'Proca -9 & #1'})

    def editFields(self):
        self.versions.inputs['version-of'].setText('99999999')
        self.versions.inputs['after'].setText('88888888')
        self.versions.inputs['versionists'].setPlainText('Jane Doe\nИван\nLast, First')
        self.versions.inputs['correctors'].setPlainText('Alex & Sam')
        self.popeye.inputNonStandardStipulation.setText('Proca -9 & #1')

    def test_editing_marks_dirty_without_online_validation(self):
        with patch('requests.post', side_effect=AssertionError('Unexpected online validation')):
            self.editFields()
        self.assertEqual(gui.Mainframe.model.cur(), self.entryWithFields())
        self.assertTrue(gui.Mainframe.model.is_dirty)
        self.assertTrue(gui.Mainframe.model.dirty_flags[0])

    def test_drafts_allow_people_without_references_and_long_stipulations(self):
        self.versions.inputs['versionists'].setPlainText('Given Name Only')
        self.versions.inputs['correctors'].setPlainText('Nickname')
        long_text = 'Local draft ' * 30
        self.popeye.inputNonStandardStipulation.setText(long_text)
        entry = gui.Mainframe.model.cur()
        self.assertEqual(entry['versionists'], ['Given Name Only'])
        self.assertEqual(entry['correctors'], ['Nickname'])
        self.assertNotIn('version-of', entry)
        self.assertGreater(len(entry['non-standard-stipulation']), 255)
        self.assertIn('Version by Given Name Only', self.frame.infoView.toPlainText())
        self.assertIn('Correction by Nickname', self.frame.infoView.toPlainText())

    def test_blank_fields_remove_only_optional_data(self):
        self.editFields()
        for field, widget in self.versions.inputs.items():
            widget.clear()
        self.popeye.inputNonStandardStipulation.clear()
        self.assertEqual(gui.Mainframe.model.cur(), self.entry)
        self.assertEqual(self.frame.boardView.labelStipulation.text(), '#2')
        self.assertEqual(self.frame.boardView.labelStipulation.toolTip(), '')

    def test_reference_numbers_are_not_restricted_to_wiki_minimum(self):
        validator = self.versions.inputs['version-of'].validator()
        self.assertEqual(validator.validate('1', 1)[0], validator.Acceptable)
        self.versions.inputs['version-of'].setText('1')
        self.versions.inputs['after'].setText('2')
        self.assertEqual(gui.Mainframe.model.cur()['version-of'], 1)
        self.assertEqual(gui.Mainframe.model.cur()['after'], 2)
        gui.Mainframe.model.cur()['version-of'] = 'Local note'
        gui.Mainframe.sigWrapper.sigModelChanged.emit()
        self.versions.inputs['correctors'].setPlainText('Jane')
        self.assertEqual(gui.Mainframe.model.cur()['version-of'], 'Local note')

    def test_partial_attribution_has_no_dangling_by(self):
        self.versions.inputs['version-of'].setText('347013')
        lines = model.attributionLines(gui.Mainframe.model.cur(), Lang)
        self.assertEqual(lines, ['Version of >>347013'])
        self.versions.inputs['version-of'].clear()
        self.versions.inputs['correctors'].setPlainText('Jane')
        self.assertEqual(model.attributionLines(gui.Mainframe.model.cur(), Lang), ['Correction by Jane'])
        self.assertIn('Correction by', self.frame.infoView.toPlainText())

    def test_entry_switch_loads_fields_without_dirtying_or_leaking(self):
        gui.Mainframe.model.add(self.entryWithFields(), False)
        gui.Mainframe.sigWrapper.sigModelChanged.emit()
        self.assertEqual(self.versions.inputs['version-of'].text(), '99999999')
        self.assertEqual(self.versions.inputs['versionists'].toPlainText(), 'Jane Doe\nИван\nLast, First')
        self.assertFalse(gui.Mainframe.model.is_dirty)
        gui.Mainframe.model.setNewCurrent(0)
        gui.Mainframe.sigWrapper.sigModelChanged.emit()
        self.assertEqual(self.versions.inputs['version-of'].text(), '')
        self.assertEqual(self.versions.inputs['versionists'].toPlainText(), '')
        self.assertEqual(self.popeye.inputNonStandardStipulation.text(), '')
        self.assertFalse(gui.Mainframe.model.is_dirty)
        self.assertEqual(gui.Mainframe.model.entries[1], self.entryWithFields())

    def test_file_yaml_and_clipboard_round_trip(self):
        self.editFields()
        expected = copy.deepcopy(gui.Mainframe.model.cur())
        with tempfile.TemporaryDirectory() as directory:
            filename = os.path.join(directory, 'versions.olv')
            gui.Mainframe.model.filename = filename
            self.frame.onSaveFile()
            self.frame.openCollection(filename)
            self.assertEqual(gui.Mainframe.model.cur(), expected)
            self.assertFalse(gui.Mainframe.model.is_dirty)
            self.assertEqual(yaml.safe_load(self.frame.yamlView.toPlainText()), expected)
            self.frame.entryList.setCurrentItem(self.frame.entryList.topLevelItem(0))
            self.frame.entryList.onCopy()
            self.frame.entryList.onPaste()
            self.assertEqual(gui.Mainframe.model.cur(), expected)
            self.assertEqual(len(gui.Mainframe.model.entries), 2)

    def test_display_stipulation_keeps_standard_solver_input(self):
        self.editFields()
        self.assertEqual(self.frame.boardView.labelStipulation.text(), 'Proca -9 & #1')
        self.assertEqual(self.frame.boardView.labelStipulation.toolTip(), '#2')
        self.assertIn('Stipulation #2', self.popeye.input.toPlainText())
        self.assertNotIn('Proca', self.popeye.input.toPlainText())
        self.popeye.inputStipulation.setEditText('h#3')
        self.assertEqual(gui.Mainframe.model.cur()['non-standard-stipulation'], 'Proca -9 & #1')
        self.assertEqual(self.frame.boardView.labelStipulation.toolTip(), 'h#3')

    def test_header_and_exports_include_attribution_and_escape_new_text(self):
        self.editFields()
        entry = gui.Mainframe.model.cur()
        entry['versionists'] = ['<Jane> & "Sam"', 'Last, First']
        entry['non-standard-stipulation'] = '<Last move?> & "text"'
        gui.Mainframe.sigWrapper.sigModelChanged.emit()
        self.assertEqual(yaml.safe_load(self.frame.yamlView.toPlainText()), entry)
        header = exporters.pdf.ExportDocument.header(entry, Lang, Conf)
        self.assertIn('of &gt;&gt;99999999', header)
        self.assertIn('After &gt;&gt;88888888', header)
        self.assertIn('Correction by', header)
        self.assertIn('&lt;Jane&gt; &amp;', header)
        self.assertNotIn('&amp;amp;', header)
        self.assertNotIn('<Jane>', header)
        self.assertLess(header.index('Original Author'), header.index('Version by'))
        rendered = exporters.html.render(entry, self.frame.publishingView.settings())
        self.assertIn('<span title="#2">&lt;Last move?&gt; &amp; &quot;text&quot;</span>', rendered)
        self.assertIn('<Last move?> & "text"', self.frame.publishingView.richText.toPlainText())
        tex = exporters.latex.entry(entry, Lang)
        self.assertIn(r'Version by <Jane> \& "Sam" \& Last, First of >>99999999', tex)
        self.assertIn('After >>88888888', tex)
        self.assertIn('Correction by Alex \\& Sam', tex)
        self.assertIn('\\stipulation{<Last move?> \\& "text"}', tex)
        self.assertEqual(exporters.latex.text2LaTeX('Name_{x} $5'), r'Name\_\{x\} \$5')
        document = exporters.pdf.ExportDocument([entry], Lang, Conf)
        with tempfile.TemporaryDirectory() as directory:
            filename = os.path.join(directory, 'versions.pdf')
            document.doExport(filename)
            with open(filename, 'rb') as result:
                self.assertEqual(result.read(4), b'%PDF')

    def test_new_references_and_exclusive_parent_controls(self):
        with patch('requests.post', side_effect=AssertionError('Unexpected online validation')):
            self.versions.inputs['version-of'].setText('4')
            self.versions.inputs['correction-of'].setText('5')
            self.versions.inputs['anticipated-by'].setText('6')
        entry = gui.Mainframe.model.cur()
        self.assertNotIn('version-of', entry)
        self.assertEqual(self.versions.inputs['version-of'].text(), '')
        self.assertEqual(entry['correction-of'], 5)
        self.assertEqual(entry['anticipated-by'], 6)
        self.assertEqual(model.attributionLines(entry, Lang), ['Correction of >>5', 'Anticipated by >>6'])
        self.versions.inputs['version-of'].setText('7')
        self.assertNotIn('correction-of', entry)
        self.assertEqual(entry['version-of'], 7)
        self.assertEqual(entry['anticipated-by'], 6)
        self.assertEqual(self.versions.inputs['correction-of'].text(), '')

    def test_new_reference_file_yaml_and_clipboard_round_trip(self):
        self.editFields()
        self.versions.inputs['correction-of'].setText('77777777')
        self.versions.inputs['anticipated-by'].setText('66666666')
        expected = copy.deepcopy(gui.Mainframe.model.cur())
        self.assertNotIn('version-of', expected)
        # Keep locally unfinished person attribution; do not silently remove it.
        self.assertIn('versionists', expected)
        with tempfile.TemporaryDirectory() as directory:
            filename = os.path.join(directory, 'new-links.olv')
            gui.Mainframe.model.filename = filename
            self.frame.onSaveFile()
            self.frame.openCollection(filename)
            self.assertEqual(gui.Mainframe.model.cur(), expected)
            self.assertEqual(yaml.safe_load(self.frame.yamlView.toPlainText()), expected)
            self.frame.entryList.setCurrentItem(self.frame.entryList.topLevelItem(0))
            self.frame.entryList.onCopy()
            self.frame.entryList.onPaste()
            self.assertEqual(gui.Mainframe.model.cur(), expected)

    def test_loading_local_conflicting_parents_preserves_draft(self):
        entry = gui.Mainframe.model.cur()
        entry.update({'version-of': 4, 'correction-of': 5, 'anticipated-by': 'Draft note'})
        gui.Mainframe.sigWrapper.sigModelChanged.emit()
        self.assertEqual(entry['version-of'], 4)
        self.assertEqual(entry['correction-of'], 5)
        self.assertEqual(self.versions.inputs['anticipated-by'].text(), 'Draft note')
        self.assertFalse(gui.Mainframe.model.is_dirty)
        self.versions.inputs['correctors'].setPlainText('Corrector')
        self.assertEqual(entry['anticipated-by'], 'Draft note')

    def test_new_attribution_exports_and_correct_word_order(self):
        entry = gui.Mainframe.model.cur()
        entry.update({'version-of': 4, 'versionists': ['Jane'], 'anticipated-by': 6})
        self.assertEqual(model.attributionLines(entry, Lang),
                         ['Version by Jane of >>4', 'Anticipated by >>6'])
        header = exporters.pdf.ExportDocument.header(entry, Lang, Conf)
        self.assertIn('Version by <b>Jane</b> of &gt;&gt;4', header)
        self.assertIn('Version by Jane of >>4', exporters.latex.entry(entry, Lang))
        del entry['version-of'], entry['versionists']
        entry.update({'correction-of': 5, 'correctors': ['<Jane>']})
        self.assertEqual(model.attributionLines(entry, Lang),
                         ['Correction by <Jane> of >>5', 'Anticipated by >>6'])
        header = exporters.pdf.ExportDocument.header(entry, Lang, Conf)
        self.assertIn('Correction by <b>&lt;Jane&gt;</b> of &gt;&gt;5', header)
        self.assertIn('Anticipated by &gt;&gt;6', header)
        self.assertIn('Correction by <Jane> of >>5', exporters.latex.entry(entry, Lang))
        self.assertNotIn('<Jane>', header)

    def test_languages_and_tab_placement(self):
        self.assertEqual(self.frame.tabBar2.indexOf(self.versions),
                         self.frame.tabBar2.indexOf(self.frame.easyEditView) + 1)
        for language in Conf.value('languages'):
            Lang.current = language
            gui.Mainframe.sigWrapper.sigLangChanged.emit()
            self.assertEqual(self.frame.tabBar2.tabText(3), Lang.value('TC_Versions'))
            for field, label in self.versions.fields:
                self.assertEqual(self.versions.labels[field].text(), Lang.value(label) + ':')
                self.assertTrue(self.versions.inputs[field].toolTip())
            self.assertIn(Lang.value('EP_Anticipated_by'),
                          model.attributionLines({'anticipated-by': 4}, Lang)[0])
            self.assertEqual(self.popeye.labelNonStandardStipulation.text(),
                             Lang.value('EP_Non_standard_stipulation') + ':')
        Lang.current = 'en'


if __name__ == '__main__':
    unittest.main()
