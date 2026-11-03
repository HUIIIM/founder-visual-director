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
# claude-code-action v1.0.266, tag-mode tool additions reviewed in #36 round 5 and #40.
REVIEWED_ACTION_SHA = "d535f5172dec02b204866b393d6b20b9b2aaf98d"


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

    def test_gh_limited_to_pr_and_issue_reads_and_comments(self):  # dispatch step (first list)
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

    def test_read_scoped_and_secret_paths_denied(self):
        # #40: tag mode adds a bare Read, so the denies carry the protection on their own.
        self.assertNotIn("Read", self.allowed)
        for rule in ("Read(//proc/**)", "Read(~/.claude/**)", "Bash(gh * --body-file*)", "Bash(gh * -F*)"):
            self.assertIn(rule, self.denied)

    def test_git_commit_cannot_read_a_file_or_run_a_command(self):
        # #47 round 7: commit message from a file (-F/--file/-t) or from $(…)/backticks, then
        # the allowed push, is the same read-a-secret-and-publish chain as gh --body-file.
        for rule in (
            "Bash(git commit -F*)", "Bash(git commit * -F*)",
            "Bash(git commit --file*)", "Bash(git commit * --file*)",
            "Bash(git commit -t*)", "Bash(git commit * -t*)",
            "Bash(git commit --template*)", "Bash(git commit * --template*)",
            "Bash(*$(*)", "Bash(*`*)",
        ):
            self.assertIn(rule, self.denied)

    def test_git_dir_read_denied_and_checkout_keeps_no_token(self):
        # #50: the action puts its token in .git/config (origin URL); tag mode's bare Read
        # would otherwise reach it.
        for rule in ("Read(.git/**)", "Read(**/.git/**)"):
            self.assertIn(rule, self.denied)
        with open(WORKFLOW, encoding="utf-8") as f:
            self.assertRegex(f.read(), r"persist-credentials:\s*false")

    def test_git_cannot_read_a_file_through_pathspec_from_file(self):
        # #51 round 1: git checkout/commit --pathspec-from-file=.git/config echoed the file
        # (origin URL with the action's token) line by line in the error output.
        for cmd in ("checkout", "commit", "add", "rm", "switch"):
            for opt in ("--pathspec-from-file", "--pathspec-file-nul"):
                self.assertIn(f"Bash(git {cmd} {opt}*)", self.denied)
                self.assertIn(f"Bash(git {cmd} * {opt}*)", self.denied)

    def test_action_keeps_its_token_out_of_git_config(self):
        # #51 round 2: a non-empty allowed_non_write_users switches claude-code-action to a
        # credential helper (no token in the origin URL). The value must be a login GitHub
        # cannot issue, and the workflow must not pass github_token (which would arm the
        # action's permission bypass for listed users).
        with open(WORKFLOW, encoding="utf-8") as f:
            text = f.read()
        m = re.search(r'allowed_non_write_users:\s*"([^"]*)"', text)
        self.assertIsNotNone(m, "allowed_non_write_users is not set")
        for login in m.group(1).split(","):
            login = login.strip()
            self.assertTrue(login, "empty entry")
            self.assertNotEqual(login, "*")
            # GitHub logins: alphanumerics and single hyphens, no leading/trailing hyphen.
            self.assertIsNone(re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}", login), login)
        self.assertNotRegex(text, r"^\s*github_token:", "github_token would arm the non-write bypass")

    def test_fragment_denies_for_abbreviated_options_and_environ(self):
        # #51 round 3: git takes unique prefixes (--pathspec-fr), and GH_TOKEN is in the
        # subprocess environment (/proc/self/environ); deny by fragment as well.
        for rule in ("Bash(*pathspec*)", "Bash(*environ*)", "Bash(*/proc/*)"):
            self.assertIn(rule, self.denied)

    def test_event_runs_have_no_git_subcommand_that_reads_a_file(self):
        # #51 round 3: git option abbreviations and shell quoting defeat any deny over the
        # command text, and GH_TOKEN is in the subprocess env. Comment/issue runs therefore
        # get no git subcommand that takes a file option and commit through the API.
        with open(WORKFLOW, encoding="utf-8") as f:
            text = f.read()
        # Stdlib only (CI has no PyYAML): split the job into its claude-code-action steps.
        blocks = re.split(r"\n      - name: ", text)
        runs = [b for b in blocks if "anthropics/claude-code-action@" in b]
        self.assertEqual(len(runs), 2, "expected one dispatch step and one event step")
        conds = [re.search(r"^\s+if: (.+)$", b, re.MULTILINE).group(1).strip() for b in runs]
        self.assertEqual(
            sorted(conds),
            sorted(["github.event_name == 'workflow_dispatch'", "github.event_name != 'workflow_dispatch'"]),
        )
        event = runs[conds.index("github.event_name != 'workflow_dispatch'")]
        self.assertRegex(event, r"\n\s+use_commit_signing: true\b")
        allowed = re.search(r'--allowedTools "([^"]*)"', event).group(1).split(",")
        for rule in allowed:
            self.assertNotRegex(rule, r"^Bash\(git (checkout|switch|add|commit|rm|push|restore|reset|stash)\b", rule)
            # #51 round 4: gh write commands take --body-file/-F, which quote-splitting gets past.
            self.assertNotRegex(rule, r"^Bash\(gh (pr|issue) (comment|create|edit|review)\b", rule)
        for b in runs:
            self.assertRegex(b, r'allowed_non_write_users: "-no-such-user-"')

    def test_turn_cap(self):
        # #44 item 2 (SOTA ARCH-4): the agent loop has a hard step bound.
        with open(WORKFLOW, encoding="utf-8") as f:
            m = re.search(r"--max-turns (\d+)", f.read())
        self.assertIsNotNone(m, "claude_args has no --max-turns")
        self.assertLessEqual(int(m.group(1)), 60)

    def test_action_pin_reviewed(self):
        # #40 item 2: claude-code-action adds its own tools in tag mode (v1.0.266: Read, LS,
        # Glob, Grep, git add/commit/rm, its git-push.sh, MCP tools). This test only sees
        # claude_args, so a new action SHA must fail here until someone re-reads
        # src/modes/tag/index.ts and confirms the added tools reopen nothing, then updates it.
        with open(WORKFLOW, encoding="utf-8") as f:
            pins = re.findall(r"anthropics/claude-code-action@([0-9a-f]{40})", f.read())
        self.assertTrue(pins)
        self.assertEqual(set(pins), {REVIEWED_ACTION_SHA})


if __name__ == "__main__":
    unittest.main()
