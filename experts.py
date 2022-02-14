import click
import os
import subprocess
from datetime import datetime

GOLANG_GIT_REPO = "https://github.com/golang/go.git"

def get_authors_for_directory(directory):
    # store authors in text file
    print('Fetching authors for directory...')
    author_file_name = 'authors.txt'
    os.system('touch {}'.format(author_file_name))
    cmd = "cd go && git --no-pager shortlog -s -n -e --all --no-merges {} > ../{}".format(directory, author_file_name)
    os.system(cmd)

    # parse authors from text file to array
    print('Parsing authors for directory...')
    authors = []
    with open(author_file_name, "r") as file:
        for line in file:
            author_email = parse_email(line)
            authors.append(author_email)

    return authors

def get_logs_for_authors(authors, directory):
    # store git log for each user
    if not os.path.exists('author_logs'):
        os.makedirs('author_logs')

    # TO DO: thread these fetches??
    # for a in authors:
    #     print('Fetching logs for author {}...'.format(a))
    #     author_file_name = 'author_logs/{}.txt'.format(a)
    #     os.system('touch {}'.format(author_file_name))
    #     cmd = "cd go && git --no-pager log --stat --author={} {} > ../{}".format(a, directory, author_file_name)
    #     os.system(cmd)
    
    logs_by_author_obj = {}
    for a in authors:
        current_author_commits = parse_log_text_to_object(a, directory)
        logs_by_author_obj[a] = current_author_commits
    
    for x in logs_by_author_obj['rsc@golang.org']:
        print(x)

def parse_log_text_to_object(author, directory):
    current_author_commits = []
    curr_commit_obj = {}

    author_file_name = 'author_logs/{}.txt'.format(author)
    with open(author_file_name, "r") as file:
        in_commit_msg = False
        num_lines_commit_msg = 0
        reviewed_by_emails = []

        for line in file:
            line = line.strip()

            # new commit -- push prev object and start new one
            if line.startswith("commit") and len((line.split("commit")[1]).strip()) == 40:
                # push reviewed by emails before resetting value upon new commit
                curr_commit_obj['reviewed_by'] = reviewed_by_emails

                if curr_commit_obj != {}:
                    current_author_commits.append(curr_commit_obj)
                    curr_commit_obj = {}
                    in_commit_msg = False
                    num_lines_commit_msg = 0
                    reviewed_by_emails = []

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
            elif in_commit_msg:
                num_lines_commit_msg += 1
            elif line.startswith('Reviewed-by:'):
                reviewed_by_string = parse_log_value(line, 'Reviewed-by:')
                reviewed_by_email = parse_email(reviewed_by_string)
                reviewed_by_emails.append(reviewed_by_email)
            
            elif 'files changed' in line or 'file changed' in line:
                line_parts = line.split(',')
                print(line_parts)
                for l in line_parts:
                    num_changes = int(l.split()[0])
                    if 'files changed' in l or 'file changed' in l:
                        curr_commit_obj['num_files_changed'] = num_changes
                    elif 'insertion' in l:
                        curr_commit_obj['num_insertions'] = num_changes
                    elif 'deletion' in l:
                        curr_commit_obj['num_deletions'] = num_changes
                
            # else:
            #     print(line)
        
        # cover last commit case
        current_author_commits.append(curr_commit_obj)
    
    return current_author_commits


def parse_log_value(line, substring):
    return line[len(substring):].strip()

def parse_email(line):
    print(line)
    return (((line.split("<",1)[1])[::-1]).split(">",1)[1])[::-1]


@click.command()
@click.option("--directory", help="Directory name, relative to the root of the Go source git tree")
def expert(directory):
    """CLI to implement the Expert feature for Github.
    Given a git repository, determines the top 3 experts for a given directory
    within the Golang git repo."""

    click.echo(directory)
    
    authors = get_authors_for_directory(directory)
    get_logs_for_authors(authors, directory)

if __name__ == '__main__':
    expert()