# 🤝 Contributing to nbpull

Thanks for your interest in contributing! This guide will help you
get started.

## 🚀 Getting Started

### Prerequisites

- **Python 3.13+**
- **[uv](https://docs.astral.sh/uv/)** — fast Python package manager
- A **NetBox** instance with a read-only API token (for integration
  tests only)

### Setup

```bash
# 1. Fork & clone the repo
git clone https://github.com/<your-username>/nbpull.git
cd nbpull

# 2. Install all dependencies (including dev)
make install

# 3. Copy the example env file
cp .env.example .env
# Fill in your NetBox URL and token
```

### Running Checks

```bash
make all        # format → lint → typecheck → test
make test       # unit tests only (no network)
make lint       # ruff linter
make format     # auto-format with ruff
make typecheck  # mypy strict mode
```

## 🔀 Workflow

1. **Create an issue** describing the bug or feature
2. **Fork the repo** and create a branch:
   `git checkout -b feat/my-feature` or `git checkout -b fix/my-bug`
3. **Make your changes** — keep commits focused and atomic
4. **Run `make all`** to ensure everything passes
5. **Open a Pull Request** against `main`

### Branch Naming

| Prefix    | Purpose               |
|-----------|-----------------------|
| `feat/`   | New feature           |
| `fix/`    | Bug fix               |
| `docs/`   | Documentation only    |
| `refactor/` | Code refactoring    |
| `test/`   | Adding/updating tests |
| `chore/`  | Maintenance / tooling |

## 🧪 Testing

- **Unit tests** (`make test`) run without network access using mocked
  HTTP responses via [respx](https://github.com/lundberg/respx).
- **Integration tests** (`make test-integration`) hit a real NetBox API
  and require `NETBOX_URL` + `NETBOX_TOKEN` in your environment.
- Write tests for all new functionality. Aim for the same style as
  existing tests in `tests/`.

## 📐 Code Style

- **Formatter / Linter:** [Ruff](https://docs.astral.sh/ruff/)
  (line length 88)
- **Type checking:** [mypy](https://mypy-lang.org/) in strict mode
- **Import order:** isort via Ruff
- **Strings:** f-strings exclusively for interpolation
- **Logging:** use `logging` stdlib — no `print()` statements
- **Async I/O:** `async`/`await` for all HTTP operations
- **Models:** [Pydantic v2](https://docs.pydantic.dev/) for data
  validation

## 🔒 Safety Invariant

**This tool is read-only.** The `NetBoxClient` only exposes HTTP GET
methods. Never add POST/PUT/PATCH/DELETE capabilities. Every PR is
reviewed with this invariant in mind.

## 📝 Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add --role filter to prefixes command
fix: handle empty pagination response from NetBox
docs: expand CLI examples in README
test: add VRF model edge cases
```

## 💬 Questions?

Open a [Discussion](https://github.com/Champion2005/nbpull/discussions)
or file an issue. We're happy to help!
