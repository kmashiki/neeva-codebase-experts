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
The most basic command is `python3 experts_cli.py --directory=<directory_name>`. This finds the top 3 experts for the given directory, and defaults all other options.
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

# Implementation Details
Below is the high level process I took when approaching this exercise:

### Parsing the Dataset
First, I explored data the most basic git commands (`git log` and `git blame` could get me). These commands work well in conjunction with each other, as git log shows historical trends while git blame tells us about the current state of the directory.

For log history, I decided to parse out a handful of data points *by author* for each commit. These include: `num_files_changed`, `num_insertions`, `num_deletions`, `commit_date`, `num_lines_commit_message`, and `reviewed_by`. These elements would be sufficient to derive a few basic metrics (e.g., number of commits by authour) and a few more sophisticated heuristics (e.g., historical code score based on recency of commits as well as sum of number of insertions and deletions, with the latter carrying less weight as insertions represent better expertise than deletions).

For blame stats, I also parsed data points by author, including: `num_lines_contributed`, `num_lines_code_contributed`, and `num_lines_comments_contributed`, thinking that knowing the type of commit would be helpful in determining expertise. For instance, lines of code would indicate more expertise than comments. I eventually ended up storing these fields *by year* so that metric calculations can take recency into account.

### Fetching and Storing Data
The 3 git commands I use to collect information are:
- `git --no-pager shortlog -s -n -e --all --no-merges <directory>` to get all authors for a given directory (i.e. anyone who has ever contributed to the directory)
- `git --no-pager log --stat --author={a} <directory>` to capture the log history for a given author
- `git --no-pager blame -e <file_name>` to capture who contributed each current line of code and when

I dump outputs from each of these commands into a text file that I then parse into a dict (hence the inclusion of `--no-pager`).

Find pseudocode for this process at [`pseudo_code.md`](https://github.com/kmashiki/neeva-codebase-experts/blob/main/pseudo_code.md)

## Components of the Expert Score
The two high level components of the expert score are the blame score and the log score. As I mentioned above, the blame score represents eexpertise around the current state of the codebase, while the log score represents historical expertise.

The blame score is made up of 3 components:
    1. % of lines contributed per author. This was a way to normalize total number of commits.
    2. Code score based on recency: code that was pushed after the year of the average code commit is weighted more heeavily than code that was pushed before the year of the average code commit. This is then normalized with a helper function.
    3. % of files touched (i.e., a file that has a current line of code contributed by an author) per author in this directory.

The log score is also made up of 3 components:
    1. # of commits by author (normalized).
    2. Code score based on insertions and deletions. The default case weighs insertions more than deletions. Again, this is normalized.
    3. Num reviews by author (normalized). This doesn't have to do with lines that a person wrote themselves, but rather reviews on other engineer's code.

Note that there are a handful of fields that I parse that I did not use in the current implementation of this project. There is potential to expand on these heuristics with additional fields.

## Comparing Two Ranking Functions
To compare two ranking functions, I added scalars to each metrics so that various weights could be adjusted. To turn a given component off, a scalar can be set to 0. Default values can be found in `ranking_configs/default_ranking_config.json`. Users can pass in their own json files (assuming they have the necessary scalar values) via the `-r1` and `-r2` options in the CLI.

Results for each ranking are output to `outputs.txt` so a user can compare the full list of expert scores. The CLI prints the top n of these based on the `-n` option, and also prints a few metrics that a user can use to compare ranking functions. For now, these are simply the minimum, maximum, mean, and median scores, as well as an indication of if the top scorer was the same across ranking functions.

## Expansion Potential
The first potential expansion is adding heuristics for more datapoints. For instance, I do not currently use `num_lines_code_contributed` and `num_lines_comments_contributed`, though the functions that calculate blame metrics by `contribution_type` are abstracted to easily included these metrics. Similarly, I've parsed and stored the length of a commit message, which doesn't necessarily indicate expertise, but does imply coding best practices. I could also add parsing data around code review comments and contributions. Finally, I do not include metrics around velocity of coding, just basic recency metrics given a line of code's age relative to the average commit year.

There is also room for improvement on the CLI and how much flexibility is offers a user. For instance, I could add a flag that allows a user to re-clone a git repo, in case they were working with a repo that was pushed to often.

Last but not least, I could make the comparison of two ranking functions more robust. Right now, the CLI prints stats for each of the ranking functions for a user to compare; it does not actually do any comparison of these stats, except for determining if the expert has changed from one ranking function to another.
