# -*- coding: utf-8 -*-

import yaml
from base import get_write_dir


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

    @classmethod
    def write(cls):
        with open(cls.file, 'wb') as f:
            f.write(cls.dump(cls.values))
        with open(cls.popeye_file, 'wb') as f:
            f.write(cls.dump(cls.popeye))
        with open(cls.chest_file, 'wb') as f:
            f.write(cls.dump(cls.chest))

    @classmethod
    def value(cls, v):
        return cls.values[v]

    @classmethod
    def dump(cls, object):
        return yaml.dump(object, encoding="utf8", allow_unicode=True)
