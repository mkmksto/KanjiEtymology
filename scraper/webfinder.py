# -*- coding: utf-8 -*-
# Copyright: Tanaka Aiko (https://github.com/aiko-tanaka)
# License: GNU AGPL, version 3 or later; https://www.gnu.org/licenses/agpl-3.0.en.html

from bs4 import BeautifulSoup

import urllib.request
import urllib.parse
import json
import time
import re

test_in_anki = False

if test_in_anki:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from anki.hooks import addHook
    from aqt.utils import showInfo
    from aqt import mw

    try:
        config = mw.addonManager.getConfig(dir_path)
        expression_field = config['expressionField']
        vocab_field = config['vocabField']
        keybinding = config['keybinding'] #nothing by default
    except Exception as e:
        # expression_field = 'Expression'
        expression_field = 'Reading'
        vocab_field = "Vocab"
        # create this in ANKI!
        kanji_etym_field = "Kanji_Etym"
        keybinding = ""  # nothing by default
        force_update = "no"

# site2 = 'https://jisho.org/search/{}'.format(urllib.parse.quote(term))
# site3 = 'http://www.weblio.jp/content/'.format(urllib.parse.quote(term))

sample_vocab = '自業' #自得だと思わないか' #！夢この前、あの姿勢のまま寝てるの見ましたよ固執流河麻薬所持容疑'

# https://stackoverflow.com/questions/34587346/python-check-if-a-string-contains-chinese-character
# removes latin and hiragana text
def extract_kanji(text):
    """
    returns a unique set of Kanji extracted from the vocab
    """
    kanji_only_set = re.findall(r'[\u4e00-\u9fff]+', text)
    kanji_only_set = ''.join(kanji_only_set)
    # print(set(kanji_only_set))
    return set(kanji_only_set)

# print(extract_kanji(sample_vocab))

def extract_etymology(kanji_set):
    """
    Usage: extract_etymology(extract_kanji(sample_vocab))
    Returns a Single string separated by break lines of all etymologies of the kanji set it is fed

    Args:
        List/Set of Kanji
    Returns:
        String of Etymologies per Kanji
    """
    num_retries = 10  # retries per term
    full_etymology_list = ''
    for kanji in kanji_set:

        site = 'https://www.dong-chinese.com/dictionary/{}'.format(urllib.parse.quote(kanji.encode('utf-8')))

        # try waiting for a while if website returns an error
        try:
            response = urllib.request.urlopen(site)
        except Exception as e:
            for i in range(num_retries):
                try:
                    response = urllib.request.urlopen(site)
                except Exception as e:
                    time.sleep(0.05)


        soup = BeautifulSoup(response, features='html.parser')
        soup_text = str(soup)

        # get only the relevant JS part of dong-chinese which is formatted as a JSON
        soup_text = soup_text.split('<script>window["')[-1].split('__sink__charData_')[-1].split(']=')[-1]
        # returns a pure JSON object
        soup_text = soup_text.split(';</script>')[0]

        dong_text_not_found = '"error":"Word not found"'

        # not and error, i.e. something was actually found inside dong
        if not(dong_text_not_found in soup_text):
            # turn into JSON and parse
            soup_json = json.loads(soup_text)
            try:
                etymology = soup_json['hint']
            # usually KeyError
            except Exception as e:
                etymology = ''
            # try:
            #     decomposition = soup_json['components']
            # except Exception as e:
            #     decomposition = ''

            if etymology:
                # NOTE: you might want to change \n to <br> for Anki HTML
                add_str = kanji + ': ' + etymology + '\n'
                full_etymology_list += add_str

    print(full_etymology_list)
    return full_etymology_list

extract_etymology(extract_kanji(sample_vocab))


if test_in_anki:

    class Regen():
        """Used to organize the work flow to update the selected cards
           Attributes
           ----------
           ed :
               Anki Card browser object
           fids :
               List of selected cards
           completed : int
               Track how many cards were already processed
           """
        def __init__(self, ed, fids):
            self.ed         = ed
            # ed.selectedNotes
            self.fids       = fids
            self.completed  = 0
            # self.config     = mw.addonManager.getConfig(__name__)
            if len(self.fids) == 1:
                # Single card selected, need to deselect it before updating
                self.row = self.ed.currentRow()
                self.ed.form.tableView.selectionModel().clear()
            mw.progress.start(max=len(self.fids), immediate=True)
            mw.progress.update(
                label=label_progress_update,
                value=0)

        def _update_progress(self):
            self.completed += 1
            mw.progress.update(
                label=label_progress_update,
                value=self.completed)
            if self.completed >= len(self.fids):
                mw.progress.finish()
                return

        def generate(self):
            fs = [mw.col.getNote(id=fid) for fid in self.fids]

            for f in fs:
                # empty sentence field (probably very rare)
                if not f[vocab_field]:
                    continue

                vocab = str(f[vocab_field])

                try:
                    # kanji etymology field already contains something
                    if force_update == 'no' and f[kanji_etym_field]:
                        # do nothing, count it as progress
                        self._update_progress()
                        mw.progress.finish()
                        continue

                    # kanji etym field is empty, fill it
                    elif not f[kanji_etym_field]:
                        f[kanji_etym_field] = extract_etymology(extract_kanji(vocab))
                        self._update_progress()
                        mw.progress.finish()

                    elif force_update == 'yes' and f[kanji_etym_field]:
                        f[kanji_etym_field] += extract_etymology(extract_kanji(vocab))
                        self._update_progress()
                        mw.progress.finish()

                    else:
                        pass

                except Exception as e:
                    showInfo('error from generate() function, - {}'.format(str(e)))

                try:
                    f.flush()
                except Exception as e:
                    pass

                # just a fail-safe
                if self.completed >= len(self.fids):
                    mw.progress.finish()
                    showInfo('Extraction done for {} out of {} notes done'.format(
                                                                            self.completed,
                                                                            len(self.fids)
                                                                            ))

                    return

    def setup_menu(ed):
        """
        Add entry in Edit menu
        """
        a = QAction(label_menu, ed)
        a.triggered.connect(lambda _, e=ed: on_regen_vocab(e))
        ed.form.menuEdit.addAction(a)
        a.setShortcut(QKeySequence(keybinding))


    def add_to_context_menu(view, menu):
        """
        Add entry to context menu (right click)
        """
        menu.addSeparator()
        a = menu.addAction(label_menu)
        a.triggered.connect(lambda _, e=view: on_regen_vocab(e))
        a.setShortcut(QKeySequence(keybinding))


    def on_regen_vocab(ed):
        """
        main function
        """
        regen = Regen(ed, ed.selectedNotes())
        regen.generate()
        mw.reset()
        mw.requireReset()

    addHook('browser.setupMenus', setup_menu)
    addHook('browser.onContextMenu', add_to_context_menu)