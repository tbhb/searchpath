import os
from typing import TYPE_CHECKING, Literal

import pytest

from searchpath import GlobMatcher, Match, PatternFileError, SearchPath

from tests.conftest import Symlink

if TYPE_CHECKING:
    from conftest import TreeFactory


class TestFirst:
    def test_finds_first_matching_file(self, tmp_tree: "TreeFactory"):
        root = tmp_tree({"config.toml": "", "other.txt": ""})
        sp = SearchPath(("dir", root))

        result = sp.first("*.toml")

        assert result == root / "config.toml"

    def test_returns_none_when_not_found(self, tmp_tree: "TreeFactory"):
        root = tmp_tree({"readme.txt": ""})
        sp = SearchPath(("dir", root))

        result = sp.first("*.py")

        assert result is None

    def test_returns_none_for_empty_searchpath(self):
        sp = SearchPath()

        result = sp.first("*.py")

        assert result is None

    def test_respects_search_order(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "dir1": {"config.toml": "from dir1"},
                "dir2": {"config.toml": "from dir2"},
            }
        )
        dir1 = root / "dir1"
        dir2 = root / "dir2"

        sp = SearchPath(("first", dir1), ("second", dir2))
        result = sp.first("config.toml")

        assert result is not None
        assert result == dir1 / "config.toml"

    def test_skips_nonexistent_directories(self, tmp_tree: "TreeFactory"):
        root = tmp_tree({"existing": {"config.toml": ""}})
        existing = root / "existing"
        missing = root / "missing"

        sp = SearchPath(("missing", missing), ("existing", existing))
        result = sp.first("*.toml")

        assert result == existing / "config.toml"

    def test_with_exclude_patterns(self, tmp_tree: "TreeFactory"):
        root = tmp_tree({"main.py": "", "test_main.py": ""})
        sp = SearchPath(("dir", root))

        result = sp.first("*.py", exclude=["test_*"])

        assert result == root / "main.py"


class TestMatch:
    def test_returns_match_with_correct_metadata(self, tmp_tree: "TreeFactory"):
        root = tmp_tree({"config.toml": ""})
        sp = SearchPath(("project", root))

        result = sp.match("*.toml")

        assert result is not None
        assert isinstance(result, Match)
        assert result.scope == "project"
        assert result.source == root
        assert result.path == root / "config.toml"
        assert result.relative.as_posix() == "config.toml"

    def test_returns_none_when_not_found(self, tmp_tree: "TreeFactory"):
        root = tmp_tree({"readme.txt": ""})
        sp = SearchPath(("dir", root))

        result = sp.match("*.py")

        assert result is None

    def test_returns_none_for_empty_searchpath(self):
        sp = SearchPath()

        result = sp.match("*.py")

        assert result is None

    def test_nested_file_relative_path(self, tmp_tree: "TreeFactory"):
        root = tmp_tree({"src": {"utils": {"helpers.py": ""}}})
        sp = SearchPath(("project", root))

        result = sp.match("**/*.py")

        assert result is not None
        assert result.relative.as_posix() == "src/utils/helpers.py"

    def test_provenance_tracks_correct_source(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "dir1": {},
                "dir2": {"config.toml": ""},
            }
        )
        dir1 = root / "dir1"
        dir2 = root / "dir2"

        sp = SearchPath(("first", dir1), ("second", dir2))
        result = sp.match("*.toml")

        assert result is not None
        assert result.scope == "second"
        assert result.source == dir2


class TestAll:
    def test_finds_all_matching_files(self, tmp_tree: "TreeFactory"):
        root = tmp_tree({"a.py": "", "b.py": "", "readme.txt": ""})
        sp = SearchPath(("dir", root))

        result = sorted(sp.all("*.py"))

        assert result == sorted([root / "a.py", root / "b.py"])

    def test_returns_empty_list_when_not_found(self, tmp_tree: "TreeFactory"):
        root = tmp_tree({"readme.txt": ""})
        sp = SearchPath(("dir", root))

        result = sp.all("*.py")

        assert result == []

    def test_returns_empty_list_for_empty_searchpath(self):
        sp = SearchPath()

        result = sp.all("*.py")

        assert result == []

    def test_finds_files_in_nested_directories(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "src": {"main.py": ""},
                "tests": {"test_main.py": ""},
            }
        )
        src = root / "src"
        tests = root / "tests"
        sp = SearchPath(("project", root))

        result = sorted(sp.all("**/*.py"))

        assert result == sorted([src / "main.py", tests / "test_main.py"])

    def test_multi_entry_search_order(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "dir1": {"unique_to_dir1.py": ""},
                "dir2": {"unique_to_dir2.py": ""},
            }
        )
        dir1 = root / "dir1"
        dir2 = root / "dir2"

        sp = SearchPath(("first", dir1), ("second", dir2))
        result = sp.all("*.py")

        assert dir1 / "unique_to_dir1.py" in result
        assert dir2 / "unique_to_dir2.py" in result


class TestMatches:
    def test_returns_match_objects_with_provenance(self, tmp_tree: "TreeFactory"):
        root = tmp_tree({"config.toml": ""})
        sp = SearchPath(("project", root))

        result = sp.matches("*.toml")

        assert len(result) == 1
        assert result[0].scope == "project"
        assert result[0].source == root

    def test_returns_empty_list_when_not_found(self, tmp_tree: "TreeFactory"):
        root = tmp_tree({"readme.txt": ""})
        sp = SearchPath(("dir", root))

        result = sp.matches("*.py")

        assert result == []

    def test_returns_empty_list_for_empty_searchpath(self):
        sp = SearchPath()

        result = sp.matches("*.py")

        assert result == []

    def test_multi_entry_provenance(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "dir1": {"file1.py": ""},
                "dir2": {"file2.py": ""},
            }
        )
        dir1 = root / "dir1"
        dir2 = root / "dir2"

        sp = SearchPath(("first", dir1), ("second", dir2))
        result = sp.matches("*.py")

        file1_match = next(m for m in result if m.path.name == "file1.py")
        file2_match = next(m for m in result if m.path.name == "file2.py")

        assert file1_match.scope == "first"
        assert file1_match.source == dir1
        assert file2_match.scope == "second"
        assert file2_match.source == dir2


class TestDeduplication:
    @pytest.mark.parametrize(
        ("dedupe", "expected_count"),
        [
            pytest.param(True, 1, id="dedupe-true-keeps-first"),
            pytest.param(False, 2, id="dedupe-false-returns-all"),
        ],
    )
    def test_all_dedupe_behavior(
        self,
        tmp_tree: "TreeFactory",
        *,
        dedupe: bool,
        expected_count: int,
    ):
        root = tmp_tree(
            {
                "dir1": {"config.toml": "from dir1"},
                "dir2": {"config.toml": "from dir2"},
            }
        )
        dir1 = root / "dir1"
        dir2 = root / "dir2"

        sp = SearchPath(("first", dir1), ("second", dir2))
        result = sp.all("config.toml", dedupe=dedupe)

        assert len(result) == expected_count
        assert dir1 / "config.toml" in result
        if not dedupe:
            assert dir2 / "config.toml" in result

    def test_dedupe_matches_keeps_first_occurrence(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "dir1": {"config.toml": ""},
                "dir2": {"config.toml": ""},
            }
        )
        dir1 = root / "dir1"
        dir2 = root / "dir2"

        sp = SearchPath(("first", dir1), ("second", dir2))
        result = sp.matches("config.toml", dedupe=True)

        assert len(result) == 1
        assert result[0].scope == "first"

    def test_dedupe_uses_relative_path_as_key(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "dir1": {"sub": {"file.py": ""}},
                "dir2": {"sub": {"file.py": ""}},
            }
        )
        dir1 = root / "dir1"
        dir2 = root / "dir2"

        sp = SearchPath(("first", dir1), ("second", dir2))
        result = sp.matches("**/file.py", dedupe=True)

        assert len(result) == 1
        assert result[0].relative.as_posix() == "sub/file.py"
        assert result[0].scope == "first"

    def test_different_relative_paths_not_deduped(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "dir1": {"a.py": ""},
                "dir2": {"b.py": ""},
            }
        )
        dir1 = root / "dir1"
        dir2 = root / "dir2"

        sp = SearchPath(("first", dir1), ("second", dir2))
        result = sp.all("*.py", dedupe=True)

        expected_count = 2
        assert len(result) == expected_count


class TestKindFiltering:
    @pytest.mark.parametrize(
        ("kind", "expected_name"),
        [
            pytest.param("files", "file.py", id="kind-files-returns-only-files"),
            pytest.param("dirs", "subdir", id="kind-dirs-returns-only-directories"),
        ],
    )
    def test_all_kind_filtering(
        self,
        tmp_tree: "TreeFactory",
        kind: Literal["files", "dirs"],
        *,
        expected_name: str,
    ):
        root = tmp_tree({"file.py": "", "subdir": {}})
        sp = SearchPath(("dir", root))

        result = sp.all(kind=kind)

        assert len(result) == 1
        assert result[0] == root / expected_name

    def test_kind_both_returns_files_and_directories(self, tmp_tree: "TreeFactory"):
        root = tmp_tree({"file.py": "", "subdir": {}})
        sp = SearchPath(("dir", root))

        result = sorted(sp.all(kind="both"))

        assert result == sorted([root / "file.py", root / "subdir"])

    def test_first_with_kind_dirs(self, tmp_tree: "TreeFactory"):
        root = tmp_tree({"file.py": "", "subdir": {}})
        sp = SearchPath(("dir", root))

        result = sp.first(kind="dirs")

        assert result == root / "subdir"


class TestPatternFileLoading:
    def test_include_from_single_file(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "main.py": "",
                "readme.txt": "",
                "config.json": "",
                "patterns.txt": "*.py\n*.txt\n",
            }
        )

        sp = SearchPath(("dir", root))
        result = sorted(sp.all(include_from=root / "patterns.txt"))

        filtered = [p for p in result if p.name != "patterns.txt"]
        assert sorted(filtered) == sorted([root / "main.py", root / "readme.txt"])

    def test_exclude_from_single_file(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "main.py": "",
                "test_main.py": "",
                "conftest.py": "",
                "exclude.txt": "test_*\nconftest.py\n",
            }
        )

        sp = SearchPath(("dir", root))
        result = sp.all("*.py", exclude_from=root / "exclude.txt")

        assert result == [root / "main.py"]

    def test_include_from_multiple_files(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "main.py": "",
                "readme.txt": "",
                "config.json": "",
                "patterns1.txt": "*.py\n",
                "patterns2.txt": "*.txt\n",
            }
        )

        sp = SearchPath(("dir", root))
        result = sorted(
            sp.all(include_from=[root / "patterns1.txt", root / "patterns2.txt"])
        )

        filtered = [p for p in result if not p.name.startswith("patterns")]
        assert sorted(filtered) == sorted([root / "main.py", root / "readme.txt"])

    def test_include_combined_with_include_from(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "main.py": "",
                "readme.txt": "",
                "config.json": "",
                "patterns.txt": "*.py\n",
            }
        )

        sp = SearchPath(("dir", root))
        result = sorted(sp.all(include="*.json", include_from=root / "patterns.txt"))

        assert root / "main.py" in result
        assert root / "config.json" in result
        assert root / "readme.txt" not in result

    def test_exclude_combined_with_exclude_from(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "main.py": "",
                "test_main.py": "",
                "conftest.py": "",
                "exclude.txt": "test_*\n",
            }
        )

        sp = SearchPath(("dir", root))
        result = sp.all(
            "*.py", exclude="conftest.py", exclude_from=root / "exclude.txt"
        )

        assert result == [root / "main.py"]

    def test_include_from_with_string_path(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "main.py": "",
                "patterns.txt": "*.py\n",
            }
        )

        sp = SearchPath(("dir", root))
        result = sp.all(include_from=str(root / "patterns.txt"))

        assert root / "main.py" in result

    def test_include_from_nonexistent_file_raises_error(self, tmp_tree: "TreeFactory"):
        root = tmp_tree({"main.py": ""})
        sp = SearchPath(("dir", root))
        nonexistent = root / "missing_patterns.txt"

        with pytest.raises(PatternFileError):
            _ = sp.all(include_from=nonexistent)

    def test_exclude_from_nonexistent_file_raises_error(self, tmp_tree: "TreeFactory"):
        root = tmp_tree({"main.py": ""})
        sp = SearchPath(("dir", root))
        nonexistent = root / "missing_patterns.txt"

        with pytest.raises(PatternFileError):
            _ = sp.all("*.py", exclude_from=nonexistent)

    def test_exclude_from_multiple_files(self, tmp_tree: "TreeFactory"):
        root = tmp_tree(
            {
                "main.py": "",
                "test_main.py": "",
                "conftest.py": "",
                "exclude1.txt": "test_*\n",
                "exclude2.txt": "conftest.py\n",
            }
        )

        sp = SearchPath(("dir", root))
        result = sp.all(
            "*.py", exclude_from=[root / "exclude1.txt", root / "exclude2.txt"]
        )

        assert result == [root / "main.py"]


class TestCustomMatcher:
    def test_accepts_custom_matcher(self, tmp_tree: "TreeFactory"):
        root = tmp_tree({"file.py": "", "file.txt": ""})

        matcher = GlobMatcher()
        sp = SearchPath(("dir", root))
        result = sp.all("*.py", matcher=matcher)

        assert result == [root / "file.py"]


class TestEdgeCases:
    def test_pattern_as_string(self, tmp_tree: "TreeFactory"):
        root = tmp_tree({"config.toml": ""})
        sp = SearchPath(("dir", root))

        result = sp.first("*.toml")

        assert result is not None

    @pytest.mark.parametrize(
        ("include", "expected_names"),
        [
            pytest.param("*.py", ["main.py"], id="include-as-string"),
            pytest.param(
                ["*.py", "*.txt"], ["main.py", "readme.txt"], id="include-as-list"
            ),
        ],
    )
    def test_include_format(
        self,
        tmp_tree: "TreeFactory",
        include: str | list[str],
        *,
        expected_names: list[str],
    ):
        root = tmp_tree({"main.py": "", "readme.txt": "", "config.json": ""})
        sp = SearchPath(("dir", root))

        result = sorted(sp.all(include=include))

        expected = sorted([root / name for name in expected_names])
        assert result == expected

    @pytest.mark.parametrize(
        ("exclude", "expected_names"),
        [
            pytest.param("test_*", ["main.py", "conftest.py"], id="exclude-as-string"),
            pytest.param(["test_*", "conftest.py"], ["main.py"], id="exclude-as-list"),
        ],
    )
    def test_exclude_format(
        self,
        tmp_tree: "TreeFactory",
        exclude: str | list[str],
        *,
        expected_names: list[str],
    ):
        root = tmp_tree({"main.py": "", "test_main.py": "", "conftest.py": ""})
        sp = SearchPath(("dir", root))

        result = sorted(sp.all("*.py", exclude=exclude))

        expected = sorted([root / name for name in expected_names])
        assert result == expected

    def test_default_pattern_matches_all(self, tmp_tree: "TreeFactory"):
        root = tmp_tree({"file1.py": "", "file2.txt": ""})
        sp = SearchPath(("dir", root))

        result = sorted(sp.all())

        assert result == sorted([root / "file1.py", root / "file2.txt"])

    @pytest.mark.skipif(
        os.name == "nt",
        reason="Symlinks not always available on Windows",
    )
    @pytest.mark.parametrize(
        ("follow_symlinks", "expect_link_content"),
        [
            pytest.param(True, True, id="follow-symlinks-true"),
            pytest.param(False, False, id="follow-symlinks-false"),
        ],
    )
    def test_follow_symlinks_behavior(
        self,
        tmp_tree: "TreeFactory",
        *,
        follow_symlinks: bool,
        expect_link_content: bool,
    ):
        root = tmp_tree(
            {
                "real": {"file.py": ""},
                "link": Symlink("real"),
            }
        )

        sp = SearchPath(("dir", root))
        result = sorted(sp.all("**/*.py", follow_symlinks=follow_symlinks))

        assert root / "real" / "file.py" in result
        if expect_link_content:
            assert root / "link" / "file.py" in result
        else:
            assert root / "link" / "file.py" not in result
