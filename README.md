# 🤖 GitHub Assistant

Your AI-powered personal assistant for Git and GitHub operations. Automate commits, reviews, pull requests, and repository management with intelligent AI assistance powered by Claude.

## ✨ Features

### Git Operations
- **Smart Commits**: AI-generated commit messages from your changes
- **Push/Pull**: Seamless remote synchronization
- **Branch Management**: Create, switch, and manage branches
- **Status & History**: Beautiful visualization of your repository state

### GitHub Operations
- **Repository Management**: Create, list, and manage repositories
- **Pull Requests**: Create PRs with AI-generated descriptions
- **PR Reviews**: AI-powered code review and analysis
- **Issue Management**: Create and manage issues

### AI-Powered Intelligence
- **Code Review**: Get instant AI feedback on your changes
- **Commit Messages**: Generate professional commit messages automatically
- **PR Descriptions**: Auto-generate comprehensive PR descriptions
- **Ask Questions**: Get help with Git/GitHub concepts

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

### 2. Configuration

Copy [.env.example](.env.example) to `.env` and add your API keys:

```bash
GITHUB_TOKEN=your_github_personal_access_token_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

**Get your tokens:**
- GitHub: [Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens)
- Anthropic: [Anthropic Console](https://console.anthropic.com/)

### 3. Usage

The assistant is available via the `gh-assist` command:

```bash
gh-assist --help
```

## 📖 Commands

### Git Operations

#### Commit with AI-generated message
```bash
gh-assist commit --all --ai
```

#### Commit with custom message
```bash
gh-assist commit -m "feat: add new feature" file1.py file2.py
```

#### Push to remote
```bash
gh-assist push                    # Push current branch
gh-assist push -u                 # Push and set upstream
gh-assist push --force            # Force push (use carefully!)
```

#### Pull from remote
```bash
gh-assist pull                    # Pull current branch
gh-assist pull --rebase           # Pull with rebase
```

#### Check status
```bash
gh-assist status                  # Basic status
gh-assist status -v               # Verbose with diff
```

#### View commit history
```bash
gh-assist log                     # Last 10 commits
gh-assist log -n 20               # Last 20 commits
```

#### Branch operations
```bash
gh-assist branch feature/new-thing        # Create branch
gh-assist branch -c feature/new-thing     # Create and checkout
gh-assist checkout main                   # Switch branch
```

### GitHub Operations

#### Create repository
```bash
gh-assist create-repo my-awesome-project
gh-assist create-repo my-project --private --description "My cool project"
```

#### List repositories
```bash
gh-assist list-repos              # Show 10 repos
gh-assist list-repos -n 20        # Show 20 repos
```

#### Create pull request
```bash
gh-assist create-pr "Add new feature"
gh-assist create-pr "Fix bug" --base main --ai
gh-assist create-pr "Update docs" --repo owner/repo
```

#### List pull requests
```bash
gh-assist list-prs                # Open PRs
gh-assist list-prs --state all    # All PRs
gh-assist list-prs --repo owner/repo
```

#### Review pull request with AI
```bash
gh-assist review-pr 123           # Review PR #123
gh-assist review-pr 42 --repo owner/repo
```

### AI-Powered Commands

#### Review your changes
```bash
gh-assist review                  # Review unstaged changes
gh-assist review --staged         # Review staged changes
```

#### Ask AI assistant
```bash
gh-assist ask "How do I rebase my branch?"
gh-assist ask "What's the difference between merge and rebase?"
gh-assist ask "How to undo last commit?"
```

## 🔥 Workflow Examples

### Daily Commit Workflow
```bash
# Make your changes
# ...

# Review changes
gh-assist status -v

# AI review before committing
gh-assist review

# Commit with AI-generated message
gh-assist commit --all --ai

# Push to remote
gh-assist push
```

### Create PR Workflow
```bash
# Create feature branch
gh-assist branch -c feature/awesome-thing

# Make changes and commit
gh-assist commit --all --ai

# Push with upstream
gh-assist push -u

# Create PR with AI description
gh-assist create-pr "Add awesome feature" --ai
```

### Review PR Workflow
```bash
# List open PRs
gh-assist list-prs

# Review specific PR with AI
gh-assist review-pr 123

# The AI will analyze the PR and optionally post review
```

### New Repository Workflow
```bash
# Create repository on GitHub
gh-assist create-repo my-new-project --description "My awesome project"

# It will offer to clone automatically
# Start coding!
```

## 🎯 Real-World Use Cases

### 1. Quick Daily Commits
Instead of:
```bash
git add .
git commit -m "updates"  # Bad commit message!
git push
```

Do this:
```bash
gh-assist commit --all --ai
gh-assist push
```

### 2. Professional PR Creation
Instead of writing PR descriptions manually:
```bash
gh-assist create-pr "Implement user authentication" --ai
```

The AI will analyze your changes and generate:
- Summary of changes
- List of modifications
- Testing notes
- Checklist

### 3. Code Review Before Commit
Catch issues before they're committed:
```bash
gh-assist review --ai
```

Get feedback on:
- Code quality
- Potential bugs
- Security concerns
- Best practices

### 4. Learning Git/GitHub
```bash
gh-assist ask "What's a good branching strategy?"
gh-assist ask "How to resolve merge conflicts?"
gh-assist ask "When should I use rebase vs merge?"
```

## 🛠️ Configuration

Your credentials are stored in [.env](.env):

```env
# Required
GITHUB_TOKEN=your_github_personal_access_token_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## 📋 Requirements

- Python 3.8+
- Git installed
- GitHub account and token
- Anthropic API key

## 🔐 Security

- **Never commit your `.env` file!** (It's in .gitignore)
- Keep your tokens secure
- Use repository-scoped tokens when possible
- Regularly rotate your API keys

## 🤝 Tips

1. **Use AI commit messages**: They're often better than hastily written ones
2. **Review before committing**: Catch issues early
3. **AI PR reviews**: Get instant feedback on pull requests
4. **Ask questions**: The AI is great for learning Git/GitHub concepts
5. **Combine commands**: Use `--ai` flags for intelligent automation

## 📝 License

MIT License - Use freely for personal or commercial projects!

## 🚀 Next Steps

1. Install the assistant
2. Configure your tokens
3. Try your first AI commit: `gh-assist commit --all --ai`
4. Explore other commands with `gh-assist --help`

---

**Built with:**
- [Claude](https://anthropic.com/) for AI intelligence
- [PyGithub](https://pygithub.readthedocs.io/) for GitHub API
- [GitPython](https://gitpython.readthedocs.io/) for Git operations
- [Rich](https://rich.readthedocs.io/) for beautiful CLI output
## Installation Guide
Run pip install -e .
