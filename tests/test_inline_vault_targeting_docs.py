from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class InlineVaultTargetingDocsTest(unittest.TestCase):
    def read(self, relpath: str) -> str:
        return (ROOT / relpath).read_text()

    def test_central_protocol_documents_inline_override_before_fallbacks(self) -> None:
        llm_wiki = self.read(".skills/wiki/beeweave-core/SKILL.md")
        agents = self.read("bootstrap/AGENTS.md")

        self.assertIn("0. **Inline vault override (`@name`)", llm_wiki)
        self.assertIn("0. **Inline vault override (`@name`)", agents)
        self.assertIn("resolve `~/.beeweave/config.<name>` directly", llm_wiki)
        self.assertIn("do **not** silently fall back to the default", agents)

    def test_skill_resolution_summaries_include_inline_override(self) -> None:
        stale = []
        for skill_file in sorted((ROOT / ".skills").glob("*/SKILL.md")):
            text = skill_file.read_text()
            if "follow the Config Resolution Protocol" not in text:
                continue
            if "walk up CWD for `.env`" in text and "inline `@name` override" not in text:
                stale.append(skill_file.relative_to(ROOT).as_posix())

        self.assertEqual(stale, [])

    def test_agent_bootstrap_files_mention_named_vault_routing(self) -> None:
        for relpath in [
            "bootstrap/AGENTS.md",
            "bootstrap/agent/rules/beeweave.md",
            "bootstrap/cursor/rules/beeweave.mdc",
            ".github/copilot-instructions.md",
            "bootstrap/kiro/steering/beeweave.md",
            "bootstrap/windsurf/rules/beeweave.md",
            "README.md",
            "SETUP.md",
        ]:
            with self.subTest(relpath=relpath):
                self.assertIn("@name", self.read(relpath))

    def test_claude_stop_hook_lives_under_bootstrap(self) -> None:
        hook = ROOT / "bootstrap/claude/hooks/beeweave-stop-capture.sh"
        template = ROOT / "bootstrap/claude/settings.stop-hook.json"

        self.assertTrue(hook.is_file())
        self.assertTrue(template.is_file())
        self.assertFalse((ROOT / ".claude/hooks/beeweave-stop-capture.sh").exists())
        self.assertFalse((ROOT / ".claude/settings.json").exists())
        self.assertIn("BEEWEAVE_CAPTURE=false", hook.read_text())
        self.assertIn("bootstrap/claude/hooks/beeweave-stop-capture.sh", template.read_text())

    def test_readme_says_all_supported_agents_inherit_named_vault_routing(self) -> None:
        readme = self.read("README.md")

        self.assertIn("All supported agents can use this syntax", readme)
        self.assertIn("Claude Code, Cursor, Windsurf, Codex, Gemini", readme)

    def test_core_skill_descriptions_include_named_vault_examples(self) -> None:
        examples = {
            ".skills/wiki/beeweave-query/SKILL.md": "beeweave-query @work",
            ".skills/wiki/beeweave-update/SKILL.md": "@work update wiki",
            ".skills/wiki/beeweave-capture/SKILL.md": "@research save this",
        }

        for relpath, expected in examples.items():
            with self.subTest(relpath=relpath):
                self.assertIn(expected, self.read(relpath))

    def test_wiki_query_does_not_prefer_default_over_inline_override(self) -> None:
        wiki_query = self.read(".skills/wiki/beeweave-query/SKILL.md")

        self.assertIn("For cross-project queries without `@name`", wiki_query)
        self.assertNotIn("Prefer `~/.beeweave/config` for cross-project queries", wiki_query)

    def test_repository_does_not_ship_runtime_workspace_instances(self) -> None:
        self.assertFalse((ROOT / "vault").exists())
        self.assertFalse((ROOT / "workbench").exists())

    def test_docs_describe_generated_workspace_layout(self) -> None:
        for relpath in ["README.md", "SETUP.md", "bootstrap/AGENTS.md"]:
            text = self.read(relpath)
            with self.subTest(relpath=relpath):
                self.assertIn("workbench/inbox", text)
                self.assertIn("captures/", text)
                self.assertIn("web/", text)
                self.assertIn("archived/", text)
                self.assertIn("rejected/", text)
                self.assertNotIn("BEEWEAVE_RAW_DIR", text)

    def test_docs_use_hermes_md_context_name(self) -> None:
        readme = self.read("README.md")
        setup = self.read("SETUP.md")

        self.assertIn("HERMES.md", readme)
        self.assertIn("HERMES.md", setup)
        self.assertNotIn(".hermes.md", readme)
        self.assertNotIn(".hermes.md", setup)

    def test_digest_saves_to_workbench_drafts(self) -> None:
        digest = self.read(".skills/wiki/beeweave-digest/SKILL.md")

        self.assertIn("workbench/articles/drafts/digest-YYYY-MM-DD.md", digest)
        self.assertNotIn("$BEEWEAVE_VAULT_PATH/journal", digest)


if __name__ == "__main__":
    unittest.main()
