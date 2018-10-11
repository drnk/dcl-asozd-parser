import os
import os.path
import unittest
import shutil
import json

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
        with open('%s\\%s.json' % (DEST_DIR, DEST_FNAME), 'r', encoding='utf-8') as json_file:
            cls.data = json.loads(json_file.read())
        #cls.instance.saveResultImages(results_dir=DEST_DIR)

    @classmethod
    def tearDownClass(cls):
        #shutil.rmtree(DEST_DIR)
        pass


    def test_destination_filename(self):
        """Verify that saving parsing results with passed filename is working correct"""
        path = "%s\\%s.json" % (DEST_DIR, DEST_FNAME) 
        self.assertEqual(os.path.isfile(path), True)

    def test_json_fio_is_correct(self):
        """Verify that 'fio' in json result file is correct"""
        self.assertEqual(self.data['fio'], "Бессарабов Даниил Владимирович")

    def test_json_lobby_is_full_simple(self):
        """Verify that 'lobby' in json result file is full"""
        self.assertEqual(self.data['lobby'],  ["региональное лобби/Алтайский край"])

    def test_json_family_is_empty(self):
        """Verify that 'family' in json result is empty"""
        self.assertEqual(self.data['family'], None)

    def test_json_submitted_is_full(self):
        """Verify that 'submitted' value in json result is full"""
        tgt = 'Тематика законодательных инициатив Даниила Бессарабова касается регулирования статей '+\
            'Трудового кодекса: упразднение временных норм трудового законодательства; внесение изменений, '+\
            'приостановление действия или признание утратившими силу положений ТК РФ, которые должны '+\
            'осуществляться отдельными федеральными законами.  Инициативы вносятся в соавторстве с депутатами '+\
            'из других фракций Госдумы.\r\nБессарабов стал инициатором законопроектов об уточнении полномочий '+\
            'в сфере благоустройства территории муниципальных образований, полномочий регионов в  вопросах '+\
            'увековечения памяти погибших при защите Отечества.\r\nВыступления Бессарабова на пленарных '+\
            'заседаниях касаются бюджета Пенсионного фонда, пенсионного страхования и индексации пенсий.'
        self.assertEqual(self.data['submitted'], tgt)

    def test_json_position_is_full(self):
        """Verify that 'position' value in json result is full"""
        tgt = 'Депутат Государственной Думы VII созыва, избран от избирательного '+\
            'округа 0039 (Барнаульский - Алтайский край)'
        self.assertEqual(self.data['position'], tgt)

    def test_json_relations_is_full(self):
        """Verify that 'relations' value in json result is full"""
        tgt = 'Даниил Бессарабов близок и лоялен бывшему губернатору Алтайского края Александру Карлину'+\
            ', который <a href="https://altapress.ru/politika/story/aleksandr-karlin-ushel-v-'+\
            'otstavku-s-posta-gubernatora-altayskogo-kraya-222426">ушел в отставку 28 мая 2018 '+\
            'года</a> (1). Бессарабов - сын друга Карлина. <a href="http://politsib.ru/news/97428">'+\
            'Родители</a> (2) Даниила Бессарабова учились в Томском государственном университете, '+\
            'который окончила супруга Александра Карлина Галина Викторовна. Александр Карлин и отец '+\
            'депутата Владимир Бессарабов работали в прокуратуре Алтайского края. В разное время '+\
            'возглавляли один и тот же отдел - по надзору за соблюдением законов в социальной и '+\
            'экономической сфере. В 1990-х годах они работали в Генеральной прокуратуре. \r\nВ 1993 '+\
            'году <a href="http://politsib.ru/news/97428">отец Даниила Бессарабова Владимир Григорьевич'+\
            '</a> (3) избрался депутатом Госдумы по Рубцовскому округу, и семья переехала в Москву. '+\
            'После завершения депутатских полномочий Владимир Бессарабов работал в Генеральной прокуратуре.'
        self.assertEqual(self.data['relations'], tgt)

    def test_json_bio_is_full(self):
        """Verify that 'bio' value in json result is full"""
        tgt = 'Родился 9 июля 1976 г. в Кемеровской области. Окончил Алтайский государственный '+\
            'университет (1998), Российскую Академию государственной службы при Президенте РФ (2007). '+\
            'Кандидат юридических наук. В 1999 г. получил статус адвоката. Работал в адвокатской '+\
            'конторе № 2 Железнодорожного района г. Барнаула (Алтайский край). В 2004 году избран '+\
            'депутатом Алтайского краевого совета народных депутатов по списку партии ЛДПР. В '+\
            'региональном парламенте входил в группу “Объединенные депутаты”, затем перешел во '+\
            'фракцию “Единая Россия”. 2 марта 2008 г. избран депутатом Алтайского краевого '+\
            'законодательного собрания (бывший краевой совет народных депутатов) от партии '+\
            '“Единая Россия”. В 2010 году назначен заместителем губернатора Алтайского края '+\
            'Александра Карлина (координировал деятельность органов исполнительной власти края '+\
            'в сфере социальной политики). С мая 2011 г. возглавлял Территориальный фонд обязательного '+\
            'медицинского страхования края (по должности). Президент федерации дзюдо Алтайского края. '+\
            '\r\nС 2016 года - депутат Государственной Думы седьмого созыва.'
        self.assertEqual(self.data['bio'], tgt)