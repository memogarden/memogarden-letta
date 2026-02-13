# MemoGarden Utils

Shared utilities for MemoGarden project.

## Test Runners

Each MemoGarden project has a `run_tests.sh` script that provides a standardized entrypoint for running tests.

### Usage

```bash
# Default (textbox format)
./memogarden-api/run_tests.sh

# Markdown format (for agents/logs)
./memogarden-api/run_tests.sh --format=markdown

# Plaintext format
./memogarden-api/run_tests.sh --format=plaintext

# Show help
./memogarden-api/run_tests.sh -h

# Pass pytest args
./memogarden-api/run_tests.sh --format=md -xvs tests/test_api.py
```

### Format Options

| Format | Description | Use Case |
|--------|-------------|----------|
| `textbox` (default) | Bordered box with Unicode characters | Human terminal output |
| `plaintext` | Plain text without formatting | CI/CD logs, basic terminals |
| `markdown`, `md` | Markdown formatted with H3 headings | Agent consumption, documentation |

### Environment Variables

- `TEST_FORMAT` - Override default format (textbox/plaintext/markdown)
- `WIDTH` - Override default box width (default: 60)

### For Agents

When running tests and parsing output, prefer `--format=markdown` for easier parsing:

```bash
# Get summary only (grep-able)
./memogarden-api/run_tests.sh --format=md --tb=no -q 2>&1 | grep -A 5 "Test Summary"
```

Output:
```markdown
### Test Summary

**Status:** PASSED
**Tests:** 251 passed
**Duration:** 96.55s
**Test Run ID:** 20260213-081842
```

## Format Scripts

Direct access to formatting utilities (used by `run_tests.sh`):

```bash
# Textbox format
/workspaces/memogarden/utils/format/textbox.py --title "Title" --body "Line 1" "Line 2"

# Plaintext format
/workspaces/memogarden/utils/format/plaintext.py --title "Title" --body "Line 1" "Line 2"

# Markdown format
/workspaces/memogarden/utils/format/markdown.py --title "Title" --body "Line 1" "Line 2"
```
