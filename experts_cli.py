import click

from experts_calculator import ExpertCalculator
from helpers import (
    setup
)

GOLANG_GIT_REPO = 'https://github.com/golang/go.git'

#########################
########## CLI ##########
#########################

@click.command()
@click.option('--directory', '-d', help='Directory name, relative to the root of the Go source git tree')
@click.option('--print-logs', '-p', is_flag=True, help='Print logs (aka debug mode)')
@click.option('--num-experts', '-n', default=3, help='Number of experts to show')
@click.option('--action', default='calculate', help="""
    (1) calcualte -- Calculate experts for a given repo
    (2) compare -- Compare two ranking functions given two config files')
    """
)
def expert_cli(directory, print_logs, num_experts, action):
    """
    CLI to implement the Expert feature for Github. Given a git repository,
    determines the top 3 experts for a given directory within the Golang git repo.
    """

    if action=='calculate':
        ec = ExpertCalculator(directory, print_logs, num_experts)

        setup()
        
        # Note: there is no check if the directory is valid. It is assumed the directory
        # exists and is relative to go/
        
        authors = ec.get_authors_for_directory()
        logs_by_author_obj = ec.get_logs_for_authors(authors)
        blame_by_author_obj = ec.get_current_contributions_per_author()

        expert_scores = ec.calculate_expert_scores(blame_by_author_obj, logs_by_author_obj)
        ec.print_expert_scores(expert_scores)
    else:
        print('compare is being implemented')
    
if __name__ == '__main__':
    expert_cli()