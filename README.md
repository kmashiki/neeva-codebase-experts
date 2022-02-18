# CLI: Installation, Setup and Use
## Installation
Clone the repository: `git clone git@github.com:kmashiki/neeva-codebase-experts.git`

## Setup
```
    cd neeva-codebase-experts
    virtualenv venv
    source venv/bin/activate
    pip3 install -r requirements.txt
```

## Using the CLI
`experts_cli.py` is the entry point into the CLI, and is implemented using [the click library](https://pypi.org/project/click/).
You can run `python3 experts_cli.py --help` to see CLI options.
The most basic command is `python3 experts_cli.py --directory=<directory_name>`. This runs the CLI for the given directory, and defaults all other options.
Some other options include
- `'--print-logs', '-p'` to print logs. This is turned off by default.
- `'--num-experts', '-n'` to indicate how many experts you want to be printed. This is defualted to 3.
- `'--action', '-a'` to indicate if you want to `calculate` scores for one ranking function or if you want to `compare` scores for two separate ranking functions.
- `'--ranking1_config', '-r1'` to indicate a json file that holds constants to adjust scalars for different aspects of the first ranking function. This defaults `ranking_configs/default_ranking_config.json`.
- `'--ranking2_config', '-r2'` to indicate a json file that holds constants to adjust scalars for different aspects of the second ranking function (only used when `action=compare`). This defaults `ranking_configs/default_ranking_config.json`.

For example,
```
python3 experts_cli.py -d src/crypto/ecdsa -p -n 5 --action=compare -r1=ranking_configs/ranking1_config.json -r2=ranking_configs/ranking2_config.json 
```
will compare ranking functions with scalars at `ranking_configs/ranking1_config.json` and `ranking_configs/ranking2_config.json` and produce the top 5 experts, printing logs when the CLI runs.

# Design Choices
Brainstorming:
* Collecting and storing data
* Which git commands to use
* Which metrics to derive from git data
* Pseudo code for collecting, parsing, and analyzing data

# Implementation Details
## Components of Expert Score

## Comparing Two Ranking Functions

## Expansion Potential
