import re
import unittest
from pathlib import Path

import yaml

from conf import ConfigurationError
from configuration import format_errors
from lang import Lang


class ConfigurationLanguageTest(unittest.TestCase):
    def setUp(self):
        self.translations = yaml.safe_load(Path('conf/lang.yaml').read_text(encoding='utf8'))
        for attribute in ('current', 'values'):
            if hasattr(Lang, attribute):
                self.addCleanup(setattr, Lang, attribute, getattr(Lang, attribute))
            else:
                self.addCleanup(delattr, Lang, attribute)
        Lang.values = self.translations
        Lang.current = 'en'

    def test_configuration_translations_cover_languages_and_placeholders(self):
        languages = set(yaml.safe_load(Path('conf/dist/main.yaml').read_text(encoding='utf8'))['languages'])
        keys = {key for key in self.translations
                if key.startswith(('CFG_', 'MI_Configuration', 'MSG_Configuration'))}
        for filename in ('conf.py', 'configuration.py', 'gui.py'):
            used = set(re.findall(r"['\"]((?:CFG_|MI_Configuration|MSG_Configuration)[A-Za-z_]*)['\"]",
                                  Path(filename).read_text(encoding='utf8')))
            self.assertFalse(used - keys, filename)
        for key in keys:
            with self.subTest(key=key):
                translations = self.translations[key]
                self.assertEqual(languages, set(translations))
                placeholders = re.findall(r'%[sd]', translations['en'])
                for language in languages:
                    self.assertTrue(translations[language].strip())
                    self.assertEqual(placeholders, re.findall(r'%[sd]', translations[language]))

    def test_errors_are_translated_at_presentation_time(self):
        error = ConfigurationError('CFG_Field_type', 'memory')
        for language in ('en', 'rs', 'ru', 'de', 'ro'):
            Lang.current = language
            for diagnostic, expected in (
                (error, Lang.value('CFG_Field_type') % 'memory'),
                (FileNotFoundError('English OS text'), Lang.value('CFG_File_missing')),
                (PermissionError('English OS text'), Lang.value('CFG_Access_denied')),
                (OSError('English OS text'), Lang.value('CFG_File_error')),
                (ValueError('English library text'), Lang.value('CFG_Invalid_settings')),
                (yaml.YAMLError('English parser text'), Lang.value('CFG_Invalid_yaml')),
            ):
                self.assertEqual('main.yaml: ' + expected, format_errors([('main.yaml', diagnostic)]))


if __name__ == '__main__':
    unittest.main()
