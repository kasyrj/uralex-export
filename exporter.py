#!/usr/bin/python3

import sys

class UralexExporter():
    
    def __init__(self, dataset):
        self._dataset = dataset
        self._with_charsets = None         # set by setCharsets
        self._meaning_list = None          # set by setMeaningList
        self._export_format = None         # set by setFormat
        self._export_dialect = None        # set by setFormat
        self._language_exclude_list = None # set by setLanguageExcludelist
        self._exported_languages = None    # cached languages, built as needed
        self._exported_meanings = None     # cached meanings, built as needed
        self._valid_chars = {}             # cached character states, built as needed

    def __del__(self):
        pass

    def setCharsets(self,value):
        '''Set exporter to export without charsets for each meaning'''
        self._with_charsets = value

    def setMeaningList(self,mlist):
        '''Set meaning list for exporter'''
        if mlist in self._dataset.getMeaningLists() + ["all"]:
            self._meaning_list = mlist
        else:
            print("Invalid meaning list. Must be one of following: \n",file=sys.stderr)
            for l in self._dataset.getMeaningLists() + ["all"]:
                print(l, file=sys.stderr)
            sys.exit(1)
        
    def setFormat(self, eformat, edialect):
        '''Set up exporter's export format and dialect'''
        if eformat in self._getValidFormats():
            self._export_format = eformat
        else:
            print("Invalid export format. Must be one of following: \n",file=sys.stderr)
            for i in self._getValidFormats():
                print(i, file=sys.stderr)
            sys.exit(1)

        if edialect in self._getValidDialects(self._export_format):
            self._export_dialect = edialect
        else:
            print("Invalid %s dialect. Must be one of following: \n" % self._export_format, file=sys.stderr)
            for i in self._getValidDialects(self._export_format):
                print(i, file=sys.stderr)
            sys.exit(1)

    def setLanguageExcludeList(self,llist):
        '''Set excluded languages'''
        languages = self._dataset.getLanguages()
        for i in llist:
            if i not in languages.values():
                print("Unknown language in exclude language list: %s.\n Valid values are:\n" % i, file=sys.stderr)
                for i in sorted(languages.values()):
                    print(i,file=sys.stderr)
                sys.exit(1)
        self._language_exclude_list = llist
            
    def export(self):
        '''Export data based on exporter settings'''
        if self._export_format == "nexus":
            return self._exportNexus()
        return []

    def _getValidFormats(self):
        '''Return list of valid formats'''
        return ["nexus"]           
    
    def _getValidDialects(self, format):
        '''Return list of valid dialects of format'''
        if format == "nexus":
            return ["mrbayes", "beast", "splitstree"]
        else:
            return []

    def _getNexusHeader(self):
        '''Return list of NEXUS header lines'''
        outlines = []
        outlines.append("#NEXUS")
        outlines.append("[ dialect: %s ]" % self._export_dialect)
        outlines.append("[ data version: %s ]" % self._dataset.getVersion())
        outlines.append("[ meaning list: %s ]" % self._meaning_list)
        if self._language_exclude_list != []:
            outlines.append("[ exclude taxa: %s ]" % str(self._language_exclude_list)[1:-1])
        if self._with_charsets == False:
            outlines.append("[ Partitioning: none ]")
        else:
            outlines.append("[ Partitioning: per-meaning ]")
        outlines.append("")
        return outlines

    def _getExportedLanguages(self):
        '''Return list of exported languages'''
        if self._exported_languages == None:
            all_languages = set(self._dataset.getLanguages().values())
            excluded_languages = set(self._language_exclude_list)
            self._exported_languages = sorted(all_languages.difference(excluded_languages))
        return self._exported_languages
    
    def _getNexusTaxaBlock(self):
        '''return a nexus taxa block based on the current generator settings.'''
        out = []
        out.append("begin taxa;")
        out.append("dimensions ntax=%s;" % str(len(self._getExportedLanguages())))
        line = "taxlabels"
        for l in self._getExportedLanguages():
            line += (" " + l)
        line += (";")
        out.append(line)
        out.append("end;")
        out.append("")
        return out

    def _getExportedMeanings(self):
        '''Return a list of exported meanings'''
        if self._exported_meanings == None:
            self._exported_meanings = self._dataset.getMeanings(self._meaning_list)
        return self._dataset.getMeanings(self._meaning_list)

    def _getValidCharacterStates(self, meaning):
        '''Return a sorted set of valid character states for a meaning based on exporter settings'''
        if meaning in self._valid_chars.keys():
            return self._valid_chars[meaning]
        valid_chars = []
        for l in self._getExportedLanguages():
            current = self._dataset.getCharacterAlignment(l, meaning)
            for c in current:
                if c == "?":
                    continue
                valid_chars += c
        valid_chars = set(valid_chars)
        result = sorted(valid_chars,
                        key=lambda word: [self._dataset.MULTISTATE_CHARS.index(c) for c in word])
        self._valid_chars[meaning] = result
        return result

    def _getMeaningAsBinary(self, language, meaning):
        '''Return meaning of language as a binary representation'''
        valid_chars = self._getValidCharacterStates(meaning)
        output = ""
        chars = self._dataset.getCharacterAlignment(language, meaning)
        if chars == ["?"]:
            output += "?" * len(valid_chars)
        else:
            for c in valid_chars:
                if c in chars:
                    output += "1"
                else:
                    output += "0"
        if self._export_dialect == "beast" and self._with_charsets == True:
            return self._getAscertainmentMarker(output) + output
        return output

    def _getAllMeaningsAsBinary(self, language):
        '''Return a tuple consisting of a list of all meanings and a corresponding list of their binary representations'''
        mngs = self._getExportedMeanings()
        substrings = []
        for m in mngs:
            substrings.append(self._getMeaningAsBinary(language,m))
        return (mngs,substrings)
    
    def _getFullBinaryString(self,language):
        '''Return the full binary alignment of language based on generator settings'''
        output = ""
        mngs, chars = self._getAllMeaningsAsBinary(language)
        for i in range(len(chars)):
            output += chars[i]
        if self._export_dialect == "beast" and self._with_charsets == False:
            output = self._getAscertainmentMarker(output) + output
        return output
    
    def _getAscertainmentMarker(self, c):
        '''Return the proper BEAST ascertainment bias marker for charset (string of characters) c'''
        if len(set(c)) == 1:
            if "?" in set(c):
                return "?"
        return "0"

    def _getAssumptionsBlock(self):
        '''Return assumptions block (BEAST)'''
        out = []
        out.append("begin assumptions;")
        out += self._getCharsetRows()
        out.append("end;")
        return out

    def _getMrBayesBlock(self):
        '''Return MrBayes block'''
        out = []
        out.append("begin mrbayes;")
        out += self._getCharsetRows()
        out.append("lset applyto=(all) coding=noabsencesites;") # set "noabsencesites" ascertainment bias correction 
        out.append("end;")
        return out

    def _getCharsetRows(self):
        '''Return NEXUS charset rows for each meaning'''
        out = []
        if self._with_charsets == False:
            start_fill = "[ "
            end_fill = " ]"
        else:
            start_fill = ""
            end_fill = ""
        if self._with_charsets == False and self._export_dialect == "beast":
            start_pos = 2
        else:
            start_pos = 1
        first_lang = self._getExportedLanguages()[0]
        mngs, chars = self._getAllMeaningsAsBinary(first_lang)
        for i in range(len(mngs)):
            end_pos = start_pos + len(chars[i])-1
            if end_pos == start_pos:
                out.append("%scharset %s = %i;%s" % (start_fill, mngs[i], end_pos, end_fill))
            else:
                out.append("%scharset %s = %i-%i;%s" % (start_fill, mngs[i], start_pos, end_pos, end_fill))
            start_pos = end_pos + 1
        return out
    
    def _getCharacterCount(self):
        '''Calculate character count'''
        lang = self._getExportedLanguages()[0] # Calculate based on first language
        return len(self._getFullBinaryString(lang))
    
    def _getNexusCharacterBlock(self):
        '''return a NEXUS character block based on the current generator settings.'''
        out = []
        out.append("begin characters;")
        out.append("dimensions nchar=%s;" % str(self._getCharacterCount()))
        if self._export_dialect in ["beast", "mrbayes"]:
            out.append("format missing=? datatype=restriction;")
        elif self._export_dialect == "splitstree":
            out.append("format symbols=\"01\" missing=?;")        
        out.append("matrix")
        langs = self._getExportedLanguages()
        for lang in langs:
            out.append(lang + " " + self._getFullBinaryString(lang))
        out.append(";")
        out.append("end;")
        return out

    def _exportNexus(self):
        '''Export NEXUS format'''
        outlines = []
        outlines += self._getNexusHeader()
        outlines += self._getNexusTaxaBlock()
        outlines += self._getNexusCharacterBlock()
        if self._export_dialect == "beast":
            outlines += self._getAssumptionsBlock()
        elif self._export_dialect == "mrbayes":
            outlines += self._getMrBayesBlock()
        return outlines

if __name__ == '__main__':
    print("Exporter class for uralex_export")
