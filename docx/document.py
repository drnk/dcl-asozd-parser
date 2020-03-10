"""
Contains definition of DOCXDocument class.
Provides basic routines for working with docx files.
"""
import logging
import os
from pathlib import PurePath
from pprint import pprint
from zipfile import ZipFile

from bs4 import BeautifulSoup

from .items import DOCXParagraph


logger = logging.getLogger(__name__)

# for some reasons ZipFile operates archive members paths
# in Posix format, even been running on Windows
# so any use of os.path or PurePath libraries leads up
# to error in accessing the file in Windows
DOCX_CONTENTS_FILE_NAME = r'word/document.xml'
DOCX_RELS_FILE_NAME = r'word/_rels/document.xml.rels'
DOCX_IMG_DIR_NAME = r'word'


class DOCXDocument(object):
    """Definition and common routines for docx document."""

    rels_dict = {}

    _debug = False
    _VERSION = None

    _is_already_opened = False
    _version_check_complete = False

    def __init__(self, file_name: str, **kwargs):
        self.file_name = file_name

        if kwargs.get('debug'):
            self._debug = kwargs['debug']

        self._open_docx()
        self._docx_paragraph_iterator = []
        self._docx_body = None

    def _dbg(self, msg):
        raise NotImplementedError

    def __enter__(self):
        self._open_docx()
        return self

    def __exit__(self, res_type, value, traceback):
        # Exception handling here
        self._rels.close()
        self._doc.close()
        self._zipfile.close()

    def get_ms_word_version(self):
        """
        Returns version of Microsoft Word product
        used for docx file creation.
        """
        res_version = None

        if self._version_check_complete:
            res_version = self._VERSION
        else:
            # 12.0000 = Word 2007
            # 14.0000 = Word 2010
            # 15.0000 = Word 2013
            # 16.0000 = Word 2016

            app_fn: str = os.path.join('docProps', 'app.xml')
            try:
                soup = BeautifulSoup(
                    self._zipfile.open(app_fn, 'r').read(),
                    'lxml-xml'
                )
                res_version = soup.find('AppVersion').text
            except FileNotFoundError:
                logger.warning("Couln't determine Microsoft "
                               'Word version from {}', app_fn)
            except KeyError:
                logger.warning('Something went wrong during determinig '
                               'Microsoft Word version from {}', app_fn)

        return res_version

    @property
    def zip_file(self):
        """ZipFile pointer to docx."""
        return self._zipfile

    def get_zip_file(self):
        """Returns ZipFile pointer to docx."""
        #return self._zipfile
        raise NotImplementedError

    def open_docx_image(self, image_name):
        """Returns opened file pointer to image with 'image_name' within dox"""
        # zipfile is using Posix file paths even in Unix
        return self.zip_file.open(
            '{}/{}'.format(DOCX_IMG_DIR_NAME, image_name), 'r'
        )

    def load(self) -> None:
        """Loads relationship and document content data into the clas instance"""
        self.load_relationships_data()
        self.load_document_data()

    def _open_docx(self) -> None:
        """Open docx document and set pointer objects for Relationships and Document content"""
        if not self._is_already_opened:
            self._zipfile = ZipFile(self.file_name, 'r')
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
        """Load Relationships data into internal structure."""
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
            raise ValueError('Couldn''t find <w:body> withing '
                             'loaded docs document {}'.format(self.file_name))

        self._docx_paragraph_iterator = self._docx_body.findChildren(
            DOCXParagraph.FULL_TAG_NAME,
            recursive=False
        )


    def get_doc_paragraphs_iter(self):
        """Returns list of document paragraphs"""
        #print('Document paragraph list length: %d' % len(self._docx_paragraph_iterator))
        return self._docx_paragraph_iterator
