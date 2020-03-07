import logging
import os
import re
import traceback

from asozd import ASOZDParser

from clize import run


logger = logging.getLogger(__name__)
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)  # default level is INFO

DEBUG = False


def parse_file(file_name: str,
               dest_dir: str = None,
               dest_file_name: str = None) -> None:
    logger.info('Looking {} file for valuable content.'.format(file_name))

    try:
        # parser init
        P = ASOZDParser(file_name, debug=DEBUG)
        # parse
        P.load_paragraphs()
        # storing parsed results
        P.save_all_results(
            results_dir=dest_dir,
            results_file_name=dest_file_name
        )
    except KeyboardInterrupt:
        raise
    except:
        logging.error('='*50)
        logging.error("!!!PARSING ERROR OCCURED!!!")
        logging.error("Error occurred during parsing file: %s" % file_name)
        logging.error(traceback.format_exc())
        logging.error('='*50)


def is_filename_fit(file_name: str) -> bool:
    result = True

    if not file_name.endswith('.docx') or file_name.startswith('~$'):
        logger.info(
            'Skipping {} as non supportable file.'.format(file_name)
        )
        result = False

    # skip dead and left out
    if re.search(r"(ВЫБЫЛ(А)?|УМЕР(ЛА)?|СДАЛ)", file_name):
        logger.info(
            'Skipping {} as left out or dead person.'.format(file_name)
        )
        result = False

    # skip technical files
    if re.search(r"^Вопросы", file_name):
        logger.info('Skipping {} as technical document.'.format(file_name))
        result = False

    return result


def parser(file_name: str,
           destination: str = None,
           json_file: str = None,
           verbose: bool = False) -> None:
    """
    Convert specific structured Open Office XML files into json.

    :param file_name: filename (*.docx) or directory for parsing.
                      Only *.docx files will be parsed
    :param destination: Destination directory ('out' used by default)
    :param json_file: Destination file name (without extension).
                      Works only if file_name references to file
    :param verbose: Increase output verbosity
    """

    try:
        is_directory = os.path.isdir(file_name)
    except FileNotFoundError:
        raise ValueError((
            f"Couldn't determine is [{file_name}]"
            " a folder or file. Possible "
            "the name is incorrect. Please verify."))

    dest_file_name = json_file

    if is_directory:
        logger.info('Directory detected: {}'.format(file_name))
        # target_list = os.listdir(file_name)
        target_dir = file_name

        dest_file_name = None
    else:
        logger.info('File detected: {}'.format(file_name))
        # target_list = [file_name]

    if is_directory:
        # traverse root directory, and list directories
        # as dirs and files as files
        for folder, dirs, files in os.walk(target_dir):
            for file_name in files:
                full_file_name = os.path.join(folder, file_name)
                if is_filename_fit(file_name):
                    parse_file(
                        full_file_name,
                        destination,
                        dest_file_name
                    )

    else:
        base_file_name = os.path.basename(file_name)
        if is_filename_fit(base_file_name):
            parse_file(file_name, destination, json_file)


if __name__ == '__main__':
    run(parser)
