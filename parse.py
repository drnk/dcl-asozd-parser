import argparse
import os
import re
import traceback

from asozd import ASOZDParser
#from DOCX import DOCXDocument, DOCXParagraph, DOCXItem


DEBUG = False

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
    parser.add_argument("-dbg", "--debug_mode", help="Debug mode")

    args = parser.parse_args()

    if args.debug_mode:
        DEBUG = True

    try:
        is_directory = os.path.isdir(args.fname)
    except FileNotFoundError:
        raise ValueError("Couldn't determine is [%s] a folder or file. Possible " % args.fname +\
            "the name is incorrect. Please verify.")

    dest_file_name = args.jsonFileName
    
    if is_directory:
        print('Directory detected: %s' % args.fname)
        target_list = os.listdir(args.fname)
        target_dir = args.fname

        dest_file_name = None
    else:
        print('File detected: %s' % args.fname)
        target_list = [args.fname]

    def parse_file(file_name, dest_dir, dest_file_name):
        print('Looking %s file for valuable content.' % file_name)

        try:
            # parser init
            P = ASOZDParser(file_name, debug=DEBUG)
            # parse
            P.load_paragraphs()
            # storing parsed results
            P.save_all_results(results_dir=dest_dir, results_file_name=dest_file_name)
        except KeyboardInterrupt:
            raise
        except:
            print('='*50)
            print("!!!PARSING ERROR OCCURED!!!")
            print("Error occurred during parsing file: %s" % file_name)
            print(traceback.format_exc())
            print('='*50)


    def is_filename_fit(file_name): 
        result = True

        if not file_name.endswith('.docx') or file_name.startswith('~$'):
            print('Skipping %s as non supportable file.' % file_name)
            result = False

        # skip dead and left out
        if re.search(r"(ВЫБЫЛ(А)?|УМЕР(ЛА)?|СДАЛ)", file_name):
            print('Skipping %s as left out or dead person.' % file_name)
            result = False

        # skip technical files
        if re.search(r"^Вопросы", file_name):
            print('Skipping %s as technical document.' % file_name)
            result = False

        return result

    if is_directory:
        # traverse root directory, and list directories as dirs and files as files
        for folder, dirs, files in os.walk(target_dir):
            for file_name in files:
                full_file_name = os.path.join(folder, file_name)
                if is_filename_fit(file_name):
                    parse_file(full_file_name, args.destination, dest_file_name)
                        
    else:
        file_name = os.path.basename(args.fname)
        if is_filename_fit(file_name):
            parse_file(args.fname, args.destination, dest_file_name)
            



