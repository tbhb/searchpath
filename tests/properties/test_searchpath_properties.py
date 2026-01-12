from pathlib import Path

from hypothesis import given, strategies as st

from searchpath import Entry, SearchPath

# Strategy for generating valid path strings
path_str: st.SearchStrategy[str] = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N"),
        whitelist_characters="_-./",
    ),
    min_size=1,
    max_size=50,
).map(lambda s: "/" + s.lstrip("/"))

# Strategy for scope names
scope_name: st.SearchStrategy[str] = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="_-"),
    min_size=1,
    max_size=20,
)

# Strategy for tuple entries
tuple_entry: st.SearchStrategy[tuple[str, Path]] = st.tuples(
    scope_name, path_str.map(Path)
)

# Strategy for bare path entries
bare_path_entry: st.SearchStrategy[Path] = path_str.map(Path)

# Strategy for any valid entry (including None)
any_entry: st.SearchStrategy[Entry] = st.one_of(
    tuple_entry,
    bare_path_entry,
    st.none(),
)

# Strategy for lists of entries
entry_list: st.SearchStrategy[list[Entry]] = st.lists(
    any_entry, min_size=0, max_size=20
)


def count_non_none(entries: list[Entry]) -> int:
    """Count entries that are not None and don't have None as path."""
    count = 0
    for entry in entries:
        if entry is None:
            continue
        if isinstance(entry, tuple):
            _, path = entry
            if path is None:
                continue
        count += 1
    return count


@given(entries=entry_list)
def test_none_entries_ignored(entries: list[Entry]) -> None:
    sp = SearchPath(*entries)
    expected = count_non_none(entries)

    assert list(sp.items()) == list(sp.items())[:expected]


@given(entries=entry_list, suffix=st.text(min_size=1, max_size=10))
def test_with_suffix_preserves_scopes(entries: list[Entry], suffix: str) -> None:
    sp = SearchPath(*entries)
    sp2 = sp.with_suffix(suffix)

    assert sp2.scopes == sp.scopes


@given(entries=entry_list)
def test_filter_true_preserves_all_entries(entries: list[Entry]) -> None:
    sp = SearchPath(*entries)
    filtered = sp.filter(lambda _: True)

    assert list(filtered) == list(sp)


@given(entries=entry_list)
def test_filter_false_gives_empty(entries: list[Entry]) -> None:
    sp = SearchPath(*entries)
    filtered = sp.filter(lambda _: False)

    assert not filtered


@given(entries1=entry_list, entries2=entry_list)
def test_add_concatenates_in_order(
    entries1: list[Entry], entries2: list[Entry]
) -> None:
    sp1 = SearchPath(*entries1)
    sp2 = SearchPath(*entries2)
    combined = sp1 + sp2

    combined_list = list(combined.items())
    sp1_items = list(sp1.items())
    sp2_items = list(sp2.items())

    assert combined_list == sp1_items + sp2_items


@given(entries=entry_list)
def test_dirs_and_iter_yield_same_paths(entries: list[Entry]) -> None:
    sp = SearchPath(*entries)

    assert sp.dirs == list(sp)


@given(entries=entry_list)
def test_items_yields_scope_path_pairs(entries: list[Entry]) -> None:
    sp = SearchPath(*entries)

    for scope, path in sp.items():
        assert isinstance(scope, str)
        assert isinstance(path, Path)


@given(entries=entry_list)
def test_bool_false_only_when_no_entries(entries: list[Entry]) -> None:
    sp = SearchPath(*entries)

    if count_non_none(entries) == 0:
        assert not sp
    else:
        assert sp


@given(entries=entry_list)
def test_empty_str_only_when_no_entries(entries: list[Entry]) -> None:
    sp = SearchPath(*entries)

    if count_non_none(entries) == 0:
        assert str(sp) == "(empty)"


@given(entries=entry_list)
def test_repr_always_contains_searchpath(entries: list[Entry]) -> None:
    sp = SearchPath(*entries)

    assert "SearchPath" in repr(sp)
