#!/usr/bin/python3

import sys

class UralexExporter:
    
    def __init__(self, dataset, args):
        self._charset_labels = args.charset_labels
        self._dataset = dataset            # Reader class
        self._with_charsets = None         # set by setCharsets
        self._export_format = None         # set by setFormat
        self._export_dialect = None        # set by setFormat
        self.setCharsets(args.charsets)
        self.setFormat(args.format, args.dialect)
        # self._language_exclude_list = None # set by setLanguageExcludelist
        # self._exported_languages = None    # cached languages, built as needed
        # self._exported_meanings = None     # cached meanings, built as needed
        self._character_state_cache = {}             # cached character states, built as needed

    def __del__(self):
        pass

    def export(self):
        '''Export data based on exporter settings'''
        if self._export_format == "nexus":
            return self._exportNexus()
        if self._export_format == "cldf":
            return self._exportCldf()
        if self._export_format == "harvest":
            return self._exportHarvest()
        return []

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

    def _exportCldf(self):
        '''Export CLDF format'''
        outlines = ["Language_ID,Feature_ID,Value"]
        langs = self._dataset.getLanguages()
        mngs = self._dataset.getMeanings()
        for l in langs:
            for m in mngs:
                c = self._dataset.getCharacterAlignment(l, m)
                for i in c:
                    outlines.append(l + "," + m + "," + i)
        return outlines

    def _exportHarvest(self):
        '''Export harvest format'''
        outlines = []
        header = "language,"
        for mng in self._dataset.getMeanings():
            header += mng + ","
        header = header[:-1]
        outlines.append(header)
        langs = self._dataset.getLanguages()
        mngs = self._dataset.getMeanings()
        for l in langs:
            newline = ""
            newline += l + ","
            for m in mngs:
                c = self._dataset.getCharacterAlignment(l, m)
                newline += c[0] + ','
            newline = newline[:-1]
            outlines.append(newline)
        return outlines
    
    def _getNexusHeader(self):
        '''Return list of NEXUS header lines'''
        outlines = []
        outlines.append("#NEXUS")
        outlines.append("[ dialect: %s ]" % self._export_dialect)
        outlines.append("[ data version: %s ]" % self._dataset.getVersion())
        outlines.append("[ meaning list: %s ]" % self._dataset.getMeaningList())
        if self._dataset.getExcludedLanguages() != []:
            outlines.append("[ exclude taxa: %s ]" % ",".join(self._dataset.getExcludedLanguages()))
        if self._with_charsets == False:
            outlines.append("[ Partitioning: none ]")
        else:
            outlines.append("[ Partitioning: per-meaning ]")
        outlines.append("")
        return outlines    
    
    def setCharsets(self,value):
        '''Set exporter to export without charsets for each meaning'''
        self._with_charsets = value

    def setFormat(self, eformat, edialect):
        '''Set up exporter's export format and dialect'''
        if eformat in self._getValidFormats():
            self._export_format = eformat
        else:
            print("Invalid export format. Must be one of following: \n",file=sys.stderr)
            for i in self._getValidFormats():
                print(i, file=sys.stderr)
            sys.exit(1)

        if self._getValidDialects(self._export_format) != []:
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
            if i not in languages:
                print("Unknown language in exclude language list: %s.\n Valid values are:\n" % i, file=sys.stderr)
                for i in sorted(languages):
                    print(i,file=sys.stderr)
                sys.exit(1)
        self._language_exclude_list = llist
            
    def _getValidFormats(self):
        '''Return list of valid formats'''
        return ["nexus","cldf","harvest"]           
    
    def _getValidDialects(self, format):
        '''Return list of valid dialects of format'''
        if format == "nexus":
            return ["mrbayes", "beast", "splitstree"]
        return []

    def _getNexusTaxaBlock(self):
        '''return a nexus taxa block based on the current generator settings.'''
        out = []
        out.append("begin taxa;")
        out.append("dimensions ntax=%s;" % str(len(self._dataset.getLanguages())))
        line = "taxlabels"
        for l in self._dataset.getLanguages():
            line += (" " + l)
        line += (";")
        out.append(line)
        out.append("end;")
        out.append("")
        return out

    def _getValidCharacterStates(self, meaning):
        '''Return a sorted set of valid character states for a meaning based on exporter settings'''
        if meaning in self._character_state_cache.keys():                  # use cached states if available
            return self._character_state_cache[meaning]
        valid_chars = []
        for l in self._dataset.getLanguages():
            current = self._dataset.getCharacterAlignment(l, meaning)      # determine what characters are used
            for c in current:                                              # add everything but ? to valid character states
                if c == "?":
                    continue
                valid_chars.append(c)
        result = sorted(set(valid_chars))                                  # remove duplicates
        self._character_state_cache[meaning] = result                      # store to cache for later use
        return result

    def _getMeaningAsBinary(self, language, meaning):
        '''Return meaning of language as a binary representation'''
        valid_chars = self._getValidCharacterStates(meaning)               # ordered based on _getValidCharacterStates
        output = ""
        chars = self._dataset.getCharacterAlignment(language, meaning)
        if chars == ["?"]:                                                 # if character states contain ?, fill meaning with ?s
            output += "?" * len(valid_chars)
        else:
            for c in valid_chars:
                if c in chars:
                    output += "1"
                else:
                    output += "0"
        if self._export_dialect == "beast" and self._with_charsets == True:
            return self._getAscertainmentMarker(output) + output             # with ascertainment bias marker
        return output                                                        # without ascertainment bias marker

    def _getAllMeaningsAsBinary(self, language):
        '''Return a tuple consisting of a list of all meanings and a corresponding list of their binary representations'''
        mngs = self._dataset.getMeanings()                              # ordered according to getMeanings
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
        first_lang = self._dataset.getLanguages()[0]
        mngs, chars = self._getAllMeaningsAsBinary(first_lang)
        for i in range(len(mngs)):
            end_pos = start_pos + len(chars[i])-1
            if end_pos == start_pos:
                out.append("%scharset %s = %i;%s" % (start_fill, mngs[i], end_pos, end_fill))
            else:
                out.append("%scharset %s = %i-%i;%s" % (start_fill, mngs[i], start_pos, end_pos, end_fill))
            start_pos = end_pos + 1
        return out

    def _getCharacterPositions(self, with_ascertainment=True):
        '''Return list of character positions of the form mng_char, followed by their positions in the matrix'''
        out = []
        char_pos = 1
        for mng in self._dataset.getMeanings():                     # meanings ordered according to _getMeanings()
            charstates = self._getValidCharacterStates(mng)         # character states ordered according to _getValidCharacterStates()
            if with_ascertainment:
                out.append("    %i %s_0ascertainment," % (char_pos, mng))
                char_pos += 1
            for char in charstates:
                out.append("    %i %s_%s," % (char_pos, mng, char))
                char_pos += 1
        out[-1] = out[-1][0:-1]  # remove comma from last entry
        out.append(";")
        #for line in out:
        #    print(line)
        return out

    
    def _getCharacterCount(self):
        '''Calculate character count'''
        lang = self._dataset.getLanguages()[0] # Calculate based on first language
        return len(self._getFullBinaryString(lang))
    
    def _getNexusCharacterBlock(self):
        '''return a NEXUS character block based on the current generator settings.'''
        out = []
        if self._charset_labels:  # with charset labels datatype must be standard
            out.append("begin data;")
            out.append("dimensions ntax=%i nchar=%i;" % (len(self._dataset.getLanguages()), self._getCharacterCount()))
            out.append("format datatype=standard missing=? symbols=\"01\";")
            out.append("charstatelabels")
            out += (self._getCharacterPositions())
        else:        
            out.append("begin characters;")
            out.append("dimensions nchar=%i;" % self._getCharacterCount())
            if self._export_dialect in ["beast", "mrbayes"]:
                out.append("format missing=? datatype=restriction")
            elif self._export_dialect == "splitstree":
                out.append("format symbols=\"01\" missing=?;")
            
        out.append("matrix")
        for lang in self._dataset.getLanguages():
            out.append(lang + " " + self._getFullBinaryString(lang))
        out.append(";")
        out.append("end;")
        return out

if __name__ == '__main__':
    print("Exporter class for uralex_export")
