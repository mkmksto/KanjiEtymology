# -*- coding: utf-8 -*-
# Copyright: Tanaka Aiko (https://github.com/aiko-tanaka)
# License: GNU AGPL, version 3 or later; https://www.gnu.org/licenses/agpl-3.0.en.html

from .consts import LABEL_PROGRESS_UPDATE, LABEL_MENU
from .config import config

from .utils import extract_kanji, download_image, calculate_time_class_method
from .online_dictionaries import okjiten_etymology

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from anki.hooks import addHook
from aqt.utils import showInfo
from aqt import mw


# TODO: better progress dialog lol
# TODO: empty vocab fields sometimes makes it crash
# TODO: doesn't handle 'https://www.dong-chinese.com/dictionary/search/%E8%81%B4', i.e. Japanese variant
# TODO: kanji decomposition tool (https://characterpop.com/) better: https://hanzicraft.com/character/%E5%AE%89
# TODO: (VERY IMP) priority = 2 create a JSON cache file, where before querying, the program checks if it already exists
# inside the json file, if it does exist, skip the URL queries and copy from the JSON file instead
# the first value should be the site/source, if the kanji and site match -> then skip, if the kanji is found
# but the site is diff, then still continue with the query then save the result inside the JSON file
# TODO: check paste image as WEBP to see how he resizes images
# TODO: priority = 3, create another menu bar menu which adds the option to choose whether to scrape from dong or okjiten
# DO something like regen.generate() requires another argument, source
# regen.generate(source='okjiten') would go to another menu option, so would source='dongchinese'
# TODO: search pycharm how to convert functions into a module
# TODO: priority = 4, dynamically determine kanji_etym_field, if Dong menu is selected Set etym field to dong


expression_field    = config.get('expression_field')
vocab_field         = config.get('vocab_field')
kanji_etym_field    = config.get('kanji_etym_field')
keybinding          = config.get('keybinding')
force_update        = config.get('force_update')


class Regen:
    """
    Used to organize the work flow to update the selected cards
    Attributes
    ----------
    ed :
        Anki Card browser object
    fids :
        List of selected cards
    completed : int
        Track how many cards were already processed
    """
    def __init__(self, ed=None, fids=None):
        self.ed         = ed
        # ed.selectedNotes
        self.fids       = fids
        self.completed  = 0
        if len(self.fids) == 1:
            # Single card selected, need to deselect it before updating
            self.row = self.ed.currentRow()
            self.ed.form.tableView.selectionModel().clear()
        mw.progress.start(max=len(self.fids), immediate=True)
        mw.progress.update(
            label=LABEL_PROGRESS_UPDATE,
            value=0)


    def _update_progress(self):
        self.completed += 1
        mw.progress.update(
            label=LABEL_PROGRESS_UPDATE,
            value=self.completed)
        if self.completed >= len(self.fids):
            mw.progress.finish()
            return


    @calculate_time_class_method
    def generate(self):
        """
        Generate Kanji Etymology strings
        """

        if not __name__ == '__main__':
            fs = [mw.col.getNote(id=fid) for fid in self.fids]
        else:
            # if run inside pycharm, self.finds would be a list of vocab
            # fs = [fid for fid in self.fids]
            pass

        for f in fs:
            if __name__ != '__main__':
                # empty vocab field
                if not f[vocab_field]:
                    self._update_progress()
                    continue
            else:
                # vocab = f['vocab_field']
                pass


            vocab = f[vocab_field]
            if vocab:
                vocab = str(vocab)
                kanji_only = extract_kanji(vocab)
            else:
                self._update_progress()
                continue

            if kanji_only:
                etym_info_list = okjiten_etymology(kanji_only)
            else:
                self._update_progress()
                continue

            if not etym_info_list:
                self._update_progress()
                continue

            okjiten_str = ''

            for index, etym_info in enumerate(etym_info_list, start=1):
                etym_info: dict
                kanji           = etym_info.get('kanji')
                definition      = etym_info.get('definition')
                etymology_text  = etym_info.get('etymology_text')
                anki_img_url    = etym_info.get('anki_img_url')
                online_img_url  = etym_info.get('online_img_url')

                try:
                    src = etym_info.get('src')
                    LABEL_PROGRESS_UPDATE = '{} from {}'.format(LABEL_PROGRESS_UPDATE, src)
                except:
                    pass

                image_filename  = etym_info.get('image_filename')

                kanji_and_def = '{}({})'.format(kanji, definition)

                download_image(online_img_url, image_filename)

                # use <pseudo-newline> for JS-splitting inside anki because I already use <br> inside
                # etymology_text  = etym_info['etymology_text'] to replace the character '※'
                if index < len(etym_info_list):
                    okjiten_str += '{} | {} | {}<pseudo-newline>'.format(kanji_and_def, anki_img_url, etymology_text)
                elif index == len(etym_info_list):
                    okjiten_str += '{} | {} | {}'.format(kanji_and_def, anki_img_url, etymology_text)

            okjiten_str = okjiten_str.replace(r'\n', '').strip()

            # the vocab might not contain any Kanji AT ALL
            if not okjiten_str:
                self._update_progress()
                continue

            try:
                # kanji etymology field already contains something
                if force_update is False and f[kanji_etym_field]:
                    # do nothing, count it as progress
                    self._update_progress()
                    # mw.progress.finish()
                    continue

                # kanji etym field is empty, fill it
                elif not f[kanji_etym_field]:
                    f[kanji_etym_field] = okjiten_str
                    self._update_progress()
                    # mw.progress.finish()

                elif force_update and f[kanji_etym_field]:
                    f[kanji_etym_field] = okjiten_str
                    self._update_progress()
                    # mw.progress.finish()

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
    a = QAction(LABEL_MENU, ed)
    a.triggered.connect(lambda _, e=ed: on_regen_vocab(e))
    ed.form.menuEdit.addAction(a)
    a.setShortcut(QKeySequence(keybinding))


def add_to_context_menu(view, menu):
    """
    Add entry to context menu (right click)
    """
    menu.addSeparator()
    a = menu.addAction(LABEL_MENU)
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

if __name__ == '__main__':
    sample_vocab = '参夢紋脅' #統參参夢紋泥恢疎姿勢'  # 自得だと思わないか' #！夢この前、あの姿勢のまま寝てるの見ましたよ固執流河麻薬所持容疑'
    from pprint import pprint
    # pprint(okjiten_etymology(extract_kanji(sample_vocab)))

    # fids = [{'vocab_field': '参夢'},{'vocab_field': '紋脅'}]
    # regen = Regen(fids=fids)
    # res = regen.generate()
    # pprint(res)