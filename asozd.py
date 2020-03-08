"""
Definition of ASOZDParser class.
Provides parser logic for docx files.
"""
import io
import json
import logging
import operator
import os
import re
import shutil
from typing import Dict

from docx.document import DOCXDocument
from docx.items import DOCXDrawing, DOCXParagraph


logger = logging.getLogger(__name__)

# CONFIG_FILE_NAME = r'parser_config.json'
CONFIG_FILE_NAME = r'config.json'

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
IN_DIR = r'in'
OUT_DIR = r'out'
IMAGES_OUT_DIR = r'images'


class ASOZDConfig(object):

    CRE = re.compile(r'.*_re$')

    def __init__(self, *args, **kwargs):
        # for somehow the instance will have the conif at the moment
        data = self.__getattribute__('_data')
        if data:
            self.data = data

        if self.data:
            self._init_re()

    @property
    def data(self):
        return self._data

    def _init_re(self):
        # two level hierarchy configs are only supported:
        for tl in self._data.keys():
            if isinstance(self._data[tl], Dict):
                for sl in [self._data[tl][k]
                           for k in self._data[tl].keys() if self.CRE.match(k)]:
                    logger.debug(
                        'Compiling re for the path: /%s/%s...', tl, sl
                    )
                    self._data[tl][sl] = re.compile(self._data[tl][sl])


class ASOZDConfigOld(ASOZDConfig):

    def __init__(self, *args, **kwargs):
        from parser_config import config
        self._data = config

        super(ASOZDConfigNew, self).__init__(*args, **kwargs)


class ASOZDConfigNew(ASOZDConfig):

    def __init__(self, config_file=None, *args, **kwargs):
        if not config_file:
            logger.warning('Config file didn\'t received. Using '
                           'default config: [%s]', CONFIG_FILE_NAME)
            config_file = os.path.abspath(CONFIG_FILE_NAME)

        with open(config_file, 'r', encoding='utf-8') as fp:
            self._data = json.load(fp)

        super(ASOZDConfigNew, self).__init__(*args, **kwargs)


class ASOZDParser(DOCXDocument):
    """Class for retreiving data from formed docx documents"""

    def __init__(self, file_name, *args, **kwargs):
        super(ASOZDParser, self).__init__(file_name, *args, **kwargs)

        self._line_separator = os.linesep
        if kwargs.get('linesep'):
            self._line_separator = kwargs.get('linesep')

        # file name for docx document
        self.file_name = file_name

        # configuration
        self.config = ASOZDConfigNew().data

        # list for storing paragraph data
        # self.pStorage = []

        self._init_config()

        self._doc = DOCXDocument(self.file_name)

    @property
    def linesep(self):
        """Operation system specific line separator value"""
        return self._line_separator

    def get_doc(self):
        """Returns reference to Document"""
        return self._doc

    def _init_config(self):
        dct = {}
        for item in self.config['sections'].items():
            if item[1].get('check_re'):
                dct[item[1]['check_re']] = item[0]
        self._re_list = dct

        dct = {}
        for item in self.config['sections'].items():
            if item[1].get('check_re'):
                dct[item[1]['order_id']] = item[0]
        zero_get = operator.itemgetter(0)
        self._config_ordered = \
            [self.config['sections'][x[1]]
             for x in sorted(dct.items(), key=zero_get)]

        # dct = {}
        # for item in self.config['sections'].items():
        #     dct[item[0]] = {
        #         'text': None,
        #         'raw_text': []
        #     }
        # self._results = dct
        self._results = {item[0]: {'text': None, 'raw_text': []}
                         for item in self.config['sections'].items()}

    def get_config(self, res_type, key):
        """Returns config 'key' value for specified 'type'"""
        return self.config['sections'][res_type].get(key)

    def add_result(self,
                   res_type,
                   text,
                   raw_text=None,
                   replace_check_re_with=None):
        """Adds recognition result to internal storage"""

        replacement = replace_check_re_with
        config_dont_replace = \
            self.get_config(res_type, 'do_not_replace_check_re')

        text_to_save = text

        # raw_text_to_save = [x[0] for x in raw_text]
        if raw_text:
            raw_text_to_save = raw_text.copy()
        else:
            raw_text_to_save = text_to_save.split(self.linesep)

        if not(replacement is None) and not config_dont_replace:
            # replace find pattern string in plain text
            text_to_save = re.sub(
                self.get_config(res_type, 'check_re'),
                replacement,
                text_to_save
            )

            # replace find pattern string in raw text list
            if raw_text_to_save:
                if re.sub(self.get_config(res_type, 'check_re'),
                          replacement,
                          raw_text_to_save[0]) == '':
                    logger.debug(
                        ('Raw-text-to-save element '
                         f'removed {raw_text_to_save[0]}')
                    )
                    raw_text_to_save.pop(0)

        # adding plain text to internal storage
        self._results[res_type]['text'] = (
            self._results[res_type]['text']
            if self._results[res_type]['text']
            else ''
            ) + text_to_save

        self._results[res_type]['raw_text'] = (
            self._results[res_type]['raw_text']
            if self._results[res_type]['raw_text']
            else []) + raw_text_to_save

    def add_result_image(self, res_type, image_name):
        """Adding image data to specific result domain"""
        logger.info(
            "Adding image {} for recognized {}".format(image_name, res_type)
        )
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
                logger.info('Trying to save image: {}'.format(img_name))

                filename = self.gen_abs_fname_for_result_image(
                    img_name, results_dir
                )
                if filename:
                    with open(filename, 'wb') as fimg:
                        try:
                            docx_img = None
                            doc = self.get_doc()
                            docx_img = doc.open_docx_image(img_name)
                            shutil.copyfileobj(docx_img, fimg)
                        finally:
                            if docx_img:
                                docx_img.close()
                logger.info('Image saved.')

    def gen_fname_for_result_json(
            self,
            results_dir=None,
            results_file_name=None):
        """
        Returns filename for docx parsing results.

        With adding json as the extension.
        """
        if results_file_name:
            if results_file_name.endswith('.json'):
                filename = results_file_name.replace('.json', '')
            else:
                filename = results_file_name
        else:
            filename = self.get_fio()

        if results_dir:
            out_dir = results_dir
        else:
            out_dir = os.path.join(BASE_DIR, OUT_DIR)

        return os.path.join(out_dir, '%s.%s' % (filename, 'json'))

    def gen_abs_fname_for_result_image(
            self,
            original_image_name,
            results_dir=None):
        """Returns absolute file destination path for image"""
        filepath = self.gen_fname_for_result_image(original_image_name)

        if results_dir:
            out_dir = results_dir
        else:
            out_dir = os.path.join(BASE_DIR, OUT_DIR)

        return os.path.join(out_dir, filepath) or None

    def gen_fname_for_result_image(self, original_image_name):
        """Destination file name for image."""
        filename = self.get_fio()
        match_res = re.search(r'\.(.+)$', original_image_name)
        result = None
        if match_res:
            fileext = match_res.groups(1)[0]
            logger.debug('Image name extenstion: {}'.format(fileext))
            if fileext:
                result = os.path.join(
                    IMAGES_OUT_DIR,
                    '{}.{}'.format(filename, fileext)
                )
        return result

    def get_results_for_save(self):
        """
        Returns results close to the destination json format.

        Changing the content if the config has a setting
        `list_of_strings`: True for the domain or if the config
        has a setting "'is_image': True" for the domain.
        """
        res = {}
        for item in self.config['sections'].items():
            if self.config['sections'][item[0]].get('list_of_strings') is True:
                remove_empty_items = self.config['sections'][item[0]]\
                    .get('remove_empty_items')

                if remove_empty_items is True:
                    res[item[0]] = [
                        y for y in self._results[item[0]]['raw_text']
                        if y.split()
                    ]
                else:
                    res[item[0]] = [
                        y for y in self._results[item[0]]['raw_text']
                    ]

            elif self.config['sections'][item[0]].get('is_image') is True:
                if self._results[item[0]].get('images'):
                    res[item[0]] = [
                        self.gen_fname_for_result_image(img_name)
                        for img_name in self._results[item[0]]['images']
                    ]
            else:
                res[item[0]] = self._results[item[0]]['text']
        return res

    def save_results_json(self, results_dir=None, results_file_name=None):
        """Saving text results of paragraph to the destination file."""
        filepath = self.gen_fname_for_result_json(
            results_dir,
            results_file_name
        )
        logger.debug('save_results_json.filename {}'.format(filepath))

        with io.open(filepath, 'w', encoding='utf8') as json_file:
            json.dump(
                self.get_results_for_save(),
                json_file,
                ensure_ascii=False,
                indent=3
            )

    def get_internal_results(self):
        """Returns internal results of recognition"""
        return self._results

    def get_ordered_config(self):
        """Return ordered config"""
        return self._config_ordered

    def get_config_str(self):
        """Return config as json"""
        return json.dumps(self.config, indent=4, sort_keys=True)

    # def add_paragraph(self, para):
    #    self.pStorage.append({
    #        'id': para.getId(),
    #        'text': para.getText(),
    #        'ref': para
    #    })

    # def get_paragraphs_text(self, cleaned=True):
    #    if cleaned:
    #        return [p['ref'].getCleanedText() for p in self.pStorage]
    #    else:
    #        return [p['ref'].getText() for p in self.pStorage]

    # def getParagraphsId(self):
    #    return [p['id'] for p in self.pStorage]
#
    # def getParagraphsRefs(self):
    #    return [p['ref'] for p in self.pStorage]

    def recognize_paragraph(self, para):
        """
        Run process of recognition of paragraph.

        Looping over internal config and applying `check_re`
        regular expressions to determine type of the
        paragraph content.
        """
        logger.debug(
            'Paragraph text (%s): %s', para._item.tag, para.getCleanedText()
        )
        for regexp in self._re_list.items():
            tmp_re = re.compile(regexp[0])
            logger.debug(
                'Trying to recognize paragraph '
                '[{}] as {} with regex {}'.format(
                    para.getId(), regexp[1], regexp[0]
                )
            )
            if tmp_re.match(para.getCleanedText().strip()):

                not_re = self.config['sections'][regexp[1]].get('not_re')
                if not_re:
                    tmp_not_re = re.compile(not_re)
                    if not tmp_not_re.match(para.getCleanedText().strip()):
                        logger.debug(
                            'Paragraph text: %s', para.getCleanedText()
                        )
                        return regexp[1]
                    else:
                        pass
                else:
                    return regexp[1]

        return None

    def load_paragraphs(self):
        """
        Load docx paragraphs (one by one) to
        instance with recognition all of them.
        """
        # open file
        document = self._doc

        # load data from file
        document.load()

        # iterate over document paragraphs
        par_iter = 1
        last_recognized_type = None

        for praw in document.get_doc_paragraphs_iter():

            para = DOCXParagraph(praw, docx=document)
            # self.addParagraph(p)
            pid = para.getId()
            logger.debug('----> (%02d) Paragraph %s', par_iter, pid)

            if para.getCleanedText().strip() == '':
                logger.debug(
                    'Paragraph {} text is empty. Skipping it.'.format(pid)
                )
                continue

            p_type = self.recognize_paragraph(para)

            if p_type or last_recognized_type:

                # forming paragraph text as joining raw
                # data without any join chars
                par_text = ''.join(para.getRawText())

                # to avoid fragmented values within raw value
                # we split text into strings it is usefull for
                # lobby parsing, because every word in docx
                # could be separated to own element and it is
                # difficult to strip 'check_re' matches from
                # the list where evary word is element
                # raw_text = par_text.split(self.linesep)

                work_type = p_type if p_type else last_recognized_type

                # determine if we have to find something
                # within recognized paragraph
                extra_types_list = self.get_config(work_type, 'also_contains')
                if extra_types_list:

                    logger.debug('Found {} extra types: {}'.format(
                            len(extra_types_list), extra_types_list
                        )
                    )
                    for extra_type in extra_types_list:
                        if self.get_config(extra_type, 'is_image'):
                            logger.debug(
                                'Try to find images within paragraph...'
                            )
                            for img in para.getImages():
                                drw = DOCXDrawing(
                                    img,
                                    docx=document
                                )
                                img_name = drw.getImageName()
                                logger.info('Image %s found', img_name)

                                # adding image to result
                                self.add_result_image(extra_type, img_name)

                        elif self.get_config(extra_type, 'text_re'):

                            # check do we need to remove links or not
                            if self.get_config(extra_type, 'remove_links'):
                                extra_par_text = para.getCleanedText()

                            logger.debug("Found 'text_re' for %s", extra_type)
                            logger.debug(
                                'Searching [%s] in [%s]',
                                self.get_config(extra_type, 'text_re'),
                                extra_par_text
                            )
                            match_res = re.search(
                                self.get_config(extra_type, 'text_re'),
                                extra_par_text
                            )
                            if match_res:
                                search_res = match_res.group(0).strip()
                                self.add_result(extra_type, search_res)
                                if (
                                    not self.get_config(
                                        extra_type, 'leave_also_contains_data'
                                        )
                                   ):
                                    par_text = par_text.replace(search_res, '')

                if p_type:
                    logger.info('Paragraph recognized as [%s]', p_type)
                    last_recognized_type = p_type

                    self.add_result(p_type, par_text, replace_check_re_with='')
                elif last_recognized_type:
                    logger.info(
                        'Paragraph hasn`t recognized. Add data to the last '
                        'recognized as [%s]', last_recognized_type
                    )
                    self.add_result(
                        last_recognized_type,
                        self.linesep + par_text
                    )
            else:
                logger.warning('Paragraph iter %s was skipped.', par_iter)

            par_iter = par_iter + 1

    def recreate_dest_folder_sturture(self, results_dir=None):
        """Creates default or specified output directory structure"""

        if results_dir:
            out_json_dir = results_dir
        else:
            out_json_dir = os.path.join(BASE_DIR, OUT_DIR)

        out_images_dir = os.path.join(out_json_dir, IMAGES_OUT_DIR)

        # verifying out json directory
        if not os.path.exists(out_json_dir):
            os.makedirs(out_json_dir)

        # verifying out images directory
        if not os.path.exists(out_images_dir):
            os.makedirs(out_images_dir)

    def save_all_results(self, results_dir=None, results_file_name=None):
        self.recreate_dest_folder_sturture(results_dir=results_dir)
        self.save_results_json(
            results_dir=results_dir,
            results_file_name=results_file_name)
        self.save_result_images(results_dir=results_dir)
