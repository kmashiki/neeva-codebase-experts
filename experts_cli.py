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
@click.option('--num-experts', '-n', help='Number of experts to show')
def expert_cli(directory, print_logs, num_experts):
    """CLI to implement the Expert feature for Github.
    Given a git repository, determines the top 3 experts for a given directory
    within the Golang git repo."""

    ec = ExpertCalculator(directory, print_logs, int(num_experts))

    setup()
    
    authors = ec.get_authors_for_directory()
    logs_by_author_obj = ec.get_logs_for_authors(authors)
    blame_by_author_obj = ec.get_current_contributions_per_author()

    expert_scores = ec.calculate_expert_scores(blame_by_author_obj, logs_by_author_obj)
    ec.print_expert_scores(expert_scores)
    
if __name__ == '__main__':
    expert_cli()