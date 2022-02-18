import click
import json

from experts_calculator import ExpertCalculator
from helpers import (
    setup
)

#########################
########## CLI ##########
#########################

@click.command()
@click.option('--directory', '-d', help='Directory name, relative to the root of the Go source git tree')
@click.option('--print-logs', '-p', is_flag=True, help='Print logs (aka debug mode)')
@click.option('--num-experts', '-n', default=3, help='Number of experts to show')
@click.option('--action', '-a', default='calculate', help="""
    (1) calcualte -- Calculate experts for a given repo
    (2) compare -- Compare two ranking functions given two config files')
    """
)
@click.option('--ranking1_config', '-r1', default='ranking_configs/default_ranking_config.json', help="First set of constants to be used in ranking function")
@click.option('--ranking2_config', '-r2', default='ranking_configs/default_ranking_config.json', help="Second set of constants to be used in ranking function")
def expert_cli(directory, print_logs, num_experts, action, ranking1_config, ranking2_config):
    """
    CLI to implement the Expert feature for Github. Given a git repository,
    determines the top 3 experts for a given directory within the Golang git repo.
    """

    if action=='calculate':
        with open(ranking1_config) as config_file:
            constants = json.load(config_file)

        setup()
        ec = ExpertCalculator(directory, print_logs, num_experts, constants, ranking1_config)
        expert_scores = run_expert_calculator(ec)
        ec.print_expert_scores(expert_scores)
    elif action=='compare':
        with open(ranking1_config) as config_file1:
            constants1 = json.load(config_file1)
        
        with open(ranking2_config) as config_file2:
            constants2 = json.load(config_file2)

        setup()

        print(f'\nRunning expert calculator on {ranking1_config}')
        ec1 = ExpertCalculator(directory, print_logs, num_experts, constants1, ranking1_config)
        expert_scores1 = run_expert_calculator(ec1)

        print(f'\nRunning expert calculator on {ranking2_config}')
        ec2 = ExpertCalculator(directory, print_logs, num_experts, constants2, ranking2_config)
        expert_scores2 = run_expert_calculator(ec2)

        ec1.print_expert_scores(expert_scores1)
        ec2.print_expert_scores(expert_scores2)

        ec1.write_scores_to_output_file(expert_scores1)
        ec2.write_scores_to_output_file(expert_scores2)

        print(f'\nStats from {ranking1_config}')
        print(ec1.get_score_stats(expert_scores1))

        print(f'\nStats from {ranking2_config}')
        print(ec1.get_score_stats(expert_scores2))

        if next(iter(expert_scores1)) == next(iter(expert_scores1)):
            print('\nRanking functions returned the same top expert')
        else:
            print('\nRanking functions dit NOT return the same top expert')

def run_expert_calculator(ec):
    authors = ec.get_authors_for_directory()
    logs_by_author_obj = ec.get_logs_for_authors(authors)
    blame_by_author_obj = ec.get_current_contributions_per_author()
    expert_scores = ec.calculate_expert_scores(blame_by_author_obj, logs_by_author_obj)

    return expert_scores

if __name__ == '__main__':
    expert_cli()