# -*- coding: utf-8 -*-
# Copyright: Tanaka Aiko (https://github.com/aiko-tanaka)
# License: GNU AGPL, version 3 or later; https://www.gnu.org/licenses/agpl-3.0.en.html

# parts of this code are copied from tatsumoto-ren/Ajatt-tools
# https://github.com/Ajatt-Tools/PasteImagesAsWebP/blob/main/config.py

from aqt import mw


def get_config() -> dict:
    cfg: dict = mw.addonManager.getConfig(__name__) or dict()

    # https://stackoverflow.com/questions/11152559/best-idiom-to-get-and-set-a-value-in-a-python-dict
    cfg['kanji_etym_field']: str        = cfg.get('kanji_etym_field', 'Okjiten_Kanji_Etym')
    cfg['dong_kanji_etym_field']: str   = cfg.get('dong_kanji_etym_field', 'Dong_Kanji_Etym')
    cfg['expression_field']: str        = cfg.get('expression_field', 'Reading')
    cfg['vocab_field']: str             = cfg.get('vocab_field', 'Vocab')
    cfg['force_update']: str            = cfg.get('force_update', 'no')
    cfg['keybinding']: str              = cfg.get('keybinding', '')
    cfg['update_separator']: str        = cfg.get('update_separator', '<br>')
    cfg['error_tag']: str               = cfg.get('error_tag', 'KanjiEtymError')

    return cfg


config = get_config()