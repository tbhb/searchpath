import os
from typing import TYPE_CHECKING

import pytest

import searchpath
from searchpath import Match, PatternFileError

if TYPE_CHECKING:
    from pathlib import Path


class TestFirst:
    def test_finds_first_matching_file(self, tmp_path: "Path"):
        (tmp_path / "config.toml").touch()
        (tmp_path / "other.txt").touch()

        result = searchpath.first("*.toml", ("dir", tmp_path))

        assert result == tmp_path / "config.toml"

    def test_returns_none_when_not_found(self, tmp_path: "Path"):
        (tmp_path / "readme.txt").touch()

        result = searchpath.first("*.py", ("dir", tmp_path))

        assert result is None

    def test_returns_none_for_no_entries(self):
        result = searchpath.first("*.py")

        assert result is None

    def test_respects_search_order(self, tmp_path: "Path"):
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        _ = (dir1 / "config.toml").write_text("from dir1", encoding="utf-8")
        _ = (dir2 / "config.toml").write_text("from dir2", encoding="utf-8")

        result = searchpath.first("config.toml", ("first", dir1), ("second", dir2))

        assert result is not None
        assert result == dir1 / "config.toml"

    def test_with_exclude_patterns(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()
        (tmp_path / "test_main.py").touch()

        result = searchpath.first("*.py", ("dir", tmp_path), exclude=["test_*"])

        assert result == tmp_path / "main.py"

    def test_with_kind_dirs(self, tmp_path: "Path"):
        (tmp_path / "file.py").touch()
        (tmp_path / "subdir").mkdir()

        result = searchpath.first("*", ("dir", tmp_path), kind="dirs")

        assert result == tmp_path / "subdir"

    def test_accepts_string_path(self, tmp_path: "Path"):
        (tmp_path / "config.toml").touch()

        result = searchpath.first("*.toml", ("dir", str(tmp_path)))

        assert result == tmp_path / "config.toml"

    def test_skips_nonexistent_directories(self, tmp_path: "Path"):
        existing = tmp_path / "existing"
        missing = tmp_path / "missing"
        existing.mkdir()
        (existing / "config.toml").touch()

        result = searchpath.first(
            "*.toml", ("missing", missing), ("existing", existing)
        )

        assert result == existing / "config.toml"


class TestMatch:
    def test_returns_match_with_correct_metadata(self, tmp_path: "Path"):
        (tmp_path / "config.toml").touch()

        result = searchpath.match("*.toml", ("project", tmp_path))

        assert result is not None
        assert isinstance(result, Match)
        assert result.scope == "project"
        assert result.source == tmp_path
        assert result.path == tmp_path / "config.toml"
        assert result.relative.as_posix() == "config.toml"

    def test_returns_none_when_not_found(self, tmp_path: "Path"):
        (tmp_path / "readme.txt").touch()

        result = searchpath.match("*.py", ("dir", tmp_path))

        assert result is None

    def test_returns_none_for_no_entries(self):
        result = searchpath.match("*.py")

        assert result is None

    def test_provenance_tracks_correct_source(self, tmp_path: "Path"):
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        (dir2 / "config.toml").touch()

        result = searchpath.match("*.toml", ("first", dir1), ("second", dir2))

        assert result is not None
        assert result.scope == "second"
        assert result.source == dir2

    def test_with_include_patterns(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()
        (tmp_path / "readme.txt").touch()

        result = searchpath.match("*.py", ("dir", tmp_path), include=["main*"])

        assert result is not None
        assert result.path == tmp_path / "main.py"


class TestAll:
    def test_finds_all_matching_files(self, tmp_path: "Path"):
        (tmp_path / "a.py").touch()
        (tmp_path / "b.py").touch()
        (tmp_path / "readme.txt").touch()

        result = sorted(searchpath.all("*.py", ("dir", tmp_path)))

        assert result == sorted([tmp_path / "a.py", tmp_path / "b.py"])

    def test_returns_empty_list_when_not_found(self, tmp_path: "Path"):
        (tmp_path / "readme.txt").touch()

        result = searchpath.all("*.py", ("dir", tmp_path))

        assert result == []

    def test_returns_empty_list_for_no_entries(self):
        result = searchpath.all("*.py")

        assert result == []

    def test_finds_files_in_nested_directories(self, tmp_path: "Path"):
        src = tmp_path / "src"
        tests = tmp_path / "tests"
        src.mkdir()
        tests.mkdir()
        (src / "main.py").touch()
        (tests / "test_main.py").touch()

        result = sorted(searchpath.all("**/*.py", ("project", tmp_path)))

        assert result == sorted([src / "main.py", tests / "test_main.py"])

    def test_dedupe_true_keeps_first_occurrence(self, tmp_path: "Path"):
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        _ = (dir1 / "config.toml").write_text("from dir1", encoding="utf-8")
        _ = (dir2 / "config.toml").write_text("from dir2", encoding="utf-8")

        result = searchpath.all(
            "config.toml", ("first", dir1), ("second", dir2), dedupe=True
        )

        assert len(result) == 1
        assert result[0] == dir1 / "config.toml"

    def test_dedupe_false_returns_all(self, tmp_path: "Path"):
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        (dir1 / "config.toml").touch()
        (dir2 / "config.toml").touch()

        result = searchpath.all(
            "config.toml", ("first", dir1), ("second", dir2), dedupe=False
        )

        expected_count = 2
        assert len(result) == expected_count
        assert dir1 / "config.toml" in result
        assert dir2 / "config.toml" in result

    def test_with_kind_both(self, tmp_path: "Path"):
        (tmp_path / "file.py").touch()
        (tmp_path / "subdir").mkdir()

        result = sorted(searchpath.all("*", ("dir", tmp_path), kind="both"))

        assert result == sorted([tmp_path / "file.py", tmp_path / "subdir"])


class TestMatches:
    def test_returns_match_objects_with_provenance(self, tmp_path: "Path"):
        (tmp_path / "config.toml").touch()

        result = searchpath.matches("*.toml", ("project", tmp_path))

        assert len(result) == 1
        assert result[0].scope == "project"
        assert result[0].source == tmp_path

    def test_returns_empty_list_when_not_found(self, tmp_path: "Path"):
        (tmp_path / "readme.txt").touch()

        result = searchpath.matches("*.py", ("dir", tmp_path))

        assert result == []

    def test_returns_empty_list_for_no_entries(self):
        result = searchpath.matches("*.py")

        assert result == []

    def test_multi_entry_provenance(self, tmp_path: "Path"):
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        (dir1 / "file1.py").touch()
        (dir2 / "file2.py").touch()

        result = searchpath.matches("*.py", ("first", dir1), ("second", dir2))

        file1_match = next(m for m in result if m.path.name == "file1.py")
        file2_match = next(m for m in result if m.path.name == "file2.py")

        assert file1_match.scope == "first"
        assert file1_match.source == dir1
        assert file2_match.scope == "second"
        assert file2_match.source == dir2

    def test_dedupe_matches_keeps_first_occurrence(self, tmp_path: "Path"):
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()
        (dir1 / "config.toml").touch()
        (dir2 / "config.toml").touch()

        result = searchpath.matches(
            "config.toml", ("first", dir1), ("second", dir2), dedupe=True
        )

        assert len(result) == 1
        assert result[0].scope == "first"


class TestExports:
    def test_first_exported(self):
        assert hasattr(searchpath, "first")
        assert callable(searchpath.first)

    def test_match_exported(self):
        assert hasattr(searchpath, "match")
        assert callable(searchpath.match)

    def test_all_exported(self):
        assert hasattr(searchpath, "all")
        assert callable(searchpath.all)

    def test_matches_exported(self):
        assert hasattr(searchpath, "matches")
        assert callable(searchpath.matches)

    def test_all_in_module_all(self):
        assert "first" in searchpath.__all__
        assert "match" in searchpath.__all__
        assert "all" in searchpath.__all__
        assert "matches" in searchpath.__all__


class TestPatternFileLoading:
    def test_include_from_single_file(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()
        (tmp_path / "readme.txt").touch()
        (tmp_path / "config.json").touch()

        patterns_file = tmp_path / "patterns.txt"
        _ = patterns_file.write_text("*.py\n*.txt\n", encoding="utf-8")

        result = sorted(
            searchpath.all("**", ("dir", tmp_path), include_from=patterns_file)
        )

        filtered = [p for p in result if p.name != "patterns.txt"]
        expected = sorted([tmp_path / "main.py", tmp_path / "readme.txt"])
        assert sorted(filtered) == expected

    def test_exclude_from_single_file(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()
        (tmp_path / "test_main.py").touch()
        (tmp_path / "conftest.py").touch()

        exclude_file = tmp_path / "exclude.txt"
        _ = exclude_file.write_text("test_*\nconftest.py\n", encoding="utf-8")

        result = searchpath.all("*.py", ("dir", tmp_path), exclude_from=exclude_file)

        assert result == [tmp_path / "main.py"]

    def test_include_from_nonexistent_file_raises_error(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()
        nonexistent = tmp_path / "missing_patterns.txt"

        with pytest.raises(PatternFileError):
            _ = searchpath.all("**", ("dir", tmp_path), include_from=nonexistent)


class TestEdgeCases:
    def test_default_pattern_matches_all(self, tmp_path: "Path"):
        (tmp_path / "file1.py").touch()
        (tmp_path / "file2.txt").touch()

        result = sorted(searchpath.all("**", ("dir", tmp_path)))

        assert result == sorted([tmp_path / "file1.py", tmp_path / "file2.txt"])

    def test_nested_file_relative_path(self, tmp_path: "Path"):
        subdir = tmp_path / "src" / "utils"
        subdir.mkdir(parents=True)
        (subdir / "helpers.py").touch()

        result = searchpath.match("**/*.py", ("project", tmp_path))

        assert result is not None
        assert result.relative.as_posix() == "src/utils/helpers.py"


class TestSymlinks:
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

        result = sorted(
            searchpath.all("**/*.py", ("dir", tmp_path), follow_symlinks=True)
        )

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

        result = searchpath.all("**/*.py", ("dir", tmp_path), follow_symlinks=False)

        assert tmp_path / "real" / "file.py" in result
        assert tmp_path / "link" / "file.py" not in result
