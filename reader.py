#!/usr/bin/python3
# Reader class for UraLex files

import io
import os
import sys
import zipfile
import csvhelpers
import urllib.request

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
    
    def getMeaningLists(self):
        '''Return a list of all meaning lists'''
        mnglists = []
        for i in self._mlists.keys():
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
            mngs = set(self._data["uralex_mng"])
        else:
            for i in range(len(self._mlists[mnglist])):
                if self._mlists[mnglist][i] == "1":
                    mngs.append(self._mlists["uralex_mng"][i])
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
            # self._citations   = csvhelpers.readCsv(open(os.path.join("raw", CITATION_FILE),    encoding="utf-8"), as_dict=True)
            self._languages   = csvhelpers.readCsv(open(os.path.join("raw", LANGUAGE_FILE),    encoding="utf-8"), as_dict=True)
            self._mlists      = csvhelpers.readCsv(open(os.path.join("raw", MLISTS_FILE),      encoding="utf-8"), as_dict=True)
            self._mlists_desc = csvhelpers.readCsv(open(os.path.join("raw", MLISTS_DESC_FILE), encoding="utf-8"), as_dict=True)
            self._mnames      = csvhelpers.readCsv(open(os.path.join("raw", MNAMES_FILE),      encoding="utf-8"), as_dict=True)
            self._data        = csvhelpers.readCsv(open(os.path.join("raw", DATA_MAIN_FILE),   encoding="utf-8"), as_dict=True)

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
            # self._citations   = csvhelpers.readCsv(io.TextIOWrapper(z.open(version["dir"] + "/raw/" + CITATION_FILE),    encoding="utf-8"), as_dict=True)
            self._languages   = csvhelpers.readCsv(io.TextIOWrapper(z.open(version["dir"] + "/raw/" + LANGUAGE_FILE),    encoding="utf-8"), as_dict=True)
            self._mlists      = csvhelpers.readCsv(io.TextIOWrapper(z.open(version["dir"] + "/raw/" + MLISTS_FILE),      encoding="utf-8"), as_dict=True)
            self._mlists_desc = csvhelpers.readCsv(io.TextIOWrapper(z.open(version["dir"] + "/raw/" + MLISTS_DESC_FILE), encoding="utf-8"), as_dict=True)
            self._mnames      = csvhelpers.readCsv(io.TextIOWrapper(z.open(version["dir"] + "/raw/" + MNAMES_FILE),      encoding="utf-8"), as_dict=True)
            self._data        = csvhelpers.readCsv(io.TextIOWrapper(z.open(version["dir"] + "/raw/" + DATA_MAIN_FILE),   encoding="utf-8"), as_dict=True)
            z.close()
        except:
            print("%s: Could not load dataset zip file contents." % version["zipfile"], file=sys.stderr)
            sys.exit(1)
            
    def _getLanguageDict(self):
        '''Generate a language dict (key: _language_id, value: _language_ascii_id)'''
        language_id_set = set(self._data[self._language_id])
        language_dict = {}
        for key in language_id_set:
            i = self._languages[self._language_id].index(key)
            language_dict[key] = self._languages[self._language_ascii_id][i]
        return language_dict

    def _getCognSetOrder(self):
        '''Return a list of all cogn_set values present in the data matrix, with
        one-character sets in an alphabetical order, followed by two-character sets in
        an alphabetical order.'''
        cogn_sorting_order = []
        one_char = []
        two_char = []
        for i in set(self._data["cogn_set"]):
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
        for i in set(self._data["form_set"]):
            if i not in self._missing_values:
                forms.append(i)
        forms.sort(key=int)
        return(forms)

    def _getMngListsDict(self):
        '''Return a meaning list dict, including an "all" list containing all meanings'''
        mnglists = {}
        for i in self._mlists.keys():
            if i not in ["LJ_rank","uralex_mng","mng_item"]:
                mnglists[i] = []
        for mlist in mnglists.keys():
            for i in range(len(self._mlists[mlist])):
                if self._mlists[mlist][i] == "1":
                    mnglists[mlist].append(self._mlists["uralex_mng"][i])
        mnglists["all"] = []
        for i in self._mlists["uralex_mng"]:
            mnglists["all"].append(i)
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
        meaning_set = set(self._data["uralex_mng"])
        for lang in data_matrix.keys():
            for mng in meaning_set:
                data_matrix[lang][mng] = []
        for i in range(len(self._data[self._language_id])):
            current_language = self._data[self._language_id][i]
            current_meaning = self._data["uralex_mng"][i]
            if use_correlate_chars == True:
                current_data = self._data["form_set"][i].strip().rstrip()
            else:
                current_data = self._data["cogn_set"][i].strip().rstrip()
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
