#!/usr/bin/python3
# Reader class for UraLex files

import io
import os
import sys
import zipfile
import urllib.request
import csv

DATA_MAIN_FILE           = 'Data.tsv'
LANGUAGE_FILE            = 'Languages.tsv'
MLISTS_FILE              = 'Meaning_lists.tsv'
MNAMES_FILE              = 'Meanings.tsv'
MISSING_VALUES           = ("?","0")
MULTISTATE_CHARS         = "abcdefghijklmnopqrstuvwxyz123456789"

class UraLexReader:
    def __init__(self, version, args):
        if version == "raw":
            self._readCustomVersion(version)
        else:
            self._readReleaseVersion(version)
        self._data = self._addUralexLanguageCode()
        self._meaning_list = args.meaning_list
        self.excluded_languages = args.exclude_taxa.split(",")
        self._data = self._filterLanguages(self.excluded_languages)
        self._meanings = self._getMeaningsFromList(args.meaning_list)
        self._data = self._filterMeanings()
        self._missing_values = MISSING_VALUES
        if args.no_singletons:
            self._data = self._filterSingletons(args.correlate)
        self._meanings = self.getMeanings(True)
        self._languages = self.getLanguages(True)
        self._meaning_list = args.meaning_list
        self._data_dict = self._getDataDict(args.correlate)
        self._mnglists_dict = self._getMngListsDict()
        self.MULTISTATE_CHARS = MULTISTATE_CHARS

    def __del__(self):
        pass

    def _readCsv(self, filename):
        rows = []
        reader = csv.DictReader(filename, delimiter="\t")
        for row in reader:
            rows.append(row)
        return rows
    
    def getMeaningLists(self):
        '''Return a list of all meaning lists'''
        mnglists = []
        for i in self._mlists[0].keys():
            if i not in ["LJ_rank","uralex_mng","mng_item"]:
                mnglists.append(i)
        return sorted(mnglists)

    def getMeaningList(self, not_cached=False):
        '''Return the current meaning list of the data. Use not_cached=True to update cached version.'''
        if not_cached:
            output = []
            for row in self._data:
                if row["uralex_mng"] not in output:
                    output.append(row["uralex_lang"])
            return output
        return self._meaning_list
    
    def getLanguages(self, not_cached =False):
        '''Return a list of languages. Use not_cached=True to update cached version'''
        if not_cached:
            output = []
            for row in self._data:
                if row["uralex_lang"] not in output:
                    output.append(row["uralex_lang"])
            return sorted(output)
        return self._languages

    def getMeanings(self, mnglist="all"):
        '''Return list of meanings belonging to mnglist'''
        return sorted(self._meanings)

    def getCharacterAlignment(self, language, meaning):
        '''Return character alignment of meaning in language'''
        result = self._data_dict[language][meaning]
        if "?" in result:
            return result
        return sorted(result,
                      key=lambda word: [MULTISTATE_CHARS.index(c) for c in word])

    def getVersion(self):
        '''Return dataset version'''
        return self._version

    def _readCustomVersion(self,folder):
        '''Read custom version from an extracted raw folder'''
        self._version = "custom"
        try:
            self._languages   = self._readCsv(open(os.path.join("raw", LANGUAGE_FILE)))
            self._mlists      = self._readCsv(open(os.path.join("raw", MLISTS_FILE)))
            self._mnames      = self._readCsv(open(os.path.join("raw", MNAMES_FILE)))
            self._data        = self._readCsv(open(os.path.join("raw", DATA_MAIN_FILE)))

        except:
            print("Could not load raw folder contents. Please ensure that you have a 'raw' folder containing all the TSV files.")
            sys.exit(1)

    def _downloadDataset(self,version):
        '''Download the dataset specified by version'''
        while True:
            print("Dataset not found. Download latest version? (y/n)", file=sys.stderr)
            prompt = input()
            if (prompt == "y" or prompt == "n"):
                break
        if (prompt == "n"):
            print("Aborting.")
            sys.exit()
        print("Downloading %s" % version["zipfile"], file=sys.stderr)
        urllib.request.urlretrieve(version["url"],version["zipfile"])
            
    def _readReleaseVersion(self,version):
        '''Read release version from zip file. Download if necessary.'''
        self._version = os.path.splitext(version["zipfile"])[0]
        if os.path.isfile(version["zipfile"]) == False:
            self._downloadDataset(version)
        try:
            z = zipfile.ZipFile(version["zipfile"])
            self._languages   = self._readCsv(io.TextIOWrapper(z.open(version["dir"] + "/raw/" + LANGUAGE_FILE)))
            self._mlists      = self._readCsv(io.TextIOWrapper(z.open(version["dir"] + "/raw/" + MLISTS_FILE)))
            self._mnames      = self._readCsv(io.TextIOWrapper(z.open(version["dir"] + "/raw/" + MNAMES_FILE)))
            self._data        = self._readCsv(io.TextIOWrapper(z.open(version["dir"] + "/raw/" + DATA_MAIN_FILE)))
            z.close()
        except:
            print("%s: Could not load dataset zip file contents." % version["zipfile"], file=sys.stderr)
            sys.exit(1)

    def _getCognSetOrder(self):
        '''Return a list of all cogn_set values present in the data matrix, with
        one-character sets in an alphabetical order, followed by two-character sets in
        an alphabetical order.'''
        cogn_sorting_order = []
        one_char = []
        two_char = []
        cogn_characters = []
        for row in self._data:
            cogn_characters.append(row["cogn_set"])
        cogn_characters = set(cogn_characters)
        for i in cogn_characters:
            try:
                a,b = i
                two_char.append(i)
            except:
                if i not in self._missing_values:
                    one_char.append(i)
        cogn_sorting_order += sorted(one_char) + sorted(two_char)
        return(cogn_sorting_order)

    def _getFormSetOrder(self):
        '''Return a list of all form_set values present in the data matrix, in an ascending order.'''
        forms = []
        form_characters = []
        for row in self._data:
            form_characters.append(row["form_set"])
        form_characters = set(form_characters)

        for i in form_characters:
            if i not in self._missing_values:
                forms.append(i)
        forms.sort(key=int)
        return(forms)

    def _getMngListsDict(self):
        '''Return a meaning list dict, including an "all" list containing all meanings'''
        mnglists = {}
        for k in self._mlists[0].keys():
            if k not in ["LJ_rank","uralex_mng","mng_item"]:
                mnglists[k] = []
        for row in self._mlists:
            for mlist in mnglists.keys():
                if row[mlist] == "1":
                    mnglists[mlist].append(row["uralex_mng"])
        mnglists["all"] = []
        for row in self._mlists:
            mnglists["all"].append(row["uralex_mng"])
        return mnglists

    def _addUralexLanguageCode(self):
        '''Add ASCII language codes to raw data to ease processing'''
        if "uralex_lang" in self._data[0].keys():
            return self._data
        output  = []
        for d_row in self._data:
            for l_row in self._languages:
                if l_row["lgid3"] == d_row["lgid3"]:
                    d_row["uralex_lang"] = l_row["ASCII_name"]
                    break
            output.append(d_row)
        return output

    def _filterLanguages(self,excluded_langs):
        '''Remove excluded languages from data'''
        output = []
        for row in self._data:
            if row["uralex_lang"] in excluded_langs:
                continue
            output.append(row)
        return(output)

    def _getMeaningsFromList(self,meaning_list):
        output = []
        mlists = []
        for i in self._mlists[0].keys():
            if i not in ["uralex_mng", "LJ_rank", "mng_item"]:
                mlists.append(i)
        for row in self._mlists:
            if meaning_list == "all":
                output.append(row["uralex_mng"])
                continue
            if row[meaning_list] == "1":
                output.append(row["uralex_mng"])
                continue
        return output
    
    def _filterMeanings(self):
        '''Remove meanings from data'''
        output = []
        for row in self._data:
            if row["uralex_mng"] in self._meanings:
                output.append(row)
        return output
            
    def _filterSingletons(self, use_correlate_chars):
        '''Remove singletons from data'''
        output = []
        if use_correlate_chars == True:
            data_field = "form_set"
        else:
            data_field = "cogn_set"
        mngs = {}
        for row in self._data:
            m = row["uralex_mng"]
            d = row[data_field]
            if d in MISSING_VALUES:
                continue
            try:
                mngs[m].append(d)
            except KeyError:
                mngs[m] = [d]
        #print(mngs)
        count = 0
        to_filter = {}
        for mng in mngs:
            to_filter[mng] = []
            for item in set(mngs[mng]):
                if mngs[mng].count(item) == 1:
                    to_filter[mng].append(item)
                    count += 1
        for row in self._data:
            if row[data_field] in to_filter[row["uralex_mng"]]:
                continue
            output.append(row)
        for k in sorted(to_filter.keys()):
            print(k + ": " + str(sorted(to_filter[k])),file=sys.stderr)
        print("Removed %i singletons." % count, file=sys.stderr)
        return output
            
    def _getDataDict(self,use_correlate_chars):
        '''Return a data dict with [ASCII_name][mng] structure'''
        if use_correlate_chars == True:
            char_set_order = self._getFormSetOrder()
        else:
            char_set_order = self._getCognSetOrder()
        char_set_dict = {}
        data_matrix = {}
        for lang in self.getLanguages():
            data_matrix[lang] = {}
        meaning_set = self.getMeanings()
        for lang in data_matrix.keys():
            for mng in meaning_set:
                data_matrix[lang][mng] = []
        for row in self._data:
            current_language = row["uralex_lang"]
            current_meaning = row["uralex_mng"]
            if use_correlate_chars == True:
                current_data = row["form_set"].strip().rstrip()
            else:
                current_data = row["cogn_set"].strip().rstrip()
            if current_data == "0":
                current_data = "?"
            data_matrix[current_language][current_meaning].append(current_data)
        return data_matrix
    
if __name__ == '__main__':
    print("Reader class for UraLex dataset")
