"""Command-line interface for GitHub Assistant."""

import sys
import os

# Fix Windows encoding issues
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from github_assistant.core.git_client import GitClient
from github_assistant.core.github_client import GitHubClient
from github_assistant.core.ai_agent import AIAgent

console = Console()


def get_clients():
    """Initialize and return Git, GitHub, and AI clients."""
    try:
        git_client = GitClient()
        github_client = GitHubClient()
        ai_agent = AIAgent()
        return git_client, github_client, ai_agent
    except Exception as e:
        console.print(f"[red]Error initializing clients: {str(e)}[/red]")
        console.print("\n[yellow]Make sure .env file has GITHUB_TOKEN and ANTHROPIC_API_KEY[/yellow]")
        sys.exit(1)


@click.group()
@click.version_option(version='1.0.0')
def cli():
    """GitHub Assistant - Your AI-powered Git and GitHub automation tool."""
    pass


# ============================================================================
# GIT OPERATIONS
# ============================================================================

@cli.command()
@click.option('--all', '-a', is_flag=True, help='Stage all changes')
@click.option('--ai', is_flag=True, help='Generate commit message with AI')
@click.option('--message', '-m', help='Commit message')
@click.argument('files', nargs=-1)
def commit(all, ai, message, files):
    """Commit changes with optional AI-generated message."""
    git, github, agent = get_clients()

    try:
        # Stage files
        if all:
            git.add(all=True)
            console.print("[green]OK[/green] Staged all changes")
        elif files:
            git.add(list(files))
            console.print(f"[green]OK[/green] Staged {len(files)} file(s)")
        else:
            console.print("[yellow]No files specified. Use --all or specify files.[/yellow]")
            return

        # Get diff
        diff = git.get_diff(staged=True)
        if not diff:
            console.print("[yellow]No staged changes to commit.[/yellow]")
            return

        # Generate or use provided message
        if ai and not message:
            console.print("[cyan]AI: Generating commit message...[/cyan]")
            message = agent.generate_commit_message(diff)
            console.print("\n[bold]Generated message:[/bold]")
            console.print(Panel(message, border_style="cyan"))

            if not click.confirm("\nUse this message?", default=True):
                message = click.prompt("Enter commit message")

        if not message:
            message = click.prompt("Enter commit message")

        # Commit
        commit_sha = git.commit(message)
        console.print(f"\n[green]OK Committed: {commit_sha}[/green]")
        console.print(f"  {message.split(chr(10))[0]}")

    except Exception as e:
        console.print(f"[red]ERROR Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--remote', '-r', default='origin', help='Remote name')
@click.option('--branch', '-b', help='Branch name')
@click.option('--set-upstream', '-u', is_flag=True, help='Set upstream tracking')
@click.option('--force', '-f', is_flag=True, help='Force push')
def push(remote, branch, set_upstream, force):
    """Push commits to remote repository."""
    git, _, _ = get_clients()

    try:
        with console.status("[cyan]Pushing changes...[/cyan]"):
            result = git.push(
                remote=remote,
                branch=branch,
                set_upstream=set_upstream,
                force=force
            )

        console.print(f"[green]OK {result}[/green]")

    except Exception as e:
        console.print(f"[red]ERROR Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--remote', '-r', default='origin', help='Remote name')
@click.option('--branch', '-b', help='Branch name')
@click.option('--rebase', is_flag=True, help='Rebase instead of merge')
def pull(remote, branch, rebase):
    """Pull changes from remote repository."""
    git, _, _ = get_clients()

    try:
        with console.status("[cyan]Pulling changes...[/cyan]"):
            result = git.pull(remote=remote, branch=branch, rebase=rebase)

        console.print(f"[green]OK {result}[/green]")

    except Exception as e:
        console.print(f"[red]ERROR Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--verbose', '-v', is_flag=True, help='Show detailed status')
def status(verbose):
    """Show repository status."""
    git, _, _ = get_clients()

    try:
        status_info = git.status()

        # Display current branch
        console.print(f"\n[bold cyan]On branch:[/bold cyan] {status_info['current_branch']}")

        # Display modified files
        if status_info['modified']:
            console.print("\n[yellow]Modified files:[/yellow]")
            for file in status_info['modified']:
                console.print(f"  [yellow]M[/yellow] {file}")

        # Display staged files
        if status_info['staged']:
            console.print("\n[green]Staged files:[/green]")
            for file in status_info['staged']:
                console.print(f"  [green]A[/green] {file}")

        # Display untracked files
        if status_info['untracked']:
            console.print("\n[red]Untracked files:[/red]")
            for file in status_info['untracked']:
                console.print(f"  [red]?[/red] {file}")

        # Clean working tree
        if not status_info['is_dirty']:
            console.print("\n[green]OK Working tree clean[/green]")

        # Show diff if verbose
        if verbose and status_info['is_dirty']:
            diff = git.get_diff()
            if diff:
                console.print("\n[bold]Changes:[/bold]")
                syntax = Syntax(diff, "diff", theme="monokai", line_numbers=True)
                console.print(syntax)

    except Exception as e:
        console.print(f"[red]ERROR Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('branch_name')
@click.option('--checkout', '-c', is_flag=True, help='Checkout after creating')
def branch(branch_name, checkout):
    """Create a new branch."""
    git, _, _ = get_clients()

    try:
        git.create_branch(branch_name, checkout=checkout)

        if checkout:
            console.print(f"[green]OK Created and switched to branch '{branch_name}'[/green]")
        else:
            console.print(f"[green]OK Created branch '{branch_name}'[/green]")

    except Exception as e:
        console.print(f"[red]ERROR Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('branch_name')
def checkout(branch_name):
    """Checkout a branch."""
    git, _, _ = get_clients()

    try:
        git.checkout(branch_name)
        console.print(f"[green]OK Switched to branch '{branch_name}'[/green]")

    except Exception as e:
        console.print(f"[red]ERROR Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--count', '-n', default=10, help='Number of commits to show')
def log(count):
    """Show commit history."""
    git, _, _ = get_clients()

    try:
        commits = git.get_log(max_count=count)

        table = Table(title="Commit History", show_header=True, header_style="bold cyan")
        table.add_column("SHA", style="yellow", width=8)
        table.add_column("Author", style="green")
        table.add_column("Date", style="cyan")
        table.add_column("Message")

        for commit in commits:
            table.add_row(
                commit['sha'],
                commit['author'],
                commit['date'][:10],
                commit['message'].split('\n')[0][:50]
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]ERROR Error: {str(e)}[/red]")
        sys.exit(1)


# ============================================================================
# GITHUB OPERATIONS
# ============================================================================

@cli.command(name='create-repo')
@click.argument('name')
@click.option('--description', '-d', default='', help='Repository description')
@click.option('--private', is_flag=True, help='Make repository private')
@click.option('--init', is_flag=True, default=True, help='Initialize with README')
def create_repo(name, description, private, init):
    """Create a new GitHub repository."""
    _, github, _ = get_clients()

    try:
        with console.status(f"[cyan]Creating repository '{name}'...[/cyan]"):
            repo = github.create_repository(
                name=name,
                description=description,
                private=private,
                auto_init=init
            )

        console.print(f"\n[green]OK Repository created successfully![/green]")
        console.print(f"\n[bold]Repository:[/bold] {repo.full_name}")
        console.print(f"[bold]URL:[/bold] {repo.html_url}")
        console.print(f"[bold]Clone:[/bold] {repo.clone_url}")

        if click.confirm("\nClone to current directory?"):
            git, _, _ = get_clients()
            git.clone_repository(repo.clone_url, name)
            console.print(f"[green]OK Cloned to ./{name}[/green]")

    except Exception as e:
        console.print(f"[red]ERROR Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command(name='list-repos')
@click.option('--limit', '-n', default=10, help='Number of repositories to show')
def list_repos(limit):
    """List your GitHub repositories."""
    _, github, _ = get_clients()

    try:
        repos = github.list_repositories()[:limit]

        table = Table(title="Your Repositories", show_header=True, header_style="bold cyan")
        table.add_column("Name", style="green")
        table.add_column("Description")
        table.add_column("Stars", justify="right", style="yellow")
        table.add_column("Private", justify="center")

        for repo in repos:
            table.add_row(
                repo.name,
                (repo.description or '')[:50],
                str(repo.stargazers_count),
                "Private" if repo.private else "Public"
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]ERROR Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.option('--staged', is_flag=True, help='Review staged changes')
@click.option('--ai', is_flag=True, default=True, help='Use AI for review')
def review(staged, ai):
    """Review code changes with AI analysis."""
    git, _, agent = get_clients()

    try:
        # Get diff
        diff = git.get_diff(staged=staged)

        if not diff:
            console.print("[yellow]No changes to review.[/yellow]")
            return

        # Show diff
        console.print("\n[bold]Changes:[/bold]")
        syntax = Syntax(diff[:2000], "diff", theme="monokai")
        console.print(syntax)

        if len(diff) > 2000:
            console.print(f"\n[dim]... ({len(diff) - 2000} more characters)[/dim]")

        # AI review
        if ai:
            with console.status("[cyan]AI: AI is reviewing your code...[/cyan]"):
                review_data = agent.review_code_changes(diff)

            console.print("\n[bold cyan]AI Review:[/bold cyan]")
            console.print(Panel(review_data.get('summary', 'No summary'), title="Summary", border_style="cyan"))

            if review_data.get('issues'):
                console.print("\n[yellow]Issues Found:[/yellow]")
                for issue in review_data['issues']:
                    console.print(f"  • {issue}")

            if review_data.get('suggestions'):
                console.print("\n[green]Suggestions:[/green]")
                for suggestion in review_data['suggestions']:
                    console.print(f"  • {suggestion}")

            if review_data.get('security_concerns'):
                console.print("\n[red]Security Concerns:[/red]")
                for concern in review_data['security_concerns']:
                    console.print(f"  WARNING: {concern}")

            rating = review_data.get('rating', 'N/A')
            console.print(f"\n[bold]Rating:[/bold] {rating}/10")
            console.print(f"[bold]Recommendation:[/bold] {review_data.get('recommendation', 'N/A')}")

    except Exception as e:
        console.print(f"[red]ERROR Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command(name='create-pr')
@click.argument('title')
@click.option('--base', '-b', default='main', help='Base branch')
@click.option('--head', '-h', help='Head branch (defaults to current)')
@click.option('--body', '-d', help='PR description')
@click.option('--ai', is_flag=True, help='Generate description with AI')
@click.option('--repo', '-r', help='Repository name')
def create_pr(title, base, head, body, ai, repo):
    """Create a pull request."""
    git, github, agent = get_clients()

    try:
        # Get current branch if head not specified
        if not head:
            head = git.get_current_branch()

        # Get repository name
        if not repo:
            remote_url = git.get_remote_url()
            # Extract repo name from URL
            repo = remote_url.split('/')[-1].replace('.git', '')
            if '/' not in repo:
                repo = f"{github.user.login}/{repo}"

        # Generate description with AI if requested
        if ai and not body:
            console.print("[cyan]AI: Generating PR description...[/cyan]")
            diff = git.get_diff()
            commits = git.get_log(max_count=10)
            commit_messages = [c['message'] for c in commits]

            body = agent.generate_pr_description(diff, head, commit_messages)

            console.print("\n[bold]Generated description:[/bold]")
            console.print(Panel(body, border_style="cyan"))

            if not click.confirm("\nUse this description?", default=True):
                body = click.prompt("Enter PR description")

        if not body:
            body = click.prompt("Enter PR description (optional)", default="")

        # Create PR
        with console.status("[cyan]Creating pull request...[/cyan]"):
            pr = github.create_pull_request(
                repo_name=repo,
                title=title,
                head=head,
                base=base,
                body=body
            )

        console.print(f"\n[green]OK Pull request created![/green]")
        console.print(f"\n[bold]PR #{pr.number}:[/bold] {pr.title}")
        console.print(f"[bold]URL:[/bold] {pr.html_url}")

    except Exception as e:
        console.print(f"[red]ERROR Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command(name='list-prs')
@click.option('--repo', '-r', help='Repository name')
@click.option('--state', '-s', default='open', type=click.Choice(['open', 'closed', 'all']))
def list_prs(repo, state):
    """List pull requests."""
    git, github, _ = get_clients()

    try:
        # Get repository name
        if not repo:
            remote_url = git.get_remote_url()
            repo = remote_url.split('/')[-1].replace('.git', '')
            if '/' not in repo:
                repo = f"{github.user.login}/{repo}"

        prs = github.list_pull_requests(repo, state=state)

        table = Table(title=f"Pull Requests ({state})", show_header=True, header_style="bold cyan")
        table.add_column("#", style="yellow", width=6)
        table.add_column("Title", style="green")
        table.add_column("Author")
        table.add_column("State")

        for pr in prs[:20]:
            state_style = "green" if pr.state == "open" else "dim"
            table.add_row(
                f"#{pr.number}",
                pr.title[:50],
                pr.user.login,
                f"[{state_style}]{pr.state}[/{state_style}]"
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]ERROR Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command(name='review-pr')
@click.argument('pr_number', type=int)
@click.option('--repo', '-r', help='Repository name')
def review_pr(pr_number, repo):
    """Review a pull request with AI."""
    git, github, agent = get_clients()

    try:
        # Get repository name
        if not repo:
            remote_url = git.get_remote_url()
            repo = remote_url.split('/')[-1].replace('.git', '')
            if '/' not in repo:
                repo = f"{github.user.login}/{repo}"

        # Get PR
        with console.status(f"[cyan]Fetching PR #{pr_number}...[/cyan]"):
            pr = github.get_pull_request(repo, pr_number)
            diff = github.get_pr_diff(repo, pr_number)

        console.print(f"\n[bold]PR #{pr.number}:[/bold] {pr.title}")
        console.print(f"[bold]By:[/bold] {pr.user.login}")
        console.print(f"[bold]State:[/bold] {pr.state}")

        # AI Review
        with console.status("[cyan]AI: AI is reviewing the PR...[/cyan]"):
            review = agent.review_pull_request(
                pr_title=pr.title,
                pr_description=pr.body or "",
                diff=diff,
                files_changed=pr.changed_files
            )

        console.print("\n")
        console.print(Panel(
            review.get('review_comment', 'No review generated'),
            title="AI Review",
            border_style="cyan"
        ))

        console.print(f"\n[bold]Recommendation:[/bold] {review.get('recommendation', 'N/A')}")

        if click.confirm("\nPost this review to GitHub?"):
            github.comment_on_pr(repo, pr_number, review['review_comment'])
            console.print("[green]OK Review posted![/green]")

    except Exception as e:
        console.print(f"[red]ERROR Error: {str(e)}[/red]")
        sys.exit(1)


@cli.command()
@click.argument('question')
def ask(question):
    """Ask the AI assistant a question about Git/GitHub."""
    _, _, agent = get_clients()

    try:
        with console.status("[cyan]AI: Thinking...[/cyan]"):
            answer = agent.ask_question(question)

        console.print("\n[bold cyan]AI Assistant:[/bold cyan]")
        console.print(Panel(Markdown(answer), border_style="cyan"))

    except Exception as e:
        console.print(f"[red]ERROR Error: {str(e)}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    cli()
