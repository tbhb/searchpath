import pytest

from searchpath import PatternSyntaxError, RegexMatcher


class TestRegexMatchingBasic:
    def test_exact_match(self):
        matcher = RegexMatcher()

        assert matcher.matches("config.toml", include=["config.toml"])
        assert not matcher.matches("other.toml", include=["config.toml"])
        assert not matcher.matches("config.toml.bak", include=["config.toml"])

    def test_dot_matches_any_character(self):
        matcher = RegexMatcher()

        assert matcher.matches("a", include=["."])
        assert matcher.matches("X", include=["."])
        assert not matcher.matches("ab", include=["."])

    def test_dot_star_matches_any_characters(self):
        matcher = RegexMatcher()

        assert matcher.matches("", include=[".*"])
        assert matcher.matches("anything", include=[".*"])
        assert matcher.matches("src/main.py", include=[".*"])

    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            pytest.param("a.txt", True, id="first-char-in-class"),
            pytest.param("b.txt", True, id="middle-char-in-class"),
            pytest.param("c.txt", True, id="last-char-in-class"),
            pytest.param("d.txt", False, id="char-not-in-class"),
        ],
    )
    def test_character_class_matches(self, path: str, *, expected: bool):
        matcher = RegexMatcher()
        assert matcher.matches(path, include=["[abc].txt"]) == expected

    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            pytest.param("a", True, id="single-match"),
            pytest.param("aaa", True, id="multiple-matches"),
            pytest.param("", False, id="empty-no-match"),
            pytest.param("b", False, id="different-char-no-match"),
        ],
    )
    def test_quantifier_plus_matches(self, path: str, *, expected: bool):
        matcher = RegexMatcher()
        assert matcher.matches(path, include=["a+"]) == expected

    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            pytest.param("", True, id="empty-matches"),
            pytest.param("a", True, id="single-matches"),
            pytest.param("aaa", True, id="multiple-matches"),
            pytest.param("b", False, id="different-char-no-match"),
        ],
    )
    def test_quantifier_star_matches(self, path: str, *, expected: bool):
        matcher = RegexMatcher()
        assert matcher.matches(path, include=["a*"]) == expected

    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            pytest.param("", True, id="empty-matches"),
            pytest.param("a", True, id="single-matches"),
            pytest.param("aa", False, id="double-no-match"),
        ],
    )
    def test_quantifier_question_matches(self, path: str, *, expected: bool):
        matcher = RegexMatcher()
        assert matcher.matches(path, include=["a?"]) == expected

    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            pytest.param("aaa", True, id="exact-count-matches"),
            pytest.param("aa", False, id="too-few-no-match"),
            pytest.param("aaaa", False, id="too-many-no-match"),
        ],
    )
    def test_quantifier_braces_matches(self, path: str, *, expected: bool):
        matcher = RegexMatcher()
        assert matcher.matches(path, include=["a{3}"]) == expected

    @pytest.mark.parametrize(
        ("path", "expected"),
        [
            pytest.param("foo", True, id="first-alternative"),
            pytest.param("bar", True, id="second-alternative"),
            pytest.param("baz", False, id="non-matching"),
        ],
    )
    def test_alternation_matches(self, path: str, *, expected: bool):
        matcher = RegexMatcher()
        assert matcher.matches(path, include=["foo|bar"]) == expected


class TestRegexMatchingSpecialCases:
    def test_is_dir_parameter_accepted(self):
        matcher = RegexMatcher()

        assert matcher.matches("dir", include=["dir"], is_dir=True)
        assert matcher.matches("dir", include=["dir"], is_dir=False)


class TestRegexMatchingAnchored:
    def test_pattern_must_match_entire_path(self):
        matcher = RegexMatcher()

        # "src" does NOT match "src/main.py" with fullmatch
        assert matcher.matches("src", include=["src"])
        assert not matcher.matches("src/main.py", include=["src"])

    def test_dot_star_matches_path_with_slashes(self):
        matcher = RegexMatcher()

        assert matcher.matches("src/main.py", include=["src/.*"])
        assert matcher.matches("src/a/b/c.py", include=["src/.*"])
        assert not matcher.matches("other/main.py", include=["src/.*"])

    def test_full_path_pattern(self):
        matcher = RegexMatcher()

        assert matcher.matches("src/main.py", include=[r"src/main\.py"])
        assert not matcher.matches("src/main_py", include=[r"src/main\.py"])

    def test_partial_pattern_does_not_match(self):
        matcher = RegexMatcher()

        assert not matcher.matches("prefix_config.toml", include=["config.toml"])
        assert not matcher.matches("config.toml_suffix", include=["config.toml"])
        assert not matcher.matches("dir/config.toml", include=["config.toml"])


class TestRegexMatcherIncludeExclude:
    def test_empty_include_matches_all(self):
        matcher = RegexMatcher()

        assert matcher.matches("anything.txt")
        assert matcher.matches("src/main.py")

    def test_include_filters_paths(self):
        matcher = RegexMatcher()

        assert matcher.matches("main.py", include=[r".*\.py"])
        assert not matcher.matches("main.txt", include=[r".*\.py"])

    def test_exclude_rejects_paths(self):
        matcher = RegexMatcher()

        assert not matcher.matches("test_main.py", exclude=["test_.*"])
        assert matcher.matches("main.py", exclude=["test_.*"])

    def test_include_and_exclude_combined(self):
        matcher = RegexMatcher()

        # Matches *.py but not test_*
        include = [r".*\.py"]
        exclude = ["test_.*"]
        assert matcher.matches("main.py", include=include, exclude=exclude)
        assert not matcher.matches("test_main.py", include=include, exclude=exclude)
        assert not matcher.matches("main.txt", include=include, exclude=exclude)

    def test_multiple_include_patterns(self):
        matcher = RegexMatcher()

        assert matcher.matches("main.py", include=[r".*\.py", r".*\.txt"])
        assert matcher.matches("readme.txt", include=[r".*\.py", r".*\.txt"])
        assert not matcher.matches("config.json", include=[r".*\.py", r".*\.txt"])

    def test_multiple_exclude_patterns(self):
        matcher = RegexMatcher()

        assert not matcher.matches("test_main.py", exclude=["test_.*", ".*_test.py"])
        assert not matcher.matches("main_test.py", exclude=["test_.*", ".*_test.py"])
        assert matcher.matches("main.py", exclude=["test_.*", ".*_test.py"])


class TestRegexMatcherErrors:
    def test_empty_pattern_in_include_raises(self):
        matcher = RegexMatcher()

        with pytest.raises(PatternSyntaxError) as exc_info:
            _ = matcher.matches("file.py", include=[""])

        assert exc_info.value.pattern == ""
        assert "empty pattern" in exc_info.value.message

    def test_empty_pattern_in_exclude_raises(self):
        matcher = RegexMatcher()

        with pytest.raises(PatternSyntaxError) as exc_info:
            _ = matcher.matches("file.py", exclude=[""])

        assert exc_info.value.pattern == ""
        assert "empty pattern" in exc_info.value.message

    def test_invalid_regex_raises(self):
        matcher = RegexMatcher()

        with pytest.raises(PatternSyntaxError) as exc_info:
            _ = matcher.matches("file.py", include=["[invalid"])

        assert exc_info.value.pattern == "[invalid"
        assert exc_info.value.message  # Should have error message from re.error


class TestRegexMatcherProperties:
    def test_supports_negation_false(self):
        matcher = RegexMatcher()

        assert matcher.supports_negation is False

    def test_supports_dir_only_false(self):
        matcher = RegexMatcher()

        assert matcher.supports_dir_only is False
