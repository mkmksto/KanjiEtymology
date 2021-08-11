# -*- coding: utf-8 -*-
# Copyright: Tanaka Aiko (https://github.com/aiko-tanaka)
# License: GNU AGPL, version 3 or later; https://www.gnu.org/licenses/agpl-3.0.en.html

from bs4 import BeautifulSoup
from collections import OrderedDict

from pprint import pprint

from .consts import LABEL_PROGRESS_UPDATE, LABEL_MENU

import urllib.request
import urllib.parse
import requests
import json
import time
import re
import os

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

test_in_anki = True

if test_in_anki:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from anki.hooks import addHook
    from aqt.utils import showInfo
    from aqt import mw

    # TODO: move to config.py
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
        kanji_etym_field = "Okjiten_Kanji_Etym"
        keybinding = ""  # nothing by default
        force_update = "no"

# MEDIA_STORAGE = r'D:\TeMP\1_!_!_!_TEMP\Z_trash_Anki_media'

# TODO: (VERY IMPORTANT) priority = 1 FIND THIS DYNAMICALLY BASED ON WHICH PROFILE YOU ARE ON!
# TODO: move to config.py
MEDIA_STORAGE = r'C:\Users\Mi\AppData\Roaming\Anki2\User 1\collection.media'

# https://stackoverflow.com/questions/34587346/python-check-if-a-string-contains-chinese-character
def extract_kanji(text):
    """
    returns a unique set/list of Kanji extracted from the vocab
    also removes latin and hiragana text
    https://stackoverflow.com/questions/480214/how-do-you-remove-duplicates-from-a-list-whilst-preserving-order
    """
    if text:
        kanji_only_set = re.findall(r'[\u4e00-\u9fff]+', text)
        kanji_only_set = ''.join(kanji_only_set)
        return list(OrderedDict.fromkeys(kanji_only_set))
    else:
        return []

def try_access_site(site, sleep_time=0.1, num_retries=10):
    response = None
    try:
        response = urllib.request.urlopen(site)

    except Exception as e:
        for i in range(num_retries):
            try:
                response = urllib.request.urlopen(site)
            except Exception as e:
                time.sleep(sleep_time)
    finally:
        return response

def bs_remove_html(html):
    """
    https://www.geeksforgeeks.org/remove-all-style-scripts-and-html-tags-using-beautifulsoup/
    """
    soup = BeautifulSoup(html, "html.parser")

    for data in soup(['style', 'script']):
        # Remove tags
        data.decompose()

    # return data by retrieving the tag content
    return ' '.join(soup.stripped_strings)

def download_image(online_url, filename):
    """
    https://stackoverflow.com/questions/37158246/how-to-download-images-from-beautifulsoup
    filename: the name of the file to be saved as, usually diff from the online_url because I added a string preceding it
    """
    complete_file_location = os.path.join(MEDIA_STORAGE, filename)
    if not os.path.isfile(complete_file_location):
        try:
            with open(complete_file_location, 'wb') as f:
                request = None
                try:
                    request = requests.get(online_url)
                except:
                    for i in range(10):
                        try:
                            request = requests.get(online_url)
                        except Exception as e:
                            time.sleep(0.1)
                finally:
                    if request:
                        f.write(request.content)

        except Exception as e:
            # showInfo('Could not save image {} because {}'.format(filename, e) )
            pass
    else:
        print('file already exists')
        pass

def tangorin_kanji_info(kanji):
    """
    Usage:
        To be used inside okjiten_etymology
    Args:
        Takes in a single kanji ONLY, not a list
    https://tangorin.com/kanji?search=%E5%8F%82
    """
    response = try_access_site(
        site='https://tangorin.com/kanji?search={}'.format(urllib.parse.quote(kanji.encode('utf-8')))
    )
    soup = BeautifulSoup(response, features='html.parser')
    en_definitions = soup.find('p', attrs={'class':  'k-meanings'})
    en_definitions = en_definitions.get_text().strip()
    try:
        en_definitions = en_definitions.split('; ')
        # limit num of definitions to only 3 defs
        if len(en_definitions) > 3:
            en_definitions = en_definitions[:3]
            en_definitions = '; '.join(en_definitions)
        else:
            en_definitions = '; '.join(en_definitions)
    except:
        pass
    if not en_definitions: en_definitions = ''
    return en_definitions

def dong_etymology(kanji_set):
    """
    Usage: dong_etymology(extract_kanji(sample_vocab))
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
        response = ''
        response = try_access_site(site=site, sleep_time=0.05)

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

            try:
                # <div class="MuiGrid-root MuiGrid-item MuiGrid-grid-xs-12" style="padding:8px">
                definition = soup.find('div',
                                       attrs={'class': 'MuiGrid-root MuiGrid-item MuiGrid-grid-xs-12',
                                              'style': 'padding:8px'}
                                       )
                definition = str(definition).split('<span><span><span>')[-1].split('</span></span><a href=')[0]

                # get only one keyword from the many keywords separated by ; and or ,
                if ';' in definition:
                    definition = definition.split('; ')[0]
                    if ',' in definition:
                        definition = definition.split(', ')[0]
                elif ',' in definition:
                    definition = definition.split(', ')[0]

            except Exception as e:
                definition = ''

            try:
                decomposition = soup_json['components']
            except Exception as e:
                decomposition = ''


            # concatenate the strings
            concat_str = '<b>{}</b>'.format(kanji)
            full_etymology_list += concat_str

            if definition:
                add_str = '({}): '.format(definition)
                full_etymology_list += add_str
            else:
                full_etymology_list += ': '

            if etymology:
                full_etymology_list += etymology

            # decomposition is a list of DICT objects
            # e.g. "components":[  {"character":"木","type":["iconic"],"hint":null},
            # {"character":"◎","type":["iconic"],"hint":"Depicts roots."}   ]
            if decomposition:
                # decom_json_list = [json.loads(decom) for decom in decomposition]
                for decom in decomposition:
                    try:
                        char = str(decom['character'])
                    except Exception as e:
                        char =''

                    try:
                        func = str(decom['type'])
                    except Exception as e:
                        func = ''

                    try:
                        hint = str(decom['hint'])
                    except:
                        hint = ''

                    add_str_decom = ' [{}-{}-{}]'.format(char, func, hint)
                    full_etymology_list += add_str_decom

            # \n when testing inside pycharm, <br> when inside Anki
            if test_in_anki:
                full_etymology_list += '<br>'
            else:
                full_etymology_list += '\n'

    # print(full_etymology_list)
    return full_etymology_list

def okjiten_json_dict(kanji, save_to_dict=True):
    """
    checks if a certain kanji's okjiten formatting is already inside the JSON dict
    If there is, then return it

    If there isn't then, wait for the querying to finish and sive it inside the JSON
    Args:
        kanji
        mode (mode 1 = check, mode 2 = write)
    Returns:
        if mode 1: JSON-formatted okjiten definition
        if mode 2: none (only saves the JSON to the dictionary)
    """
    if save_to_dict:
        pass
    else:
        pass

def okjiten_etymology(kanji_set):
    """
        Usage: okjiten_etymology(extract_kanji(sample_vocab))

        Note: this won't return the image itself, only the online source and its anki src format
        You'll have to use download_image() wherever your main funciton is

        Also, won't return a neat string, you have to format it yourself to turn it into a string
        why? because the return can be neatly stored in a JSON file for chaching/querying

        you then loop through the result like:

        for res in result_list:
            kanji       = res['kanji']
            etymology   = res['etymology_text']
            etc...

        Args:
            List/Set of Kanji
        Returns:
            LIST of JSONs/Dicts
            each JSON/dict containing: (as dict properties)
                name/kanji itself       :   kanji
                definition              :   kanji definition
                online image URL        :   online_img_url
                anki image src URL      :   anki_img_url
                etymology_text          :   etymology_text
                src                     :   okijiten (constant) - for use when searching JSON files
                onyomi
                kunyomi
                bushu
        """

    result_list = []

    for kanji in kanji_set:
        sites= [
            'https://okjiten.jp/10-jyouyoukanjiitiran.html',
            'https://okjiten.jp/8-jouyoukanjigai.html', # (kanken pre-1 and 1)
            'https://okjiten.jp/9-jinmeiyoukanji.html']

        indiv_kanji_info = {}
        for site in sites:

            # try waiting for a while if website returns an error
            response = ''
            response = try_access_site(site)

            soup = BeautifulSoup(response, features='html.parser')
            if kanji in str(soup) and soup:
                print('found {} from {}'.format(kanji, site))

                indiv_kanji_info['kanji']       = kanji
                indiv_kanji_info['definition']  = (tangorin_kanji_info(kanji))

                # for some stupid reason, it can't match for kanji like 参, but will match its kyuujitai 參
                # TODO, if exception, try searching for its kyuujitai counterpart, look for a website that does that
                # or might be nvm because for some reason it werks now

                ### ------------------------ START (1) ------------------------
                ### (1) scrape the 成り立ち image table

                found       = soup.find('a', text=kanji)
                href        = found.get('href') # returns a str
                href        = 'https://okjiten.jp/{}'.format(href)

                kanji_page  = try_access_site(href)
                kanji_soup  = BeautifulSoup(kanji_page, features='html.parser')

                # https://github.com/rgamici/anki_plugin_jaja_definitions/blob/master/__init__.py#L86
                # https://beautiful-soup-4.readthedocs.io/en/latest/
                # tables will be reused in the other scrapers
                TABLES = kanji_soup.find_all('td', attrs={'colspan': 12} )

                # len(TABLES) == 3 ALWAYS!
                for table in TABLES:
                    kanji_soup = table.find('td', attrs={'height': 100})
                    if kanji_soup: break

                etymology_image_src             = kanji_soup.find('img')
                try:
                    etymology_image_src         = etymology_image_src.get('src')
                # AttributeError: 'NoneType' object has no attribute 'get'
                except Exception as e:
                    etymology_image_src         = ''
                etymology_image_url             = 'https://okjiten.jp/{}'.format(etymology_image_src)

                # use image_filename for downloading and storing the media
                # add _ before img filename before anki keeps deleting these GIFs
                # could be because I use them inside a JS script
                image_filename                  = '_okijiten-{}'.format(etymology_image_src)
                anki_image_src                  = '<img src = "{}">'.format(image_filename)

                indiv_kanji_info['image_filename']      = image_filename
                indiv_kanji_info['online_img_url']      = etymology_image_url
                indiv_kanji_info['anki_img_url']        = anki_image_src
                # download_image(online_url=etymology_image_url, filename=image_filename)
                ### ------------------------ END (1) ------------------------
                # TODO: scrape the image and put it inside the media folder, try to resize it if u can


                ### ------------------------ START (2) ------------------------
                ### (2) scrape the 成り立ち text table / usually https://okjiten.jp/{}#a
                # do a findall and the etym text is always the 3rd table row from the top, etc., this is always the same
                # the 3rd table - TABLES[2] always contains the main content

                main_body = TABLES[2]
                th = main_body.find('th', attrs={'align': 'left'})

                def_text = ''
                if th:
                    th          = BeautifulSoup(str(th), features='html.parser')
                    etymology   = th.get_text().strip()
                    etymology   = ''.join(etymology.split())
                    etymology   = etymology.replace('※', '<br>') # for anki

                    def_text    += etymology

                else:
                    # there are cases where len(th)==0, usually it uses a td instead of a th
                    # sample: https://okjiten.jp/kanji1408.html(脅)
                    # in such cases, just go through every tr, and find what is relevant

                    # http://nihongo.monash.edu/kanjitypes.html (6 kanji types) (only 4 are on the site)
                    kanji_class = [
                        '象形文字',  # pictographs/hieroglyphs
                        '指事文字',  # "logograms", "simple ideographs", representation of abstract ideas
                        '会意文字',  # compound ideograph e.g. 休 (rest) from 人 (person) and 木 (tree
                        '会意兼形声文字',  # compound ideo + phono-semantic at the same time
                        '形声文字',  # semasio-phonetic"
                        '国字',  # check last, not usually found at the start of the sentence, but inside
                         ]

                    tr = main_body.find_all('tr')
                    # tr[7] is usually the .gif for the etymology image, tr[8] is etymology text

                    if tr:
                        etymology = tr[8]

                        etymology = BeautifulSoup(str(etymology), features='html.parser')
                        etymology = etymology.get_text().strip()

                        if any(class_ in etymology for class_ in kanji_class):
                            etymology   = ''.join(etymology.split())
                            etymology   = etymology.replace('※', '<br>')  # for anki
                            def_text    += etymology

                indiv_kanji_info['etymology_text']  = def_text
                indiv_kanji_info['src']             = 'okijiten'
                ### ------------------------ END (2) ------------------------

                # TODO
                ### (3) scrape the 読み table / usually https://okjiten.jp/{}#b
                # TODO
                ### (4) scrape the 部首 table / usually https://okjiten.jp/{}#c

                # break out for site for sites loop -> if kanji in str(soup) and soup:
                # because if the kanji is inside the site, no need to go over the other sites
                # as such this for loop only runs one if the kanji is within the site at first try
                result_list.append(indiv_kanji_info)
                break

    # print(result_dict['online_img_url'])
    return result_list


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
    def __init__(self, ed=None, fids=None):
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
                    # self._update_progress()
                    continue
            else:
                # vocab = f['vocab_field']
                pass


            vocab = str(f[vocab_field])

            # etymology = dong_etymology(extract_kanji(vocab))

            etym_info_list = okjiten_etymology(extract_kanji(vocab))

            okjiten_str = ''

            for index, etym_info in enumerate(etym_info_list, start=1):
                kanji           = etym_info['kanji']
                definition      = etym_info['definition']
                etymology_text  = etym_info['etymology_text']
                anki_img_url    = etym_info['anki_img_url']
                online_img_url  = etym_info['online_img_url']

                try:
                    src = etym_info['src']
                    LABEL_PROGRESS_UPDATE = '{} from {}'.format(LABEL_PROGRESS_UPDATE, src)
                except:
                    pass

                image_filename  = etym_info['image_filename']

                kanji_and_def = '{}({})'.format(kanji, definition)

                download_image(online_img_url, image_filename)

                # use <pseudo-newline> for JS-splitting inside anki because I already use <br> inside
                # etymology_text  = etym_info['etymology_text'] to replace the character '※'
                if index < len(etym_info_list):
                    okjiten_str += '{} | {} | {}<pseudo-newline>'.format(kanji_and_def, anki_img_url, etymology_text)
                elif index == len(etym_info_list):
                    okjiten_str += '{} | {} | {}'.format(kanji_and_def, anki_img_url, etymology_text)

            # # h = header, b = body, f = footer
            # h =  """<table class="etym_table">
            #             <tbody>"""
            #
            # b = ''
            # for etym_info in etym_info_list:
            #     kanji           = etym_info['kanji']
            #     definition      = etym_info['definition']
            #     etymology_text  = etym_info['etymology_text']
            #     anki_img_url    = etym_info['anki_img_url']
            #     online_img_url  = etym_info['online_img_url']
            #
            #     image_filename  = etym_info['image_filename']
            #
            #     download_image(online_img_url, image_filename)
            #
            #     kanji_and_def   = kanji + definition
            #
            #     b +=    """"
            #             <tr>
            #                 <td>{}</td>
            #                 <td>{}</td>
            #                 <td>{}</td>
            #             </tr>""".format(
            #                         kanji_and_def,
            #                         anki_img_url,
            #                         etymology_text
            #                         )
            # f =     """</tbody>
            #     </table>"""
            #
            # okjiten_str = h + b + f


            # if __name__ == '__main__':
            #     return okjiten_str


            okjiten_str = okjiten_str.replace(r'\n', '').strip()

            # the vocab might not contain any Kanji AT ALL
            if not okjiten_str:
                self._update_progress()
                continue

            try:
                # kanji etymology field already contains something
                if force_update == 'no' and f[kanji_etym_field]:
                    # do nothing, count it as progress
                    self._update_progress()
                    # mw.progress.finish()
                    continue

                # kanji etym field is empty, fill it
                elif not f[kanji_etym_field]:
                    f[kanji_etym_field] = okjiten_str
                    self._update_progress()
                    # mw.progress.finish()

                elif force_update == 'yes' and f[kanji_etym_field]:
                    f[kanji_etym_field] += okjiten_str
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


if test_in_anki:
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
    # pprint(okjiten_etymology(extract_kanji(sample_vocab)))

    # fids = [{'vocab_field': '参夢'},{'vocab_field': '紋脅'}]
    # regen = Regen(fids=fids)
    # res = regen.generate()
    # pprint(res)