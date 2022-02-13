import click

@click.command()
@click.option("--directory", help="Directory name, relative to the root of the Go source git tree")
def expert(directory):
    """CLI to implement the Expert feature for Github.
    Given a git repository, determines the top 3 experts for a given directory
    within the Golang git repo."""
    
    click.echo(directory)

if __name__ == '__main__':
    expert()