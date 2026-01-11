import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pytest_codspeed.plugin import BenchmarkFixture
    from pytest_mock import MockerFixture


class TestBenchImportTime:
    def test_import_time_searchpath(
        self, benchmark: "BenchmarkFixture", mocker: "MockerFixture"
    ) -> None:
        def import_searchpath():
            _ = mocker.patch("sys.modules", {})
            _ = importlib.import_module("searchpath", "test_bench_imports")

        benchmark(import_searchpath)
