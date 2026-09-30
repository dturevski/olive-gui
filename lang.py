# -*- coding: utf-8 -*-

import yaml
from base import get_write_dir
from conf import Conf


class Lang:
    file = get_write_dir() + '/conf/lang.yaml'

    @classmethod
    def read(cls):
        f = open(cls.file, 'r', encoding="utf8")
        try:
            cls.values = yaml.safe_load(f)
        finally:
            f.close()
        cls.current = Conf.value('default-lang')

    @classmethod
    def value(cls, v):
        return cls.values[v][cls.current]
