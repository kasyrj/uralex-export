# uralex-export

Python3 command-line tool to create MrBayes, BEAST and SplitsTree NEXUS files from the [UraLex Basic vocabulary dataset](https://zenodo.org/record/1459402). Use `uralex-export.py` or `uralex-export.py --help` to see available options.

## Basic usage with release version of dataset

Run uralex-export.py with the desired parameters. The tool prompts for permission to download the dataset if necessary.

### Customized dataset

1. Extract the "raw" folder from the UraLex dataset and place it as a subfolder in the same folder where the tool is located.
2. Use argument `-r` or `--raw_folder` when running uralex-export.

With the customized dataset you can e.g. include additional sublists into Meaning_lists.tsv with
the same syntax as the existing lists.
