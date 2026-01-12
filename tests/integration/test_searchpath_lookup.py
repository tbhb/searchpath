"""Integration tests for SearchPath lookup methods."""

import os
from typing import TYPE_CHECKING

import pytest

from searchpath import GlobMatcher, Match, PatternFileError, SearchPath

if TYPE_CHECKING:
    from pathlib import Path


class TestFirst:
    def test_finds_first_matching_file(self, tmp_path: "Path"):
        (tmp_path / "config.toml").touch()
        (tmp_path / "other.txt").touch()
        sp = SearchPath(("dir", tmp_path))

        result = sp.first("*.toml")

        assert result == tmp_path / "config.toml"

    def test_returns_none_when_not_found(self, tmp_path: "Path"):
        (tmp_path / "readme.txt").touch()
        sp = SearchPath(("dir", tmp_path))

        result = sp.first("*.py")

        assert result is None

    def test_returns_none_for_empty_searchpath(self):
        sp = SearchPath()

        result = sp.first("*.py")

        assert result is None

    def test_respects_search_order(self, tmp_path: "Path"):
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        _ = (dir1 / "config.toml").write_text("from dir1", encoding="utf-8")
        _ = (dir2 / "config.toml").write_text("from dir2", encoding="utf-8")

        sp = SearchPath(("first", dir1), ("second", dir2))
        result = sp.first("config.toml")

        assert result is not None
        assert result == dir1 / "config.toml"

    def test_skips_nonexistent_directories(self, tmp_path: "Path"):
        existing = tmp_path / "existing"
        missing = tmp_path / "missing"
        existing.mkdir()
        (existing / "config.toml").touch()

        sp = SearchPath(("missing", missing), ("existing", existing))
        result = sp.first("*.toml")

        assert result == existing / "config.toml"

    def test_with_exclude_patterns(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()
        (tmp_path / "test_main.py").touch()
        sp = SearchPath(("dir", tmp_path))

        result = sp.first("*.py", exclude=["test_*"])

        assert result == tmp_path / "main.py"


class TestMatch:
    def test_returns_match_with_correct_metadata(self, tmp_path: "Path"):
        (tmp_path / "config.toml").touch()
        sp = SearchPath(("project", tmp_path))

        result = sp.match("*.toml")

        assert result is not None
        assert isinstance(result, Match)
        assert result.scope == "project"
        assert result.source == tmp_path
        assert result.path == tmp_path / "config.toml"
        assert result.relative.as_posix() == "config.toml"

    def test_returns_none_when_not_found(self, tmp_path: "Path"):
        (tmp_path / "readme.txt").touch()
        sp = SearchPath(("dir", tmp_path))

        result = sp.match("*.py")

        assert result is None

    def test_returns_none_for_empty_searchpath(self):
        sp = SearchPath()

        result = sp.match("*.py")

        assert result is None

    def test_nested_file_relative_path(self, tmp_path: "Path"):
        subdir = tmp_path / "src" / "utils"
        subdir.mkdir(parents=True)
        (subdir / "helpers.py").touch()
        sp = SearchPath(("project", tmp_path))

        result = sp.match("**/*.py")

        assert result is not None
        assert result.relative.as_posix() == "src/utils/helpers.py"

    def test_provenance_tracks_correct_source(self, tmp_path: "Path"):
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        (dir2 / "config.toml").touch()

        sp = SearchPath(("first", dir1), ("second", dir2))
        result = sp.match("*.toml")

        assert result is not None
        assert result.scope == "second"
        assert result.source == dir2


class TestAll:
    def test_finds_all_matching_files(self, tmp_path: "Path"):
        (tmp_path / "a.py").touch()
        (tmp_path / "b.py").touch()
        (tmp_path / "readme.txt").touch()
        sp = SearchPath(("dir", tmp_path))

        result = sorted(sp.all("*.py"))

        assert result == sorted([tmp_path / "a.py", tmp_path / "b.py"])

    def test_returns_empty_list_when_not_found(self, tmp_path: "Path"):
        (tmp_path / "readme.txt").touch()
        sp = SearchPath(("dir", tmp_path))

        result = sp.all("*.py")

        assert result == []

    def test_returns_empty_list_for_empty_searchpath(self):
        sp = SearchPath()

        result = sp.all("*.py")

        assert result == []

    def test_finds_files_in_nested_directories(self, tmp_path: "Path"):
        src = tmp_path / "src"
        tests = tmp_path / "tests"
        src.mkdir()
        tests.mkdir()
        (src / "main.py").touch()
        (tests / "test_main.py").touch()
        sp = SearchPath(("project", tmp_path))

        result = sorted(sp.all("**/*.py"))

        assert result == sorted([src / "main.py", tests / "test_main.py"])

    def test_multi_entry_search_order(self, tmp_path: "Path"):
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        (dir1 / "unique_to_dir1.py").touch()
        (dir2 / "unique_to_dir2.py").touch()

        sp = SearchPath(("first", dir1), ("second", dir2))
        result = sp.all("*.py")

        assert dir1 / "unique_to_dir1.py" in result
        assert dir2 / "unique_to_dir2.py" in result


class TestMatches:
    def test_returns_match_objects_with_provenance(self, tmp_path: "Path"):
        (tmp_path / "config.toml").touch()
        sp = SearchPath(("project", tmp_path))

        result = sp.matches("*.toml")

        assert len(result) == 1
        assert result[0].scope == "project"
        assert result[0].source == tmp_path

    def test_returns_empty_list_when_not_found(self, tmp_path: "Path"):
        (tmp_path / "readme.txt").touch()
        sp = SearchPath(("dir", tmp_path))

        result = sp.matches("*.py")

        assert result == []

    def test_returns_empty_list_for_empty_searchpath(self):
        sp = SearchPath()

        result = sp.matches("*.py")

        assert result == []

    def test_multi_entry_provenance(self, tmp_path: "Path"):
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        (dir1 / "file1.py").touch()
        (dir2 / "file2.py").touch()

        sp = SearchPath(("first", dir1), ("second", dir2))
        result = sp.matches("*.py")

        file1_match = next(m for m in result if m.path.name == "file1.py")
        file2_match = next(m for m in result if m.path.name == "file2.py")

        assert file1_match.scope == "first"
        assert file1_match.source == dir1
        assert file2_match.scope == "second"
        assert file2_match.source == dir2


class TestDeduplication:
    def test_dedupe_true_keeps_first_occurrence(self, tmp_path: "Path"):
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        _ = (dir1 / "config.toml").write_text("from dir1", encoding="utf-8")
        _ = (dir2 / "config.toml").write_text("from dir2", encoding="utf-8")

        sp = SearchPath(("first", dir1), ("second", dir2))
        result = sp.all("config.toml", dedupe=True)

        assert len(result) == 1
        assert result[0] == dir1 / "config.toml"

    def test_dedupe_false_returns_all(self, tmp_path: "Path"):
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        (dir1 / "config.toml").touch()
        (dir2 / "config.toml").touch()

        sp = SearchPath(("first", dir1), ("second", dir2))
        result = sp.all("config.toml", dedupe=False)

        expected_count = 2
        assert len(result) == expected_count
        assert dir1 / "config.toml" in result
        assert dir2 / "config.toml" in result

    def test_dedupe_matches_keeps_first_occurrence(self, tmp_path: "Path"):
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        (dir1 / "config.toml").touch()
        (dir2 / "config.toml").touch()

        sp = SearchPath(("first", dir1), ("second", dir2))
        result = sp.matches("config.toml", dedupe=True)

        assert len(result) == 1
        assert result[0].scope == "first"

    def test_dedupe_uses_relative_path_as_key(self, tmp_path: "Path"):
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        sub1 = dir1 / "sub"
        sub2 = dir2 / "sub"
        sub1.mkdir(parents=True)
        sub2.mkdir(parents=True)
        (sub1 / "file.py").touch()
        (sub2 / "file.py").touch()

        sp = SearchPath(("first", dir1), ("second", dir2))
        result = sp.matches("**/file.py", dedupe=True)

        assert len(result) == 1
        assert result[0].relative.as_posix() == "sub/file.py"
        assert result[0].scope == "first"

    def test_different_relative_paths_not_deduped(self, tmp_path: "Path"):
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        (dir1 / "a.py").touch()
        (dir2 / "b.py").touch()

        sp = SearchPath(("first", dir1), ("second", dir2))
        result = sp.all("*.py", dedupe=True)

        expected_count = 2
        assert len(result) == expected_count


class TestKindFiltering:
    def test_kind_files_returns_only_files(self, tmp_path: "Path"):
        (tmp_path / "file.py").touch()
        (tmp_path / "subdir").mkdir()
        sp = SearchPath(("dir", tmp_path))

        result = sp.all(kind="files")

        assert len(result) == 1
        assert result[0] == tmp_path / "file.py"

    def test_kind_dirs_returns_only_directories(self, tmp_path: "Path"):
        (tmp_path / "file.py").touch()
        (tmp_path / "subdir").mkdir()
        sp = SearchPath(("dir", tmp_path))

        result = sp.all(kind="dirs")

        assert len(result) == 1
        assert result[0] == tmp_path / "subdir"

    def test_kind_both_returns_files_and_directories(self, tmp_path: "Path"):
        (tmp_path / "file.py").touch()
        (tmp_path / "subdir").mkdir()
        sp = SearchPath(("dir", tmp_path))

        result = sorted(sp.all(kind="both"))

        assert result == sorted([tmp_path / "file.py", tmp_path / "subdir"])

    def test_first_with_kind_dirs(self, tmp_path: "Path"):
        (tmp_path / "file.py").touch()
        (tmp_path / "subdir").mkdir()
        sp = SearchPath(("dir", tmp_path))

        result = sp.first(kind="dirs")

        assert result == tmp_path / "subdir"


class TestPatternFileLoading:
    def test_include_from_single_file(self, tmp_path: "Path"):
        # Create files
        (tmp_path / "main.py").touch()
        (tmp_path / "readme.txt").touch()
        (tmp_path / "config.json").touch()

        # Create include pattern file
        patterns_file = tmp_path / "patterns.txt"
        _ = patterns_file.write_text("*.py\n*.txt\n", encoding="utf-8")

        sp = SearchPath(("dir", tmp_path))
        result = sorted(sp.all(include_from=patterns_file))

        filtered = [p for p in result if p.name != "patterns.txt"]
        assert sorted(filtered) == sorted(
            [tmp_path / "main.py", tmp_path / "readme.txt"]
        )

    def test_exclude_from_single_file(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()
        (tmp_path / "test_main.py").touch()
        (tmp_path / "conftest.py").touch()

        exclude_file = tmp_path / "exclude.txt"
        _ = exclude_file.write_text("test_*\nconftest.py\n", encoding="utf-8")

        sp = SearchPath(("dir", tmp_path))
        result = sp.all("*.py", exclude_from=exclude_file)

        assert result == [tmp_path / "main.py"]

    def test_include_from_multiple_files(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()
        (tmp_path / "readme.txt").touch()
        (tmp_path / "config.json").touch()

        patterns1 = tmp_path / "patterns1.txt"
        patterns2 = tmp_path / "patterns2.txt"
        _ = patterns1.write_text("*.py\n", encoding="utf-8")
        _ = patterns2.write_text("*.txt\n", encoding="utf-8")

        sp = SearchPath(("dir", tmp_path))
        result = sorted(sp.all(include_from=[patterns1, patterns2]))

        filtered = [p for p in result if not p.name.startswith("patterns")]
        assert sorted(filtered) == sorted(
            [tmp_path / "main.py", tmp_path / "readme.txt"]
        )

    def test_include_combined_with_include_from(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()
        (tmp_path / "readme.txt").touch()
        (tmp_path / "config.json").touch()

        patterns_file = tmp_path / "patterns.txt"
        _ = patterns_file.write_text("*.py\n", encoding="utf-8")

        sp = SearchPath(("dir", tmp_path))
        result = sorted(sp.all(include="*.json", include_from=patterns_file))

        assert tmp_path / "main.py" in result
        assert tmp_path / "config.json" in result
        assert tmp_path / "readme.txt" not in result

    def test_exclude_combined_with_exclude_from(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()
        (tmp_path / "test_main.py").touch()
        (tmp_path / "conftest.py").touch()

        exclude_file = tmp_path / "exclude.txt"
        _ = exclude_file.write_text("test_*\n", encoding="utf-8")

        sp = SearchPath(("dir", tmp_path))
        result = sp.all("*.py", exclude="conftest.py", exclude_from=exclude_file)

        assert result == [tmp_path / "main.py"]

    def test_include_from_with_string_path(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()

        patterns_file = tmp_path / "patterns.txt"
        _ = patterns_file.write_text("*.py\n", encoding="utf-8")

        sp = SearchPath(("dir", tmp_path))
        result = sp.all(include_from=str(patterns_file))

        assert tmp_path / "main.py" in result

    def test_include_from_nonexistent_file_raises_error(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()
        sp = SearchPath(("dir", tmp_path))
        nonexistent = tmp_path / "missing_patterns.txt"

        with pytest.raises(PatternFileError):
            _ = sp.all(include_from=nonexistent)

    def test_exclude_from_nonexistent_file_raises_error(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()
        sp = SearchPath(("dir", tmp_path))
        nonexistent = tmp_path / "missing_patterns.txt"

        with pytest.raises(PatternFileError):
            _ = sp.all("*.py", exclude_from=nonexistent)

    def test_exclude_from_multiple_files(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()
        (tmp_path / "test_main.py").touch()
        (tmp_path / "conftest.py").touch()

        exclude1 = tmp_path / "exclude1.txt"
        exclude2 = tmp_path / "exclude2.txt"
        _ = exclude1.write_text("test_*\n", encoding="utf-8")
        _ = exclude2.write_text("conftest.py\n", encoding="utf-8")

        sp = SearchPath(("dir", tmp_path))
        result = sp.all("*.py", exclude_from=[exclude1, exclude2])

        assert result == [tmp_path / "main.py"]


class TestCustomMatcher:
    def test_accepts_custom_matcher(self, tmp_path: "Path"):
        (tmp_path / "file.py").touch()
        (tmp_path / "file.txt").touch()

        matcher = GlobMatcher()
        sp = SearchPath(("dir", tmp_path))
        result = sp.all("*.py", matcher=matcher)

        assert result == [tmp_path / "file.py"]


class TestEdgeCases:
    def test_pattern_as_string(self, tmp_path: "Path"):
        (tmp_path / "config.toml").touch()
        sp = SearchPath(("dir", tmp_path))

        result = sp.first("*.toml")

        assert result is not None

    def test_include_as_string(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()
        (tmp_path / "readme.txt").touch()
        sp = SearchPath(("dir", tmp_path))

        result = sp.all(include="*.py")

        assert result == [tmp_path / "main.py"]

    def test_include_as_list(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()
        (tmp_path / "readme.txt").touch()
        (tmp_path / "config.json").touch()
        sp = SearchPath(("dir", tmp_path))

        result = sorted(sp.all(include=["*.py", "*.txt"]))

        assert result == sorted([tmp_path / "main.py", tmp_path / "readme.txt"])

    def test_exclude_as_string(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()
        (tmp_path / "test_main.py").touch()
        sp = SearchPath(("dir", tmp_path))

        result = sp.all("*.py", exclude="test_*")

        assert result == [tmp_path / "main.py"]

    def test_exclude_as_list(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()
        (tmp_path / "test_main.py").touch()
        (tmp_path / "conftest.py").touch()
        sp = SearchPath(("dir", tmp_path))

        result = sp.all("*.py", exclude=["test_*", "conftest.py"])

        assert result == [tmp_path / "main.py"]

    def test_default_pattern_matches_all(self, tmp_path: "Path"):
        (tmp_path / "file1.py").touch()
        (tmp_path / "file2.txt").touch()
        sp = SearchPath(("dir", tmp_path))

        result = sorted(sp.all())

        assert result == sorted([tmp_path / "file1.py", tmp_path / "file2.txt"])

    @pytest.mark.skipif(
        os.name == "nt",
        reason="Symlinks not always available on Windows",
    )
    def test_follow_symlinks_true(self, tmp_path: "Path"):
        real_dir = tmp_path / "real"
        real_dir.mkdir()
        (real_dir / "file.py").touch()
        symlink = tmp_path / "link"
        symlink.symlink_to(real_dir)

        sp = SearchPath(("dir", tmp_path))
        result = sorted(sp.all("**/*.py", follow_symlinks=True))

        assert tmp_path / "real" / "file.py" in result
        assert tmp_path / "link" / "file.py" in result

    @pytest.mark.skipif(
        os.name == "nt",
        reason="Symlinks not always available on Windows",
    )
    def test_follow_symlinks_false(self, tmp_path: "Path"):
        real_dir = tmp_path / "real"
        real_dir.mkdir()
        (real_dir / "file.py").touch()
        symlink = tmp_path / "link"
        symlink.symlink_to(real_dir)

        sp = SearchPath(("dir", tmp_path))
        result = sp.all("**/*.py", follow_symlinks=False)

        assert tmp_path / "real" / "file.py" in result
        assert tmp_path / "link" / "file.py" not in result
