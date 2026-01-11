from typing import TYPE_CHECKING

import pytest

from searchpath import GitignoreMatcher, GlobMatcher, RegexMatcher

if TYPE_CHECKING:
    from pytest_codspeed.plugin import BenchmarkFixture


SAMPLE_PATHS = [
    "src/main.py",
    "src/utils/helpers.py",
    "src/utils/validators.py",
    "tests/test_main.py",
    "tests/unit/test_utils.py",
    "docs/index.md",
    "docs/api/reference.md",
    "README.md",
    "setup.py",
    "pyproject.toml",
]

MANY_PATHS = [f"src/module{i}/file{j}.py" for i in range(20) for j in range(50)]


class TestBenchGlobMatcherSinglePattern:
    def test_simple_extension_pattern(self, benchmark: "BenchmarkFixture") -> None:
        matcher = GlobMatcher()

        def run() -> list[bool]:
            return [matcher.matches(p, include=["*.py"]) for p in SAMPLE_PATHS]

        result = benchmark(run)
        assert any(result)

    def test_recursive_glob_pattern(self, benchmark: "BenchmarkFixture") -> None:
        matcher = GlobMatcher()

        def run() -> list[bool]:
            return [matcher.matches(p, include=["**/*.py"]) for p in SAMPLE_PATHS]

        result = benchmark(run)
        assert any(result)

    def test_directory_prefix_pattern(self, benchmark: "BenchmarkFixture") -> None:
        matcher = GlobMatcher()

        def run() -> list[bool]:
            return [matcher.matches(p, include=["src/**"]) for p in SAMPLE_PATHS]

        result = benchmark(run)
        assert any(result)

    def test_complex_glob_pattern(self, benchmark: "BenchmarkFixture") -> None:
        matcher = GlobMatcher()

        def run() -> list[bool]:
            return [matcher.matches(p, include=["**/test_*.py"]) for p in SAMPLE_PATHS]

        result = benchmark(run)
        assert any(result)


class TestBenchGlobMatcherMultiplePatterns:
    def test_multiple_include_patterns(self, benchmark: "BenchmarkFixture") -> None:
        matcher = GlobMatcher()
        patterns = ["**/*.py", "**/*.md", "**/*.toml"]

        def run() -> list[bool]:
            return [matcher.matches(p, include=patterns) for p in SAMPLE_PATHS]

        result = benchmark(run)
        assert any(result)

    def test_include_and_exclude_patterns(self, benchmark: "BenchmarkFixture") -> None:
        matcher = GlobMatcher()

        def run() -> list[bool]:
            return [
                matcher.matches(
                    p,
                    include=["**/*.py"],
                    exclude=["**/test_*"],
                )
                for p in SAMPLE_PATHS
            ]

        result = benchmark(run)
        assert any(result)

    def test_many_exclude_patterns(self, benchmark: "BenchmarkFixture") -> None:
        matcher = GlobMatcher()
        excludes = [
            "__pycache__/**",
            "*.pyc",
            ".git/**",
            "node_modules/**",
            "dist/**",
            "build/**",
            ".venv/**",
            "*.egg-info/**",
            ".mypy_cache/**",
            ".pytest_cache/**",
        ]

        def run() -> list[bool]:
            return [
                matcher.matches(p, include=["**/*.py"], exclude=excludes)
                for p in SAMPLE_PATHS
            ]

        result = benchmark(run)
        assert any(result)


class TestBenchGlobMatcherScaling:
    def test_many_paths_single_pattern(self, benchmark: "BenchmarkFixture") -> None:
        matcher = GlobMatcher()

        def run() -> list[bool]:
            return [matcher.matches(p, include=["**/*.py"]) for p in MANY_PATHS]

        result = benchmark(run)
        assert all(result)

    def test_many_paths_multiple_patterns(self, benchmark: "BenchmarkFixture") -> None:
        matcher = GlobMatcher()
        patterns = ["**/module*/file*.py", "src/**/*.py"]

        def run() -> list[bool]:
            return [matcher.matches(p, include=patterns) for p in MANY_PATHS]

        result = benchmark(run)
        assert any(result)


class TestBenchGlobMatcherCaching:
    def test_repeated_pattern_same_matcher(self, benchmark: "BenchmarkFixture") -> None:
        matcher = GlobMatcher()
        pattern = ["**/module[0-9]/file[0-9].py"]

        _ = matcher.matches(MANY_PATHS[0], include=pattern)

        def run() -> list[bool]:
            return [matcher.matches(p, include=pattern) for p in MANY_PATHS]

        result = benchmark(run)
        assert any(result)

    def test_many_unique_patterns(self, benchmark: "BenchmarkFixture") -> None:
        matcher = GlobMatcher()

        def run() -> list[bool]:
            results: list[bool] = []
            for i, path in enumerate(SAMPLE_PATHS):
                pattern = [f"**/*{i}*"]
                results.append(matcher.matches(path, include=pattern))
            return results

        _ = benchmark(run)


class TestBenchRegexMatcher:
    def test_simple_regex_pattern(self, benchmark: "BenchmarkFixture") -> None:
        matcher = RegexMatcher()

        def run() -> list[bool]:
            return [matcher.matches(p, include=[r".*\.py"]) for p in SAMPLE_PATHS]

        result = benchmark(run)
        assert any(result)

    def test_complex_regex_pattern(self, benchmark: "BenchmarkFixture") -> None:
        matcher = RegexMatcher()

        def run() -> list[bool]:
            return [
                matcher.matches(p, include=[r"(?:src|tests)/.*\.py"])
                for p in SAMPLE_PATHS
            ]

        result = benchmark(run)
        assert any(result)

    def test_regex_many_paths(self, benchmark: "BenchmarkFixture") -> None:
        matcher = RegexMatcher()

        def run() -> list[bool]:
            return [matcher.matches(p, include=[r".*\.py"]) for p in MANY_PATHS]

        result = benchmark(run)
        assert all(result)


class TestBenchGitignoreMatcher:
    def test_simple_gitignore_pattern(self, benchmark: "BenchmarkFixture") -> None:
        matcher = GitignoreMatcher()

        def run() -> list[bool]:
            return [matcher.matches(p, include=["*.py"]) for p in SAMPLE_PATHS]

        result = benchmark(run)
        assert any(result)

    def test_recursive_gitignore_pattern(self, benchmark: "BenchmarkFixture") -> None:
        matcher = GitignoreMatcher()

        def run() -> list[bool]:
            return [matcher.matches(p, include=["**/*.py"]) for p in SAMPLE_PATHS]

        result = benchmark(run)
        assert any(result)

    def test_gitignore_many_patterns(self, benchmark: "BenchmarkFixture") -> None:
        matcher = GitignoreMatcher()
        excludes = [
            "__pycache__/",
            "*.pyc",
            ".git/",
            "node_modules/",
            "dist/",
            "build/",
            ".venv/",
            "*.egg-info/",
            ".mypy_cache/",
            ".pytest_cache/",
        ]

        def run() -> list[bool]:
            return [
                matcher.matches(p, include=["**/*.py"], exclude=excludes)
                for p in SAMPLE_PATHS
            ]

        result = benchmark(run)
        assert any(result)

    def test_gitignore_many_paths(self, benchmark: "BenchmarkFixture") -> None:
        matcher = GitignoreMatcher()

        def run() -> list[bool]:
            return [matcher.matches(p, include=["**/*.py"]) for p in MANY_PATHS]

        result = benchmark(run)
        assert all(result)


class TestBenchGlobMatcherAdditional:
    def test_glob_many_paths(self, benchmark: "BenchmarkFixture") -> None:
        glob_matcher = GlobMatcher()

        def run_glob() -> list[bool]:
            return [glob_matcher.matches(p, include=["**/*.py"]) for p in MANY_PATHS]

        result = benchmark(run_glob)
        assert all(result)

    @pytest.mark.slow
    def test_all_matchers_many_patterns(self, benchmark: "BenchmarkFixture") -> None:
        glob_matcher = GlobMatcher()

        def run() -> list[bool]:
            return [
                glob_matcher.matches(
                    p,
                    include=["**/*.py", "**/test_*", "src/**"],
                    exclude=["**/__pycache__/**"],
                )
                for p in MANY_PATHS
            ]

        result = benchmark(run)
        assert any(result)
