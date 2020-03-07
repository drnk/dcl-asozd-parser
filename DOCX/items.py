"""
Module contains classes definition for DOCX elements:
  * paragraph (DOCXParagraph)
  * hyperlink (DOCXHyperlink)
  * text (DOCXText)
  * run (DOCXRun)
  * drawings (DOCXDrawing)
  * br (DOCXBr)
"""
import abc
import logging
import os
import re

from bs4 import element


logger = logging.getLogger(__name__)

LINESEP = os.linesep

CLEANING_REGEXP = re.compile('<[^>]+>')


class DOCXItemProto(abc.ABC):

    @abc.abstractmethod
    def _getRawText(self):
        raise NotImplementedError

    @abc.abstractmethod
    def getText(self):
        raise NotImplementedError

    @abc.abstractmethod
    def getRawText(self):
        raise NotImplementedError


class DOCXItem(DOCXItemProto):
    """Common class for docx elements."""

    _doc: 'DOCXDocument' = None  # reference to Document
    _debug = True

    # exclusion list for retrieving children elements
    EXCLUDE_LIST = ['pPr', 'rPr', 'proofErr', 'bookmarkStart']

    def __init__(self, item, **kwargs):

        if isinstance(item, element.Tag):
            self._item = item
            if kwargs.get('docx'):
                self._doc = kwargs['docx']

        if kwargs.get('debug'):
            self._debug = kwargs.get('debug') is True

    def getDoc(self):
        """Returns reference to DOCXDocument instance"""
        # return self._doc
        raise NotImplementedError

    @property
    def doc(self):
        """Reference to DOCXDocument instance."""
        return self._doc

    @property
    def name(self):
        """Name of the element."""
        return self._item.name

    @staticmethod
    def factory(item, *args, **kwargs):
        """Factory for create DOCX element instances."""
        if isinstance(item, element.Tag):
            if item.name == "p":
                return DOCXParagraph(item, *args, **kwargs)
            if item.name == "r":
                return DOCXRun(item, *args, **kwargs)
            if item.name == "hyperlink":
                return DOCXHyperlink(item, *args, **kwargs)
            if item.name == "drawing":
                return DOCXDrawing(item, *args, **kwargs)
            if item.name == "br":
                return DOCXBr(item, *args, **kwargs)
            if item.name == "t":
                return DOCXText(item, *args, **kwargs)

        return None

    def is_debug(self):
        """Returns True is debug mode is on, otherwise returns False"""
        return self._debug is True

    def _getRawText(self) -> str:
        """Returns unprocessed text from element"""

        res = []
        for child in self.getChildren():

            docx_child = DOCXItem.factory(
                child,
                docx=self.doc,
                debug=self.is_debug()
            )
            if docx_child:
                res = res + docx_child.getRawText()
        return res

    def getText(self):
        """Returns text representation of the element"""
        return ''.join(self._getRawText())

    def getRawText(self):
        """
        DOCXItem str representation.

        Returns the list where each element is a string."""
        return self._getRawText()

    def getChildren(self):
        """Direct children elements."""
        return self._item.findChildren(
            lambda tag: tag.name not in self.EXCLUDE_LIST,
            recursive=False
        )

    def __str__(self):
        return self.getText()

    def getCleanedText(self):
        """
        Returns text element value cleaned from the elements.

        Example: (<el>text</el> -> text)
        """
        return CLEANING_REGEXP.sub('', self.getText())


class DOCXParagraph(DOCXItem):
    """Paragraph definition for docs document"""

    FULL_TAG_NAME = 'w:p'
    TAG_NAME = 'p'

    _id = None

    def __init__(self, item, *args, **kwargs):
        super(DOCXParagraph, self).__init__(item, *args, **kwargs)

        if self._item.name == 'p':
            if item.attrs.get('w14:paraId'):
                self._id = item.attrs['w14:paraId']

    def getImages(self):
        return self._item.findChildren(
            DOCXDrawing.FULL_TAG_NAME,
            recursive=True
        )

    def getId(self):
        return '' if self._id is None else self._id

    def __repr__(self):
        return self._item.__repr__()


class DOCXDrawing(DOCXItem):
    """Representation of w:drawing docx element"""
    FULL_TAG_NAME = 'w:drawing'
    TAG_NAME = 'drawing'

    def getText(self):
        return None

    def getImageName(self):
        """
        Returns image name.

        From <w:drawing>/../<a:blip r:embed="referenceId">
        referenceId will be replaced with target reference
        from relationships docx file.
        """
        embed_tag = self._item.find('pic:blipFill').find('a:blip')
        # pic_tag = self._item.find('pic:cNvPr')
        if embed_tag:
            #  <a:blip r:embed="rId6"/>
            rId = embed_tag.get('r:embed')
            if rId and self.doc:
                return self.doc.get_relationship_target_by_id(rId)

        return None


class DOCXHyperlink(DOCXItem):
    """Representation of w:t docx element."""

    FULL_TAG_NAME = 'w:hyperlink'
    TAG_NAME = 'hyperlink'

    def getRelationshipId(self):
        """Returns relationship identifier."""
        return self._item.get('r:id')

    def _getRawText(self):
        href = None
        if self.doc:
            href = self.doc.get_relationship_target_by_id(
                self.getRelationshipId()
            )

        text = DOCXRun(self._item.find(DOCXRun.FULL_TAG_NAME)).getText()
        return ['<a href="{}">{}</a>'.format(href, text)]

    def getCleanedText(self):
        return self._item.get_text()


class DOCXRun(DOCXItem):
    """
    Representation of <w:r> docx element.

    Runs most commonly contain text elements <w:t>
    (which contain the actual literal text of a paragraph),
    but they may also contain such special content as symbols,
    tabs, hyphens, carriage returns, drawings, breaks,
    and footnote references.

    Current versions supports only <w:t> and <w:br> elements
    """

    FULL_TAG_NAME = 'w:r'
    TAG_NAME = 'r'

    def _getRawText(self):
        res = []

        tag_target_list = [DOCXText.FULL_TAG_NAME, DOCXBr.FULL_TAG_NAME]
        for item in self._item.findChildren(tag_target_list, recursive=False):
            el = DOCXItem.factory(item, docx=self.doc)
            if el:
                txt = el.getRawText()
                if txt:
                    res = res + txt
        return res

    def getCleanedText(self):
        return self._item.get_text()


class DOCXText(DOCXItem):
    """Representation of <w:t> docx element"""

    FULL_TAG_NAME = 'w:t'
    TAG_NAME = 't'

    def _getRawText(self):
        return [self._item.text]


class DOCXBr(DOCXItem):
    """Representation of <w:br> docx element"""

    FULL_TAG_NAME = 'w:br'
    TAG_NAME = 'br'

    def _getRawText(self):
        return [LINESEP]
