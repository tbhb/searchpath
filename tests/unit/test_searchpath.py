from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from searchpath import SearchPath

if TYPE_CHECKING:
    from tests.conftest import TreeFactory


class TestEntryParsing:
    @pytest.mark.parametrize(
        ("entry", "expected_path"),
        [
            pytest.param(("user", Path("/home/user")), Path("/home/user"), id="path"),
            pytest.param(("user", "/home/user"), Path("/home/user"), id="string"),
        ],
    )
    def test_tuple_entry_types(
        self, entry: tuple[str, Path | str], expected_path: Path
    ):
        sp = SearchPath(entry)

        assert list(sp) == [expected_path]
        assert sp.scopes == ["user"]

    @pytest.mark.parametrize(
        ("entries", "expected_scopes"),
        [
            pytest.param(
                (Path("/first"), Path("/second")),
                ["dir0", "dir1"],
                id="path-entries",
            ),
            pytest.param(("/first", "/second"), ["dir0", "dir1"], id="string-entries"),
        ],
    )
    def test_bare_entries_auto_named(
        self, entries: tuple[Path | str, ...], expected_scopes: list[str]
    ):
        sp = SearchPath(*entries)

        assert sp.scopes == expected_scopes

    def test_none_entry_ignored(self):
        sp = SearchPath(("a", Path("/a")), None, ("b", Path("/b")))

        assert sp.scopes == ["a", "b"]
        assert list(sp) == [Path("/a"), Path("/b")]

    def test_tuple_with_none_path_ignored(self):
        sp = SearchPath(("a", Path("/a")), ("b", None), ("c", Path("/c")))

        assert sp.scopes == ["a", "c"]

    def test_auto_index_skips_none(self):
        sp = SearchPath(Path("/first"), None, Path("/second"))

        assert sp.scopes == ["dir0", "dir1"]

    def test_mixed_entries(self):
        sp = SearchPath(
            ("explicit", Path("/explicit")),
            Path("/auto1"),
            "/auto2",
            None,
            ("another", "/another"),
        )

        assert sp.scopes == ["explicit", "dir0", "dir1", "another"]

    def test_empty_searchpath(self):
        sp = SearchPath()

        assert list(sp) == []
        assert not sp

    def test_all_none_entries_gives_empty(self):
        sp = SearchPath(None, None, None)

        assert not sp


class TestWithSuffix:
    def test_single_suffix(self):
        sp = SearchPath(("user", Path("/home/user")))
        sp2 = sp.with_suffix(".config")

        assert list(sp2) == [Path("/home/user/.config")]

    def test_multiple_suffix_parts(self):
        sp = SearchPath(("user", Path("/home/user")))
        sp2 = sp.with_suffix(".config", "myapp")

        assert list(sp2) == [Path("/home/user/.config/myapp")]

    def test_preserves_scopes(self):
        sp = SearchPath(("user", Path("/user")), ("system", Path("/sys")))
        sp2 = sp.with_suffix("data")

        assert sp2.scopes == ["user", "system"]

    def test_does_not_mutate_original(self):
        sp = SearchPath(("user", Path("/home/user")))
        original_dirs = list(sp)
        _ = sp.with_suffix(".config")

        assert list(sp) == original_dirs


class TestAdd:
    def test_concatenates_entries(self):
        sp1 = SearchPath(("a", Path("/a")))
        sp2 = SearchPath(("b", Path("/b")))
        combined = sp1 + sp2

        assert list(combined) == [Path("/a"), Path("/b")]
        assert combined.scopes == ["a", "b"]

    def test_preserves_order(self):
        sp1 = SearchPath(("first", Path("/1")), ("second", Path("/2")))
        sp2 = SearchPath(("third", Path("/3")))
        combined = sp1 + sp2

        assert combined.scopes == ["first", "second", "third"]

    def test_does_not_mutate_original(self):
        sp1 = SearchPath(("a", Path("/a")))
        sp2 = SearchPath(("b", Path("/b")))
        original_dirs = list(sp1)
        _ = sp1 + sp2

        assert list(sp1) == original_dirs

    def test_add_empty_searchpath(self):
        sp1 = SearchPath(("a", Path("/a")))
        sp2 = SearchPath()
        combined = sp1 + sp2

        assert list(combined) == [Path("/a")]

    def test_add_to_empty_searchpath(self):
        sp1 = SearchPath()
        sp2 = SearchPath(("b", Path("/b")))
        combined = sp1 + sp2

        assert list(combined) == [Path("/b")]

    def test_add_non_searchpath_returns_not_implemented(self):
        sp = SearchPath(("a", Path("/a")))
        result = sp.__add__([Path("/b")])

        assert result is NotImplemented


class TestFilter:
    def test_filter_keeps_matching(self):
        sp = SearchPath(("a", Path("/short")), ("b", Path("/much/longer/path")))
        filtered = sp.filter(lambda p: p.name == "short")

        assert list(filtered) == [Path("/short")]
        assert filtered.scopes == ["a"]

    def test_filter_removes_non_matching(self):
        sp = SearchPath(("a", Path("/a")), ("b", Path("/b")), ("c", Path("/c")))
        filtered = sp.filter(lambda p: p.name != "b")

        assert list(filtered) == [Path("/a"), Path("/c")]

    def test_filter_all_removed_gives_empty(self):
        sp = SearchPath(("a", Path("/a")), ("b", Path("/b")))
        filtered = sp.filter(lambda _: False)

        assert not filtered

    def test_filter_does_not_mutate_original(self):
        sp = SearchPath(("a", Path("/a")), ("b", Path("/b")))
        original_dirs = list(sp)
        _ = sp.filter(lambda _: False)

        assert list(sp) == original_dirs


class TestExisting:
    def test_existing_filters_nonexistent(self, fake_tree: "TreeFactory"):
        root = fake_tree({"exists": {}})
        existing_dir = root / "exists"
        missing_dir = root / "missing"

        sp = SearchPath(("exists", existing_dir), ("missing", missing_dir))
        filtered = sp.existing()

        assert list(filtered) == [existing_dir]
        assert filtered.scopes == ["exists"]

    def test_existing_with_all_missing(self, fake_tree: "TreeFactory"):
        _ = fake_tree({})
        sp = SearchPath(
            ("a", Path("/definitely/not/existing/path/abc123")),
            ("b", Path("/another/missing/path/xyz789")),
        )
        filtered = sp.existing()

        assert not filtered


class TestIteration:
    def test_iter_yields_paths(self):
        sp = SearchPath(("a", Path("/a")), ("b", Path("/b")))

        assert list(sp) == [Path("/a"), Path("/b")]

    def test_items_yields_tuples(self):
        sp = SearchPath(("a", Path("/a")), ("b", Path("/b")))

        assert list(sp.items()) == [("a", Path("/a")), ("b", Path("/b"))]

    def test_dirs_returns_list(self):
        sp = SearchPath(("a", Path("/a")), ("b", Path("/b")))

        assert sp.dirs == [Path("/a"), Path("/b")]

    def test_scopes_returns_list(self):
        sp = SearchPath(("a", Path("/a")), ("b", Path("/b")))

        assert sp.scopes == ["a", "b"]

    def test_iteration_preserves_order(self):
        paths = [Path(f"/path{i}") for i in range(10)]
        entries = [(f"scope{i}", p) for i, p in enumerate(paths)]
        sp = SearchPath(*entries)

        assert list(sp) == paths


class TestBool:
    @pytest.mark.parametrize(
        ("entries", "expected"),
        [
            pytest.param((("a", Path("/a")),), True, id="non-empty"),
            pytest.param((), False, id="empty"),
        ],
    )
    def test_bool_evaluation(
        self, entries: tuple[tuple[str, Path], ...], *, expected: bool
    ):
        sp = SearchPath(*entries)
        assert bool(sp) == expected

    def test_usable_in_if_statement(self):
        sp = SearchPath(("a", Path("/a")))

        result = "has entries" if sp else "empty"

        assert result == "has entries"


class TestStrAndRepr:
    def test_str_shows_scope_path_pairs(self):
        project_path = Path("/project")
        user_path = Path("/user")
        sp = SearchPath(("project", project_path), ("user", user_path))
        result = str(sp)

        assert f"project: {project_path}" in result
        assert f"user: {user_path}" in result

    def test_str_empty_shows_empty(self):
        sp = SearchPath()

        assert str(sp) == "(empty)"

    def test_repr_contains_searchpath(self):
        sp = SearchPath(("a", Path("/a")))

        assert "SearchPath" in repr(sp)

    def test_repr_contains_entries(self):
        sp = SearchPath(("user", Path("/home/user")))
        result = repr(sp)

        assert "user" in result
        assert "/home/user" in result

    def test_repr_empty(self):
        sp = SearchPath()

        assert repr(sp) == "SearchPath()"
