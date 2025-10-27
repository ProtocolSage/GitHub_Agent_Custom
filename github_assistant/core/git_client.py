"""Git client for local repository operations."""

from typing import List, Optional, Dict
from pathlib import Path
import git
from git import Repo, GitCommandError, InvalidGitRepositoryError


class GitClient:
    """Comprehensive Git client for local operations."""

    def __init__(self, repo_path: Optional[str] = None):
        """Initialize Git client with repository path (defaults to current directory)."""
        self.repo_path = Path(repo_path or ".").resolve()
        try:
            self.repo = Repo(self.repo_path)
        except InvalidGitRepositoryError:
            self.repo = None

    def init_repository(self, path: Optional[str] = None) -> Repo:
        """Initialize a new Git repository."""
        target_path = Path(path or self.repo_path)
        target_path.mkdir(parents=True, exist_ok=True)
        self.repo = Repo.init(target_path)
        self.repo_path = target_path
        return self.repo

    def clone_repository(self, url: str, path: Optional[str] = None) -> Repo:
        """Clone a repository from URL."""
        try:
            target_path = Path(path or ".").resolve()
            self.repo = Repo.clone_from(url, target_path)
            self.repo_path = target_path
            return self.repo
        except GitCommandError as e:
            raise Exception(f"Failed to clone repository: {str(e)}")

    # Status and Information

    def status(self) -> Dict[str, List[str]]:
        """Get repository status."""
        self._ensure_repo()

        return {
            "modified": [item.a_path for item in self.repo.index.diff(None)],
            "staged": [item.a_path for item in self.repo.index.diff("HEAD")],
            "untracked": self.repo.untracked_files,
            "current_branch": self.repo.active_branch.name,
            "is_dirty": self.repo.is_dirty(),
        }

    def get_diff(self, staged: bool = False) -> str:
        """Get diff of changes."""
        self._ensure_repo()

        if staged:
            return self.repo.git.diff("--staged")
        else:
            return self.repo.git.diff()

    def get_log(self, max_count: int = 10, branch: Optional[str] = None) -> List[Dict]:
        """Get commit history."""
        self._ensure_repo()

        commits = []
        ref = branch or self.repo.active_branch.name

        for commit in self.repo.iter_commits(ref, max_count=max_count):
            commits.append({
                "sha": commit.hexsha[:7],
                "author": str(commit.author),
                "date": commit.committed_datetime.isoformat(),
                "message": commit.message.strip(),
            })

        return commits

    # Staging Operations

    def add(self, files: Optional[List[str]] = None, all: bool = False) -> None:
        """Stage files for commit."""
        self._ensure_repo()

        try:
            if all:
                self.repo.git.add(A=True)
            elif files:
                self.repo.index.add(files)
            else:
                raise ValueError("Specify files to add or use all=True")
        except GitCommandError as e:
            raise Exception(f"Failed to stage files: {str(e)}")

    def reset(self, files: Optional[List[str]] = None) -> None:
        """Unstage files."""
        self._ensure_repo()

        try:
            if files:
                self.repo.index.reset(files)
            else:
                self.repo.index.reset()
        except GitCommandError as e:
            raise Exception(f"Failed to unstage files: {str(e)}")

    # Commit Operations

    def commit(self, message: str, author: Optional[str] = None, email: Optional[str] = None) -> str:
        """Create a commit."""
        self._ensure_repo()

        try:
            if author and email:
                commit = self.repo.index.commit(
                    message,
                    author=git.Actor(author, email)
                )
            else:
                commit = self.repo.index.commit(message)

            return commit.hexsha[:7]
        except GitCommandError as e:
            raise Exception(f"Failed to commit: {str(e)}")

    def amend_commit(self, message: Optional[str] = None) -> str:
        """Amend the last commit."""
        self._ensure_repo()

        try:
            if message:
                commit = self.repo.index.commit(message, amend=True)
            else:
                commit = self.repo.index.commit(amend=True)

            return commit.hexsha[:7]
        except GitCommandError as e:
            raise Exception(f"Failed to amend commit: {str(e)}")

    # Branch Operations

    def create_branch(self, branch_name: str, checkout: bool = True) -> None:
        """Create a new branch."""
        self._ensure_repo()

        try:
            new_branch = self.repo.create_head(branch_name)
            if checkout:
                new_branch.checkout()
        except GitCommandError as e:
            raise Exception(f"Failed to create branch: {str(e)}")

    def checkout(self, branch_name: str, create: bool = False) -> None:
        """Checkout a branch."""
        self._ensure_repo()

        try:
            if create:
                self.create_branch(branch_name, checkout=True)
            else:
                self.repo.heads[branch_name].checkout()
        except (GitCommandError, IndexError) as e:
            raise Exception(f"Failed to checkout branch: {str(e)}")

    def delete_branch(self, branch_name: str, force: bool = False) -> None:
        """Delete a branch."""
        self._ensure_repo()

        try:
            self.repo.delete_head(branch_name, force=force)
        except GitCommandError as e:
            raise Exception(f"Failed to delete branch: {str(e)}")

    def list_branches(self, remote: bool = False) -> List[str]:
        """List all branches."""
        self._ensure_repo()

        if remote:
            return [ref.name for ref in self.repo.remote().refs]
        else:
            return [head.name for head in self.repo.heads]

    def get_current_branch(self) -> str:
        """Get the current branch name."""
        self._ensure_repo()
        return self.repo.active_branch.name

    # Remote Operations

    def add_remote(self, name: str, url: str) -> None:
        """Add a remote."""
        self._ensure_repo()

        try:
            self.repo.create_remote(name, url)
        except GitCommandError as e:
            raise Exception(f"Failed to add remote: {str(e)}")

    def remove_remote(self, name: str) -> None:
        """Remove a remote."""
        self._ensure_repo()

        try:
            self.repo.delete_remote(name)
        except GitCommandError as e:
            raise Exception(f"Failed to remove remote: {str(e)}")

    def list_remotes(self) -> List[str]:
        """List all remotes."""
        self._ensure_repo()
        return [remote.name for remote in self.repo.remotes]

    def fetch(self, remote: str = "origin", prune: bool = False) -> None:
        """Fetch from remote."""
        self._ensure_repo()

        try:
            remote_obj = self.repo.remote(remote)
            remote_obj.fetch(prune=prune)
        except GitCommandError as e:
            raise Exception(f"Failed to fetch from {remote}: {str(e)}")

    def pull(self, remote: str = "origin", branch: Optional[str] = None, rebase: bool = False) -> str:
        """Pull changes from remote."""
        self._ensure_repo()

        try:
            remote_obj = self.repo.remote(remote)
            target_branch = branch or self.repo.active_branch.name

            if rebase:
                result = remote_obj.pull(target_branch, rebase=True)
            else:
                result = remote_obj.pull(target_branch)

            return f"Pulled from {remote}/{target_branch}"
        except GitCommandError as e:
            raise Exception(f"Failed to pull: {str(e)}")

    def push(
        self,
        remote: str = "origin",
        branch: Optional[str] = None,
        set_upstream: bool = False,
        force: bool = False
    ) -> str:
        """Push changes to remote."""
        self._ensure_repo()

        try:
            remote_obj = self.repo.remote(remote)
            target_branch = branch or self.repo.active_branch.name

            if set_upstream:
                remote_obj.push(refspec=f"{target_branch}:{target_branch}", set_upstream=True)
            elif force:
                remote_obj.push(refspec=f"{target_branch}:{target_branch}", force=True)
            else:
                remote_obj.push(refspec=f"{target_branch}:{target_branch}")

            return f"Pushed to {remote}/{target_branch}"
        except GitCommandError as e:
            raise Exception(f"Failed to push: {str(e)}")

    # Merge Operations

    def merge(self, branch_name: str, no_ff: bool = False) -> str:
        """Merge a branch into current branch."""
        self._ensure_repo()

        try:
            if no_ff:
                self.repo.git.merge(branch_name, no_ff=True)
            else:
                self.repo.git.merge(branch_name)

            return f"Merged {branch_name} into {self.repo.active_branch.name}"
        except GitCommandError as e:
            raise Exception(f"Failed to merge: {str(e)}")

    def abort_merge(self) -> None:
        """Abort an ongoing merge."""
        self._ensure_repo()

        try:
            self.repo.git.merge(abort=True)
        except GitCommandError as e:
            raise Exception(f"Failed to abort merge: {str(e)}")

    # Stash Operations

    def stash(self, message: Optional[str] = None, include_untracked: bool = False) -> None:
        """Stash changes."""
        self._ensure_repo()

        try:
            if include_untracked:
                self.repo.git.stash("save", "-u", message or "WIP")
            else:
                self.repo.git.stash("save", message or "WIP")
        except GitCommandError as e:
            raise Exception(f"Failed to stash: {str(e)}")

    def stash_pop(self, index: int = 0) -> None:
        """Pop stashed changes."""
        self._ensure_repo()

        try:
            self.repo.git.stash("pop", f"stash@{{{index}}}")
        except GitCommandError as e:
            raise Exception(f"Failed to pop stash: {str(e)}")

    def stash_list(self) -> List[str]:
        """List all stashes."""
        self._ensure_repo()

        try:
            output = self.repo.git.stash("list")
            return output.split("\n") if output else []
        except GitCommandError:
            return []

    # Tag Operations

    def create_tag(self, tag_name: str, message: Optional[str] = None) -> None:
        """Create a tag."""
        self._ensure_repo()

        try:
            if message:
                self.repo.create_tag(tag_name, message=message)
            else:
                self.repo.create_tag(tag_name)
        except GitCommandError as e:
            raise Exception(f"Failed to create tag: {str(e)}")

    def delete_tag(self, tag_name: str) -> None:
        """Delete a tag."""
        self._ensure_repo()

        try:
            self.repo.delete_tag(tag_name)
        except GitCommandError as e:
            raise Exception(f"Failed to delete tag: {str(e)}")

    def list_tags(self) -> List[str]:
        """List all tags."""
        self._ensure_repo()
        return [tag.name for tag in self.repo.tags]

    # Utility Methods

    def _ensure_repo(self) -> None:
        """Ensure repository is initialized."""
        if self.repo is None:
            raise Exception("Not a git repository. Run 'git init' first.")

    def is_repo(self) -> bool:
        """Check if current directory is a git repository."""
        return self.repo is not None

    def get_remote_url(self, remote: str = "origin") -> str:
        """Get remote URL."""
        self._ensure_repo()

        try:
            return list(self.repo.remote(remote).urls)[0]
        except (IndexError, ValueError):
            raise Exception(f"Remote '{remote}' not found")
