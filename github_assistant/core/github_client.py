"""GitHub API client for repository and remote operations."""

from typing import List, Optional, Dict, Any
from github import Github, GithubException, Repository, PullRequest, Issue, RateLimitExceededException
from github.GithubObject import NotSet
import os
import time
import logging

logger = logging.getLogger(__name__)


class GitHubClient:
    """Comprehensive GitHub API client with rate limit handling."""

    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub client with token from env or parameter."""
        self.token = token or os.getenv('GITHUB_TOKEN')
        if not self.token:
            raise ValueError("GitHub token required. Set GITHUB_TOKEN env variable.")

        self.client = Github(self.token)
        self.user = self.client.get_user()
        logger.debug(f"GitHub client initialized for user: {self.user.login}")

    def _handle_rate_limit(self, func, *args, **kwargs):
        """
        Execute function with rate limit handling.

        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If function fails after retry
        """
        max_retries = 3
        retry_delay = 60  # seconds

        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except RateLimitExceededException:
                if attempt < max_retries - 1:
                    rate_limit = self.client.get_rate_limit()
                    reset_time = rate_limit.core.reset
                    wait_time = (reset_time - time.time()) + 5  # Add 5s buffer

                    logger.warning(
                        f"Rate limit exceeded. Waiting {wait_time:.0f}s until reset..."
                    )
                    time.sleep(min(wait_time, retry_delay))
                else:
                    logger.error("Rate limit exceeded, max retries reached")
                    raise
            except GithubException as e:
                if e.status == 403 and 'rate limit' in str(e).lower():
                    if attempt < max_retries - 1:
                        logger.warning(f"Rate limit hit, retrying in {retry_delay}s...")
                        time.sleep(retry_delay)
                    else:
                        raise
                else:
                    raise

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        rate_limit = self.client.get_rate_limit()
        return {
            "core": {
                "limit": rate_limit.core.limit,
                "remaining": rate_limit.core.remaining,
                "reset": rate_limit.core.reset.isoformat()
            },
            "search": {
                "limit": rate_limit.search.limit,
                "remaining": rate_limit.search.remaining,
                "reset": rate_limit.search.reset.isoformat()
            }
        }

    # Repository Operations

    def create_repository(
        self,
        name: str,
        description: str = "",
        private: bool = False,
        auto_init: bool = True,
        gitignore_template: Optional[str] = None,
        license_template: Optional[str] = None
    ) -> Repository:
        """Create a new repository."""
        try:
            repo = self.user.create_repo(
                name=name,
                description=description,
                private=private,
                auto_init=auto_init,
                gitignore_template=gitignore_template or NotSet,
                license_template=license_template or NotSet
            )
            return repo
        except GithubException as e:
            raise Exception(f"Failed to create repository: {e.data.get('message', str(e))}")

    def get_repository(self, repo_name: str) -> Repository:
        """Get a repository by name (owner/repo or just repo for user's repos)."""
        try:
            if '/' in repo_name:
                return self.client.get_repo(repo_name)
            else:
                return self.user.get_repo(repo_name)
        except GithubException as e:
            raise Exception(f"Repository not found: {repo_name}")

    def list_repositories(
        self,
        type: str = "all",
        sort: str = "updated",
        direction: str = "desc"
    ) -> List[Repository]:
        """List user's repositories."""
        return list(self.user.get_repos(type=type, sort=sort, direction=direction))

    def delete_repository(self, repo_name: str) -> bool:
        """Delete a repository."""
        try:
            repo = self.get_repository(repo_name)
            repo.delete()
            return True
        except Exception as e:
            raise Exception(f"Failed to delete repository: {str(e)}")

    def fork_repository(self, repo_full_name: str) -> Repository:
        """Fork a repository."""
        try:
            repo = self.client.get_repo(repo_full_name)
            return self.user.create_fork(repo)
        except GithubException as e:
            raise Exception(f"Failed to fork repository: {str(e)}")

    # Pull Request Operations

    def create_pull_request(
        self,
        repo_name: str,
        title: str,
        head: str,
        base: str = "main",
        body: str = "",
        draft: bool = False
    ) -> PullRequest:
        """Create a pull request."""
        try:
            repo = self.get_repository(repo_name)
            pr = repo.create_pull(
                title=title,
                body=body,
                head=head,
                base=base,
                draft=draft
            )
            return pr
        except GithubException as e:
            raise Exception(f"Failed to create PR: {e.data.get('message', str(e))}")

    def list_pull_requests(
        self,
        repo_name: str,
        state: str = "open",
        sort: str = "created",
        direction: str = "desc"
    ) -> List[PullRequest]:
        """List pull requests for a repository."""
        repo = self.get_repository(repo_name)
        return list(repo.get_pulls(state=state, sort=sort, direction=direction))

    def get_pull_request(self, repo_name: str, number: int) -> PullRequest:
        """Get a specific pull request."""
        repo = self.get_repository(repo_name)
        return repo.get_pull(number)

    def merge_pull_request(
        self,
        repo_name: str,
        number: int,
        commit_message: Optional[str] = None,
        merge_method: str = "merge"
    ) -> bool:
        """Merge a pull request."""
        try:
            pr = self.get_pull_request(repo_name, number)
            result = pr.merge(
                commit_message=commit_message,
                merge_method=merge_method
            )
            return result.merged
        except GithubException as e:
            raise Exception(f"Failed to merge PR: {str(e)}")

    def get_pr_diff(self, repo_name: str, number: int) -> str:
        """Get the diff for a pull request."""
        pr = self.get_pull_request(repo_name, number)
        files = pr.get_files()

        diff_content = []
        for file in files:
            diff_content.append(f"\n--- {file.filename} ---")
            diff_content.append(f"Status: {file.status}")
            diff_content.append(f"Changes: +{file.additions} -{file.deletions}")
            if file.patch:
                diff_content.append(file.patch)

        return "\n".join(diff_content)

    def comment_on_pr(self, repo_name: str, number: int, comment: str) -> None:
        """Add a comment to a pull request."""
        pr = self.get_pull_request(repo_name, number)
        pr.create_issue_comment(comment)

    # Issue Operations

    def create_issue(
        self,
        repo_name: str,
        title: str,
        body: str = "",
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None
    ) -> Issue:
        """Create an issue."""
        try:
            repo = self.get_repository(repo_name)
            issue = repo.create_issue(
                title=title,
                body=body,
                labels=labels or [],
                assignees=assignees or []
            )
            return issue
        except GithubException as e:
            raise Exception(f"Failed to create issue: {str(e)}")

    def list_issues(
        self,
        repo_name: str,
        state: str = "open",
        labels: Optional[List[str]] = None,
        sort: str = "created",
        direction: str = "desc"
    ) -> List[Issue]:
        """List issues for a repository."""
        repo = self.get_repository(repo_name)
        return list(repo.get_issues(
            state=state,
            labels=labels or NotSet,
            sort=sort,
            direction=direction
        ))

    def close_issue(self, repo_name: str, number: int) -> None:
        """Close an issue."""
        repo = self.get_repository(repo_name)
        issue = repo.get_issue(number)
        issue.edit(state="closed")

    def comment_on_issue(self, repo_name: str, number: int, comment: str) -> None:
        """Add a comment to an issue."""
        repo = self.get_repository(repo_name)
        issue = repo.get_issue(number)
        issue.create_comment(comment)

    # Branch Operations

    def create_branch(self, repo_name: str, branch_name: str, from_branch: str = "main") -> None:
        """Create a new branch from an existing branch."""
        try:
            repo = self.get_repository(repo_name)
            source = repo.get_branch(from_branch)
            repo.create_git_ref(f"refs/heads/{branch_name}", source.commit.sha)
        except GithubException as e:
            raise Exception(f"Failed to create branch: {str(e)}")

    def delete_branch(self, repo_name: str, branch_name: str) -> None:
        """Delete a branch."""
        try:
            repo = self.get_repository(repo_name)
            ref = repo.get_git_ref(f"heads/{branch_name}")
            ref.delete()
        except GithubException as e:
            raise Exception(f"Failed to delete branch: {str(e)}")

    def list_branches(self, repo_name: str) -> List[str]:
        """List all branches in a repository."""
        repo = self.get_repository(repo_name)
        return [branch.name for branch in repo.get_branches()]

    # Release Operations

    def create_release(
        self,
        repo_name: str,
        tag_name: str,
        name: str,
        body: str = "",
        draft: bool = False,
        prerelease: bool = False,
        target_commitish: Optional[str] = None
    ):
        """Create a new release."""
        try:
            repo = self.get_repository(repo_name)
            return repo.create_git_release(
                tag=tag_name,
                name=name,
                message=body,
                draft=draft,
                prerelease=prerelease,
                target_commitish=target_commitish or NotSet
            )
        except GithubException as e:
            raise Exception(f"Failed to create release: {str(e)}")

    def list_releases(self, repo_name: str) -> list:
        """List all releases for a repository."""
        repo = self.get_repository(repo_name)
        return list(repo.get_releases())

    # User Operations

    def get_user_info(self) -> Dict[str, Any]:
        """Get authenticated user information."""
        return {
            "login": self.user.login,
            "name": self.user.name,
            "email": self.user.email,
            "bio": self.user.bio,
            "public_repos": self.user.public_repos,
            "followers": self.user.followers,
            "following": self.user.following,
        }

    # Notification Operations

    def get_notifications(self, all: bool = False, participating: bool = False) -> list:
        """Get user notifications."""
        return list(self.user.get_notifications(all=all, participating=participating))

    def mark_notifications_as_read(self) -> None:
        """Mark all notifications as read."""
        self.user.mark_notifications_as_read()
