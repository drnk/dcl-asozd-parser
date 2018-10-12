from bs4 import BeautifulSoup
from zipfile import ZipFile

from .items import DOCXParagraph
from pprint import pprint

DOCX_CONTENTS_FILE_NAME = 'word/document.xml'
DOCX_RELS_FILE_NAME = 'word/_rels/document.xml.rels'
DOCX_IMG_DIR_NAME = 'word'

class DOCXDocument(object):
    """Definition and common routines for docx document"""

    RD = {}

    _DEBUG = False
    _VERSION = None

    _is_already_opened = False
    _version_check_complete = False

    def __init__(self, file_name, *args, **kwargs):
        self.file_name = file_name

        if kwargs.get('debug'):
            self._DEBUG = kwargs['debug']

        self._openDocx()

    def _dbg(self, msg):
        if self._DEBUG:
            pprint(msg)


    def __enter__(self):
        self._openDocx()
        return self
    
    def __exit__(self, type, value, traceback):
        #Exception handling here
        self._rels.close()
        self._doc.close()
        self._zipfile.close()

    def getMSWordVersion(self):
        res_version = None

        if self._version_check_complete:
            res_version = self._VERSION
        else:
            #12.0000 = Word 2007
            #14.0000 = Word 2010
            #15.0000 = Word 2013
            #16.0000 = Word 2016

            app_file_name = 'docProps/app.xml'
            try:
                soup = BeautifulSoup(self._zipfile.open(app_file_name, 'r').read(), 'lxml-xml')
                res_version = soup.find('AppVersion').text
            except FileNotFoundError:
                self._dbg('Couln\'t determine Microsoft Word version from %s' % app_file_name)
            except KeyError:
                self._dbg('Something went wrong during determinig Microsoft Word version from %s' % app_file_name)

        return res_version

    def getZipFile(self):
        return self._zipfile

    def openDocxImage(self, image_name):
        return self.getZipFile().open('%s/%s' % (DOCX_IMG_DIR_NAME, image_name), 'r')

    def load(self):
        self.loadRelationshipsData()
        self.loadDocumentData()

    def _openDocx(self):
        """Open docx document and set pointer objects for Relationships and Document content"""
        if not self._is_already_opened:
            
            self._zipfile = ZipFile(self.file_name, 'r')
            #dbg("Contents of the %s" % self.file_name)
            #dbg(self._zipfile.printdir())
            self._rels = self._zipfile.open(DOCX_RELS_FILE_NAME, 'r')
            self._doc = self._zipfile.open(DOCX_CONTENTS_FILE_NAME, 'r')
            
            self._is_already_opened = True


    def getDocumentRawData(self):
        """Return raw Document data from docx file"""
        return self._doc.read()

    def getRelationshipTargetById(self, rId):
        """Returns target value for the reference from docx"""
        if self.RD.get(rId):
            return self.RD[rId]['Target']
        else:
            return None

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
        
        self._docx_paragraph_iterator = self._docx_body.findChildren(DOCXParagraph.full_tag_name, recursive=False)


    def getDocParagraphsIter(self):
        """Returns list of document paragraphs"""
        #print('Document paragraph list length: %d' % len(self._docx_paragraph_iterator))
        return self._docx_paragraph_iterator