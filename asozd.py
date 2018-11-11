"""
Definition of ASOZDParser class.
Provides parser logic for docx files.
"""
import io
import shutil
import os
import operator
import re
import json

from pprint import pprint
from DOCX.document import DOCXDocument
from DOCX.items import DOCXParagraph, DOCXDrawing


CONFIG_FILE_NAME = 'parser_config.json'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IN_DIR = '\\in'
OUT_DIR = '\\out'
IMAGES_OUT_DIR = OUT_DIR + '\\images'

DEBUG = True


class ASOZDParser(DOCXDocument):
    """Class for retreiving data from formed docx documents"""

    _debug = False

    def _dbg(self, msg):
        if self._debug:
            pprint(msg)

    def __init__(self, file_name, *args, **kwargs):
        super(ASOZDParser, self).__init__(file_name, *args, **kwargs)

        #if kwargs.get('debug'):
        #    self._debug = (kwargs.get('debug') == True)

        self._line_separator = os.linesep
        if kwargs.get('linesep'):
            self._line_separator = kwargs.get('linesep')

        # file name for docx document
        self.file_name = file_name

        # configuration
        from parser_config import config
        self.config = config

        # list for storing paragraph data
        #self.pStorage = []

        self._init_config()

        self._doc = DOCXDocument(self.file_name)

    def is_debug(self):
        """Returns True is debug mode is switched on, otherwise returns false"""
        return self._debug is True

    @property
    def linesep(self):
        """Operation system specific line separator value"""
        return self._line_separator


    def get_doc(self):
        """Returns reference to Document"""
        return self._doc


    def _init_config(self):
        dct = {}
        for item in self.config['types'].items():
            if item[1].get('check_re'):
                dct[item[1]['check_re']] = item[0]
        self._re_list = dct
        #self._dbg('RE list created:')
        #pprint(self._re_list)

        dct = {}
        for item in self.config['types'].items():
            if item[1].get('check_re'):
                dct[item[1]['order_id']] = item[0]
        self._config_ordered = \
            [self.config['types'][x[1]] for x in sorted(dct.items(), key=operator.itemgetter(0))]
        #self._dbg('Ordered config created:')
        #pprint(self._config_ordered)

        #dct = {}
        #for item in self.config['types'].items():
        #    dct[item[0]] = {
        #        'text': None,
        #        'raw_text': []
        #    }
        #self._results = dct
        self._results = {item[0]: {'text': None, 'raw_text': []}\
            for item in self.config['types'].items()}


    def get_config(self, res_type, key):
        """Returns config 'key' value for specified 'type'"""
        return self.config['types'][res_type].get(key)


    def add_result(self, res_type, text, raw_text=None, replace_check_re_with=None):
        """Adds recognition result to internal storage"""

        replacement = replace_check_re_with
        config_dont_replace = self.get_config(res_type, 'do_not_replace_check_re')

        text_to_save = text

        #raw_text_to_save = [x[0] for x in raw_text]
        if raw_text:
            raw_text_to_save = raw_text.copy()
        else:
            raw_text_to_save = text_to_save.split(self.linesep)

        if not(replacement is None) and not config_dont_replace:
            # replace find pattern string in plain text
            text_to_save = re.sub(self.get_config(res_type, 'check_re'), replacement, text_to_save)

            # replace find pattern string in raw text list
            if raw_text_to_save:
                if re.sub(self.get_config(res_type, 'check_re'),
                          replacement,
                          raw_text_to_save[0]
                         ) == '':
                    self._dbg('Raw-text-to-save element removed %s' % raw_text_to_save[0])
                    raw_text_to_save.pop(0)

        # adding plain text to internal storage
        self._results[res_type]['text'] =\
            (self._results[res_type]['text'] if self._results[res_type]['text'] else '') \
            + text_to_save
        self._results[res_type]['raw_text'] =\
            (self._results[res_type]['raw_text'] if self._results[res_type]['raw_text'] else []) \
            + raw_text_to_save


    def add_result_image(self, res_type, image_name):
        """Adding image data to specific result domain"""
        self._dbg("Adding image %s for recognized %s" % (image_name, res_type))
        if self._results[res_type].get('images'):
            self._results[res_type]['images'].append(image_name)
        else:
            self._results[res_type]['images'] = [image_name]


    def get_fio(self):
        """Returns 'fio' text value for the instance"""
        return self._results['fio']['text'].strip()


    def save_result_images(self, results_dir=None):
        """Copying images from docx zip structure to the destination folder"""
        if self._results['photo'].get('images'):
            for img_name in self._results['photo']['images']:
                self._dbg('Trying to save image: %s' % img_name)

                filename = self.gen_abs_fname_for_result_image(img_name, results_dir)
                if filename:
                    with open(filename, 'wb') as fimg:
                        try:
                            doc = self.get_doc()
                            docx_img = doc.open_docx_image(img_name)
                            shutil.copyfileobj(docx_img, fimg)
                        finally:
                            if docx_img:
                                docx_img.close()
                self._dbg('Image saved.')


    def gen_fname_for_result_json(self, results_dir=None, results_file_name=None):
        """Returns filename for docx parsing results (adding json as the extenstion)"""
        if results_file_name:
            if results_file_name.endswith('.json'):
                filename = results_file_name.replace('.json', '')
            else:
                filename = results_file_name
        else:
            filename = self.get_fio()

        if results_dir:
            out_dir = results_dir if results_dir.endswith('\\') else results_dir + '\\'
        else:
            out_dir = '%s\\%s\\' % (BASE_DIR, OUT_DIR)

        fileext = 'json'
        return '%s\\%s.%s' % (out_dir, filename, fileext)


    def gen_abs_fname_for_result_image(self, original_image_name, results_dir=None):
        """Returns absolute file destination path for image"""
        filepath = self.gen_fname_for_result_image(original_image_name)

        if results_dir:
            out_dir = results_dir if results_dir.endswith('\\') else results_dir + '\\'
        else:
            out_dir = '%s\\' % BASE_DIR

        #if filepath:
        #    return '%s%s' % (out_dir, filepath)
        #else:
        #    return None
        return '%s%s' % (out_dir, filepath) if filepath else None


    def gen_fname_for_result_image(self, original_image_name):
        """Returns destination file name for image"""
        filename = self.get_fio()
        match_res = re.search(r'\.(.+)$', original_image_name)
        if match_res:
            fileext = match_res.groups(1)[0]
            #self._dbg('Image name extenstion: %s' % fileext)
            if fileext:
                return '%s\\%s.%s' % (IMAGES_OUT_DIR, filename, fileext)
        return None


    def get_results_for_save(self):
        """Returns results close to the destination json format. Changing the content if
        th config has a setting "'list_of_strings': True" for the domain or if the config
        has a setting "'is_image': True" for the domain.
        """
        res = {}
        for item in self.config['types'].items():
            if self.config['types'][item[0]].get('list_of_strings') is True:
                #dbg('--->List of Strings: %s' % self._results[item[0]]['raw_text'])
                res[item[0]] = [y for y in self._results[item[0]]['raw_text']]
                #try:
                #    res[item[0]] = [y for y in self._results[item[0]]['raw_text']]
                ##except:
                #    self._dbg('Error data %s:' % self._results[item[0]])
                #    self._dbg(self._results[item[0]])
            elif self.config['types'][item[0]].get('is_image') is True:
                if self._results[item[0]].get('images'):
                    res[item[0]] = [self.gen_fname_for_result_image(img_name)
                                    for img_name in self._results[item[0]]['images']]
            else:
                res[item[0]] = self._results[item[0]]['text']
        return res


    def save_results(self, results_dir=None, results_file_name=None):
        """Saving text results of paragraph uploading to the destination file"""
        filepath = self.gen_fname_for_result_json(results_dir, results_file_name)

        with io.open(filepath, 'w', encoding='utf8') as json_file:
            json.dump(self.get_results_for_save(), json_file, ensure_ascii=False, indent=3)


    def get_internal_results(self):
        """Returns internal results of recognition"""
        return self._results


    def get_ordered_config(self):
        """Return ordered config"""
        return self._config_ordered


    def get_config_str(self):
        """Return config as json"""
        return json.dumps(self.config, indent=4, sort_keys=True)


    #def add_paragraph(self, para):
    #    self.pStorage.append({
    #        'id': para.getId(),
    #        'text': para.getText(),
    #        'ref': para
    #    })

    #def get_paragraphs_text(self, cleaned=True):
    #    if cleaned:
    #        return [p['ref'].getCleanedText() for p in self.pStorage]
    #    else:
    #        return [p['ref'].getText() for p in self.pStorage]

    #def getParagraphsId(self):
    #    return [p['id'] for p in self.pStorage]
#
    #def getParagraphsRefs(self):
    #    return [p['ref'] for p in self.pStorage]


    def recognize_paragraph(self, para):
        """Run process of recognition of paragraph.
        Looping over internal config and applying 'check_re' regular expressions to
        determine type of the paragraph content.
        """
        #dbg('Paragraph text (%s): %s' % (para._item.tag, para.getCleanedText()))
        for regexp in self._re_list.items():
            tmp_re = re.compile(regexp[0])
            self._dbg('Trying to recognize paragraph [%s] as %s with regex %s' % (para.getId(), regexp[1], regexp[0]))
            #self._dbg('Paragraph text: %s' % para.getCleanedText().strip())
            if tmp_re.match(para.getCleanedText().strip()):

                not_re = self.config['types'][regexp[1]].get('not_re')
                if not_re:
                    tmp_not_re = re.compile(not_re)
                    if not tmp_not_re.match(para.getCleanedText().strip()):
                        self._dbg('Paragraph text: '+para.getCleanedText())
                        return regexp[1]
                    else:
                        pass
                else:
                    return regexp[1]

        return None

    def load_paragraphs(self):
        """Load docx paragraphs (one by one) to instance with recognition all of them
        """
        # open file
        document = self._doc

        # load data from file
        document.load()

        # iterate over document paragraphs
        par_iter = 1
        last_recognized_type = None
        #last_recognized_pi = None

        for praw in document.get_doc_paragraphs_iter():

            # dbg - start
            #self._dbg([c.name for c in praw.findChildren(recursive=False)])
            # dbg - stop

            para = DOCXParagraph(praw, docx=document)
            #self.addParagraph(p)
            self._dbg('----> (%02d) Paragraph '% par_iter + para.getId())

            if para.getCleanedText().strip() == '':
                self._dbg('Paragraph %s text is empty. Skipping it.' % para.getId())
                continue

            p_type = self.recognize_paragraph(para)

            if p_type or last_recognized_type:

                # forming paragraph text as joining raw data without any join chars
                par_text = ''.join(para.getRawText())

                # to avoid fragmented values within raw value we split text into strings
                # it is usefull for lobby parsing, because every word in docx could be
                # separated to own element and it is difficult to strip 'check_re' matches
                # from the list where evary word is element
                #raw_text = par_text.split(self.linesep)

                work_type = p_type if p_type else last_recognized_type

                # determine if we have to find something within recognized paragraph
                extra_types_list = self.get_config(work_type, 'also_contains')
                if extra_types_list:

                    self._dbg('Found %d extra types: %s' % \
                        (len(extra_types_list), extra_types_list))
                    for extra_type in extra_types_list:
                        if self.get_config(extra_type, 'is_image'):
                            self._dbg('Try to find images within paragraph')
                            for img in para.getImages():
                                drw = DOCXDrawing(img, docx=document, debug=self.is_debug())
                                img_name = drw.getImageName()
                                self._dbg('Image %s found' % img_name)

                                # adding image to result
                                self.add_result_image(extra_type, img_name)

                        elif self.get_config(extra_type, 'text_re'):
                            self._dbg("Found 'text_re' for %s" % extra_type)
                            self._dbg('Searching [%s] in [%s]' %
                                      (self.get_config(extra_type, 'text_re'), par_text))
                            match_res = re.search(self.get_config(extra_type, 'text_re'), par_text)
                            if match_res:
                                search_res = match_res.group(0).strip()
                                self.add_result(extra_type, search_res)
                                if not self.get_config(extra_type, 'leave_also_contains_data'):
                                    par_text = par_text.replace(search_res, '')

                if p_type:
                    self._dbg('Paragraph recognized as [%s]' % p_type)
                    last_recognized_type = p_type

                    # save result
                    #self.addResult(p_type, par_text, par_raw_text, replace_check_re_with='')
                    self.add_result(p_type, par_text, replace_check_re_with='')
                elif last_recognized_type:
                    self._dbg('Paragraph hasn''t recognized. Add data to the last '+\
                        'recognized as [%s]' % last_recognized_type)
                    self.add_result(last_recognized_type, self.linesep + par_text)
            else:
                self._dbg('Warning! Paragraph iter %d was skipped.' % par_iter)

            par_iter = par_iter + 1
