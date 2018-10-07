import argparse
from zipfile import ZipFile
from bs4 import BeautifulSoup, element
from pprint import pprint
import abc
import re
import json
import operator
import shutil
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IN_DIR = BASE_DIR + '\in'
OUT_DIR = BASE_DIR + '\out'
IMAGES_OUT_DIR = OUT_DIR + '\images'

# Useful queries:
# open('parser_config.json', 'w').write(json.dumps(P, indent=4))

DEBUG = True

def dbg(msg):
    global DEBUG
    if DEBUG: 
        pprint(msg)

#CONTENTS_FILE_NAME = 'word/document.xml'
#RELS_FILE_NAME = 'word/_rels/document.xml.rels'
#IMG_DIR_NAME = 'word/media/'

CLEANING_REGEXP = re.compile('<[^>]+>')

class DOCXItem(object):
    __metaclass__ = abc.ABCMeta
    EXCLUDE_LIST = ('pPr', 'rPr')

    def __init__(self, item, *args, **kwargs):
        #dbg('DOCXItem.__init__:', type(item), isinstance(item, element.Tag))
        if isinstance(item, element.Tag):
            self._item = item
            if kwargs.get('docx'):
                self._doc = kwargs['docx']

    def getDoc(self):
        return self._doc
    
    @staticmethod
    def factory(item, *args, **kwargs):
        if isinstance(item, element.Tag):
            if item.name == "p": 
                return DOCXParagraph(item, *args, **kwargs)
            if item.name == "r":
                return DOCXRun(item, *args, **kwargs)
            if item.name == "hyperlink":
                return DOCXHyperlink(item, *args, **kwargs)
            if item.name == "drawing":
                return DOCXDrawing(item, *args, **kwargs)

        return None
    
    @abc.abstractmethod
    def getChildren(self):
        """Returns children elements"""
        pass
    
    @abc.abstractmethod
    def getText(self):
        """Returns text representation of the element"""
        pass

    def __str__(self):
        return self.getText()

    def getCleanedText(self):
        return CLEANING_REGEXP.sub('', self.getText())
        #return self._item.get_text()


class DOCXText(DOCXItem):
    """Representation of w:t docx element"""
    full_tag_name = 'w:t'
    tag_name = 't'

    def getText(self):
        return self._item.text

class DOCXDrawing(DOCXItem):
    """Representation of w:drawing docx element"""
    full_tag_name = 'w:drawing'
    tag_name = 'drawing'

    def getText(self):
        return None
    
    def getImageName(self):
        pic_tag = self._item.find('pic:cNvPr')
        if pic_tag:
            return pic_tag.get('name')
        else:
            return None
    

class DOCXRun(DOCXItem):
    """Representation of w:r docx element"""
    full_tag_name = 'w:r'
    tag_name = 'r'

    def getText(self):
        t = self._item.find(DOCXText.full_tag_name)
        if t:
            return t.text
        else:
            return None

    def getCleanedText(self):
        return self._item.get_text()

         
class DOCXHyperlink(DOCXItem):
    """Representation of w:t docx element"""

    full_tag_name = 'w:hyperlink'
    tag_name = 'hyperlink'

    def getRelationshipId(self):
        return self._item.get('r:id')

    def getText(self):
        # calculate ref target
        href = None
        if self._doc:
            href = self._doc.RD[self.getRelationshipId()]['Target']

        text = DOCXRun(self._item.find(DOCXRun.full_tag_name)).getText()
        return '<a href="%s">%s</a>' % (href, text)

    def getCleanedText(self):
        return self._item.get_text()


class DOCXParagraph(DOCXItem):
    """Paragraph definition for docs document"""
    
    full_tag_name = 'w:p'
    tag_name = 'p'

    _id = None

    def __init__(self, item, *args, **kwargs):
        super(DOCXParagraph, self).__init__(item, *args, **kwargs)
        
        if self._item.name == 'p':
            self._id = item.attrs['w14:paraId']
    
    def getImages(self):
        return self._item.findChildren(DOCXDrawing.full_tag_name, recursive=True) 

    def getId(self):
        return self._id

    def getChildren(self):
        return self._item.findChildren(lambda tag: tag.name not in self.EXCLUDE_LIST, recursive=False)

    def getText(self):
        res = ''
        for item in self.getChildren():
            el = DOCXItem.factory(item, docx=self.getDoc())
            if el:
                txt = el.getText()
                if txt:
                    res = res + txt
        return res

    def getRawText(self):
        res = []
        for item in self.getChildren():
            el = DOCXItem.factory(item, docx=self.getDoc())
            if el:
                txt = el.getText()
                if txt:
                    res.append([txt])
        return res

    def __repr__(self):
        return self._item.__repr__()



class DOCXDocument(object):
    """Definition and common routines for docx document"""

    CONTENTS_FILE_NAME = 'word/document.xml'
    RELS_FILE_NAME = 'word/_rels/document.xml.rels'
    IMG_DIR_NAME = 'word/media'

    RD = {}

    _DEBUG = True
    _is_already_opened = False

    def __init__(self, file_name, *args, **kwargs):
        self.file_name = file_name

        if kwargs.get('debug'):
            self._DEBUG = kwargs['debug']

        self._openDocx()


    def __enter__(self):
        self._openDocx()
        return self
    
    def __exit__(self, type, value, traceback):
        #Exception handling here
        self._rels.close()
        self._doc.close()
        self._zipfile.close()

    def getZipFile(self):
        return self._zipfile

    def openDocxImage(self, image_name):
        return self.getZipFile().open('%s/%s' % (self.IMG_DIR_NAME, image_name), 'r')

    def load(self):
        self.loadRelationshipsData()
        self.loadDocumentData()

    def _openDocx(self):
        """Open docx document and set pointer objects for Relationships and Document content"""
        if not self._is_already_opened:
            
            self._zipfile = ZipFile(self.file_name, 'r')
            #dbg("Contents of the %s" % self.file_name)
            #dbg(self._zipfile.printdir())
            self._rels = self._zipfile.open(self.RELS_FILE_NAME, 'r')
            self._doc = self._zipfile.open(self.CONTENTS_FILE_NAME, 'r')
            
            self._is_already_opened = True


    def getDocumentRawData(self):
        """Return raw Document data from docx file"""
        return self._doc.read()


    def getRelationshipsRawData(self):
        """Return raw Relationships data from docx file"""
        return self._rels.read()


    def loadRelationshipsData(self):
        """Load Relationships data into internal sturcture"""
        self.RD = {}

        rs = BeautifulSoup(self.getRelationshipsRawData(), 'lxml-xml')
        for r in rs.find_all('Relationship'):
            self.RD[r['Id']] = {
                'Id': r.get('Id'),
                'Type': r.get('Type'),
                'Target': r.get('Target'),
                'TargetMode': r.get('TargetMode'),
            }


    def loadDocumentData(self):
        """Load Document data into internal sturcture"""
        raw = BeautifulSoup(self.getDocumentRawData(), 'lxml-xml')
        self._docx_body = raw.find('w:body')
        if self._docx_body is None:
            raise ValueError('Couldn''t find <w:body> withing loaded docs document %s' % self.file_name)
        
        self._docx_paragraph_iterator = self._docx_body.findChildren(DOCXParagraph.full_tag_name)


    def getDocParagraphsIter(self):
        return self._docx_paragraph_iterator




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

    def addResult(self, type, text, raw_text=None):
        if self._results[type]['text']:
            self._results[type]['text'] = self._results[type]['text'] + text
        else:
            self._results[type]['text'] = text
        
        if raw_text:
            self._results[type]['raw_text'].append(raw_text)
        else:
            self._results[type]['raw_text'].append([text])

    def addResultImage(self, type, image_name):
        dbg("Adding image %s for recognized %s" % (image_name, type))
        if self._results[type].get('images'):
            self._results[type]['images'].append(image_name)
        else:
            self._results[type]['images'] = [image_name]
    
    def getFIO(self):
        return self._results['fio']['text']

    def saveImages(self):
        for img_name in self._results['photo']['images']:
            dbg('Trying to save image: %s' % img_name)
            m = re.search(r'\.(.+)$', img_name)
            if m:
                img_ext = m.groups(1)[0]
                dbg('Image name extenstion: %s' % img_ext)
                if img_ext:
                    dest_fname = '%s\%s.%s' % (IMAGES_OUT_DIR, self.getFIO(), img_ext) 
                    dbg('Destination file name: %s' % dest_fname)
                    with open(dest_fname, 'wb') as fimg:
                        try:
                            doc = self.getDoc()
                            docx_img = doc.openDocxImage(img_name)
                            shutil.copyfileobj(docx_img, fimg)
                        finally:
                            docx_img.close()

    def getResults(self):
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

        for r in self._re_list.items():
            tmp_re = re.compile(r[0])
            dbg('Trying to recognize paragraph as %s with regex %s' % (r[1], r[0]))
            if tmp_re.match(p.getCleanedText().strip()):

                not_re = self.config['types'][r[1]].get('not_re')
                if not_re:
                    tmp_not_re = re.compile(not_re)
                    if not tmp_not_re.match(p.getCleanedText().strip()):
                        dbg('Paragraph text: '+p.getCleanedText())
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
            dbg('----> (%02d) Paragraph '%pi+p.getId())
            dbg('Text: %s' % repr(p))
            p_type = self.recognizeParagraph(p)

            if p_type:
                # start of docx part which could be related to 
                # one of the target data parts
                dbg('Paragraph recognized as [%s]' % p_type)

                last_recognized_type = p_type
                #last_recognized_pi = pi

                self.addResult(p_type, p.getText(), p.getRawText())

                extra_types_list = self.config['types'][p_type].get('also_contains')
                if extra_types_list:
                    dbg('Found %d extra types: %s' % (len(extra_types_list), extra_types_list))
                    for extra_type in extra_types_list:
                        if self.config['types'][extra_type].get('is_image'):
                            dbg('Try to find images within paragraph')
                            for img in p.getImages():
                                drw = DOCXItem.factory(img, docx=Doc)
                                img_name = drw.getImageName()
                                dbg('Image %s found' % img_name)
                                self.addResultImage(extra_type, img_name)


            elif last_recognized_type:
                self.addResult(last_recognized_type, p.getText(), p.getRawText())
            else:
                print('Warning! Paragraph iter %d was skipped.' % pi)
            
            pi = pi + 1


if __name__ == '__main__':
    # arguments definition
    parser = argparse.ArgumentParser(description='Convert ASOZD details docx into json.')
    parser.add_argument('fname', metavar='fileName', type=str, help='file name for convert')
    args = parser.parse_args()

    # parser init
    P = ASOZDParser(args.fname)
    
    # parse start
    P.loadParagraphs()
    #print(P.getOrderedConfig())
    #print(P.getParagraphsId())
    #print(P.getParagraphsText())

    pprint(P.getResults())

    P.saveImages()
