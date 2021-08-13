# -*- coding: utf-8 -*-
# Copyright: Tanaka Aiko (https://github.com/aiko-tanaka)
# License: GNU AGPL, version 3 or later; https://www.gnu.org/licenses/agpl-3.0.en.html

"""
Online dictionaries and their respective JSON cache methods (if there are any)
"""

from .utils import try_access_site
from .config import config

from bs4 import BeautifulSoup

import urllib.request
import urllib.parse
import json
import os

def tangorin_kanji_info(kanji: str) -> str:
    """
    Usage:
        To be used inside okjiten_etymology
    Args:
        Takes in a single kanji ONLY, not a list
    Returns:
        str: The english definition for the specified Kanji
    """
    response = try_access_site(site='https://tangorin.com/kanji?search={}'
                               .format(urllib.parse.quote(kanji.encode('utf-8'))))
    if response:
        soup = BeautifulSoup(response, features='html.parser')
    else:
        return ''
    if soup:
        en_definitions = soup.find('p', attrs={'class':  'k-meanings'})
    else:
        return ''
    if en_definitions:
        en_definitions = en_definitions.get_text().strip()
    else:
        return ''

    try:
        en_definitions = en_definitions.split('; ')
        # limit num of definitions to only 3 definitions
        if len(en_definitions) > 3:
            en_definitions = en_definitions[:3]
            en_definitions = '; '.join(en_definitions)
        else:
            en_definitions = '; '.join(en_definitions)
    except:
        pass

    return en_definitions if en_definitions else ''


def dong_etymology(kanji_set):
    """
    Usage: dong_etymology(extract_kanji(sample_vocab))
    Returns a Single string separated by break lines of all etymologies of the kanji set it is fed

    Args:
        List/Set of Kanji
    Returns:
        String of Etymologies per Kanji
    """
    full_etymology_list = ''
    for kanji in kanji_set:

        site = f'https://www.dong-chinese.com/dictionary/{urllib.parse.quote(kanji.encode("utf-8"))}'

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
                                              'style': 'padding:8px'} )
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

            full_etymology_list += '<br>'
            if __name__ == '__main__':
                full_etymology_list += '\n'

    # print(full_etymology_list)
    return full_etymology_list


def okjiten_cache(kanji: str = None,
                  kanji_info_to_save: dict = None,
                  save_to_dict = False) -> list or None:
    """
    JSON dict cache

    File formatting:
    The key is the okjiten site index (NOT ANYMORE)

    Just use the kanji itself as the key, they're unique anyway
    {
        '夢':     {
                    'kanji': '夢',
                    'definition': 'dream',
                    'online_img_url': ....
                  },
        '本':     {'kanji': '本', 'definition': 'book', 'online_img_url': ....}
        .....
    }

    checks if a certain kanji's okjiten formatting is already inside the JSON dict
    If there is, then return it

    If there isn't then, wait for the querying to finish and sive it inside the JSON
    Args:
        kanji
        kanji_info_to_save: dict of the kanji info to save
        mode:               (mode 1 = check, mode 2 = write)
    Returns:
        if mode 1:      JSON-formatted okjiten definition
        if mode 2:      none (only saves the JSON to the dictionary)
    """
    kanji_cache_path        = config.get('kanji_cache_path')
    okjiten_cache_filename  = config.get('okjiten_cache_filename')

    # TODO: overwrite specific kanji info if update is set to true
    force_update            = config.get('force_update')
    full_path               = os.path.join(kanji_cache_path, okjiten_cache_filename)

    # create a JSON file if it doesn't exist
    if not os.path.isfile(full_path):
        with open(full_path, 'w') as fh:
            json.dump({}, fh)

    # (mode 2)
    if save_to_dict:
        json_formatted_info = {
            kanji: kanji_info_to_save
        }

        # https://stackoverflow.com/questions/18980039/how-to-append-in-a-json-file-in-python
        with open(full_path, 'r', encoding='utf8') as fh:
            data: dict = json.load(fh)

        data.update(json_formatted_info)

        # https://stackoverflow.com/questions/18337407/saving-utf-8-texts-with-json-dumps-as-utf8-not-as-u-escape-sequence
        with open(full_path, 'w', encoding='utf8') as fh:
            json.dump(data,
                      fh,
                      indent=4,
                      ensure_ascii=False,
                      separators=(',', ': '))

    # (mode 1)
    else:
        # check cache if the kanji exists, if it does, return it

        # the return is none, pass 'True' inside okjiten_cache(save_to_dict)
        # from where it is called
        try:
            with open(full_path, 'r', encoding='utf8') as fh:
                try:
                    cache: dict = json.load(fh)

                    result = cache.get(kanji)
                    return result if result else None

                except json.decoder.JSONDecodeError:
                    return None
        except:
            raise



def okjiten_etymology(kanji_set: list) -> list:
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
        indiv_kanji_info = dict()

        cache = okjiten_cache(kanji, save_to_dict=False)
        if cache is not None:
            indiv_kanji_info = cache
            result_list.append(indiv_kanji_info)
            continue

        sites= [
            'https://okjiten.jp/10-jyouyoukanjiitiran.html',
            'https://okjiten.jp/8-jouyoukanjigai.html', # (kanken pre-1 and 1)
            'https://okjiten.jp/9-jinmeiyoukanji.html']

        for site in sites:

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
                if found:
                    href    = found.get('href') # returns a str
                else:
                    continue
                if href:
                    href    = 'https://okjiten.jp/{}'.format(href)
                else:
                    continue

                kanji_page = try_access_site(href)
                if kanji_page:
                    kanji_soup = BeautifulSoup(kanji_page, features='html.parser')
                else:
                    continue

                # https://github.com/rgamici/anki_plugin_jaja_definitions/blob/master/__init__.py#L86
                # https://beautiful-soup-4.readthedocs.io/en/latest/
                # tables will be reused in the other scrapers
                tables = kanji_soup.find_all('td', attrs={'colspan': 12} )

                if not tables: continue

                # len(TABLES) == 3 ALWAYS!
                for table in tables:
                    kanji_soup = table.find('td', attrs={'height': 100} )
                    if kanji_soup: break

                if not kanji_soup: continue

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

                main_body = tables[2]
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
                        '国字' ]  # check last, not usually found at the start of the sentence, but inside


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

                if cache is None:
                    okjiten_cache(kanji=kanji,
                                  kanji_info_to_save=indiv_kanji_info,
                                  save_to_dict=True)
                break

    # print(result_dict['online_img_url'])
    return result_list

# if __name__ == '__main__':
#     sample_vocab = '参夢紋脅' #統參参夢紋泥恢疎姿勢'  # 自得だと思わないか' #！夢この前、あの姿勢のまま寝てるの見ましたよ固執流河麻薬所持容疑'
#     from pprint import pprint
    # pprint(okjiten_etymology(extract_kanji(sample_vocab)))

    # fids = [{'vocab_field': '参夢'},{'vocab_field': '紋脅'}]
    # regen = Regen(fids=fids)
    # res = regen.generate()
    # pprint(res)

# okjiten_cache(save_to_dict=False)