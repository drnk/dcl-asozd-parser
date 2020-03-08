import json
import logging
import os
import unittest


from asozd import ASOZDParser

logger = logging.getLogger(__name__)


BASE_DIR = os.path.dirname(os.path.realpath(__file__))

SOURCE_DIR = os.path.join(BASE_DIR, 'test')
SOURCE_FNAME1 = 'source_n1.docx'
SOURCE_FNAME2 = 'source_n2.docx'

DEST_DIR = os.path.join(SOURCE_DIR, 'results')
DEST_FNAME1 = 'test_asozd_source_n1.json'
DEST_FNAME2 = 'test_asozd_source_n2.json'


class ASOZDParserResultsTest1(unittest.TestCase):
    """ASOZDParser tests."""

    @classmethod
    def setUpClass(cls):
        cls.test_file_name = os.path.join(SOURCE_DIR, SOURCE_FNAME1)

        cls.instance = ASOZDParser(cls.test_file_name)
        # parse
        cls.instance.load_paragraphs()

        try:
            os.mkdir(DEST_DIR)
        except FileExistsError:
            # nothing to do with existing folder
            pass

        # storing parsed results
        cls.instance.save_results_json(
            results_dir=DEST_DIR,
            results_file_name=DEST_FNAME1
        )

        df = os.path.join(DEST_DIR, DEST_FNAME1)
        with open(df, 'r', encoding='utf-8') as f:
            cls.data = json.loads(f.read())
        # cls.instance.saveResultImages(results_dir=DEST_DIR)

    def test_destination_filename(self):
        """Verify saving parsing results."""
        path = os.path.join(DEST_DIR, DEST_FNAME1)
        self.assertEqual(os.path.isfile(path), True)

    def test_json_fio_is_correct(self):
        """Verify that 'fio' in json result file."""
        self.assertEqual(
            self.data['fio'],
            "Бессарабов Даниил Владимирович"
        )

    def test_json_lobby_is_full_simple(self):
        """Verify that 'lobby' in json result file is full"""
        self.assertEqual(
            self.data['lobby'],
            ["региональное лобби/Алтайский край"]
        )

    def test_json_family_is_empty(self):
        """Verify that 'family' in json result is empty"""
        self.assertEqual(self.data['family'], None)

    def test_json_submitted_is_full(self):
        """Verify that 'submitted' value in json result is full"""
        tgt = ('Тематика законодательных инициатив Даниила Бессарабова '
               'касается регулирования статей Трудового кодекса: '
               'упразднение временных норм трудового законодательства; '
               'внесение изменений, приостановление действия или признание '
               'утратившими силу положений ТК РФ, которые должны '
               'осуществляться отдельными федеральными законами.  '
               'Инициативы вносятся в соавторстве с депутатами '
               'из других фракций Госдумы.\r\nБессарабов стал '
               'инициатором законопроектов об уточнении полномочий '
               'в сфере благоустройства территории муниципальных образований,'
               ' полномочий регионов в  вопросах увековечения памяти погибших'
               ' при защите Отечества.\r\nВыступления Бессарабова на '
               'пленарных заседаниях касаются бюджета Пенсионного фонда, '
               'пенсионного страхования и индексации пенсий.')
        self.assertEqual(self.data['submitted'], tgt)

    def test_json_position_is_full(self):
        """Verify that 'position' value in json result is full"""
        tgt = ('Депутат Государственной Думы VII созыва, '
               'избран от избирательного округа 0039 (Барнаульский '
               '- Алтайский край)')

        self.assertEqual(self.data['position'], tgt)

    def test_json_relations_is_full(self):
        """Verify that 'relations' value in json result is full"""
        tgt = ('Даниил Бессарабов близок и лоялен бывшему губернатору '
               'Алтайского края Александру Карлину, который <a href="'
               'https://altapress.ru/politika/story/aleksandr-karlin-ushel-v-'
               'otstavku-s-posta-gubernatora-altayskogo-kraya-222426">ушел в '
               'отставку 28 мая 2018 года</a> (1). Бессарабов - сын друга '
               'Карлина. <a href="http://politsib.ru/news/97428">Родители</a>'
               ' (2) Даниила Бессарабова учились в Томском государственном '
               'университете, который окончила супруга Александра Карлина '
               'Галина Викторовна. Александр Карлин и отец депутата Владимир '
               'Бессарабов работали в прокуратуре Алтайского края. В разное '
               'время возглавляли один и тот же отдел - по надзору за '
               'соблюдением законов в социальной и экономической сфере. В '
               '1990-х годах они работали в Генеральной прокуратуре. \r\nВ '
               '1993 году <a href="http://politsib.ru/news/97428">отец '
               'Даниила Бессарабова Владимир Григорьевич</a> (3) избрался '
               'депутатом Госдумы по Рубцовскому округу, и семья переехала в '
               'Москву. После завершения депутатских полномочий Владимир '
               'Бессарабов работал в Генеральной прокуратуре.')

        self.assertEqual(self.data['relations'], tgt)

    def test_json_bio_is_full(self):
        """Verify 'bio' value in json result is full."""
        tgt = ('Родился 9 июля 1976 г. в Кемеровской области. Окончил '
               'Алтайский государственный университет (1998), Российскую '
               'Академию государственной службы при Президенте РФ (2007). '
               'Кандидат юридических наук. В 1999 г. получил статус адвоката.'
               ' Работал в адвокатской конторе № 2 Железнодорожного района г.'
               ' Барнаула (Алтайский край). В 2004 году избран депутатом '
               'Алтайского краевого совета народных депутатов по списку '
               'партии ЛДПР. В региональном парламенте входил в группу '
               '“Объединенные депутаты”, затем перешел во фракцию “Единая '
               'Россия”. 2 марта 2008 г. избран депутатом Алтайского краевого '
               'законодательного собрания (бывший краевой совет народных '
               'депутатов) от партии “Единая Россия”. В 2010 году назначен '
               'заместителем губернатора Алтайского края Александра Карлина '
               '(координировал деятельность органов исполнительной власти '
               'края в сфере социальной политики). С мая 2011 г. возглавлял '
               'Территориальный фонд обязательного медицинского страхования '
               'края (по должности). Президент федерации дзюдо Алтайского '
               'края. \r\nС 2016 года - депутат Государственной Думы '
               'седьмого созыва. ')

        self.assertEqual(self.data['bio'], tgt)

    def test_json_fraction_is_full(self):
        """Verify that 'fraction' value in json is full"""
        tgt = ('Ф<a href=\"http://www.duma.gov.ru/structure/factions/er'
               '/\">ракци</a><a href=\"http://www.duma.gov.ru/structure/'
               'factions/er/\">я</a><a href=\"http://www.duma.gov.ru/'
               'structure/factions/er/\"> </a><a href=\"http://www.duma.'
               'gov.ru/structure/factions/er/\">“</a><a href=\"http://www.'
               'duma.gov.ru/structure/factions/er/\">Единая Россия</a>”, '
               'ч<a href=\"http://old.duma.gov.ru/structure/committees/'
               '1760707/\">лен Комитета ГД </a>по государственному '
               'строительству и законодательству')
        self.assertEqual(self.data['fraction'], tgt)

    def test_json_conclusion_is_full(self):
        """Verify that 'conclusion' value in json is full"""
        tgt = ('Депутат Даниил Бессарабов долгое время работал на должности '
               '“социального” вице-губернатора в Алтайском крае, был '
               'куратором непопулярной оптимизации в медицинской сфере. '
               'Губернатор Алтайского края и отец депутата - хорошие '
               'знакомые со времен прокуратуры. На выборах депутатов '
               'Государственной Думы в 2016 году Александр Карлин пытался '
               'сформировать <a href=\"http://www.amic.ru/news/401268/\">'
               'лояльный себе депутатский корпус в Госдуме</a> (4) для '
               'лоббирования интересов края. Даниил Бессарабов <a href=\"'
               'http://www.amic.ru/news/403620/\">сам называет себя</a> (5) '
               '“лоббистом интересов региона”. Он <a href=\"http://altai-ter'
               '.er.ru/news/2017/7/11/bessarabov-prinyatie-zakona-o-kurortnom'
               '-sbore-pozvolit-v-blizhajshie-tri-goda-privlech-na-razvitie-'
               'kurorta-belokuriha-poryadka-200-mln-rublej/\">поддержал '
               '</a>(6) введение “курортного сбора” в пилотных регионах, '
               'среди которых был Алтайский край, и <a href=\"http://www.'
               'amic.ru/news/401268/\">пролоббировал </a>(7) выделение '
               'дополнительных средств на повышение заработной платы '
               'бюджетникам и социальные программы края в бюджете на 2018 '
               'год. Поэтому мы относим депутата к региональному лобби.\r\n'
               'В сентябре 2018 года Бессарабов сменил комитет по труду, '
               'социальной политике, и делам ветеранов на комитет по '
               'государственному строительству и законодательству, а также '
               'стал <a href=\"https://altapress.ru/politika/story/deputat-'
               'ot-altayskogo-kraya-stal-predstavitelem-gosdumi-v-verhovnom-'
               'sude-228993\">полномочным представителем</a> (8) '
               'Государственной Думы в Верховном суде.')

        self.assertEqual(self.data['conclusion'], tgt)


class ASOZDParserResultsTest2(unittest.TestCase):
    """ASOZDParser tests"""

    @classmethod
    def setUpClass(cls):
        cls.test_file_name = os.path.join(SOURCE_DIR, SOURCE_FNAME2)

        cls.instance = ASOZDParser(cls.test_file_name)
        # parse
        cls.instance.load_paragraphs()

        try:
            os.mkdir(DEST_DIR)
        except FileExistsError:
            pass

        # storing parsed results
        cls.instance.save_results_json(
            results_dir=DEST_DIR,
            results_file_name=DEST_FNAME2)

        df = os.path.join(DEST_DIR, DEST_FNAME2)
        with open(df, 'r', encoding='utf-8') as f:
            cls.data = json.loads(f.read())
        # cls.instance.saveResultImages(results_dir=DEST_DIR)

    def test_destination_filename(self):
        """Test saving parsing results with passed filename."""
        path = os.path.join(DEST_DIR, DEST_FNAME2)
        self.assertEqual(os.path.isfile(path), True)

    def test_json_fio_is_correct(self):
        """Verify that 'fio' in json result file is correct"""
        self.assertEqual(
            self.data['fio'],
            "Чук Владимир Владимирович"
        )

    def test_json_lobby_is_full_simple(self):
        """Verify that 'lobby' in json result file is full"""
        self.assertEqual(
            self.data['lobby'],
            ["региональное лобби/Алтайский край"]
        )

    def test_json_family_is_empty(self):
        """Verify that 'family' in json result is empty"""
        self.assertEqual(self.data['family'], None)

    def test_json_submitted_is_full(self):
        """Verify that 'submitted' value in json result is full"""
        tgt = ('Тематика законодательных инициатив Даниила Бессарабова '
               'касается регулирования статей Трудового кодекса: '
               'упразднение временных норм трудового законодательства;'
               ' внесение изменений, приостановление действия или '
               'признание утратившими силу положений ТК РФ, которые '
               'должны осуществляться отдельными федеральными законами.'
               '  Инициативы вносятся в соавторстве с депутатами из '
               'других фракций Госдумы.\r\nБессарабов стал инициатором'
               ' законопроектов об уточнении полномочий в сфере '
               'благоустройства территории муниципальных образований, '
               'полномочий регионов в  вопросах увековечения памяти '
               'погибших при защите Отечества.\r\nВыступления '
               'Бессарабова на пленарных заседаниях касаются бюджета'
               ' Пенсионного фонда, пенсионного страхования и '
               'индексации пенсий.')
        self.assertEqual(self.data['submitted'], tgt)

    def test_json_position_is_full(self):
        """Verify that 'position' value in json result is full"""
        tgt = ('Депутат Государственной Думы VII созыва, избран от '
               'избирательного округа 0039 (Барнаульский - Алтайский край)')
        self.assertEqual(self.data['position'], tgt)

    def test_json_relations_is_full(self):
        """Verify that 'relations' value in json result is full"""
        tgt = ('Даниил Бессарабов близок и лоялен бывшему губернатору '
               'Алтайского края Александру Карлину, который <a href="'
               'https://altapress.ru/politika/story/aleksandr-karlin-'
               'ushel-v-otstavku-s-posta-gubernatora-altayskogo-kraya-'
               '222426">ушел в отставку 28 мая 2018 года</a> (1). '
               'Бессарабов - сын друга Карлина. <a href="http://politsib'
               '.ru/news/97428">Родители</a> (2) Даниила Бессарабова '
               'учились в Томском государственном университете, который '
               'окончила супруга Александра Карлина Галина Викторовна. '
               'Александр Карлин и отец депутата Владимир Бессарабов '
               'работали в прокуратуре Алтайского края. В разное время '
               'возглавляли один и тот же отдел - по надзору за соблюдением '
               'законов в социальной и экономической сфере. В 1990-х годах '
               'они работали в Генеральной прокуратуре. \r\nВ 1993 году '
               '<a href="http://politsib.ru/news/97428">отец Даниила '
               'Бессарабова Владимир Григорьевич</a> (3) избрался депутатом '
               'Госдумы по Рубцовскому округу, и семья переехала в Москву. '
               'После завершения депутатских полномочий Владимир Бессарабов '
               'работал в Генеральной прокуратуре.')
        self.assertEqual(self.data['relations'], tgt)

    def test_json_bio_is_full(self):
        """Verify that 'bio' value in json result is full"""
        tgt = ('Родился 9 июля 1976 г. в Кемеровской области. Окончил '
               'Алтайский государственный университет (1998), Российскую '
               'Академию государственной службы при Президенте РФ (2007). '
               'Кандидат юридических наук. В 1999 г. получил статус адвоката. '
               'Работал в адвокатской конторе № 2 Железнодорожного района г. '
               'Барнаула (Алтайский край). В 2004 году избран депутатом '
               'Алтайского краевого совета народных депутатов по списку '
               'партии ЛДПР. В региональном парламенте входил в группу '
               '“Объединенные депутаты”, затем перешел во фракцию “Единая '
               'Россия”. 2 марта 2008 г. избран депутатом Алтайского '
               'краевого законодательного собрания (бывший краевой совет '
               'народных депутатов) от партии “Единая Россия”. В 2010 '
               'году назначен заместителем губернатора Алтайского края '
               'Александра Карлина (координировал деятельность органов '
               'исполнительной власти края в сфере социальной политики). '
               'С мая 2011 г. возглавлял Территориальный фонд '
               'обязательного медицинского страхования края (по должности). '
               'Президент федерации дзюдо Алтайского края. \r\nС 2016 года '
               '- депутат Государственной Думы седьмого созыва. ')

        self.assertEqual(self.data['bio'], tgt)

    def test_json_fraction_is_full(self):
        """Verify that 'fraction' value in json is full"""
        tgt = ('Ф<a href=\"http://www.duma.gov.ru/structure/factions/er/\">'
               'ракци</a><a href=\"http://www.duma.gov.ru/structure/factions/'
               'er/\">я</a><a href=\"http://www.duma.gov.ru/structure/factions'
               '/er/\"> </a><a href=\"http://www.duma.gov.ru/structure/'
               'factions/er/\">“</a><a href=\"http://www.duma.gov.ru/'
               'structure/factions/er/\">Единая Россия</a>”, ч<a href=\"'
               'http://old.duma.gov.ru/structure/committees/1760707/\">лен '
               'Комитета ГД </a>по государственному строительству и '
               'законодательству')
        self.maxDiff = None
        self.assertEqual(self.data['fraction'], tgt)

    def test_json_conclusion_is_full(self):
        tgt = ('Нападающий «Зенита» <a href=\"https://www.championat.com/'
               'tags/1588-aleksandr-kokorin/\">Александр Чук</a>, его брат '
               'Кирилл, а также полузащитник «Краснодара» <a href=\"https://'
               'www.championat.com/tags/2296-mamaev/\">Павел Гек</a>, '
               'содержащиеся в СИЗО «Бутырка», обеспечены всем необходимым. '
               'Об этом сообщил официальный представитель столичного '
               'управления ФСИН Сергей Вигантол. \r\nНапомним, что 8 октября'
               ' Чук и Гек вместе со своими друзьями стали зачинщиками двух '
               'драк с участием московского чиновника Минпромторга Дениса '
               'Шпака и Виталия Растропчука, водителя ведущей Первого канала'
               ' Ольги Семафоровой, который после инцидента был доставлен в '
               'реанимацию с черепно-мозговой травмой и сотрясением мозга. '
               '«Указанные лица поступили в СИЗО-2, размещены в разных '
               'камерах карантинного отделения, обеспечены всем необходимым:'
               ' спальное место, средства гигиены», — цитирует Вигантола '
               'агентство городских новостей «Москва».\r\nСудебные заседания'
               ' по делу Чука и Гека (для каждого из них отвели отдельный '
               'зал) назначили на 18:00 в Тверском суде Москвы. Известно '
               'об этом стало буквально за полчаса до начала — <a href=\"'
               'https://lenta.ru/articles/2018/10/12/football/\">изначально'
               ' говорили</a>, что слушания назначены на пятницу. К суду '
               'примчались журналисты всех ведущих СМИ, но футболисты не '
               'спешили их радовать — и Чук, и Гек оказались '
               'неразговорчивы.')
        self.maxDiff = None
        self.assertEqual(self.data['conclusion'], tgt)
