import argparse
from bs4 import BeautifulSoup, element
from pprint import pprint, PrettyPrinter
import abc
import re
import json
import operator
import shutil
import os, sys, io

#from stat import *
from stat import ST_MODE, S_ISDIR, S_ISREG
from DOCX import DOCXDocument, DOCXParagraph, DOCXItem




BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IN_DIR = '\in'
OUT_DIR = '\out'
IMAGES_OUT_DIR = OUT_DIR + '\images'




# Useful queries:
# open('parser_config.json', 'w').write(json.dumps(P, indent=4))

DEBUG = True

def dbg(msg):
    global DEBUG
    if DEBUG: 
        pprint(msg)



class ASOZDParser(DOCXDocument):

    #ФИО
    #Фото нужно сохранить отдельным файлом (рядом с json, например)
    #Должность/позиция - текст
    #Фракция, членство в комитетах - текст
    #Биография - текст с ссылками внутри
    #Внесенные законопроекты - текст с внешними гиперссылками
    #Аффиляция, связи - текст с внешними гиперссылками (Доноры депутата в 2016 году идут сюда)
    #семейное положение - текст 
    #Выводы - текст с внешними гиперссылками
    #Группа лоббистов - массив строк

    CONFIG_FILE_NAME = 'parser_config.json'

    def __init__(self, file_name):

        # file name for docx document
        self.file_name = file_name

        # configuration
        #self.config = json.loads(open(self.CONFIG_FILE_NAME, 'r').read())
        from parser_config import config
        self.config = config
        
        # list for storing paragraph data
        self.pStorage = []

        self._init_config()

        self._doc = DOCXDocument(self.file_name)

    def getDoc(self):
        return self._doc


    def _init_config(self):
        D = {}
        for z in self.config['types'].items():
            if z[1].get('check_re'): D[z[1]['check_re']] = z[0]
        self._re_list = D
        #dbg('RE list created:')
        #pprint(self._re_list)

        D = {}
        for z in self.config['types'].items():
            if z[1].get('check_re'): D[z[1]['order_id']] = z[0]
        self._config_ordered = [self.config['types'][x[1]] for x in sorted(D.items(), key=operator.itemgetter(0))]
        #dbg('Ordered config created:')
        #pprint(self._config_ordered)

        D = {}
        for z in self.config['types'].items():
            D[z[0]] = {
                'text': None,
                'raw_text': []
            }
        self._results = D

    def get_config(self, type, key):
        """Returns config 'key' value for specified 'type'"""
        return self.config['types'][type].get(key)

    def addResult(self, type, text, raw_text=None, replace_check_re_with=None):
        """Adds recognition result to internal storage"""

        replacement = replace_check_re_with
        config_dont_replace = self.get_config(type, 'do_not_replace_check_re')
        
        #pp = PrettyPrinter()
        #print('addResult(type=%s, text=%s, raw_text=%s, replace_check_re_with=%s)' % (
        #    type,
        #    pp.pformat(text),
        #    pp.pformat(raw_text),
        #    pp.pformat(replace_check_re_with)
        #))

        text_to_save = text.strip()
        #raw_text_to_save = [x[0] for x in raw_text]
        raw_text_to_save = raw_text.copy()

        #dbg('>>> replacement: %s; config_dont_replace: %s' % (replacement, config_dont_replace))

        if not(replacement is None) and not config_dont_replace:
            # replace find pattern string in plain text
            text_to_save = re.sub(self.config['types'][type]['check_re'], replacement, text_to_save)

            # replace find pattern string in raw text list
            if raw_text_to_save:
                if re.sub(self.config['types'][type]['check_re'], replacement, raw_text_to_save[0]) == '':
                    dbg('Raw-text-to-save element removed %s' % raw_text_to_save[0])
                    raw_text_to_save.remove(raw_text_to_save[0])
        
        # adding plain text to internal storage
        if self._results[type]['text']:
            self._results[type]['text'] = self._results[type]['text'] + text_to_save
        else:
            self._results[type]['text'] = text_to_save
        
        # adding raw text list to internal storage
        if type == 'lobby':
            print('raw_text = %s' % raw_text)
            print('raw_text_to_save = %s' % raw_text_to_save)
        if raw_text:
            if raw_text_to_save:
                # it is possible that raw_text contain a string with line separators (come from w:br)
                # here we split this kind of text
                tmp = []
                for y in [x.split(os.linesep) for x in raw_text_to_save]:
                    if type == 'lobby':
                        print('Iterating [%s]' % y)
                    if y != "":
                        tmp = tmp + y
                
                self._results[type]['raw_text'] = self._results[type]['raw_text'] + [x for x in tmp if x != ""]
        else:
            self._results[type]['raw_text'].append(text_to_save.split(os.linesep))

    def addResultImage(self, type, image_name):
        dbg("Adding image %s for recognized %s" % (image_name, type))
        if self._results[type].get('images'):
            self._results[type]['images'].append(image_name)
        else:
            self._results[type]['images'] = [image_name]
    
    def getFIO(self):
        return self._results['fio']['text'].strip()

    def saveResultImages(self):
        if self._results['photo'].get('images'):
            for img_name in self._results['photo']['images']:
                dbg('Trying to save image: %s' % img_name)

                filename = self.genAbsFnameForResultImage(img_name)
                if filename:
                    with open(filename, 'wb') as fimg:
                        try:
                            doc = self.getDoc()
                            docx_img = doc.openDocxImage(img_name)
                            shutil.copyfileobj(docx_img, fimg)
                        finally:
                            docx_img.close()
                dbg('Image saved.')

    def genFnameForResultJson(self):
        filename = self.getFIO()
        fileext = 'json'
        return '%s\%s\%s.%s' % (BASE_DIR, OUT_DIR, filename, fileext)

    def genAbsFnameForResultImage(self, original_image_name):
        filepath = self.genFnameForResultImage(original_image_name)
        if filepath:
            return '%s\%s' % (BASE_DIR, filepath)
        else:
            return None

    def genFnameForResultImage(self, original_image_name):
        filename = self.getFIO()
        m = re.search(r'\.(.+)$', original_image_name)
        if m:
            fileext = m.groups(1)[0]
            #dbg('Image name extenstion: %s' % fileext)
            if fileext:
                return '%s\%s.%s' % (IMAGES_OUT_DIR, filename, fileext) 
        return None



    def getResultsForSave(self):
        res = {}
        for x in self.config['types'].items():
            if self.config['types'][x[0]].get('list_of_strings') == True:
                #dbg('--->List of Strings: %s' % self._results[x[0]]['raw_text'])
                try:
                    res[x[0]] = [y for y in self._results[x[0]]['raw_text']]
                except:
                    pprint('Error data %s:' % self._results[x[0]])
                    pprint(self._results[x[0]])
            elif self.config['types'][x[0]].get('is_image') == True:
                if self._results[x[0]].get('images'):
                    res[x[0]] = [self.genFnameForResultImage(img_name) for img_name in self._results[x[0]]['images']]
            else:
                res[x[0]] = self._results[x[0]]['text']
        return res


    def saveResults(self):
        filepath = self.genFnameForResultJson()
        #open(filepath, 'w').write(json.dumps(self.getResults(), indent=3))

        with io.open(filepath, 'w', encoding='utf8') as json_file:
            json.dump(self.getResultsForSave(), json_file, ensure_ascii=False, indent=3)

    def getInternalResults(self):
        return self._results

    def getConfig(self):
        return self.config

    def getOrderedConfig(self):
        return self._config_ordered 

    def getConfigStr(self):
        return json.dumps(self.config, indent=4, sort_keys=True)

    def addParagraph(self, p):
        self.pStorage.append({
            'id': p.getId(),
            'text': p.getText(),
            'ref': p
        })

    def getParagraphsText(self, cleaned=True):
        if cleaned:
            return [p['ref'].getCleanedText() for p in self.pStorage]
        else:
            return [p['ref'].getText() for p in self.pStorage]

    def getParagraphsId(self):
        return [p['id'] for p in self.pStorage]

    def getParagraphsRefs(self):
        return [p['ref'] for p in self.pStorage]

    def recognizeParagraph(self, p):
        #dbg('Paragraph text (%s): %s' % (p._item.tag, p.getCleanedText()))
        for r in self._re_list.items():
            tmp_re = re.compile(r[0])
            #dbg('Trying to recognize paragraph [%s] as %s with regex %s' % (p.getId(), r[1], r[0]))
            if tmp_re.match(p.getCleanedText().strip()):

                not_re = self.config['types'][r[1]].get('not_re')
                if not_re:
                    tmp_not_re = re.compile(not_re)
                    if not tmp_not_re.match(p.getCleanedText().strip()):
                        #dbg('Paragraph text: '+p.getCleanedText())
                        return r[1]
                    else:
                        pass
                else:
                    return r[1]
            
        return None

    def loadParagraphs(self):
        
        # open file
        Doc = self._doc

        # load data from file
        Doc.load()
        
        # iterate over document paragraphs
        pi = 1
        last_recognized_type = None
        #last_recognized_pi = None

        for praw in Doc.getDocParagraphsIter():

            # dbg - start
            #dbg([c.name for c in praw.findChildren(recursive=False)])
            # dbg - stop

            p = DOCXParagraph(praw, docx=Doc)
            self.addParagraph(p)
            dbg('----> (%02d) Paragraph '%pi + p.getId())
            
            if p.getCleanedText().strip() == '':
                dbg('Paragraph %s text is empty. Skipping it.' % p.getId())
                continue
            
            p_type = self.recognizeParagraph(p)

            if p_type or last_recognized_type:

                par_text = p.getText()
                par_raw_text = p.getRawText()

                work_type = p_type if p_type else last_recognized_type

                # determine if we have to find something within recognized paragraph
                extra_types_list = self.get_config(work_type, 'also_contains')
                if extra_types_list:

                    dbg('Found %d extra types: %s' % (len(extra_types_list), extra_types_list))
                    
                    for extra_type in extra_types_list:
                        if self.get_config(extra_type, 'is_image'):
                            dbg('Try to find images within paragraph')
                            for img in p.getImages():
                                drw = DOCXItem.factory(img, docx=Doc)
                                img_name = drw.getImageName()
                                dbg('Image %s found' % img_name)
                                self.addResultImage(extra_type, img_name)

                        elif self.get_config(extra_type, 'text_re'):
                            print('Found text_re for %s' % extra_type)
                            print('Searching [%s] in [%s]' % (self.get_config(extra_type, 'text_re'), par_text))
                            m = re.search(self.get_config(extra_type, 'text_re'), par_text)
                            if m:
                                search_res = m.group(0).strip()
                                self.addResult(extra_type, search_res, [search_res])
                                if not self.get_config(extra_type, 'leave_also_contains_data'):
                                    par_text = par_text.replace(search_res, '')
                                
                if p_type:
                    # start of docx part which could be related to 
                    # one of the target data parts
                    dbg('Paragraph recognized as [%s]' % p_type)

                    last_recognized_type = p_type
                    
                    # save main recognition result
                    self.addResult(p_type, par_text, par_raw_text, replace_check_re_with='')
                elif last_recognized_type:
                    dbg('Paragraph hasn''t recognized. Add data to the last recognized as [%s]' % last_recognized_type)
                    self.addResult(last_recognized_type, par_text, par_raw_text)
            else:
                print('Warning! Paragraph iter %d was skipped.' % pi)
            
            pi = pi + 1


if __name__ == '__main__':
    # arguments definition
    parser = argparse.ArgumentParser(description="""Convert ASOZD details docx into json.

Example (Windows): python parser.py "in"
                   python parser.py "filename.docx"
                   
Example (Unix): ./parser.py "in"
                ./parser.py "filename.docx\"""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('fname', metavar='fileName', type=str, help='Filename or directory with *.docx files for processing')
    args = parser.parse_args()

    try:
        mode = os.stat(args.fname)[ST_MODE]
    except FileNotFoundError:
        raise ValueError("Couldn't determine is [%s] a folder or file. Possible " % args.fname +\
            "the name is incorrect. Please verify.")

    is_directory = False
    if S_ISDIR(mode):
        # directory
        print('Directory detected: %s' % args.fname)
        target_list = os.listdir(args.fname)
        is_directory = True
    elif S_ISREG(mode):
        # file
        print('File detected: %s' % args.fname)
        target_list = [args.fname]
    else:
        raise ValueError("fileName [%s] contains non folder and non file value")

    for fname in target_list:
        if not fname.endswith('.docx') or fname.startswith('~$'):
            print('Skipping %s as non supportable file.' % fname)
            continue

        print('Looking %s file for valuable content.' % fname)
        # parser init
        P = ASOZDParser(args.fname + '\\' + fname if is_directory else args.fname)
        
        # parse start
        P.loadParagraphs()

        #pprint(P.getInternalResults())

        P.saveResults()
        P.saveResultImages()
