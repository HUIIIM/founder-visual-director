"""Guard the Claude workflow's tool allowlist (#32 P1-1, #36 SEC-A3).

A `Bash(cmd:*)` rule is a prefix match, so it accepts any option written after the prefix.
These tests fail if the allowlist regains a rule that hands the agent a shell or an
arbitrary file write through such an option.
"""
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKFLOW = os.path.join(ROOT, ".github", "workflows", "claude.yml")


def _tool_list(flag):
    with open(WORKFLOW, encoding="utf-8") as f:
        text = f.read()
    m = re.search(flag + r' "([^"]*)"', text)
    return [t.strip() for t in m.group(1).split(",")] if m else None


class ClaudeWorkflowAllowlist(unittest.TestCase):
    def setUp(self):
        self.allowed = _tool_list("--allowedTools")
        self.denied = _tool_list("--disallowedTools")
        self.assertIsNotNone(self.allowed, "claude.yml has no --allowedTools list")

    def test_no_bare_git_or_gh(self):
        for bare in ("Bash(git:*)", "Bash(gh:*)", "Bash(git)", "Bash(gh)", "Bash", "Bash(*)"):
            self.assertNotIn(bare, self.allowed)

    def test_no_fetch_or_pull(self):
        # --upload-pack runs a program; the checkout step already fetched.
        for rule in self.allowed:
            self.assertNotRegex(rule, r"^Bash\(git (fetch|pull|clone|remote|config|submodule)\b", rule)

    def test_option_dangerous_commands_are_exact(self):
        # push --receive-pack/--exec, diff/log/show --output/--ext-diff: no prefix rules.
        for rule in self.allowed:
            if re.match(r"^Bash\(git (push|diff|log|show)\b", rule):
                self.assertFalse(rule.endswith(":*)") or "*" in rule, rule)
                self.assertNotRegex(rule, r"--(receive-pack|exec|output|ext-diff)|\s-c\s", rule)

    def test_gh_limited_to_pr_and_issue_reads_and_comments(self):
        for rule in self.allowed:
            if rule.startswith("Bash(gh"):
                self.assertRegex(rule, r"^Bash\(gh (pr|issue) (create|view|list|comment):\*\)$", rule)

    def test_git_dir_write_denied(self):
        self.assertIsNotNone(self.denied, "claude.yml has no --disallowedTools list")
        for rule in ("Edit(.git/**)", "Write(.git/**)"):
            self.assertIn(rule, self.denied)

    def test_file_tools_scoped_to_workspace(self):
        # #36 round 4: git reads ~/.gitconfig and ~/.config/git/config too (core.fsmonitor,
        # core.pager, alias.*), so an unscoped Write/Edit could plant a program outside .git/.
        for tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
            self.assertNotIn(tool, self.allowed, f"bare {tool} is unscoped")
        for rule in self.allowed:
            if re.match(r"^(Write|Edit|MultiEdit|NotebookEdit)\(", rule):
                self.assertRegex(rule, r"^\w+\(\./\*\*\)$", rule)
        for rule in ("Edit(~/.gitconfig)", "Write(~/.gitconfig)", "Edit(~/.config/**)", "Write(~/.config/**)"):
            self.assertIn(rule, self.denied)


if __name__ == "__main__":
    unittest.main()
