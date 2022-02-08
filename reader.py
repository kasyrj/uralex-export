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
MLISTS_DESC_FILE         = 'Meaning_list_descriptions.tsv'
CITATION_FILE            = 'Citation_codes.tsv'
MNAMES_FILE              = 'Meanings.tsv'
MISSING_VALUES           = ("?","0")
MULTISTATE_CHARS         = "abcdefghijklmnopqrstuvwxyz123456789"


class UraLexReader:
    def __init__(self, version, use_correlate_chars):
        if version == "raw":
            self._readCustomVersion(version)
        else:
            self._readReleaseVersion(version)
        self._detectFields()
        self._missing_values = MISSING_VALUES
        self._language_dict = self._getLanguageDict()
        self._data_dict = self._getDataDict(use_correlate_chars)
        self._mnglists_dict = self._getMngListsDict()
        self.MULTISTATE_CHARS = MULTISTATE_CHARS
        self._language_id = None
        self._language_ascii_id = None

    def __del__(self):
        pass

    def _detectFields(self):
        '''Detect whether using uralex1/2 fields or uralex3 fields and set up accordingly'''
        # language_id
        if "lgid3" in self._data.keys():
            self._language_id = "lgid3"
        elif "uralex_lang" in self._data.keys():
            self._language_id = "uralex_lang"
        # language_ascii_id
        if "ASCII_name" in self._languages.keys():
            self._language_ascii_id = "ASCII_name"
        elif "uralex_lang" in self._languages.keys(): 
            self._language_ascii_id = "uralex_lang"
            
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
                
    def getLanguages(self):
        '''Return a dict with lgid3 keys and ASCII_name values of languages.'''
        return self._language_dict

    def getMeanings(self, mnglist="all"):
        '''Return list of meanings belonging to mnglist'''
        mngs = []
        if mnglist == "all":
            for row in self._data:
                mngs.append(row["uralex_mng"])
            mngs = set(mngs)
        else:
            for row in self._mlists:
                if row[mnglist] == "1":
                    mngs.append(row["uralex_mng"])
        return sorted(mngs)

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
            
    def _getLanguageDict(self):
        '''Generate a language dict (key: lgid3, value: ASCII_name)'''
        lgid3_set = []
        for row in self._data:
            lgid3_set.append(row[self._language_id])
        lgid3_set = set(lgid3_set)
        language_dict = {}
        for key in lgid3_set:
            for row in self._languages:
                if row["lgid3"] == key:
                    language_dict[key] = row[self._languages_ascii_id]
                    break
        return language_dict
    
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

    def _getDataDict(self,use_correlate_chars):
        '''Return a data dict with [language_ascii_name][mng] structure'''
        if use_correlate_chars == True:
            char_set_order = self._getFormSetOrder()
        else:
            char_set_order = self._getCognSetOrder()
        char_set_dict = {}
        for i in range(len(char_set_order)):
            char_set_dict[char_set_order[i]] = MULTISTATE_CHARS[i] #  all characters internally represented like MULTISTATE_CHARS

        data_matrix = {}
        for i in self._language_dict.values():
            data_matrix[i] = {}
        meaning_set = []
        for row in self._data:
            meaning_set.append(row["uralex_mng"])
        meaning_set = set(meaning_set)
        for lang in data_matrix.keys():
            for mng in meaning_set:
                data_matrix[lang][mng] = []
        for row in self._data:
            current_language = row[self._language_id]
            current_meaning = row["uralex_mng"]
            if use_correlate_chars == True:
                current_data = row["form_set"].strip().rstrip()
            else:
                current_data = row["cogn_set"].strip().rstrip()
            l = self._language_dict[current_language]
            if current_data == "0":
                continue
            elif current_data == "?":
                data_matrix[l][current_meaning].append(current_data)
                continue
            data_matrix[l][current_meaning].append(char_set_dict[current_data])
        return data_matrix
    
if __name__ == '__main__':
    print("Reader class for UraLex dataset")
