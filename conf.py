# -*- coding: utf-8 -*-

import copy
import os
import tempfile

import yaml
from base import get_write_dir


class ConfigurationError(ValueError):
    """A diagnostic translated by the UI in the current display language."""
    def __init__(self, key, *parameters):
        self.key = key
        self.parameters = parameters
        super().__init__(key, *parameters)


class Conf:
    file = get_write_dir() + '/conf/main.yaml'
    keywords_file = get_write_dir() + '/conf/keywords.yaml'
    zoo_file = get_write_dir() + '/conf/zoos.yaml'
    popeye_file = get_write_dir() + '/conf/popeye.yaml'
    chest_file = get_write_dir() + '/conf/chest.yaml'
    templates_file = get_write_dir() + '/conf/user-templates.yaml'

    @classmethod
    def read(cls):
        with open(cls.file, 'r', encoding="utf8") as f:
            cls.values = yaml.safe_load(f)

        cls.zoos = []
        with open(cls.zoo_file, 'r', encoding="utf8") as f:
            for zoo in yaml.safe_load_all(f):
                cls.zoos.append(zoo)

        with open(cls.keywords_file, 'r', encoding="utf8") as f:
            cls.keywords = yaml.safe_load(f)

        with open(cls.popeye_file, 'r', encoding="utf8") as f:
            cls.popeye = yaml.safe_load(f)

        with open(cls.chest_file, 'r', encoding="utf8") as f:
            cls.chest = yaml.safe_load(f)

        with open(cls.templates_file, 'r', encoding="utf8") as f:
            cls.templates = yaml.safe_load(f)

        cls._snapshots = {name: copy.deepcopy(getattr(cls, name))
                          for name in cls.editable_files()}

    @classmethod
    def editable_files(cls):
        return {'values': cls.file, 'popeye': cls.popeye_file,
                'chest': cls.chest_file}

    @staticmethod
    def merge(base, current, disk):
        """Three-way merge: external changes win conflicts, including deletions."""
        missing = object()
        result = {}
        for key in base.keys() | current.keys() | disk.keys():
            old, local, external = (d.get(key, missing) for d in (base, current, disk))
            if all(isinstance(v, dict) for v in (old, local, external)):
                value = Conf.merge(old, local, external)
            else:
                value = local if external == old else external
            if value is not missing:
                result[key] = copy.deepcopy(value)
        return result

    @classmethod
    def validate(cls, name, data):
        """Validate the public configuration before replacing running settings."""
        def require(condition, key, *parameters):
            if not condition:
                raise ConfigurationError(key, *parameters)

        require(isinstance(data, dict), 'CFG_Expected_mapping')
        fields = {
            'values': {'analyzers': list, 'auto-compactify': (int, bool),
                       'clear-popeye-output-on-entry-change': bool,
                       'collections-dir': str, 'default-lang': str,
                       'default-notation': str, 'fairy-zoo': list,
                       'horsehead-glyph': str, 'import-post-decode': dict,
                       'import-post-decode-default': str, 'languages': dict,
                       'notations': dict, 'popeye-toolbar-options': list,
                       'version': str},
            'popeye': {'path': str, 'memory': int, 'comlog': str,
                       'sticky-options': list, 'stop-max-bytes': int},
            'chest': {'path': str, 'options': str},
        }
        for key, kind in fields[name].items():
            require(key in data and isinstance(data[key], kind),
                    'CFG_Field_type', key)
        if name == 'popeye':
            for key in ('memory', 'stop-max-bytes'):
                require(type(data[key]) is int and data[key] > 0,
                        'CFG_Positive_integer', key)
            require(all(isinstance(v, str) for v in data['sticky-options']),
                    'CFG_String_list', 'sticky-options')
        if name != 'values':
            return
        require(type(data.get('font-size', 24)) is int and 1 <= data.get('font-size', 24) <= 200,
                'CFG_Font_size')
        for key in ('languages', 'import-post-decode'):
            require(data[key] and all(isinstance(k, str) and isinstance(v, str)
                                      for k, v in data[key].items()),
                    'CFG_String_mapping', key)
        require(data['default-lang'] in data['languages'], 'CFG_Unknown_value', 'default-lang')
        require('en' in data['notations'] and data['default-notation'] in data['notations'],
                'CFG_Required_notations')
        require(all(isinstance(k, str) and isinstance(v, list) and len(v) == 6
                    and all(isinstance(s, str) and s for s in v)
                    for k, v in data['notations'].items()),
                'CFG_Notation_shape')
        require(data['import-post-decode-default'] in data['import-post-decode'],
                'CFG_Unknown_value', 'import-post-decode-default')
        require(all(isinstance(v, str) for v in data['analyzers']),
                'CFG_String_list', 'analyzers')
        require(len(data['horsehead-glyph']) == 1, 'CFG_Horsehead_glyph')
        require(len(data['fairy-zoo']) == 3 and all(
            isinstance(row, list) and len(row) == 7
            and all(isinstance(v, str) for v in row) for row in data['fairy-zoo']),
            'CFG_Zoo_shape')
        for option in data['popeye-toolbar-options']:
            require(isinstance(option, dict) and type(option.get('enabled')) is bool
                    and isinstance(option.get('icon'), str)
                    and isinstance(option.get('option'), str),
                    'CFG_Toolbar_shape')

    @classmethod
    def reload(cls, name, validator=None):
        path = cls.editable_files()[name]
        with open(path, 'rb') as stream:
            raw = stream.read()
        disk = yaml.safe_load(raw)
        cls.validate(name, disk)
        current = getattr(cls, name)
        merged = cls.merge(cls._snapshots[name], current, disk)
        cls.validate(name, merged)
        if validator:
            validator(name, merged)
        changed = merged != current
        setattr(cls, name, merged)
        cls._snapshots[name] = copy.deepcopy(disk)
        return changed, raw

    @classmethod
    def write(cls, validator=None):
        errors = []
        for name, path in cls.editable_files().items():
            temporary = None
            try:
                # Re-read even if the watcher has not processed the last save yet.
                _, raw = cls.reload(name, validator)
                if getattr(cls, name) == cls._snapshots[name]:
                    continue  # Preserve formatting and comments when nothing changed.
                with tempfile.NamedTemporaryFile(dir=os.path.dirname(os.path.abspath(path)),
                                                 delete=False) as stream:
                    temporary = stream.name
                    stream.write(cls.dump(getattr(cls, name)))
                with open(path, 'rb') as stream:
                    if stream.read() != raw:
                        raise ConfigurationError('CFG_Changed_during_save')
                os.replace(temporary, path)
                temporary = None
                cls._snapshots[name] = copy.deepcopy(getattr(cls, name))
            except (OSError, ValueError, yaml.YAMLError) as error:
                errors.append((path, error))
            finally:
                if temporary is not None:
                    try:
                        os.unlink(temporary)
                    except OSError:
                        errors.append((temporary, ConfigurationError('CFG_Temporary_cleanup')))
        return errors

    @classmethod
    def value(cls, v):
        return cls.values[v]

    @classmethod
    def dump(cls, object):
        return yaml.dump(object, encoding="utf8", allow_unicode=True)
