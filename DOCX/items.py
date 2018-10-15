import abc
import re
import os

from bs4 import element

LINESEP = os.linesep

CLEANING_REGEXP = re.compile('<[^>]+>')


class DOCXItem(object):
    __metaclass__ = abc.ABCMeta
    
    _doc = None # reference to Document
    _DEBUG = True

    EXCLUDE_LIST = ['pPr', 'rPr', 'proofErr', 'bookmarkStart'] # exclusion list for retrieving children elements

    def __init__(self, item, *args, **kwargs):
        #dbg('DOCXItem.__init__:', type(item), isinstance(item, element.Tag))
        if isinstance(item, element.Tag):
            self._item = item
            if kwargs.get('docx'):
                self._doc = kwargs['docx']
        
        if kwargs.get('debug'):
            self._DEBUG = (kwargs.get('debug') == True)

    def getDoc(self):
        return self._doc

    @property
    def name(self):
        return self._item.name

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
            if item.name == "br":
                return DOCXBr(item, *args, **kwargs)
            if item.name == "t":
                return DOCXText(item, *args, **kwargs)

        return None

    def is_debug(self):
        return self._DEBUG == True
    
    @abc.abstractmethod
    def _getRawText(self):
        """Returns unprocessed text from element"""
        #if self.is_debug(): print(">>> Call <%s>.getRawText()" % self.name)
        
        t = []
        for child in self.getChildren():

            docx_child = DOCXItem.factory(child, docx=self.getDoc(), debug=self.is_debug())
            if docx_child:
                t = t + docx_child._getRawText()
        return t
    
    @abc.abstractmethod
    def getText(self):
        """Returns text representation of the element"""
        #print(self._getRawText())
        return ''.join(self._getRawText())

    @abc.abstractmethod
    def getRawText(self):
        """Returns text representation in the list where each element represent a string"""
        return self._getRawText()

    def getChildren(self):
        return self._item.findChildren(lambda tag: tag.name not in self.EXCLUDE_LIST, recursive=False)


    def __str__(self):
        return self.getText()


    def getCleanedText(self):
        return CLEANING_REGEXP.sub('', self.getText())
        #return self._item.get_text()


class DOCXParagraph(DOCXItem):
    """Paragraph definition for docs document"""
    
    full_tag_name = 'w:p'
    tag_name = 'p'

    _id = None

    def __init__(self, item, *args, **kwargs):
        super(DOCXParagraph, self).__init__(item, *args, **kwargs)
        
        if self._item.name == 'p':
            if item.attrs.get('w14:paraId'):
                self._id = item.attrs['w14:paraId']
    
    def getImages(self):
        return self._item.findChildren(DOCXDrawing.full_tag_name, recursive=True) 

    def getId(self):
        return '' if self._id is None else self._id

    def __repr__(self):
        return self._item.__repr__()


class DOCXDrawing(DOCXItem):
    """Representation of w:drawing docx element"""
    full_tag_name = 'w:drawing'
    tag_name = 'drawing'

    def getText(self):
        return None
        #return ''
    
    def getImageName(self):
        embed_tag = self._item.find('pic:blipFill').find('a:blip')
        #pic_tag = self._item.find('pic:cNvPr')
        if embed_tag:
            #  <a:blip r:embed="rId6"/>
            rId = embed_tag.get('r:embed')
            if rId and self.getDoc():
                return self.getDoc().get_relationship_target_by_id(rId)

        return None


class DOCXHyperlink(DOCXItem):
    """Representation of w:t docx element"""

    full_tag_name = 'w:hyperlink'
    tag_name = 'hyperlink'

    def getRelationshipId(self):
        return self._item.get('r:id')

    def _getRawText(self):
        href = None
        if self.getDoc():
            href = self.getDoc().get_relationship_target_by_id(self.getRelationshipId())

        text = DOCXRun(self._item.find(DOCXRun.full_tag_name)).getText()
        return ['<a href="%s">%s</a>' % (href, text)]

    def getCleanedText(self):
        return self._item.get_text()


class DOCXRun(DOCXItem):
    """
    Representation of <w:r> docx element

    Runs most commonly contain text elements <w:t>
    (which contain the actual literal text of a pararaph),
    but they may also contain such special content as symbols,
    tabs, hyphens, carriage returns, drawings, breaks,
    and footnote references.

    Current versions supports only <w:t> and <w:br> elements
    """
    
    full_tag_name = 'w:r'
    tag_name = 'r'

    def _getRawText(self):
        res = []

        tag_target_list = [DOCXText.full_tag_name, DOCXBr.full_tag_name]
        for item in self._item.findChildren(tag_target_list, recursive=False):
            el = DOCXItem.factory(item, docx=self.getDoc())
            if el:
                txt = el._getRawText()
                if txt:
                    res = res + txt
        return res

    def getCleanedText(self):
        return self._item.get_text()


class DOCXText(DOCXItem):
    """Representation of <w:t> docx element"""

    full_tag_name = 'w:t'
    tag_name = 't'

    def _getRawText(self):
        return [self._item.text]


class DOCXBr(DOCXItem):
    """Representation of <w:br> docx element"""

    full_tag_name = 'w:br'
    tag_name = 'br'

    def _getRawText(self):
        return [LINESEP]
