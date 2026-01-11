import pytest

from searchpath import GitignoreMatcher, PatternSyntaxError


class TestGitignoreMatchingBasic:
    def test_exact_match(self):
        matcher = GitignoreMatcher()

        assert matcher.matches("config.toml", include=["config.toml"])
        assert not matcher.matches("other.toml", include=["config.toml"])

    def test_star_wildcard_matches_within_component(self):
        matcher = GitignoreMatcher()

        assert matcher.matches("main.py", include=["*.py"])
        assert matcher.matches("test.py", include=["*.py"])
        assert not matcher.matches("main.txt", include=["*.py"])

    def test_star_wildcard_unanchored_matches_anywhere(self):
        matcher = GitignoreMatcher()

        # In gitignore, unanchored patterns like *.py match anywhere in the path
        # This differs from GlobMatcher which requires explicit ** for recursion
        assert matcher.matches("src/main.py", include=["*.py"])
        assert matcher.matches("main.py", include=["*.py"])

    def test_question_mark_wildcard(self):
        matcher = GitignoreMatcher()

        assert matcher.matches("a.py", include=["?.py"])
        assert matcher.matches("b.py", include=["?.py"])
        assert not matcher.matches("ab.py", include=["?.py"])
        assert not matcher.matches(".py", include=["?.py"])

    def test_character_class_matches(self):
        matcher = GitignoreMatcher()

        assert matcher.matches("a.txt", include=["[abc].txt"])
        assert matcher.matches("b.txt", include=["[abc].txt"])
        assert matcher.matches("c.txt", include=["[abc].txt"])
        assert not matcher.matches("d.txt", include=["[abc].txt"])

    def test_double_star_recursive_match(self):
        matcher = GitignoreMatcher()

        assert matcher.matches("main.py", include=["**/*.py"])
        assert matcher.matches("src/main.py", include=["**/*.py"])
        assert matcher.matches("src/sub/main.py", include=["**/*.py"])
        assert not matcher.matches("main.txt", include=["**/*.py"])

    def test_double_star_at_end(self):
        matcher = GitignoreMatcher()

        assert matcher.matches("src/file.py", include=["src/**"])
        assert matcher.matches("src/sub/file.py", include=["src/**"])
        assert not matcher.matches("other/file.py", include=["src/**"])

    def test_double_star_in_middle(self):
        matcher = GitignoreMatcher()

        assert matcher.matches("a/b/c.py", include=["a/**/c.py"])
        assert matcher.matches("a/x/y/c.py", include=["a/**/c.py"])
        assert matcher.matches("a/c.py", include=["a/**/c.py"])


class TestGitignoreMatchingNegation:
    def test_negation_re_includes_after_exclude(self):
        matcher = GitignoreMatcher()

        # In gitignore, !pattern re-includes a previously excluded path
        # With include patterns: "*.log" matches all log files,
        # "!important.log" negates (un-matches) important.log
        patterns = ["*.log", "!important.log"]
        assert matcher.matches("debug.log", include=patterns)
        assert not matcher.matches("important.log", include=patterns)

    def test_negation_only_affects_previous_patterns(self):
        matcher = GitignoreMatcher()

        # Order matters: negation applies to patterns before it
        patterns = ["!important.log", "*.log"]
        # important.log would be negated first, then matched by *.log
        assert matcher.matches("important.log", include=patterns)


class TestGitignoreMatchingDirOnly:
    def test_dir_only_pattern_does_not_match_file(self):
        matcher = GitignoreMatcher()

        # Pattern ending in / is a directory-only pattern
        # It should not match a file path (without trailing /)
        assert not matcher.matches("__pycache__", include=["__pycache__/"])

    def test_dir_only_pattern_matches_directory_path(self):
        matcher = GitignoreMatcher()

        # Directory-only pattern matches when path ends with /
        # pathspec expects trailing slash on directory paths
        assert matcher.matches("__pycache__/", include=["__pycache__/"])


class TestGitignoreMatchingAnchored:
    def test_anchored_pattern_matches_only_root(self):
        matcher = GitignoreMatcher()

        # Pattern starting with / matches only at root
        assert matcher.matches("root.py", include=["/root.py"])
        assert not matcher.matches("subdir/root.py", include=["/root.py"])

    def test_unanchored_pattern_matches_anywhere(self):
        matcher = GitignoreMatcher()

        # Pattern without leading / matches anywhere
        assert matcher.matches("root.py", include=["root.py"])
        assert matcher.matches("subdir/root.py", include=["root.py"])


class TestGitignoreMatcherIncludeExclude:
    def test_empty_include_matches_all(self):
        matcher = GitignoreMatcher()

        assert matcher.matches("anything.txt")
        assert matcher.matches("src/main.py")

    def test_include_filters_paths(self):
        matcher = GitignoreMatcher()

        assert matcher.matches("main.py", include=["*.py"])
        assert not matcher.matches("main.txt", include=["*.py"])

    def test_exclude_rejects_paths(self):
        matcher = GitignoreMatcher()

        assert not matcher.matches("test_main.py", exclude=["test_*"])
        assert matcher.matches("main.py", exclude=["test_*"])

    def test_include_and_exclude_combined(self):
        matcher = GitignoreMatcher()

        # Matches **/*.py but not test_*
        include = ["**/*.py"]
        exclude = ["test_*"]
        assert matcher.matches("main.py", include=include, exclude=exclude)
        assert not matcher.matches("test_main.py", include=include, exclude=exclude)
        assert not matcher.matches("main.txt", include=include, exclude=exclude)

    def test_multiple_include_patterns(self):
        matcher = GitignoreMatcher()

        assert matcher.matches("main.py", include=["*.py", "*.txt"])
        assert matcher.matches("readme.txt", include=["*.py", "*.txt"])
        assert not matcher.matches("config.json", include=["*.py", "*.txt"])

    def test_multiple_exclude_patterns(self):
        matcher = GitignoreMatcher()

        assert not matcher.matches("test_main.py", exclude=["test_*", "*_test.py"])
        assert not matcher.matches("main_test.py", exclude=["test_*", "*_test.py"])
        assert matcher.matches("main.py", exclude=["test_*", "*_test.py"])


class TestGitignoreMatcherSpecialCases:
    def test_is_dir_parameter_accepted(self):
        matcher = GitignoreMatcher()

        # is_dir parameter should be accepted without error
        assert matcher.matches("dir", include=["dir"], is_dir=True)
        assert matcher.matches("dir", include=["dir"], is_dir=False)


class TestGitignoreMatcherErrors:
    def test_empty_pattern_in_include_raises(self):
        matcher = GitignoreMatcher()

        with pytest.raises(PatternSyntaxError) as exc_info:
            _ = matcher.matches("file.py", include=[""])

        assert exc_info.value.pattern == ""
        assert "empty pattern" in exc_info.value.message

    def test_empty_pattern_in_exclude_raises(self):
        matcher = GitignoreMatcher()

        with pytest.raises(PatternSyntaxError) as exc_info:
            _ = matcher.matches("file.py", exclude=[""])

        assert exc_info.value.pattern == ""
        assert "empty pattern" in exc_info.value.message

    def test_empty_pattern_among_valid_patterns_raises(self):
        matcher = GitignoreMatcher()

        with pytest.raises(PatternSyntaxError) as exc_info:
            _ = matcher.matches("file.py", include=["*.py", "", "*.txt"])

        assert exc_info.value.pattern == ""
        assert "empty pattern" in exc_info.value.message


class TestGitignoreMatcherProperties:
    def test_supports_negation_true(self):
        matcher = GitignoreMatcher()

        assert matcher.supports_negation is True

    def test_supports_dir_only_true(self):
        matcher = GitignoreMatcher()

        assert matcher.supports_dir_only is True
