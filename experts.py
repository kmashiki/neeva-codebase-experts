import click
import os
import subprocess
from datetime import datetime
import numpy as np
import operator

GOLANG_GIT_REPO = "https://github.com/golang/go.git"

def get_current_contributions_per_author(directory):
    files_in_dir = get_files_in_directory(directory)

    for f in files_in_dir:
        file_name = '{}_blame.txt'.format(f.replace("/", "-").replace(".", "-"))
        os.system('touch {}'.format(file_name))

        cmd = "cd go && git --no-pager blame -e {} > ../{}".format(f, file_name)
        os.system(cmd)

    blame_by_author_obj = {}
    for f in files_in_dir:
        file_name = '{}_blame.txt'.format(f.replace("/", "-").replace(".", "-"))
        with open(file_name, "r") as file:
            for line in file:
                email = parse_email(line)
                year = parse_year(line)

                if email in blame_by_author_obj.keys():
                    if year in blame_by_author_obj[email]['num_lines_contributed'].keys():
                        blame_by_author_obj[email]['num_lines_contributed'][year] += 1
                    else:
                        blame_by_author_obj[email]['num_lines_contributed'][year] = 1
                    
                    if year in blame_by_author_obj[email]['num_lines_code_contributed'].keys():
                        blame_by_author_obj[email]['num_lines_code_contributed'][year] += is_code(line)
                    else:
                        blame_by_author_obj[email]['num_lines_code_contributed'][year] = is_code(line)
                    
                    if year in blame_by_author_obj[email]['num_lines_comments_contributed'].keys():
                        blame_by_author_obj[email]['num_lines_comments_contributed'][year] += is_comment(line)
                    else:
                        blame_by_author_obj[email]['num_lines_comments_contributed'][year] = is_comment(line)

                else:
                    blame_by_author_obj[email] = {
                        'num_lines_contributed': {year: 1},
                        'num_lines_code_contributed': {year: is_code(line)},
                        'num_lines_comments_contributed': {year: is_comment(line)}
                    }

    return blame_by_author_obj

def is_comment(line):
    index_close_paren = line.find(')')
    line = line[index_close_paren + 1:].strip()
    
    return 1 if line.startswith('//') else 0

def is_code(line):
    return int(not is_comment(line))

def get_authors_for_directory(directory):
    # store authors in text file
    if PRINT_LOGS:
        print('Fetching authors for directory...')
    author_file_name = 'authors.txt'
    os.system('touch {}'.format(author_file_name))
    cmd = "cd go && git --no-pager shortlog -s -n -e --all --no-merges {} > ../{}".format(directory, author_file_name)
    os.system(cmd)

    # parse authors from text file to array
    if PRINT_LOGS:
        print('Parsing authors for directory...')
    authors = []
    with open(author_file_name, "r") as file:
        for line in file:
            author_email = parse_email(line)
            authors.append(author_email)

    return authors

def get_logs_for_authors(authors, directory):
    if PRINT_LOGS:
        print('Fetching logs for authors.....')
    logs_by_author_obj = {}

    for a in authors:
        if PRINT_LOGS:
            print('Fetching logs for author {}'.format(a))
        os.system('touch author_log.txt')
        cmd = "cd go && git --no-pager log --stat --author={} {} > ../author_log.txt".format(a, directory)
        os.system(cmd)

        current_author_commits = parse_log_text_to_object(a, directory)
        logs_by_author_obj[a] = current_author_commits
    
    return logs_by_author_obj

def parse_log_text_to_object(author, directory):
    current_author_commits = []
    curr_commit_obj = {}

    author_file_name = 'author_log.txt'.format(author)
    with open(author_file_name, "r") as file:
        in_commit_msg = False
        num_lines_commit_msg = 0
        reviewed_by_emails = []
        files_changed = []

        for line in file:
            line = line.strip()

            # new commit -- push prev object and start new one
            if line.startswith("commit") and len((line.split("commit")[1]).strip()) == 40:
                if curr_commit_obj != {}:
                    # push reviewed by emails before resetting value upon new commit
                    curr_commit_obj['reviewed_by'] = reviewed_by_emails
                    curr_commit_obj['files_changed'] = files_changed

                    current_author_commits.append(curr_commit_obj)
                    curr_commit_obj = {}
                    in_commit_msg = False
                    num_lines_commit_msg = 0
                    reviewed_by_emails = []
                    files_changed = []

                curr_commit_obj['commit_sha'] = (line.split("commit")[1]).strip()
            elif line.startswith('Date:'):
                date_string = parse_log_value(line, 'Date:')

                # remove -0400, -0500 timezone. having trouble converting it with %z. Try to get this to run in python3
                date_string = date_string[:len(date_string) - 5].strip()
                parsed_date = datetime.strptime(date_string, '%a %b %d %H:%M:%S %Y')
                curr_commit_obj['commit_date'] = parsed_date
                in_commit_msg = True # commit message starts after date
            elif line.startswith('Change-Id:') or (line.startswith('{}'.format(directory)) and in_commit_msg == True):
                curr_commit_obj['num_lines_commit_msg'] = num_lines_commit_msg
                in_commit_msg = False # commit message ends before change id
            elif line.startswith('{}'.format(directory)):
                files_changed.append(line.split()[0])
            elif in_commit_msg:
                num_lines_commit_msg += 1
            elif line.startswith('Reviewed-by:'):
                reviewed_by_string = parse_log_value(line, 'Reviewed-by:')
                reviewed_by_email = parse_email(reviewed_by_string)
                reviewed_by_emails.append(reviewed_by_email)
            
            elif 'files changed' in line or 'file changed' in line:
                line_parts = line.split(',')
                for l in line_parts:
                    num_changes = int(l.split()[0])
                    if 'files changed' in l or 'file changed' in l:
                        curr_commit_obj['num_files_changed'] = num_changes
                    elif 'insertion' in l:
                        curr_commit_obj['num_insertions'] = num_changes
                    elif 'deletion' in l:
                        curr_commit_obj['num_deletions'] = num_changes
        
        # cover last commit case
        current_author_commits.append(curr_commit_obj)
    
    return current_author_commits

def get_files_in_directory(directory):
    files_in_dir = []

    for r, d, f in os.walk('go/' + directory):
        for item in f:
            files_in_dir.append(os.path.join(r, item)[3:])
    
    return files_in_dir


def parse_log_value(line, substring):
    return line[len(substring):].strip()

def parse_email(line):
    index_less_than = line.find("<")
    index_greater_than = line.find(">")
    return line[index_less_than + 1 : index_greater_than]

def parse_year(line):
    dash_index = line.find("-")
    return line[: dash_index][-4:]

def get_blame_metrics(blame_by_author_obj):
    num_lines_contributed_by_author_stats = get_percent_current_code_by_author(blame_by_author_obj, 'num_lines_contributed')
    num_lines_code_contributed_by_author_stats = get_percent_current_code_by_author(blame_by_author_obj, 'num_lines_code_contributed')
    num_lines_comments_contributed_by_author_stats = get_percent_current_code_by_author(blame_by_author_obj, 'num_lines_comments_contributed')

    print(sorted(num_lines_contributed_by_author_stats)[0])
    print(sorted(num_lines_code_contributed_by_author_stats)[0])
    print(sorted(num_lines_comments_contributed_by_author_stats)[0])

    num_lines_contributed__by_year_stats = get_percent_current_code_by_year(blame_by_author_obj, 'num_lines_contributed')
    print(num_lines_contributed__by_year_stats)

def get_percent_current_code_by_author(blame_by_author_obj, contribution_type):
    num_lines_by_author_obj = {}
    
    # total_lines_contributed_by_author_obj = {}
    # total_code_contributed_by_author_obj = {}
    # total_comments_contributed_by_author_obj = {}
    for a, obj in blame_by_author_obj.items():
        num_lines_by_author_obj[a] = sum(value for year, value in obj[contribution_type].items())
    
    total_lines_in_directory = sum(v for k, v in num_lines_by_author_obj.items())

    percent_lines_by_author_obj = {}
    for k, v in num_lines_by_author_obj.items():
        percent_lines_by_author_obj[k] = v / float(total_lines_in_directory)
    
    return percent_lines_by_author_obj


#### WIP
def get_percent_current_code_by_year(blame_by_author_obj, contribution_type):
    num_contributions_by_year = {}
    for author, stats in blame_by_author_obj.items():
        for year, num in stats[contribution_type].items():
            if year in num_contributions_by_year.keys():
                num_contributions_by_year[year] += num
            else:
                num_contributions_by_year[year] = num

    return num_contributions_by_year


@click.command()
@click.option("--directory", help="Directory name, relative to the root of the Go source git tree")
@click.option("--print-logs", '-p', is_flag=True, help="Print logs (aka debug mode)")
def expert(directory, print_logs):
    """CLI to implement the Expert feature for Github.
    Given a git repository, determines the top 3 experts for a given directory
    within the Golang git repo."""

    click.echo(directory)

    global PRINT_LOGS
    PRINT_LOGS = False
    if print_logs:
        PRINT_LOGS = True
        click.echo("Printing logs...")
    
    authors = get_authors_for_directory(directory)
    logs_by_author_obj = get_logs_for_authors(authors, directory)
    blame_by_author_obj = get_current_contributions_per_author(directory)

    # print(logs_by_author_obj)
    # print(blame_by_author_obj)
    
    get_blame_metrics(blame_by_author_obj)

if __name__ == '__main__':
    expert()