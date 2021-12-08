#!/usr/bin/env python3
#-*- coding=utf-8 -*-
## export phylogenetic data from UraLex basic vocabulary dataset

import sys

def checkPythonVersion():
    if (sys.version_info[0] < 3):
        print("Python 3 is needed to run this program.")
        sys.exit(1)

checkPythonVersion()
        
import os
import io
import argparse
import urllib.request
import reader
import versions
import exporter

#implied constants
PARSER_DESC           = "Export phylogenetic formats from BEDLAN spreadsheet data."
DEFAULT_NEXUS_DIALECT = "beast"
DEFAULT_CHARSETS      = True
DEFAULT_MEANING_LIST  = "all"

parser = argparse.ArgumentParser(description=PARSER_DESC)

parser.add_argument("-o","--output",
                    dest="outfile",
                    help="output to file OUTFILE. If not set, will output to STDOUT",
                    metavar="OUTFILE")
parser.add_argument("-x","--exclude-taxa",
                    dest="exclude_taxa",
                    help="comma-separated list of taxa to exclude",
                    default="",
                    type=str)
parser.add_argument("-l","--meaning-list",
                    dest="meaning_list",
                    help="meaning list to use. Defaults to \"" + DEFAULT_MEANING_LIST + "\"",
                    default=DEFAULT_MEANING_LIST,
                    type=str)
parser.add_argument("-f","--format",
                    dest="format",
                    help="Export format. Valid options: nexus, cldf.",
                    default="nexus",
                    type=str)
parser.add_argument("-d","--dialect",
                    dest="dialect",
                    help="NEXUS dialect: mrbayes, beast, splitstree. Defaults to \"" + DEFAULT_NEXUS_DIALECT + "\"",
                    default=DEFAULT_NEXUS_DIALECT)
parser.add_argument("-1","--no-charsets",
                    dest="charsets",
                    help="Export without separate characters sets for each meaning",
                    default=DEFAULT_CHARSETS,                    
                    action='store_false')
parser.add_argument("-c","--correlate",
                    dest="correlate",
                    action='store_true',
                    help="Export correlate characters instead of cognate (root-meaning form) characters.")
parser.add_argument("-r","--raw_folder",
                    dest="raw_folder",
                    action='store_true',
                    help="Look for data in an uncompressed 'raw' folder rather than a released zip file.")

if __name__ == '__main__':
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    args = parser.parse_args()

    excluded_languages = []
    if args.exclude_taxa != "":
        excluded_languages = args.exclude_taxa.split(",")
    dialect = args.dialect
    if (args.raw_folder == True):
        dataset = reader.UraLexReader("raw", args.correlate)
    else:
        dataset = reader.UraLexReader(versions.getLatestVersion(), args.correlate)

    exporter = exporter.UralexExporter(dataset)
    exporter.setMeaningList(args.meaning_list)
    exporter.setLanguageExcludeList(excluded_languages)
    exporter.setFormat(args.format, args.dialect)
    exporter.setCharsets(args.charsets)

    #print("Export")

    outlines = exporter.export()

    if args.outfile != None:
        if os.path.isfile(args.outfile):
            while True:
                prompt = input("File " + args.outfile + " already exists. Overwrite? (y/n)")
                if (prompt == "y" or prompt == "n"):
                    break
            if (prompt == "n"):
                print("File not written.")
                sys.exit()
        f = open(args.outfile,"w")
        for line in outlines:
            f.write(line + "\n")
        f.close()

    else:
        for line in outlines:
            print(line)
