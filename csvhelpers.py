#!/usr/bin/python3
## CSV helper functions

import sys
import csv

CSV_DELIMITER = '\t'

def readCsv(file_object, as_dict=False):
    '''Return a list or dict version of CSV/TSV'''
    out = []
    reader = csv.reader(file_object, delimiter=CSV_DELIMITER, dialect="excel")
    for line in reader:
        out.append(line)
    if as_dict == True:
        out = parseCsvListAsDict(out)
    return out

def parseCsvListAsDict(csv_list):
    '''Return a dict version of CSV/TSV with headers from the first row as keys. Headerless columns are omitted.'''
    out = {}
    headers = []
    for col_num in range(len(csv_list[0])):
        if csv_list[0][col_num] != "":
            headers.append(csv_list[0][col_num])
    if (len(set(headers)) != len(headers)):
        print("ERROR: column headers must be unique for dict conversion", file=sys.stderr)
        sys.exit(1)
    for col_num in range(len(csv_list[0])):
        header = csv_list[0][col_num]
        out[header] = []
        for row_num in range(1,len(csv_list)):
            out[header].append(csv_list[row_num][col_num])
    return out

if __name__ == '__main__':
    print("CSV helper functions")
