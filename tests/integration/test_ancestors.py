from typing import TYPE_CHECKING

from searchpath import SearchPath

if TYPE_CHECKING:
    from pathlib import Path


class TestAncestorPatternDiscovery:
    def test_exclude_from_ancestors_filters_files(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()
        (tmp_path / "test_main.py").touch()
        _ = (tmp_path / ".searchignore").write_text("test_*\n", encoding="utf-8")

        sp = SearchPath(("dir", tmp_path))
        result = sp.all("*.py", exclude_from_ancestors=".searchignore")

        assert result == [tmp_path / "main.py"]

    def test_include_from_ancestors_filters_files(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()
        (tmp_path / "readme.txt").touch()
        (tmp_path / "config.json").touch()
        _ = (tmp_path / ".searchinclude").write_text("*.py\n*.txt\n", encoding="utf-8")

        sp = SearchPath(("dir", tmp_path))
        result = sorted(sp.all(include_from_ancestors=".searchinclude"))

        filtered = [p for p in result if p.name != ".searchinclude"]
        assert sorted(filtered) == sorted(
            [tmp_path / "main.py", tmp_path / "readme.txt"]
        )

    def test_exclude_from_ancestors_in_subdirectory(self, tmp_path: "Path"):
        subdir = tmp_path / "src"
        subdir.mkdir()
        (subdir / "main.py").touch()
        (subdir / "test_main.py").touch()
        _ = (subdir / ".searchignore").write_text("**/test_*\n", encoding="utf-8")

        (tmp_path / "root.py").touch()
        (tmp_path / "test_root.py").touch()

        sp = SearchPath(("dir", tmp_path))
        result = sorted(sp.all("**/*.py", exclude_from_ancestors=".searchignore"))

        assert tmp_path / "root.py" in result
        assert tmp_path / "test_root.py" in result
        assert subdir / "main.py" in result
        assert subdir / "test_main.py" not in result

    def test_missing_pattern_file_silently_skipped(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()
        (tmp_path / "test_main.py").touch()

        sp = SearchPath(("dir", tmp_path))
        result = sorted(sp.all("*.py", exclude_from_ancestors=".searchignore"))

        assert result == sorted([tmp_path / "main.py", tmp_path / "test_main.py"])

    def test_empty_pattern_file_has_no_effect(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()
        _ = (tmp_path / ".searchignore").write_text("", encoding="utf-8")

        sp = SearchPath(("dir", tmp_path))
        result = sp.all("*.py", exclude_from_ancestors=".searchignore")

        assert result == [tmp_path / "main.py"]

    def test_whitespace_only_pattern_file_has_no_effect(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()
        (tmp_path / "test_main.py").touch()
        _ = (tmp_path / ".searchignore").write_text("   \n\t\n  \n", encoding="utf-8")

        sp = SearchPath(("dir", tmp_path))
        result = sorted(sp.all("*.py", exclude_from_ancestors=".searchignore"))

        assert result == sorted([tmp_path / "main.py", tmp_path / "test_main.py"])

    def test_comments_only_pattern_file_has_no_effect(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()
        (tmp_path / "test_main.py").touch()
        _ = (tmp_path / ".searchignore").write_text(
            "# This is a comment\n# Another comment\n", encoding="utf-8"
        )

        sp = SearchPath(("dir", tmp_path))
        result = sorted(sp.all("*.py", exclude_from_ancestors=".searchignore"))

        assert result == sorted([tmp_path / "main.py", tmp_path / "test_main.py"])


class TestAncestorPatternOverride:
    def test_child_patterns_append_to_parent(self, tmp_path: "Path"):
        _ = (tmp_path / ".searchignore").write_text("test_*\n", encoding="utf-8")

        subdir = tmp_path / "src"
        subdir.mkdir()
        _ = (subdir / ".searchignore").write_text("**/*_helper.py\n", encoding="utf-8")

        (tmp_path / "main.py").touch()
        (tmp_path / "test_main.py").touch()
        (subdir / "utils.py").touch()
        (subdir / "test_utils.py").touch()
        (subdir / "file_helper.py").touch()

        sp = SearchPath(("dir", tmp_path))
        result = sorted(sp.all("**/*.py", exclude_from_ancestors=".searchignore"))

        expected = sorted(
            [tmp_path / "main.py", subdir / "utils.py", subdir / "test_utils.py"]
        )
        assert result == expected

    def test_deep_nesting_collects_all_ancestors(self, tmp_path: "Path"):
        deep = tmp_path / "a" / "b" / "c"
        deep.mkdir(parents=True)

        _ = (tmp_path / ".searchignore").write_text("**/*.log\n", encoding="utf-8")
        _ = (tmp_path / "a" / ".searchignore").write_text(
            "**/*.tmp\n", encoding="utf-8"
        )
        _ = (tmp_path / "a" / "b" / ".searchignore").write_text(
            "**/*.bak\n", encoding="utf-8"
        )

        (deep / "file.py").touch()
        (deep / "file.log").touch()
        (deep / "file.tmp").touch()
        (deep / "file.bak").touch()

        sp = SearchPath(("dir", tmp_path))
        result = list(sp.all("**/*.*", exclude_from_ancestors=".searchignore"))

        py_files = [p for p in result if p.suffix == ".py"]
        assert deep / "file.py" in py_files

        assert deep / "file.log" not in result
        assert deep / "file.tmp" not in result
        assert deep / "file.bak" not in result


class TestAncestorPatternBoundary:
    def test_stops_at_entry_boundary(self, tmp_path: "Path"):
        _ = (tmp_path / ".searchignore").write_text("*.py\n", encoding="utf-8")

        entry = tmp_path / "project"
        entry.mkdir()
        (entry / "main.py").touch()

        sp = SearchPath(("project", entry))
        result = sp.all("*.py", exclude_from_ancestors=".searchignore")

        assert result == [entry / "main.py"]

    def test_pattern_at_entry_root_is_loaded(self, tmp_path: "Path"):
        _ = (tmp_path / ".searchignore").write_text("test_*\n", encoding="utf-8")
        (tmp_path / "main.py").touch()
        (tmp_path / "test_main.py").touch()

        sp = SearchPath(("dir", tmp_path))
        result = sp.all("*.py", exclude_from_ancestors=".searchignore")

        assert result == [tmp_path / "main.py"]

    def test_multiple_entries_have_independent_boundaries(self, tmp_path: "Path"):
        entry1 = tmp_path / "entry1"
        entry2 = tmp_path / "entry2"
        entry1.mkdir()
        entry2.mkdir()

        _ = (entry1 / ".searchignore").write_text("*.txt\n", encoding="utf-8")
        _ = (entry2 / ".searchignore").write_text("*.py\n", encoding="utf-8")

        (entry1 / "file.py").touch()
        (entry1 / "file.txt").touch()
        (entry2 / "file.py").touch()
        (entry2 / "file.txt").touch()

        sp = SearchPath(("e1", entry1), ("e2", entry2))
        result = sp.all("*.*", exclude_from_ancestors=".searchignore")

        assert entry1 / "file.py" in result
        assert entry1 / "file.txt" not in result
        assert entry2 / "file.py" not in result
        assert entry2 / "file.txt" in result


class TestCombinedPatternSources:
    def test_combined_with_inline_patterns(self, tmp_path: "Path"):
        _ = (tmp_path / ".searchignore").write_text("*.log\n", encoding="utf-8")

        (tmp_path / "main.py").touch()
        (tmp_path / "test_main.py").touch()
        (tmp_path / "debug.log").touch()

        sp = SearchPath(("dir", tmp_path))
        result = sp.all(
            "**/*.*",
            exclude="test_*",
            exclude_from_ancestors=".searchignore",
        )

        assert tmp_path / "main.py" in result
        assert tmp_path / "test_main.py" not in result
        assert tmp_path / "debug.log" not in result

    def test_combined_with_file_patterns(self, tmp_path: "Path"):
        _ = (tmp_path / ".searchignore").write_text("*.log\n", encoding="utf-8")

        exclude_file = tmp_path / "exclude.txt"
        _ = exclude_file.write_text("*.tmp\n", encoding="utf-8")

        (tmp_path / "main.py").touch()
        (tmp_path / "debug.log").touch()
        (tmp_path / "cache.tmp").touch()

        sp = SearchPath(("dir", tmp_path))
        result = sp.all(
            "**/*.*",
            exclude_from=exclude_file,
            exclude_from_ancestors=".searchignore",
        )

        assert tmp_path / "main.py" in result
        assert tmp_path / "debug.log" not in result
        assert tmp_path / "cache.tmp" not in result

    def test_precedence_ancestors_then_inline(self, tmp_path: "Path"):
        _ = (tmp_path / ".searchinclude").write_text("*.py\n", encoding="utf-8")

        (tmp_path / "main.py").touch()
        (tmp_path / "test.py").touch()
        (tmp_path / "readme.txt").touch()

        sp = SearchPath(("dir", tmp_path))
        result = sorted(
            sp.all(
                include="*.txt",
                include_from_ancestors=".searchinclude",
            )
        )

        filtered = [p for p in result if p.name != ".searchinclude"]
        assert tmp_path / "main.py" in filtered
        assert tmp_path / "test.py" in filtered
        assert tmp_path / "readme.txt" in filtered

    def test_both_include_and_exclude_from_ancestors(self, tmp_path: "Path"):
        _ = (tmp_path / ".searchinclude").write_text("*.py\n*.txt\n", encoding="utf-8")
        _ = (tmp_path / ".searchignore").write_text("test_*\n", encoding="utf-8")

        (tmp_path / "main.py").touch()
        (tmp_path / "test_main.py").touch()
        (tmp_path / "readme.txt").touch()
        (tmp_path / "config.json").touch()

        sp = SearchPath(("dir", tmp_path))
        result = sorted(
            sp.all(
                include_from_ancestors=".searchinclude",
                exclude_from_ancestors=".searchignore",
            )
        )

        filtered = [
            p for p in result if p.name not in (".searchinclude", ".searchignore")
        ]
        assert tmp_path / "main.py" in filtered
        assert tmp_path / "readme.txt" in filtered
        assert tmp_path / "test_main.py" not in filtered
        assert tmp_path / "config.json" not in filtered


class TestFirstMatchWithAncestors:
    def test_first_with_exclude_from_ancestors(self, tmp_path: "Path"):
        _ = (tmp_path / ".searchignore").write_text("a_*\n", encoding="utf-8")
        (tmp_path / "a_first.py").touch()
        (tmp_path / "b_second.py").touch()

        sp = SearchPath(("dir", tmp_path))
        result = sp.first("*.py", exclude_from_ancestors=".searchignore")

        assert result == tmp_path / "b_second.py"

    def test_match_with_exclude_from_ancestors(self, tmp_path: "Path"):
        _ = (tmp_path / ".searchignore").write_text("a_*\n", encoding="utf-8")
        (tmp_path / "a_first.py").touch()
        (tmp_path / "b_second.py").touch()

        sp = SearchPath(("dir", tmp_path))
        result = sp.match("*.py", exclude_from_ancestors=".searchignore")

        assert result is not None
        assert result.path == tmp_path / "b_second.py"
        assert result.scope == "dir"


class TestPatternCaching:
    def test_pattern_file_read_once_per_search(self, tmp_path: "Path"):
        subdir = tmp_path / "src"
        subdir.mkdir()
        _ = (tmp_path / ".searchignore").write_text("test_*\n", encoding="utf-8")
        (subdir / "a.py").touch()
        (subdir / "b.py").touch()
        (subdir / "c.py").touch()

        sp = SearchPath(("dir", tmp_path))
        result = sp.all("**/*.py", exclude_from_ancestors=".searchignore")

        expected_count = 3
        assert len(result) == expected_count


class TestGitignoreMatcherWithAncestors:
    def test_negation_patterns_with_ancestors(self, tmp_path: "Path"):
        from searchpath import GitignoreMatcher  # noqa: PLC0415

        _ = (tmp_path / ".gitignore").write_text("*.py\n", encoding="utf-8")

        subdir = tmp_path / "src"
        subdir.mkdir()
        _ = (subdir / ".gitignore").write_text("!main.py\n", encoding="utf-8")

        (tmp_path / "root.py").touch()
        (subdir / "main.py").touch()
        (subdir / "test.py").touch()

        sp = SearchPath(("dir", tmp_path))
        result = sp.all(
            "**/*.py",
            exclude_from_ancestors=".gitignore",
            matcher=GitignoreMatcher(),
        )

        assert subdir / "main.py" in result
        assert tmp_path / "root.py" not in result
        assert subdir / "test.py" not in result

    def test_directory_only_patterns(self, tmp_path: "Path"):
        from searchpath import GitignoreMatcher  # noqa: PLC0415

        _ = (tmp_path / ".gitignore").write_text("__pycache__/\n", encoding="utf-8")

        (tmp_path / "main.py").touch()
        cache = tmp_path / "__pycache__"
        cache.mkdir()
        (cache / "main.cpython-310.pyc").touch()

        sp = SearchPath(("dir", tmp_path))
        result = sp.all(
            exclude_from_ancestors=".gitignore",
            matcher=GitignoreMatcher(),
        )

        assert tmp_path / "main.py" in result
        assert cache / "main.cpython-310.pyc" not in result


class TestZeroOverhead:
    def test_no_overhead_when_both_none(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()

        sp = SearchPath(("dir", tmp_path))
        result = sp.all("*.py")

        assert result == [tmp_path / "main.py"]

    def test_no_overhead_first_method(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()

        sp = SearchPath(("dir", tmp_path))
        result = sp.first("*.py")

        assert result == tmp_path / "main.py"

    def test_no_overhead_match_method(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()

        sp = SearchPath(("dir", tmp_path))
        result = sp.match("*.py")

        assert result is not None
        assert result.path == tmp_path / "main.py"

    def test_no_overhead_matches_method(self, tmp_path: "Path"):
        (tmp_path / "main.py").touch()

        sp = SearchPath(("dir", tmp_path))
        result = sp.matches("*.py")

        assert len(result) == 1
        assert result[0].path == tmp_path / "main.py"
