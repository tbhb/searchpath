import contextlib
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

from hypothesis import given, settings, strategies as st
from pyfakefs.fake_filesystem_unittest import Patcher

from searchpath import GlobMatcher, PatternSyntaxError
from searchpath._traversal import traverse

if TYPE_CHECKING:
    from collections.abc import Iterator


@contextmanager
def fake_test_tree(num_files: int = 0, num_dirs: int = 0) -> "Iterator[Path]":
    """Create an isolated fake filesystem with the specified files and directories.

    For use with Hypothesis property tests where pytest fixtures don't work.
    """
    with Patcher() as patcher:
        assert patcher.fs is not None
        root = Path("/test_root")
        _ = patcher.fs.create_dir(str(root))

        for i in range(num_dirs):
            _ = patcher.fs.create_dir(str(root / f"dir{i}"))

        for i in range(num_files):
            _ = patcher.fs.create_file(str(root / f"file{i}.txt"))

        yield root


# Strategy for generating valid path component characters (no path separators)
path_component_chars: st.SearchStrategy[str] = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N"),
        whitelist_characters="_-.",
    ),
    min_size=1,
    max_size=20,
)

# Strategy for generating relative path strings
relative_path: st.SearchStrategy[str] = st.lists(
    path_component_chars,
    min_size=1,
    max_size=5,
).map(lambda parts: "/".join(parts))

# Strategy for generating simple glob patterns (valid syntax)
simple_pattern: st.SearchStrategy[str] = st.one_of(
    st.just("*"),
    st.just("**"),
    st.just("**/*"),
    st.just("*.py"),
    st.just("*.txt"),
    path_component_chars,
)


class TestPatternMatchingProperties:
    @given(path=relative_path, pattern=simple_pattern)
    def test_pattern_match_is_deterministic(self, path: str, pattern: str):
        matcher = GlobMatcher()

        result1 = matcher.matches(path, include=[pattern])
        result2 = matcher.matches(path, include=[pattern])

        assert result1 == result2

    @given(path=relative_path, pattern=simple_pattern)
    def test_exclude_and_include_same_pattern_always_false(
        self, path: str, pattern: str
    ):
        matcher = GlobMatcher()

        # If a path matches a pattern in both include and exclude,
        # exclude wins (returns False)
        result = matcher.matches(path, include=[pattern], exclude=[pattern])

        # If the path matches the pattern, it should be excluded
        if matcher.matches(path, include=[pattern]):
            assert result is False

    @given(path=relative_path)
    def test_empty_include_matches_all(self, path: str):
        matcher = GlobMatcher()

        result = matcher.matches(path, include=())

        assert result is True

    @given(path=relative_path)
    def test_empty_exclude_excludes_none(self, path: str):
        matcher = GlobMatcher()

        result = matcher.matches(path, exclude=())

        assert result is True

    @given(pattern_str=st.text(min_size=0, max_size=50))
    @settings(max_examples=100)
    def test_matcher_compilation_handles_arbitrary_strings(self, pattern_str: str):
        # This tests that compilation never crashes unexpectedly
        # It may raise PatternSyntaxError for invalid patterns, which is expected
        matcher = GlobMatcher()

        with contextlib.suppress(PatternSyntaxError):
            _ = matcher.matches("test.py", include=[pattern_str])


class TestTraverseKindProperties:
    @given(
        num_files=st.integers(min_value=0, max_value=5),
        num_dirs=st.integers(min_value=0, max_value=3),
    )
    @settings(max_examples=20)
    def test_traverse_files_never_yields_directories(
        self, num_files: int, num_dirs: int
    ):
        with fake_test_tree(num_files=num_files, num_dirs=num_dirs) as root:
            result = list(traverse(root, kind="files"))

            for path in result:
                assert path.is_file()

    @given(
        num_files=st.integers(min_value=0, max_value=5),
        num_dirs=st.integers(min_value=0, max_value=3),
    )
    @settings(max_examples=20)
    def test_traverse_dirs_never_yields_files(self, num_files: int, num_dirs: int):
        with fake_test_tree(num_files=num_files, num_dirs=num_dirs) as root:
            result = list(traverse(root, kind="dirs"))

            for path in result:
                assert path.is_dir()

    def test_traverse_both_yields_files_and_dirs(self):
        # Create at least one file and one directory
        with fake_test_tree(num_files=1, num_dirs=1) as root:
            result = list(traverse(root, kind="both"))

            has_file = any(p.is_file() for p in result)
            has_dir = any(p.is_dir() for p in result)

            assert has_file
            assert has_dir

    @given(num_files=st.integers(min_value=1, max_value=5))
    @settings(max_examples=20)
    def test_traverse_yields_absolute_paths(self, num_files: int):
        with fake_test_tree(num_files=num_files) as root:
            result = list(traverse(root))

            for path in result:
                assert path.is_absolute()

    @given(num_files=st.integers(min_value=0, max_value=5))
    @settings(max_examples=10)
    def test_traverse_result_is_deterministic(self, num_files: int):
        with fake_test_tree(num_files=num_files) as root:
            result1 = sorted(traverse(root))
            result2 = sorted(traverse(root))

            assert result1 == result2
