set shell := ['uv', 'run', '--frozen', 'bash', '-euxo', 'pipefail', '-c']
set unstable
set positional-arguments

project := "searchpath"
package := "searchpath"
module := "searchpath"
pnpm := "pnpm exec"
test_pypi_index := "https://test.pypi.org/legacy/"

# List available recipes
default:
  @just --list

# Run benchmarks
benchmark *args:
  pytest -m benchmark --codspeed "$@"

# Build distribution packages
build: clean-python
  uv build --no-sources

# Build the latest documentation
build-docs: clean-docs
  MKDOCS_ENV=latest uv run --group docs mkdocs build --strict

# Build the documentation for PR preview
[script]
build-docs-pr number: clean-docs
  rm -f mkdocs.pr.yml
  cat << EOF >> mkdocs.pr.yml
  INHERIT: ./mkdocs.yml
  site_name: typing-graph Documentation (PR-{{number}})
  site_url: https://{{number}}-typing-graph-docs-pr.tbhb.workers.dev/
  EOF
  uv run --group docs mkdocs build --strict
  echo "User-Agent: *\nDisallow: /" > site/robots.txt

# Build distribution packages with SBOM
build-release: build
  #!/usr/bin/env bash
  uv run --frozen --isolated --group release cyclonedx-py environment --of json -o dist/sbom.cdx.json

# Clean build artifacts
clean: clean-python clean-docs

# Clean documentation build artifacts
clean-docs:
  rm -rf site

# Clean Python build artifacts
clean-python:
  #!/usr/bin/env bash
  rm -rf dist
  find . -type d -name __pycache__ -exec rm -rf {} +
  find . -type d -name .pytest_cache -exec rm -rf {} +
  find . -type d -name .ruff_cache -exec rm -rf {} +

# Deploy latest documentation
deploy-docs: build-docs
  pnpm exec wrangler deploy --env ""

# Deploy documentation preview
deploy-docs-pr number: (build-docs-pr number)
  pnpm exec wrangler versions upload --env preview --preview-alias pr-{{number}}

# Develop the documentation site locally
dev-docs:
  uv run --isolated --group docs mkdocs serve --livereload --dev-addr 127.0.0.1:8000

# Format code
format:
  codespell -w
  ruff format .
  {{pnpm}} biome format --write .

# Fix code issues
fix:
  ruff format .
  ruff check --fix .
  biome format --write .
  biome check --write .

# Fix code issues including unsafe fixes
fix-unsafe:
  ruff format .
  ruff check --fix --unsafe-fixes .
  biome check --write --unsafe

# Run all linters
lint: lint-python lint-docs lint-config lint-spelling

# Lint configuration files
lint-config: lint-json lint-yaml

# Lint documentation
lint-docs: lint-markdown lint-prose

# Lint JSON files
lint-json:
  {{pnpm}} biome check "**/*.json", "**/*.jsonc"

# Lint Markdown files
lint-markdown:
  {{pnpm}} markdownlint-cli2 "**/*.md"

# Lint Python code
lint-python: lint-python-imports lint-python-style lint-python-types lint-python-complexity

# Lint Python complexity
lint-python-complexity *args:
  complexipy "$@"

# Lint Python imports
lint-python-imports:
  lint-imports
  ruff check --select I .

# Lint Python style
lint-python-style:
  ruff check .
  ruff format --check .

# Check types
lint-python-types *args:
  basedpyright "$@"

# Lint prose in Markdown files
lint-prose:
  vale docs/**/*.md CODE_OF_CONDUCT.md CONTRIBUTING.md README.md SECURITY.md

# Check spelling
lint-spelling:
  codespell

# Lint YAML files
lint-yaml:
  yamllint --strict .

# Install all dependencies (Python + Node.js)
install: install-node install-python

# Install only Node.js dependencies
install-node:
  #!/usr/bin/env bash
  pnpm install --frozen-lockfile

# Install only Python dependencies
install-python:
  #!/usr/bin/env bash
  uv sync --frozen

# Run pre-commit hooks on changed files
prek:
  prek

# Run pre-commit hooks on all files
prek-all:
  prek run --all-files

# Install pre-commit hooks
prek-install:
  prek install

# Publish to TestPyPI (requires OIDC token in CI or UV_PUBLISH_TOKEN)
publish-testpypi:
  uv publish --publish-url {{test_pypi_index}}

# Publish to PyPI (requires OIDC token in CI or UV_PUBLISH_TOKEN)
publish-pypi:
  uv publish

# Run command
run *args:
  "$@"

# Run Node.js
run-node *args:
  {{pnpm}} "$@"

# Run Python
run-python *args:
  python "$@"

# Generate SBOM for current environment
sbom output="sbom.cdx.json":
  uv run --isolated --group release cyclonedx-py environment --of json -o {{output}}

# Set development version (appends .devN)
[script]
set-dev-version number:
  base_version="$(uv version --package {{package}} | awk '{print $2}')"
  version="${base_version}.dev{{number}}"
  uv version --package {{package}} "${version}"

# Run tests (excludes benchmarks and slow tests by default)
test *args:
  pytest "$@"

# Run all tests
test-all *args:
  pytest -m "" "$@"

# Run tests with coverage
test-coverage *args:
  pytest -m "not benchmark" --cov={{module}} --cov-branch --cov-report=term-missing:skip-covered --cov-report=xml --cov-report=json "$@"

# RUn documentation tests
test-examples *args:
  pytest -m example "$@"

# Run only failed tests from last run
test-failed *args: (test args "--lf")

# Run slow tests
test-slow *args:
  pytest -m "slow" "$@"

# Update documentation examples (refresh output blocks)
update-examples *args:
  pytest -m example --update-examples "$@"

# Sync Vale styles and dictionaries
vale-sync:
  vale sync

# Show the current version
[script]
version:
  uv version --package {{package}} | awk '{print $2}'

# Verify a PyPi release (with retries for index propagation)
[script]
verify-pypi version:
  tmp_dir="/tmp/{{package}}-verify-pypi/venv"
  rm -fr "${tmp_dir}"
  mkdir -p "${tmp_dir}"
  uv venv --directory "${tmp_dir}" --python 3.10 --no-project --no-cache
  for i in 1 2 3 4 5; do
    echo "Attempt $i: Installing {{package}}=={{version}} from PyPI..."
    if uv pip install --directory "${tmp_dir}" --no-cache --strict "{{package}}=={{version}}"; then
      break
    fi
    if [ "$i" -lt 5 ]; then
      echo "Package not yet available, waiting 10 seconds..."
      sleep 10
    else
      echo "Failed to install after 5 attempts"
      exit 1
    fi
  done
  uv run --directory "${tmp_dir}" --no-project python -c "import {{module}}; print({{module}}.__version__)"

# Verify a TestPyPi release (with retries for index propagation)
[script]
verify-testpypi version:
  tmp_dir="/tmp/{{package}}-verify-testpypi/venv"
  rm -fr "${tmp_dir}"
  mkdir -p "${tmp_dir}"
  uv venv --directory "${tmp_dir}" --python 3.10 --no-project --no-cache --default-index "https://test.pypi.org/simple/" --extra-index-url "https://pypi.org/simple/"
  for i in 1 2 3 4 5; do
    echo "Attempt $i: Installing {{package}}=={{version}} from TestPyPI..."
    if uv pip install --directory "${tmp_dir}" --no-cache --strict --index-strategy unsafe-best-match --default-index "https://test.pypi.org/simple/" --extra-index-url "https://pypi.org/simple/" "{{package}}=={{version}}"; then
      break
    fi
    if [ "$i" -lt 5 ]; then
      echo "Package not yet available, waiting 10 seconds..."
      sleep 10
    else
      echo "Failed to install after 5 attempts"
      exit 1
    fi
  done
  uv run --directory "${tmp_dir}" --no-project python -c "import {{module}}; print({{module}}.__version__)"
