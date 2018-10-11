import os
import os.path
import unittest
import shutil

from asozd import ASOZDParser

DEST_DIR = 'test\\results'
DEST_FNAME = 'test_asozd'

class ASOZDParserTest(unittest.TestCase):
    """DOCXText tests"""
    
    @classmethod
    def setUpClass(cls):
        cls.test_file_name = 'test\\source_n1.docx' 

        cls.instance = ASOZDParser(cls.test_file_name)
        # parse
        cls.instance.loadParagraphs()

        try:
            os.mkdir(DEST_DIR)
        except FileExistsError:
            pass

        # storing parsed results
        cls.instance.saveResults(results_dir=DEST_DIR, results_file_name=DEST_FNAME)
        #cls.instance.saveResultImages(results_dir=DEST_DIR)

    @classmethod
    def tearDownClass(cls):
        #shutil.rmtree(DEST_DIR)
        pass


    def test_destination_filename(self):
        """Verify that saving parsing results with passed filename is working correct"""
        path = "%s\\%s.json" % (DEST_DIR, DEST_FNAME) 
        self.assertEqual(os.path.isfile(path), True)

    def test_(self):
        pass