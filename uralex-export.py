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
import errno
import argparse
import urllib.request
import reader
import versions
import exporter

#implied constants
PARSER_DESC           = "Export phylogenetic formats from the raw files of UraLex basic vocabulary dataset."
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
parser.add_argument("-c","--correlate",
                    dest="correlate",
                    action='store_true',
                    default=False,
                    help="Export correlate characters instead of cognate (root-meaning form) characters.")
parser.add_argument("-r","--raw_folder",
                    dest="raw_folder",
                    action='store_true',
                    help="Look for data in an uncompressed 'raw' folder rather than a released zip file.")
parser.add_argument("-S","--no-singletons",
                    dest="no_singletons",
                    action='store_true',
                    default=False,
                    help="Remove singleton sites from data.")
parser.add_argument("-L","--charset-labels",
                    dest="charset_labels",
                    action='store_true',
                    default=False,
                    help="(NEXUS) Include charset labels.")
parser.add_argument("-1","--no-charsets",
                    dest="charsets",
                    help="(NEXUS) Export without separate characters sets for each meaning",
                    default=DEFAULT_CHARSETS,                    
                    action='store_false')
parser.add_argument("-d","--dialect",
                    dest="dialect",
                    help="(NEXUS) NEXUS dialect: mrbayes, beast, splitstree. Defaults to \"" + DEFAULT_NEXUS_DIALECT + "\"",
                    default=DEFAULT_NEXUS_DIALECT)



if __name__ == '__main__':
    
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    args = parser.parse_args()

    if args.charset_labels and args.dialect != 'beast':
        print("Forcing beast dialect", file=sys.stderr)
        args.dialect="beast"

    excluded_languages = []
    if args.exclude_taxa != "":
        excluded_languages = args.exclude_taxa.split(",")
    dialect = args.dialect
    if (args.raw_folder == True):
        dataset = reader.UraLexReader("raw", args)
    else:
        dataset = reader.UraLexReader(versions.getLatestVersion(), args)

    exporter = exporter.UralexExporter(dataset, args)
    # exporter.setMeaningList(args.meaning_list)
    # exporter.setLanguageExcludeList(excluded_languages)

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
            try:
                print(line)
            # handle broken pipe
            except IOError as e:
                if e.errno == errno.EPIPE:
                    sys.exit(0)

