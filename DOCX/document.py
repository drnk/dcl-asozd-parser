from bs4 import BeautifulSoup
from zipfile import ZipFile

from .items import DOCXParagraph

DOCX_CONTENTS_FILE_NAME = 'word/document.xml'
DOCX_RELS_FILE_NAME = 'word/_rels/document.xml.rels'
DOCX_IMG_DIR_NAME = 'word/media'

class DOCXDocument(object):
    """Definition and common routines for docx document"""

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