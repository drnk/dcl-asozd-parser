import abc
import re

from bs4 import element


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
                    res.append(txt)
        return res

    def __repr__(self):
        return self._item.__repr__()


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


class DOCXText(DOCXItem):
    """Representation of w:t docx element"""
    full_tag_name = 'w:t'
    tag_name = 't'

    def getText(self):
        return self._item.text