# Spec-Check

**Did the AI actually build what you asked for?**

One command. Checks your spec against the built code. Shows what's done, what's missing.

```bash
$ spec-check --spec "login, signup, dashboard, tasks, dark mode" --dir ./my-app
```

> Built by NOUMENON — AI agents that debate, evolve, and build.

![PyPI](https://img.shields.io/pypi/v/spec-check)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)

## Why This Exists

Every developer using Copilot, Cursor, or Claude has this problem:
"I asked for 6 pages and it built 3." spec-check catches what's missing.

## Install

```bash
pip install spec-check

# Optional: LLM-enhanced matching
pip install spec-check[llm]
```

## Usage

```bash
# Check from text spec
spec-check --spec "login page, signup page, dashboard, task list, dark mode" --dir ./my-app

# Check from spec file
spec-check --spec-file spec.md --dir ./my-app

# Auto-detect from README
spec-check --dir ./my-app --auto

# JSON output for CI/CD
spec-check --spec "..." --dir . --format json

# Strict mode (exit 1 if < 100%)
spec-check --spec "..." --dir . --strict
```

## Output

```
  SPEC-CHECK v1.0.0

  Scanning: ./my-app (47 files)
  Spec features: 7

  Feature              Status    Evidence
  Login page           FOUND     src/pages/login.tsx
  Signup page          FOUND     src/pages/signup.tsx
  Dashboard            FOUND     src/pages/dashboard.tsx
  Task list            FOUND     src/components/Tasks.tsx
  Task creation form   MISSING
  Dark mode            PARTIAL   tailwind.config has dark
  Mobile responsive    FOUND     Breakpoints in CSS

  Completeness: ██████████████░░░░░░ 71% (5/7 features built)

  Missing: task creation form
  Partial: dark mode (config exists, not applied to all components)
```

## How It Works

1. Parse your spec into individual features
2. Generate search keywords for each feature (with synonyms)
3. Search all project files for those keywords (filenames + contents)
4. Score each feature: FOUND (2+ matches), PARTIAL (1 match), MISSING (0)
5. Calculate completeness percentage

## CI/CD Integration

```yaml
name: Spec Check
on: [push, pull_request]
jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install spec-check
      - run: spec-check --spec-file SPEC.md --dir . --strict
```

## Contributing

Ideas for better feature matching? Open a PR.

## License

MIT

---

Part of the NOUMENON ecosystem.
NOUMENON doesn't just check specs — it builds 100% of them.
16 AI agents debate, then build, then verify. Every time.
---
Built by [Noumenon](https://github.com/Noumenon-ai)
