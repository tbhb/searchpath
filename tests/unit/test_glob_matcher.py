import pytest

from searchpath import GlobMatcher, PatternSyntaxError


class TestGlobMatchingBasic:
    def test_exact_match(self):
        matcher = GlobMatcher()

        assert matcher.matches("config.toml", include=["config.toml"])
        assert not matcher.matches("other.toml", include=["config.toml"])
        assert not matcher.matches("config.toml.bak", include=["config.toml"])

    def test_star_matches_filename(self):
        matcher = GlobMatcher()

        assert matcher.matches("main.py", include=["*.py"])
        assert matcher.matches("test.py", include=["*.py"])
        assert matcher.matches(".py", include=["*.py"])
        assert not matcher.matches("main.txt", include=["*.py"])

    def test_star_does_not_match_slash(self):
        matcher = GlobMatcher()

        assert not matcher.matches("src/main.py", include=["*.py"])
        assert not matcher.matches("a/b/c.py", include=["*.py"])

    def test_double_star_matches_path(self):
        matcher = GlobMatcher()

        assert matcher.matches("src/main.py", include=["**/*.py"])
        assert matcher.matches("main.py", include=["**/*.py"])
        assert matcher.matches("a/b/c/d.py", include=["**/*.py"])

    def test_double_star_matches_deep_path(self):
        matcher = GlobMatcher()

        assert matcher.matches("src/test.py", include=["src/**/test.py"])
        assert matcher.matches("src/a/test.py", include=["src/**/test.py"])
        assert matcher.matches("src/a/b/c/test.py", include=["src/**/test.py"])
        assert not matcher.matches("other/test.py", include=["src/**/test.py"])

    def test_double_star_at_start(self):
        matcher = GlobMatcher()

        assert matcher.matches("config.toml", include=["**/config.toml"])
        assert matcher.matches("dir/config.toml", include=["**/config.toml"])
        assert matcher.matches("a/b/c/config.toml", include=["**/config.toml"])

    def test_question_mark_matches_single_char(self):
        matcher = GlobMatcher()

        assert matcher.matches("file1.txt", include=["file?.txt"])
        assert matcher.matches("filea.txt", include=["file?.txt"])
        assert not matcher.matches("file.txt", include=["file?.txt"])
        assert not matcher.matches("file12.txt", include=["file?.txt"])

    def test_question_mark_does_not_match_slash(self):
        matcher = GlobMatcher()

        assert matcher.matches("aXb", include=["a?b"])
        assert not matcher.matches("a/b", include=["a?b"])

    def test_character_class_matches(self):
        matcher = GlobMatcher()

        assert matcher.matches("a.txt", include=["[abc].txt"])
        assert matcher.matches("b.txt", include=["[abc].txt"])
        assert matcher.matches("c.txt", include=["[abc].txt"])
        assert not matcher.matches("d.txt", include=["[abc].txt"])
        assert not matcher.matches("ab.txt", include=["[abc].txt"])

    def test_character_range_matches(self):
        matcher = GlobMatcher()

        assert matcher.matches("a.txt", include=["[a-z].txt"])
        assert matcher.matches("m.txt", include=["[a-z].txt"])
        assert matcher.matches("z.txt", include=["[a-z].txt"])
        assert not matcher.matches("A.txt", include=["[a-z].txt"])
        assert not matcher.matches("1.txt", include=["[a-z].txt"])

    def test_negated_class_matches(self):
        matcher = GlobMatcher()

        assert not matcher.matches("a.txt", include=["[!abc].txt"])
        assert not matcher.matches("b.txt", include=["[!abc].txt"])
        assert matcher.matches("d.txt", include=["[!abc].txt"])
        assert matcher.matches("x.txt", include=["[!abc].txt"])

    def test_negated_class_with_caret_matches(self):
        matcher = GlobMatcher()

        assert not matcher.matches("a.txt", include=["[^abc].txt"])
        assert matcher.matches("x.txt", include=["[^abc].txt"])


class TestGlobMatchingAnchored:
    def test_pattern_anchored_full_match(self):
        matcher = GlobMatcher()

        assert matcher.matches("config.toml", include=["config.toml"])
        assert not matcher.matches("my-config.toml", include=["config.toml"])
        assert not matcher.matches("config.toml.bak", include=["config.toml"])
        assert not matcher.matches("dir/config.toml", include=["config.toml"])


class TestGlobMatchingSpecialCases:
    def test_is_dir_parameter_accepted(self):
        matcher = GlobMatcher()

        assert matcher.matches("dir", include=["dir"], is_dir=True)
        assert matcher.matches("dir", include=["dir"], is_dir=False)

    def test_special_regex_chars_escaped(self):
        matcher = GlobMatcher()

        assert matcher.matches("file.txt", include=["file.txt"])
        assert not matcher.matches("fileXtxt", include=["file.txt"])

    def test_dollar_sign_escaped(self):
        matcher = GlobMatcher()

        assert matcher.matches("$HOME", include=["$HOME"])

    def test_plus_sign_escaped(self):
        matcher = GlobMatcher()

        assert matcher.matches("c++", include=["c++"])
        assert not matcher.matches("c", include=["c++"])

    def test_bracket_literal_in_class(self):
        matcher = GlobMatcher()

        assert matcher.matches("]", include=["[]]"])

    def test_double_star_at_end_matches_all_descendants(self):
        matcher = GlobMatcher()

        assert matcher.matches("src/file.py", include=["src/**"])
        assert matcher.matches("src/a/b/c.py", include=["src/**"])
        assert not matcher.matches("other/file.py", include=["src/**"])

    def test_double_star_only_matches_all(self):
        matcher = GlobMatcher()

        assert matcher.matches("file.py", include=["**"])
        assert matcher.matches("a/b/c.py", include=["**"])

    def test_consecutive_double_stars(self):
        matcher = GlobMatcher()

        assert matcher.matches("a/b", include=["**/a/**"])
        assert matcher.matches("x/a/y", include=["**/a/**"])
        assert matcher.matches("x/y/a/z/w", include=["**/a/**"])

    def test_mid_pattern_double_star_treated_as_single_star(self):
        # Gitignore-style: ** is only recursive as complete path component
        matcher = GlobMatcher()

        assert matcher.matches("ab", include=["a**b"])
        assert matcher.matches("aXXXb", include=["a**b"])
        # ** is not a complete component, so it should NOT match across /
        assert not matcher.matches("a/b", include=["a**b"])

    def test_negated_class_does_not_match_slash(self):
        # Gitignore-style: [!x] should not match /
        matcher = GlobMatcher()

        assert matcher.matches("b", include=["[!a]"])
        assert matcher.matches("x", include=["[!a]"])
        assert not matcher.matches("a", include=["[!a]"])
        assert not matcher.matches("/", include=["[!a]"])  # Should NOT match

    def test_hyphen_at_start_of_class_is_literal(self):
        matcher = GlobMatcher()

        assert matcher.matches("-.txt", include=["[-ab].txt"])
        assert matcher.matches("a.txt", include=["[-ab].txt"])
        assert not matcher.matches("c.txt", include=["[-ab].txt"])

    def test_caret_not_at_start_is_literal(self):
        matcher = GlobMatcher()

        assert matcher.matches("a.txt", include=["[a^b].txt"])
        assert matcher.matches("^.txt", include=["[a^b].txt"])
        assert matcher.matches("b.txt", include=["[a^b].txt"])


class TestGlobMatcherIncludeExclude:
    def test_empty_include_matches_all(self):
        matcher = GlobMatcher()

        assert matcher.matches("anything.txt")
        assert matcher.matches("src/main.py")

    def test_include_filters_paths(self):
        matcher = GlobMatcher()

        assert matcher.matches("main.py", include=["*.py"])
        assert not matcher.matches("main.txt", include=["*.py"])

    def test_exclude_rejects_paths(self):
        matcher = GlobMatcher()

        assert not matcher.matches("test_main.py", exclude=["test_*"])
        assert matcher.matches("main.py", exclude=["test_*"])

    def test_include_and_exclude_combined(self):
        matcher = GlobMatcher()

        # Matches *.py but not test_*
        assert matcher.matches("main.py", include=["*.py"], exclude=["test_*"])
        assert not matcher.matches("test_main.py", include=["*.py"], exclude=["test_*"])
        assert not matcher.matches("main.txt", include=["*.py"], exclude=["test_*"])

    def test_multiple_include_patterns(self):
        matcher = GlobMatcher()

        assert matcher.matches("main.py", include=["*.py", "*.txt"])
        assert matcher.matches("readme.txt", include=["*.py", "*.txt"])
        assert not matcher.matches("config.json", include=["*.py", "*.txt"])

    def test_multiple_exclude_patterns(self):
        matcher = GlobMatcher()

        assert not matcher.matches("test_main.py", exclude=["test_*", "*_test.py"])
        assert not matcher.matches("main_test.py", exclude=["test_*", "*_test.py"])
        assert matcher.matches("main.py", exclude=["test_*", "*_test.py"])


class TestGlobMatcherErrors:
    def test_empty_pattern_in_include_raises(self):
        matcher = GlobMatcher()

        with pytest.raises(PatternSyntaxError) as exc_info:
            _ = matcher.matches("file.py", include=[""])

        assert exc_info.value.pattern == ""
        assert "empty pattern" in exc_info.value.message

    def test_empty_pattern_in_exclude_raises(self):
        matcher = GlobMatcher()

        with pytest.raises(PatternSyntaxError) as exc_info:
            _ = matcher.matches("file.py", exclude=[""])

        assert exc_info.value.pattern == ""
        assert "empty pattern" in exc_info.value.message

    def test_unclosed_bracket_raises(self):
        matcher = GlobMatcher()

        with pytest.raises(PatternSyntaxError) as exc_info:
            _ = matcher.matches("file.py", include=["[abc"])

        assert exc_info.value.pattern == "[abc"
        assert exc_info.value.position == 0
        assert "unclosed bracket" in exc_info.value.message

    def test_unclosed_bracket_at_end_raises(self):
        matcher = GlobMatcher()
        bracket_position = 4  # Position of '[' in "file["

        with pytest.raises(PatternSyntaxError) as exc_info:
            _ = matcher.matches("file.py", include=["file["])

        assert exc_info.value.position == bracket_position

    def test_unclosed_bracket_after_negation_raises(self):
        matcher = GlobMatcher()

        with pytest.raises(PatternSyntaxError) as exc_info:
            _ = matcher.matches("file.py", include=["[!"])

        assert exc_info.value.pattern == "[!"
        assert exc_info.value.position == 0
        assert "unclosed bracket" in exc_info.value.message

    def test_unclosed_bracket_after_caret_negation_raises(self):
        matcher = GlobMatcher()

        with pytest.raises(PatternSyntaxError) as exc_info:
            _ = matcher.matches("file.py", include=["[^"])

        assert exc_info.value.pattern == "[^"
        assert exc_info.value.position == 0
        assert "unclosed bracket" in exc_info.value.message

    def test_unclosed_bracket_with_trailing_backslash_raises(self):
        matcher = GlobMatcher()
        pattern = "[a\\"  # Pattern: [a\

        with pytest.raises(PatternSyntaxError) as exc_info:
            _ = matcher.matches("file.py", include=[pattern])

        assert exc_info.value.pattern == pattern
        assert exc_info.value.position == 0
        assert "unclosed bracket" in exc_info.value.message


class TestGlobMatcherBracketEscapes:
    def test_backslash_escape_in_bracket(self):
        matcher = GlobMatcher()

        # Pattern [a\]b] - the \] is an escaped ] inside the bracket
        # This matches 'a', ']', or 'b'
        assert matcher.matches("a", include=[r"[a\]b]"])
        assert matcher.matches("]", include=[r"[a\]b]"])
        assert matcher.matches("b", include=[r"[a\]b]"])

    def test_escaped_character_in_bracket(self):
        matcher = GlobMatcher()

        # Pattern [a\nb] - \n is passed through to regex as newline escape
        assert matcher.matches("a", include=[r"[a\nb]"])
        assert matcher.matches("\n", include=[r"[a\nb]"])
        assert matcher.matches("b", include=[r"[a\nb]"])
        assert not matcher.matches("n", include=[r"[a\nb]"])

    def test_escaped_hyphen_in_bracket(self):
        matcher = GlobMatcher()

        # Escaped hyphen should be treated as literal
        assert matcher.matches("-", include=[r"[a\-b]"])
        assert matcher.matches("a", include=[r"[a\-b]"])


class TestGlobMatcherProperties:
    def test_supports_negation_false(self):
        matcher = GlobMatcher()

        assert matcher.supports_negation is False

    def test_supports_dir_only_false(self):
        matcher = GlobMatcher()

        assert matcher.supports_dir_only is False
