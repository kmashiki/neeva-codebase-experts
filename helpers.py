import os
from collections import OrderedDict

######################################
########## Helper Functions ##########
######################################

def is_comment(line):
    """
    Determines if a line is a comment (i.e. if it starts with //)

    line: String
    returns Boolean
    
    Note this would need to be abstracted if this code were to be used on a repo
    that had a different commenting format (e.g. Python would look for #).
    """
    index_close_paren = line.find(')')
    line = line[index_close_paren + 1:].strip()
    
    return 1 if line.startswith('//') else 0

def is_code(line):
    """
    Determines if a line is code (i.e. if it is not a comment)

    line: String
    returns Boolean
    """
    return int(not is_comment(line))

def parse_log_value(line, substring):
    """
    removes the length of the substring from the beginning of the line
    and removes any preceding or trailing whitespace
    """
    return line[len(substring):].strip()

def get_files_in_directory(directory):
    """
    Crawls through a directory to find all files in subdirectories

    directory: String
    returns [String]
    """
    files_in_dir = []

    for r, d, f in os.walk('go/' + directory):
        for item in f:
            files_in_dir.append(os.path.join(r, item)[3:])
    
    return files_in_dir

def parse_email(line):
    """
    Follows GitHub's standard of <email> to parse emails

    line: String
    returns String
    """
    index_less_than = line.find('<')
    index_greater_than = line.find('>')
    return line[index_less_than + 1 : index_greater_than]

def parse_year(line):
    """
    First instance of - comes in the string '<text> YYYY-MM-DD <text>'
    Parse YYYY by finding the index of the first dash, substringing everything before that,
    and taking the last 4 characters from that substring

    line: String
    returns String
    """
    dash_index = line.find('-')
    return line[: dash_index][-4:]

def normalize_dictionary(dictionary):
    """
    Given a dictionary, normalizes values 

    dictionary: Object {key: raw value}
    returns Object {key: normalized value}
    """
    factor = 1.0 / sum(dictionary.values())
    for k, v in dictionary.items():
        dictionary[k] = v * factor
    
    return dictionary

def sort_dict_by_value(d):
    """
    Sorts a dictionary by its values. Uses OrderedDict to maintain order

    d: Object
    return OrderedDict
    """
    sorted_tuples = reversed(sorted(d.items(), key=lambda item: item[1]))
    sorted_dict = OrderedDict()
    for k, v in sorted_tuples:
        sorted_dict[k] = v

    return sorted_dict

def path_to_filename(path):
    """
    Convert path to filename-safe string

    path: String
    returns String
    """
    return path.replace('/', '-').replace('.', '-')

def mkdir_not_exists(dir):
    """
    Makes a directory if it doesn't already exist

    dir: String
    returns None
    """
    if not os.path.exists(dir):
        os.makedirs(dir)
    
def setup():
    """
    Makes a directory to store parsed files and clones go repo if it does not already exist

    Note: This could be adjusted to delete the go repo and download it everytime the script is
    run if we were concerned the repo would be updated often enough to change results. This could
    also be added as an option / flag to the CLI
    """
    mkdir_not_exists('parsed_files')
    os.system('rm -f outputs.txt')
    if not os.path.exists('go'):
        os.system(f'git clone {GOLANG_GIT_REPO}')