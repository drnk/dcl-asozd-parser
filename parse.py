import argparse, os

from stat import ST_MODE, S_ISDIR, S_ISREG

from asozd import ASOZDParser
from DOCX import DOCXDocument, DOCXParagraph, DOCXItem


DEBUG = True

if __name__ == '__main__':
    # arguments definition
    parser = argparse.ArgumentParser(description="""Convert ASOZD details docx into json.

Example (Windows): python parser.py "in"
                   python parser.py "filename.docx"
                   
Example (Unix): ./parser.py "in"
                ./parser.py "filename.docx\"""", formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('fname', metavar='fileName', type=str,
        help='filename (*.docx) or directory for parsing. Only *.docx files will be parsed')

    parser.add_argument("-d", "--destination", help="Destination directory ('out' used by default)")
    parser.add_argument("-j", "--jsonFileName", help="Destination file name (without extension) if fileName references to file")

    args = parser.parse_args()

    try:
        mode = os.stat(args.fname)[ST_MODE]
    except FileNotFoundError:
        raise ValueError("Couldn't determine is [%s] a folder or file. Possible " % args.fname +\
            "the name is incorrect. Please verify.")

    is_directory = False
    dest_file_name = args.jsonFileName
    if S_ISDIR(mode):
        # directory
        print('Directory detected: %s' % args.fname)
        target_list = os.listdir(args.fname)
        is_directory = True
        dest_file_name = None
    elif S_ISREG(mode):
        # file
        print('File detected: %s' % args.fname)
        target_list = [args.fname]
    else:
        raise ValueError("fileName [%s] contains non folder and non file value")

    for fname in target_list:
        if not fname.endswith('.docx') or fname.startswith('~$'):
            print('Skipping %s as non supportable file.' % fname)
            continue

        print('Looking %s file for valuable content.' % fname)

        # parser init
        P = ASOZDParser(args.fname + '\\' + fname if is_directory else args.fname, debug_mode=DEBUG)
        
        # parse start
        P.load_paragraphs()

        #pprint(P.getInternalResults())

        # storing parsed results
        P.save_results(results_dir=args.destination, results_file_name=dest_file_name)
        P.save_result_images(results_dir=args.destination)

