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


def filter_filenames(dirpath, predicate):
    """Usage:

           >>> for filename in filter_filenames('/', re.compile(r'/home.*\.bak').match):
           ....    # do something
    """
    for dir_, dirnames, filenames in os.walk(dirpath):
        for filename in filenames:
            abspath = os.path.join(dir_, filename)
            if predicate(abspath):
                yield abspath


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


def parser(source: str,
           *,
           source_mask: str = None,
           destination: str = None,
           verbose: bool = False) -> None:
    """
    Convert specific structured Open Office XML files into json.

    :param source: filename or directory for parsing.
                   Only *.docx files will be parsed in case of directory.
    :param source_mask: regexp mask for iterating over files if `source`
        is a directory
    :param destination: Destination directory ('out' used by default)
    :param json_file: Destination file name (without extension).
                      Works only if file_name references to file
    :param verbose: Increase output verbosity
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    abs_source = os.path.abspath(source)
    logger.info('Passed %s as a source file/dir name', abs_source)

    if not os.path.exists(abs_source):
        raise ValueError((
            f"Couldn't find or access a '{source}'"
            " folder or file. Please verify."))

    is_dir = os.path.isdir(abs_source)

    if is_dir:
        # -------------------------------------------------
        # DIRECTORY processing
        # -------------------------------------------------
        logger.info('  Directory detected: %s', abs_source)


        # No extra work needed. abs_source stores
        # the full path to source data
        source_dir = abs_source

        if source_mask:
            logger.info('  Source mask: %s', source_mask)
            check_re = re.compile(source_mask)

            #'\\t'.encode().decode('unicode_escape')
            logger.debug('[%s] and pattern: [%s]', str(check_re), check_re.pattern)
            predicate = check_re.match
        else:
            logger.info('Parameter `source_mask` hasn''t passed ')
            predicate = is_filename_fit

        logger.debug('source_dir=[%s]; predicate=[%s]', source_dir, str(predicate))
        for docx_item in filter_filenames(source_dir, predicate):
            logger.info('  >>>...>>>...>>>... Start processing file: %s', docx_item)
            parse_file(docx_item, destination)

    else:
        # -------------------------------------------------
        # FILE processing
        # -------------------------------------------------
        logger.info('File detected: %s', abs_source)

        file_name = os.path.basename(abs_source)
        if is_filename_fit(file_name):
            parse_file(abs_source, destination)


if __name__ == '__main__':
    run(parser)
