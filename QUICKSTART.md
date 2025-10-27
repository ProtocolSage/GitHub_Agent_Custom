# Quick Start Guide

## Setup (2 minutes)

### 1. Install Dependencies
```bash
pip install -e .
```

### 2. Add Credits to Anthropic
Your Anthropic API key needs credits for AI features:
- Go to https://console.anthropic.com/
- Add credits to your account
- Your API key is in the `.env` file

### 3. Verify Setup
```bash
python -m github_assistant --help
```
## First Commands to Try

### 1. Check your current status
```bash
python -m github_assistant status
```

### 2. View commit history
```bash
python -m github_assistant log
```

### 3. Commit with AI-generated message (requires credits)
```bash
# Make some changes first
echo "# Test" >> test.txt

# Commit with AI
python -m github_assistant commit --all --ai
```

### 4. List your GitHub repos
```bash
python -m github_assistant list-repos
```

### 5. Ask AI a question (requires credits)
```bash
python -m github_assistant ask "What's the difference between merge and rebase?"
```

## Daily Workflow

### Morning: Check what needs attention
```bash
python -m github_assistant list-repos
python -m github_assistant list-prs
```

### During coding: Quick commits
```bash
# Review your changes
python -m github_assistant review

# Commit with AI message
python -m github_assistant commit --all --ai

# Push
python -m github_assistant push
```

### Creating PRs
```bash
# Create branch
python -m github_assistant branch -c feature/new-feature

# Make changes, commit, push
python -m github_assistant commit --all --ai
python -m github_assistant push -u

# Create PR with AI description
python -m github_assistant create-pr "Add new feature" --ai
```

## Available Commands

### Git Operations
- `status` - Show repository status
- `log` - Show commit history
- `commit` - Commit changes (use `--ai` for smart messages)
- `push` - Push to remote
- `pull` - Pull from remote
- `branch` - Create branch
- `checkout` - Switch branch

### GitHub Operations
- `create-repo` - Create new repository
- `list-repos` - List your repositories
- `create-pr` - Create pull request
- `list-prs` - List pull requests
- `review-pr` - Review PR with AI

### AI Features
- `review` - AI code review
- `ask` - Ask AI questions

## Tips

1. **Always use `--ai`** for commits and PRs - the AI generates better descriptions than humans usually do!

2. **Review before committing**:
   ```bash
   python -m github_assistant review
   python -m github_assistant commit --all --ai
   ```

3. **Quick daily commits**:
   ```bash
   python -m github_assistant commit --all --ai && python -m github_assistant push
   ```

4. **Create alias** (add to your `.bashrc` or `.zshrc`):
   ```bash
   alias gha='python -m github_assistant'

   # Then use:
   gha status
   gha commit --all --ai
   gha push
   ```

## Troubleshooting

### "Not a git repository"
Initialize git first:
```bash
git init
```

### "API key has no credits"
Add credits at https://console.anthropic.com/

### Commands not working
Make sure you installed:
```bash
pip install -e .
```

### Unicode errors on Windows
Already fixed in the code! Should work fine.

## Next Steps

1. Try committing something with `--ai`
2. Create a test repository
3. Set up aliases for faster usage
4. Explore all commands with `--help`

Enjoy your new AI-powered GitHub assistant! 🚀
