"""
Contains definition of DOCXDocument class.
Provides basic routines for working with docx files.
"""
from zipfile import ZipFile
from pprint import pprint
from bs4 import BeautifulSoup

from .items import DOCXParagraph


DOCX_CONTENTS_FILE_NAME = 'word/document.xml'
DOCX_RELS_FILE_NAME = 'word/_rels/document.xml.rels'
DOCX_IMG_DIR_NAME = 'word'

class DOCXDocument(object):
    """Definition and common routines for docx document"""

    rels_dict = {}

    _debug = False
    _VERSION = None

    _is_already_opened = False
    _version_check_complete = False

    def __init__(self, file_name, **kwargs):
        self.file_name = file_name

        if kwargs.get('debug'):
            self._debug = kwargs['debug']

        self._open_docx()

        self._docx_paragraph_iterator = []

        self._docx_body = None


    def _dbg(self, msg):
        if self._debug:
            pprint(msg)


    def __enter__(self):
        self._open_docx()
        return self

    def __exit__(self, res_type, value, traceback):
        #Exception handling here
        self._rels.close()
        self._doc.close()
        self._zipfile.close()

    def get_ms_word_version(self):
        """Returns version of Microsoft Word product which have been used for docx file creation"""
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
                self._dbg('Something went wrong during determinig Microsoft Word '+\
                    'version from %s' % app_file_name)

        return res_version

    def get_zip_file(self):
        """Returns ZipFile pointer to docx"""
        return self._zipfile

    def open_docx_image(self, image_name):
        """Returns opened file pointer to image with 'image_name' within dox"""
        return self.get_zip_file().open('%s/%s' % (DOCX_IMG_DIR_NAME, image_name), 'r')

    def load(self):
        """Loads relationship and document content data into the clas instance"""
        self.load_relationships_data()
        self.load_document_data()

    def _open_docx(self):
        """Open docx document and set pointer objects for Relationships and Document content"""
        if not self._is_already_opened:

            self._zipfile = ZipFile(self.file_name, 'r')
            #dbg("Contents of the %s" % self.file_name)
            #dbg(self._zipfile.printdir())
            self._rels = self._zipfile.open(DOCX_RELS_FILE_NAME, 'r')
            self._doc = self._zipfile.open(DOCX_CONTENTS_FILE_NAME, 'r')

            self._is_already_opened = True


    def get_document_raw_data(self):
        """Return raw Document data from docx file"""
        return self._doc.read()

    def get_relationship_target_by_id(self, relationship_id):
        """Returns target value for the reference from docx"""
        if self.rels_dict.get(relationship_id):
            return self.rels_dict[relationship_id]['Target']
        else:
            return None

    def get_relationships_raw_data(self):
        """Return raw Relationships data from docx file"""
        return self._rels.read()


    def load_relationships_data(self):
        """Load Relationships data into internal sturcture"""
        self.rels_dict = {}

        rel_soup = BeautifulSoup(self.get_relationships_raw_data(), 'lxml-xml')
        for rel in rel_soup.find_all('Relationship'):
            self.rels_dict[rel['Id']] = {
                'Id': rel.get('Id'),
                'Type': rel.get('Type'),
                'Target': rel.get('Target'),
                'TargetMode': rel.get('TargetMode'),
            }


    def load_document_data(self):
        """Load Document data into internal sturcture"""
        raw = BeautifulSoup(self.get_document_raw_data(), 'lxml-xml')
        self._docx_body = raw.find('w:body')
        if self._docx_body is None:
            raise ValueError('Couldn''t find <w:body> withing '+\
                'loaded docs document %s' % self.file_name)

        self._docx_paragraph_iterator = self._docx_body.findChildren(
            DOCXParagraph.full_tag_name,
            recursive=False)


    def get_doc_paragraphs_iter(self):
        """Returns list of document paragraphs"""
        #print('Document paragraph list length: %d' % len(self._docx_paragraph_iterator))
        return self._docx_paragraph_iterator
