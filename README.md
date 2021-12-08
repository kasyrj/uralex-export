# uralex-export

Python3 command-line tool to create MrBayes, BEAST and SplitsTree NEXUS files and BEAST-compatible CLDF files from the [UraLex Basic vocabulary dataset](https://doi.org/10.5281/zenodo.1459401). Use `uralex-export.py` or `uralex-export.py --help` to see available options.

Notably, the CLDF exporter functionality produces a rudimentary CLDF version of the dataset that is mainly intended for ad-hoc experimentation with e.g. modified data sheets. The official CLDF version of UraLex is included as part of the dataset itself, and should be preferred when using the dataset for research purposes.

## Usage with an official dataset version

Run uralex-export.py with the desired parameters. The tool prompts for permission to download the dataset if necessary.

## Usage with a customized dataset

1. Extract the "raw" folder from the UraLex dataset and place it as a subfolder in the same folder where the tool is located.
2. Use argument `-r` or `--raw_folder` when running uralex-export.

With the customized dataset you can e.g. include additional sublists into Meaning_lists.tsv with
the same syntax as the existing lists.
