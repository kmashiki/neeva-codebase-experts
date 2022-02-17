import os
from datetime import datetime
from collections import OrderedDict

from helpers import (
    is_comment,
    is_code,
    parse_log_value,
    get_files_in_directory,
    parse_email,
    parse_year,
    normalize_dictionary,
    sort_dict_by_value,
    path_to_filename,
    mkdir_not_exists,
)

class ExpertCalculator:
    def __init__(self, directory, print_logs, num_experts):
        self.directory = directory
        self.print_logs = print_logs
        self.num_experts = num_experts

    #############################################
    ########## Parse Functions (Blame) ##########
    #############################################

    def get_current_contributions_per_author(self):
        """
        Determines contributions each author made to the *current* codebase for each year.
        Contribution types include `num_lines_contributed`, `num_lines_code_contributed`, `num_lines_comments_contributed`

        returns Object {author_email: {contribution_type: {year: int}}}
        """
        files_in_dir = get_files_in_directory(self.directory)

        for f in files_in_dir:
            formatted_file_name = path_to_filename(f)
            file_name = f'parsed_files/{formatted_file_name}_blame.txt'
            os.system(f'touch {file_name}')

            cmd = f'cd go && git --no-pager blame -e {f} > ../{file_name}'
            os.system(cmd)

        blame_by_author_obj = {}
        for f in files_in_dir:
            formatted_file_name = path_to_filename(f)
            file_name = f'parsed_files/{formatted_file_name}_blame.txt'

            try:
                blame_by_author_obj.update(self.parse_current_blame_file(file_name, blame_by_author_obj))
            except UnicodeDecodeError as e:
                if self.print_logs:
                    print(f'{f} has non Unicode characters. Not processing contributions to this file')

        return blame_by_author_obj

    def parse_current_blame_file(self, file_name, blame_by_author_obj):
        """
        Helper function for `get_current_contributions_per_author` to parse
        `num_lines_contributed`, `num_lines_code_contributed`, `num_lines_comments_contributed`
        for each author and each year for a given file.

        file_name: String
        blame_by_author_obj: Object {author_email: {contribution_type: {year: int}}}
        returns Object {author_email: {contribution_type: {year: int}}}
        """
        with open(file_name, 'r') as file:
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
                    
                    if file_name not in blame_by_author_obj[email]['files_touched']:
                        blame_by_author_obj[email]['files_touched'].append(file_name)

                else:
                    blame_by_author_obj[email] = {
                        'num_lines_contributed': {year: 1},
                        'num_lines_code_contributed': {year: is_code(line)},
                        'num_lines_comments_contributed': {year: is_comment(line)},
                        'files_touched': [file_name]
                    }
        
        return blame_by_author_obj

    
    ###########################################
    ########## Parse Functions (Log) ##########
    ###########################################

    ## TO DO: Document these functions!

    def get_authors_for_directory(self):
        # store authors in text file
        if self.print_logs:
            print('Fetching authors for directory...')
        author_file_name = 'parsed_files/authors.txt'
        os.system(f'touch {author_file_name}')
        cmd = f'cd go && git --no-pager shortlog -s -n -e --all --no-merges {self.directory} > ../{author_file_name}'
        os.system(cmd)

        # parse authors from text file to array
        if self.print_logs:
            print('Parsing authors for directory...')
        authors = []
        with open(author_file_name, 'r') as file:
            for line in file:
                author_email = parse_email(line)
                authors.append(author_email)

        return authors

    def get_logs_for_authors(self, authors):
        if self.print_logs:
            print('Fetching logs for authors.....')
        logs_by_author_obj = {}

        for a in authors:
            if self.print_logs:
                print(f'Fetching logs for author {a}')
            
            author_file_name = 'parsed_files/author_log.txt'
            os.system(f'touch {author_file_name}')
            cmd = f'cd go && git --no-pager log --stat --author={a} {self.directory} > ../{author_file_name}'
            os.system(cmd)

            current_author_commits = self.parse_log_text_to_object(a)
            logs_by_author_obj[a] = current_author_commits
        
        return logs_by_author_obj

    def parse_log_text_to_object(self, author):
        current_author_commits = []
        curr_commit_obj = {}
        author_file_name = 'parsed_files/author_log.txt'

        with open(author_file_name, 'r') as file:
            in_commit_msg = False
            num_lines_commit_msg = 0
            reviewed_by_emails = []
            files_changed = []

            for line in file:
                line = line.strip()

                # new commit -- push prev object and start new one
                if line.startswith('commit') and len((line.split('commit')[1]).strip()) == 40:
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

                    curr_commit_obj['commit_sha'] = (line.split('commit')[1]).strip()
                elif line.startswith('Date:'):
                    date_string = parse_log_value(line, 'Date:')

                    # remove -0400, -0500 timezone. having trouble converting it with %z. Try to get this to run in python3
                    date_string = date_string[:len(date_string) - 5].strip()
                    parsed_date = datetime.strptime(date_string, '%a %b %d %H:%M:%S %Y')
                    curr_commit_obj['commit_date'] = parsed_date
                    in_commit_msg = True # commit message starts after date
                elif line.startswith('Change-Id:') or (line.startswith(self.directory) and in_commit_msg == True):
                    curr_commit_obj['num_lines_commit_msg'] = num_lines_commit_msg
                    in_commit_msg = False # commit message ends before change id
                elif line.startswith(self.directory):
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
    

    #################################################
    ########## Heuristic Functions (Blame) ##########
    #################################################

    def get_blame_metrics(self, blame_by_author_obj):
        """
        Combines 3 top-level blame metrics into one blame_score per author. Because blame looks 
        at the codebase's *current* state, these metrics do not reflect any historical changes
        in the directory. The 3 metrics are:
            - percent_lines_contributed
            - current code score (taking recency into account)
            - percent_files_touched
        
        blame_by_author_obj: Object {author_email: {contribution_type: {year: int}}}
        returns Object {author_email: blame_score}
        """
        percent_lines_contributed_by_author_stats = self.get_percent_current_code_by_author(blame_by_author_obj, 'num_lines_contributed')
        score_current_code_by_author_and_recency = self.get_score_current_code_by_author_and_recency(blame_by_author_obj, 'num_lines_contributed')
        percent_files_touched_by_author = self.get_percent_files_touched_by_author(blame_by_author_obj)

        final_blame_score_by_author = {}
        for a in blame_by_author_obj.keys():
            final_blame_score_by_author[a] = percent_lines_contributed_by_author_stats[a] + score_current_code_by_author_and_recency[a] + percent_files_touched_by_author[a]

        return final_blame_score_by_author

    def get_percent_current_code_by_author(self, blame_by_author_obj, contribution_type):
        """
        Determines percent of lines of code each author contributed to in the code's *current* state. 

        blame_by_author_obj: Object {author_email: {contribution_type: {year: int}}}
        contribution_type: String (one of `num_lines_contributed`, `num_lines_code_contributed`, `num_lines_comments_contributed`)
        return Object {author_email: float}
        """
        total_lines_in_directory = self.get_total_lines_in_directory(blame_by_author_obj, contribution_type)

        num_lines_by_author_obj = {}
        for a, obj in blame_by_author_obj.items():
            num_lines_by_author_obj[a] = sum(value for year, value in obj[contribution_type].items())

        percent_lines_by_author_obj = {}
        for k, v in num_lines_by_author_obj.items():
            percent_lines_by_author_obj[k] = v / float(total_lines_in_directory)
        
        return percent_lines_by_author_obj

    def get_score_current_code_by_author_and_recency(self, blame_by_author_obj, contribution_type):
        """
        Determines score of number of lines of code contributed to *current* codebase taking
        recency into account. Any contribution that is < the average commit year gets weighted
        with scalar x (TO DO). Normalizes raw scores to make values comparable between authors.

        blame_by_author_obj: Object {author_email: {contribution_type: {year: int}}}
        contribution_type: String (one of `num_lines_contributed`, `num_lines_code_contributed`, `num_lines_comments_contributed`)
        return Object {author_email: normalized_score_value}
        """
        average_contribution_year = int(self.get_average_contribution_year(blame_by_author_obj, contribution_type))

        score_by_author_obj = {}
        for a, obj in blame_by_author_obj.items():
            curr_author_sum = 0
            for year, value in obj[contribution_type].items():
                curr_author_sum += value * (1 if int(year) >= average_contribution_year else 0.5)
            score_by_author_obj[a] = curr_author_sum
        
        return normalize_dictionary(score_by_author_obj)

    def get_percent_files_touched_by_author(self, blame_by_author_obj):
        """
        Determines percent of files each author contributed to in the code's *current* state. 
        That is, if an author committed code to a file historically but no current lines of a file
        were written by that author, they do not "get credit" for touching that file.

        blame_by_author_obj: Object {author_email: {contribution_type: {year: int}}}
        returns Object {author_email: float}
        """
        percent_files_touched_by_author = {}
        num_files_in_dir = float(len(get_files_in_directory(self.directory)))
        for a, obj in blame_by_author_obj.items():
            percent_files_touched_by_author[a] = len(obj['files_touched']) / num_files_in_dir
        
        return percent_files_touched_by_author

    def get_average_contribution_year(self, blame_by_author_obj, contribution_type):
        """
        Determines the year that the average line of *current* code was committed (to be used in recency heuristics)

        blame_by_author_obj: Object {author_email: {contribution_type: {year: int}}}
        contribution_type: String (one of `num_lines_contributed`, `num_lines_code_contributed`, `num_lines_comments_contributed`)
        return int (year)
        """
        half_num_lines_in_directory = self.get_total_lines_in_directory(blame_by_author_obj, contribution_type) / 2
        num_contributions_by_year = self.get_num_contributions_by_year(blame_by_author_obj, contribution_type)
        num_contributions_by_year = OrderedDict(sorted(num_contributions_by_year.items()))
        
        average_contribution_year = None
        for k, v in num_contributions_by_year.items():
            half_num_lines_in_directory -= v
            if half_num_lines_in_directory <= 0:
                average_contribution_year = k
                break

        return average_contribution_year

    def get_total_lines_in_directory(self, blame_by_author_obj, contribution_type):
        """
        Determines total number of lines in the directory (i.e. all files in sub directories)

        blame_by_author_obj: Object {author_email: {contribution_type: {year: int}}}
        contribution_type: String (one of `num_lines_contributed`, `num_lines_code_contributed`, `num_lines_comments_contributed`)
        return int
        """
        num_lines_by_author_obj = {}

        for a, obj in blame_by_author_obj.items():
            num_lines_by_author_obj[a] = sum(value for year, value in obj[contribution_type].items())
        
        total_lines_in_directory = sum(v for k, v in num_lines_by_author_obj.items())

        return total_lines_in_directory

    def get_num_contributions_by_year(self, blame_by_author_obj, contribution_type):
        """
        Determines number of lines of *current* code contributed for each year

        blame_by_author_obj: Object {author_email: {contribution_type: {year: int}}}
        contribution_type: String (one of `num_lines_contributed`, `num_lines_code_contributed`, `num_lines_comments_contributed`)
        return Object {year: count}
        """
        num_contributions_by_year = {}
        for author, stats in blame_by_author_obj.items():
            for year, num in stats[contribution_type].items():
                if year in num_contributions_by_year.keys():
                    num_contributions_by_year[year] += num
                else:
                    num_contributions_by_year[year] = num

        return num_contributions_by_year

    ###############################################
    ########## Heuristic Functions (Log) ##########
    ###############################################

    def get_log_metrics(self, logs_by_author_obj):
        """
        Calculates log_score for each author.

        logs_by_author_obj: Object {author_email: [{commit_stats_obj}]}
        return Object {author_email: log_score}
        """
        final_log_score_by_author = {}

        for a in logs_by_author_obj.keys():
            final_log_score_by_author[a] = 0

        # TO DO    
        # num total commits
        # % commits made in last 12 months
        # num insertions + (0.5 * num deletions)
        # avg num lines in commit message -- consider setting scalar to 0

        return final_log_score_by_author
    

    #################################################
    ########## Final Calculation Functions ##########
    #################################################

    def calculate_expert_scores(self, blame_by_author_obj, logs_by_author_obj):
        """
        Calculates expert scorefor each author as a combination of blame_score and log_score
        TO DO: add scalar to each of these scores

        blame_by_author_obj: Object {author_email: {contribution_type: {year: int}}}
        logs_by_author_obj: Object {author_email: [{commit_stats_obj}]}
        return Object {author_email: expert_score}
        """
        final_blame_score_by_author = self.get_blame_metrics(blame_by_author_obj)
        final_log_score_by_author = self.get_log_metrics(logs_by_author_obj)

        score_by_author = {}
        for a in final_log_score_by_author.keys():
            score_by_author[a] = final_blame_score_by_author.get(a, 0) + final_log_score_by_author.get(a)
        
        score_by_author = sort_dict_by_value(score_by_author)

        return score_by_author

    def print_expert_scores(self, expert_scores):
        """
        Prints top `num_experts` scores

        expert_scores: Object {author_email: expert_score}
        returns None
        """
        print(f'\n---- Top {self.num_experts} Experts ----')

        i = 0
        for k, v in expert_scores.items():
            if i < self.num_experts:
                print(f'{k} {round(v, 2)}')
            i += 1