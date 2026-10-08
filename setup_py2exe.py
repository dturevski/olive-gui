# -*- coding: utf-8 -*-

from distutils.core import setup
import py2exe
from glob import glob
import sys

sys.path.append("\\build-olive\\x86_Microsoft.VC90.CRT")

data_files = [("Microsoft.VC90.CRT", glob("\\build-olive\\x86_Microsoft.VC90.CRT\\*.*"))]

setup(
    data_files=data_files,
    windows=[{
        "script": "olive.py",
        "icon_resources": [(0, "olive.ico")]
    }],
    options={
        "py2exe": {
            "includes": ["sip"],
            "packages": [
                'reportlab',
                 'reportlab.graphics.charts',
                 'reportlab.graphics.samples',
                 'reportlab.graphics.widgets',
                 'reportlab.graphics.barcode',
                 'reportlab.graphics',
                 'reportlab.lib',
                 'reportlab.pdfbase',
                 'reportlab.pdfgen',
                 'reportlab.platypus',
            ]
        }
    }
)
