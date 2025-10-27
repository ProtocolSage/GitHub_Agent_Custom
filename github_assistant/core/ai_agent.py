"""AI agent for intelligent GitHub and Git operations using Claude."""

from typing import Optional, Dict, List, Any
from anthropic import Anthropic
import os
import logging

logger = logging.getLogger(__name__)


class AIAgent:
    """Claude-powered AI agent for code analysis and automation."""

    # Maximum characters for diff to prevent huge API costs
    MAX_DIFF_SIZE = 50000
    MAX_PR_DIFF_SIZE = 100000

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Initialize AI agent with Anthropic API key."""
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError("Anthropic API key required. Set ANTHROPIC_API_KEY env variable.")

        self.client = Anthropic(api_key=self.api_key)
        self.model = model or os.getenv('ANTHROPIC_MODEL', 'claude-3-5-sonnet-20241022')
        logger.debug(f"AIAgent initialized with model: {self.model}")

    def _truncate_diff(self, diff: str, max_size: int) -> tuple[str, bool]:
        """Truncate diff if too large, return (diff, was_truncated)."""
        if len(diff) <= max_size:
            return diff, False

        logger.warning(f"Diff size {len(diff)} exceeds limit {max_size}, truncating")
        truncated = diff[:max_size]
        truncated += "\n\n... (diff truncated to prevent excessive API costs)"
        return truncated, True

    def generate_commit_message(self, diff: str, context: Optional[str] = None) -> str:
        """Generate a commit message from git diff."""
        diff, was_truncated = self._truncate_diff(diff, self.MAX_DIFF_SIZE)

        prompt = f"""Analyze this git diff and generate a concise, professional commit message.

Follow conventional commit format: <type>: <description>

Types: feat, fix, docs, style, refactor, test, chore

Rules:
- First line: short summary (50 chars max)
- Optional body: detailed explanation if needed
- Focus on WHAT changed and WHY
- Be specific and actionable

{f"Context: {context}" if context else ""}
{"Note: Diff was truncated due to size." if was_truncated else ""}

Diff:
```
{diff}
```

Generate the commit message:"""

        logger.debug(f"Generating commit message for diff of length {len(diff)}")
        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()

    def review_code_changes(self, diff: str, context: Optional[str] = None) -> Dict[str, Any]:
        """Review code changes and provide feedback."""
        diff, was_truncated = self._truncate_diff(diff, self.MAX_DIFF_SIZE)

        prompt = f"""Review this code diff and provide comprehensive feedback.

Analyze:
1. Code quality and best practices
2. Potential bugs or issues
3. Performance considerations
4. Security concerns
5. Suggestions for improvement

{f"Context: {context}" if context else ""}
{"Note: Diff was truncated due to size." if was_truncated else ""}

Diff:
```
{diff}
```

Provide your review in this JSON format:
{{
    "summary": "Brief overview",
    "issues": ["List of issues found"],
    "suggestions": ["List of suggestions"],
    "security_concerns": ["Security issues if any"],
    "rating": "score from 1-10",
    "recommendation": "approve/request_changes/comment"
}}"""

        logger.debug(f"Reviewing code changes, diff length: {len(diff)}")
        response = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse the response
        import json
        import re
        try:
            review_text = response.content[0].text
            # Try to extract JSON from code block first
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', review_text, re.DOTALL)
            if json_match:
                review_data = json.loads(json_match.group(1))
                return review_data

            # Fallback: Extract JSON from response
            start = review_text.find('{')
            end = review_text.rfind('}') + 1
            if start >= 0 and end > start:
                review_data = json.loads(review_text[start:end])
                return review_data
            else:
                # Fallback if JSON not found
                logger.warning("No JSON found in AI response, using raw text")
                return {
                    "summary": review_text,
                    "issues": [],
                    "suggestions": [],
                    "security_concerns": [],
                    "rating": "N/A",
                    "recommendation": "comment"
                }
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return {
                "summary": response.content[0].text,
                "issues": [],
                "suggestions": [],
                "security_concerns": [],
                "rating": "N/A",
                "recommendation": "comment",
                "error": str(e)
            }

    def review_pull_request(
        self,
        pr_title: str,
        pr_description: str,
        diff: str,
        files_changed: int
    ) -> Dict[str, Any]:
        """Review a complete pull request."""
        diff, was_truncated = self._truncate_diff(diff, self.MAX_PR_DIFF_SIZE)

        prompt = f"""Review this pull request comprehensively.

PR Title: {pr_title}
Description: {pr_description}
Files Changed: {files_changed}
{"Note: Diff was truncated due to size." if was_truncated else ""}

Diff:
```
{diff}
```

Provide detailed review covering:
1. Overall assessment
2. Code quality
3. Test coverage
4. Documentation
5. Breaking changes
6. Specific issues or concerns
7. Final recommendation

Format as JSON:
{{
    "overall_assessment": "summary",
    "code_quality": "assessment",
    "test_coverage": "assessment",
    "documentation": "assessment",
    "breaking_changes": ["list if any"],
    "issues": ["specific issues"],
    "suggestions": ["improvements"],
    "recommendation": "approve/request_changes/needs_discussion",
    "review_comment": "detailed comment for PR"
}}"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )

        import json
        try:
            review_text = response.content[0].text
            start = review_text.find('{')
            end = review_text.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(review_text[start:end])
            else:
                return {"review_comment": review_text, "recommendation": "comment"}
        except Exception as e:
            return {
                "review_comment": response.content[0].text,
                "recommendation": "comment",
                "error": str(e)
            }

    def analyze_repository(self, repo_info: Dict[str, any]) -> str:
        """Analyze repository and provide insights."""
        prompt = f"""Analyze this GitHub repository and provide insights.

Repository Information:
{repo_info}

Provide analysis on:
1. Repository health
2. Activity level
3. Community engagement
4. Areas for improvement
5. Recommendations

Keep it concise and actionable."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()

    def suggest_issue_labels(self, issue_title: str, issue_body: str) -> List[str]:
        """Suggest appropriate labels for an issue."""
        prompt = f"""Analyze this GitHub issue and suggest appropriate labels.

Title: {issue_title}
Body: {issue_body}

Common label categories:
- Type: bug, feature, enhancement, documentation, question
- Priority: critical, high, medium, low
- Status: needs-triage, in-progress, blocked
- Area: backend, frontend, api, database, ui/ux

Respond with ONLY a comma-separated list of suggested labels (max 5).
Example: bug, high-priority, backend"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}]
        )

        labels_text = response.content[0].text.strip()
        return [label.strip() for label in labels_text.split(',')]

    def generate_pr_description(
        self,
        diff: str,
        branch_name: str,
        commits: List[str]
    ) -> str:
        """Generate a comprehensive PR description."""
        diff, was_truncated = self._truncate_diff(diff, self.MAX_PR_DIFF_SIZE)

        prompt = f"""Generate a comprehensive pull request description.

Branch: {branch_name}
Commits:
{chr(10).join(f'- {commit}' for commit in commits)}
{"Note: Diff was truncated due to size." if was_truncated else ""}

Changes:
```
{diff}
```

Format the description as:
## Summary
[Brief overview]

## Changes
- [Key change 1]
- [Key change 2]

## Testing
[How this was tested]

## Checklist
- [ ] Code follows project guidelines
- [ ] Tests added/updated
- [ ] Documentation updated
"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()

    def explain_diff(self, diff: str) -> str:
        """Explain what a diff does in plain English."""
        diff, was_truncated = self._truncate_diff(diff, self.MAX_DIFF_SIZE)

        prompt = f"""Explain this git diff in plain English. What does it do?
{"Note: Diff was truncated due to size." if was_truncated else ""}

Diff:
```
{diff}
```

Provide a clear, concise explanation suitable for a non-technical audience."""

        logger.debug(f"Explaining diff of length {len(diff)}")
        response = self.client.messages.create(
            model=self.model,
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()

    def suggest_branch_name(self, description: str) -> str:
        """Suggest a branch name based on description."""
        prompt = f"""Suggest a git branch name for this work:

{description}

Follow conventions:
- Use hyphens to separate words
- Start with type: feature/, bugfix/, hotfix/, chore/
- Keep it short but descriptive
- Use lowercase

Respond with ONLY the branch name, nothing else.
Example: feature/add-user-authentication"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()

    def triage_issue(self, issue_title: str, issue_body: str) -> Dict[str, Any]:
        """Triage an issue and suggest priority/assignment."""
        prompt = f"""Triage this GitHub issue and provide recommendations.

Title: {issue_title}
Body: {issue_body}

Analyze and provide:
{{
    "priority": "critical/high/medium/low",
    "category": "bug/feature/documentation/question",
    "complexity": "simple/moderate/complex",
    "suggested_labels": ["label1", "label2"],
    "requires_immediate_attention": true/false,
    "summary": "brief analysis"
}}"""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        import json
        try:
            text = response.content[0].text
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(text[start:end])
            else:
                return {"summary": text}
        except Exception as e:
            return {"summary": response.content[0].text, "error": str(e)}

    def ask_question(self, question: str, context: Optional[str] = None) -> str:
        """Ask the AI agent a general question about Git/GitHub."""
        prompt = f"""{question}

{f"Context: {context}" if context else ""}

Provide a clear, helpful answer."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()
