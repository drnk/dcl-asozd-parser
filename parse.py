import argparse
import logging
import os
import re
import traceback

from asozd import ASOZDParser


logger = logging.getLogger(__name__)
logging.basicConfig()
logging.getLogger().setLevel(logging.INFO)  # default level is INFO

DEBUG = False

if __name__ == '__main__':

    # arguments definition
    parser = argparse.ArgumentParser(
        description="""Convert specific structured Open Office XML files into json.

./parser.py "in"
./parser.py "filename.docx"
""",
        formatter_class=argparse.RawTextHelpFormatter
    )

    # file name
    parser.add_argument(
        'f',
        metavar='file_name',
        type=str,
        help=('filename (*.docx) or directory for parsing. '
              'Only *.docx files will be parsed')
    )

    # destination
    parser.add_argument(
        "-d",
        help="Destination directory ('out' used by default)"
    )

    # json file name
    parser.add_argument(
        "-j",
        help=("Destination file name (without extension) "
              "if fileName references to file")
    )

    # debug mode
    parser.add_argument(
        "-v",
        action="store_true",
        help="Increase output verbosity"
    )

    args = parser.parse_args()

    if args.debug_mode:
        DEBUG = True
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        is_directory = os.path.isdir(args.fname)
    except FileNotFoundError:
        raise ValueError((
            f"Couldn't determine is [{args.fname}]"
            " a folder or file. Possible "
            "the name is incorrect. Please verify."))

    dest_file_name = args.jsonFileName

    if is_directory:
        logger.info('Directory detected: {}'.format(args.fname))
        target_list = os.listdir(args.fname)
        target_dir = args.fname

        dest_file_name = None
    else:
        logger.info('File detected: {}'.format(args.fname))
        target_list = [args.fname]

    def parse_file(file_name, dest_dir, dest_file_name):
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

    def is_filename_fit(file_name):
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

    if is_directory:
        # traverse root directory, and list directories
        # as dirs and files as files
        for folder, dirs, files in os.walk(target_dir):
            for file_name in files:
                full_file_name = os.path.join(folder, file_name)
                if is_filename_fit(file_name):
                    parse_file(
                        full_file_name,
                        args.destination,
                        dest_file_name
                    )

    else:
        file_name = os.path.basename(args.fname)
        if is_filename_fit(file_name):
            parse_file(args.fname, args.destination, dest_file_name)
