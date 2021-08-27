# -*- coding: utf-8 -*-
# Copyright: Tanaka Aiko (https://github.com/aiko-tanaka)
# License: GNU AGPL, version 3 or later; https://www.gnu.org/licenses/agpl-3.0.en.html

import sys

# import tatsumoto's AJT furigana plugin
sys.path.append('../1344485230')
ajt_furigana = __import__('1344485230')

mecab = ajt_furigana.mecab_controller.MecabController()

def generate_furigana(text: str) -> str:
    res = mecab.reading(text)
    if res:
        return res
    else:
        return ''