#!/usr/bin/python3

VERSIONS                 = {1.0:
                            {"zipfile": "uralex-v1.0.zip",
                             "dir" : "lexibank-uralex-efe0a73",
                             "url"    : "https://zenodo.org/record/1459402/files/lexibank/uralex-v1.0.zip?download=1"},
                            2.0:
                            {"zipfile": "uralex-v2.0.zip",
                             "dir" : "lexibank-uralex-a37bb22",
                             "url"    : "https://zenodo.org/record/4777568/files/lexibank/uralex-v2.0.zip?download=1"}}

def getLatestVersion():
    '''Return latest version of uralex'''
    latest_ver = None
    for ver in VERSIONS.keys():
        if latest_ver == None or ver > latest_ver:
            latest_ver = ver
    return VERSIONS[latest_ver]

if __name__ == '__main__':
    print("Version information file for uralex_export.")
