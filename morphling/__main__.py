#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import getopt
from morphling.parser import MarkdownParser


def print_usage():
    print('''Usage: python -m morphling  FILE_PATH [OPTIONS...]
Morphling is a tool that converts markdown to html files.
Options:
  -o/--output=OUTPUT FILE        path to output file
  -e/--escape=no                 specify if you don't need to escape
''')


def main():
    do_not_escape = True
    try:
        source_file = sys.argv[1]
    except IndexError:
        print('source file not specified.')
        print_usage()
        sys.exit(2)
    output_path = '.'.join([source_file.split('.')[0], 'html'])
    try:
        opts, args = getopt.getopt(sys.argv[2:], 'ho:e:', ['help', 'output=', 'escape='])
    except getopt.GetoptError as e:
        print(str(e))
        sys.exit(2)
    for o, a in opts:
        if o in ('-h', '--help'):
            print_usage()
            sys.exit(2)
        if o in ('-e', '--escape'):
            do_not_escape = False
        if o in ('-o', '--output'):
            output_path = a
    mdp = MarkdownParser(source_path=source_file, output_path=output_path, escape=do_not_escape)
    mdp.parse_file()


main()
