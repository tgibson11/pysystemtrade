import pytest
import sys
from pathlib import Path
from syscore.fileutils import (
    resolve_path_and_filename_for_package,
    get_resolved_pathname,
)


@pytest.fixture()
def project_dir(request):
    module_path = Path(request.module.__file__)
    return str(module_path.parent.parent.parent.absolute())


@pytest.mark.skipif(sys.platform.startswith("win"), reason="Only runs on unix")
class TestFileUtilsUnix:
    def test_resolve_path_absolute(self):
        actual = get_resolved_pathname("/home/rob")
        assert actual == "/home/rob"

    def test_resolve_path_absolute_trailing(self):
        actual = get_resolved_pathname("/home/rob/")
        assert actual == "/home/rob"

    @pytest.mark.xfail(reason="Cannot work with new implementation")
    def test_resolve_path_absolute_dotted(self):
        actual = get_resolved_pathname(".home.rob")
        assert actual == "/home/rob"

    def test_resolve_path_relative(self, project_dir):
        actual = get_resolved_pathname("syscore.tests")
        assert actual == f"{project_dir}/syscore/tests"

    def test_resolve_path_non_existent(self, project_dir):
        with pytest.raises(ModuleNotFoundError):
            get_resolved_pathname("syscore.testz")

    def test_resolve_dotted_dir_name(self, tmp_path):
        directory = tmp_path / "dir.name.with.dots"
        directory.mkdir()
        file = directory / "hello.txt"
        file.write_text("content", encoding="utf-8")
        resolved_path = get_resolved_pathname(str(file))
        assert resolved_path == f"{tmp_path}/dir.name.with.dots/hello.txt"

    def test_resolve_dotted_file_name(self, tmp_path):
        directory = tmp_path / "dir_name"
        directory.mkdir()
        file = directory / "dotted.filename.txt"
        file.write_text("content", encoding="utf-8")
        resolved_path = get_resolved_pathname(str(file))
        assert resolved_path == f"{tmp_path}/dir_name/dotted.filename.txt"

    def test_resolve_package_separate(self):
        actual = resolve_path_and_filename_for_package("/home/rob/", "file.csv")
        assert actual == "/home/rob/file.csv"

    def test_resolve_package_combined(self):
        actual = resolve_path_and_filename_for_package("/home/rob/file.csv")
        assert actual == "/home/rob/file.csv"

    @pytest.mark.xfail(reason="Cannot work with new implementation")
    def test_resolve_package_combined_dotted(self):
        actual = resolve_path_and_filename_for_package(".home.rob.file.csv")
        assert actual == "/home/rob/file.csv"

    def test_resolve_package_module_separate(self, project_dir):
        actual = resolve_path_and_filename_for_package("syscore.tests", "file.csv")
        assert actual == f"{project_dir}/syscore/tests/file.csv"

    def test_resolve_package_module_combined(self, project_dir):
        actual = resolve_path_and_filename_for_package(
            "syscore.tests.pricetestdata.csv"
        )
        assert actual == f"{project_dir}/syscore/tests/pricetestdata.csv"

    def test_resolve_package_module_combined_dotted_filename(self, project_dir):
        actual = resolve_path_and_filename_for_package(
            "syscore.tests.price.test.data.csv"
        )
        assert actual == f"{project_dir}/syscore/tests/price.test.data.csv"

    def test_resolve_resolve_path_and_filename_for_package_with_dotted_dir_name(
        self, tmp_path
    ):
        directory = tmp_path / "dir.name.with.dots"
        directory.mkdir()
        file = directory / "hello.txt"
        file.write_text("content", encoding="utf-8")
        resolved_path = resolve_path_and_filename_for_package(
            f"{tmp_path}/dir.name.with.dots", "hello.txt"
        )
        assert resolved_path == f"{tmp_path}/dir.name.with.dots/hello.txt"

    def test_resolve_resolve_path_and_filename_for_package_with_dotted_file_name(
        self, tmp_path
    ):
        directory = tmp_path / "dir_name"
        directory.mkdir()
        file = directory / "dotted.filename.txt"
        file.write_text("content", encoding="utf-8")
        resolved_path = resolve_path_and_filename_for_package(
            f"{tmp_path}/dir_name/dotted.filename.txt"
        )
        assert resolved_path == f"{tmp_path}/dir_name/dotted.filename.txt"


@pytest.mark.skipif(sys.platform in ["linux", "darwin"], reason="Only runs on windows")
class TestFileUtilsWindoze:
    def test_resolve_path_absolute(self):
        actual = get_resolved_pathname("C:\\home\\rob\\")
        assert actual == "C:\\home\\rob"

    def test_resolve_path_absolute_trailing(self):
        actual = get_resolved_pathname("C:\\home\\rob\\")
        assert actual == "C:\\home\\rob"

    @pytest.mark.xfail(reason="Cannot work with new implementation")
    def test_resolve_path_absolute_dotted(self):
        actual = get_resolved_pathname(".home.rob")
        assert actual == "\\home\\rob"

    def test_resolve_path_relative(self, project_dir):
        actual = get_resolved_pathname("syscore.tests")
        assert actual == f"{project_dir}\\syscore\\tests"

    def test_resolve_path_non_existent(self, project_dir):
        with pytest.raises(ModuleNotFoundError):
            get_resolved_pathname("syscore.testz")

    def test_resolve_dotted_dir_name(self, tmp_path):
        directory = tmp_path / "dir.name.with.dots"
        directory.mkdir()
        file = directory / "hello.txt"
        file.write_text("content", encoding="utf-8")
        resolved_path = get_resolved_pathname(str(file))
        assert resolved_path == f"{tmp_path}\\dir.name.with.dots\\hello.txt"

    def test_resolve_dotted_file_name(self, tmp_path):
        directory = tmp_path / "dir_name"
        directory.mkdir()
        file = directory / "dotted.filename.txt"
        file.write_text("content", encoding="utf-8")
        resolved_path = get_resolved_pathname(str(file))
        assert resolved_path == f"{tmp_path}\\dir_name\\dotted.filename.txt"

    def test_resolve_package_separate(self):
        actual = resolve_path_and_filename_for_package("C:\\home\\rob\\", "file.csv")
        assert actual == "C:\\home\\rob\\file.csv"

    def test_resolve_package_combined(self):
        actual = resolve_path_and_filename_for_package("C:\\home\\rob\\file.csv")
        assert actual == "C:\\home\\rob\\file.csv"

    @pytest.mark.xfail(reason="Cannot work with new implementation")
    def test_resolve_package_combined_dotted(self):
        actual = resolve_path_and_filename_for_package(".home.rob.file.csv")
        assert actual == "\\home\\rob\\file.csv"

    def test_resolve_package_module_separate(self, project_dir):
        actual = resolve_path_and_filename_for_package("syscore.tests", "file.csv")
        assert actual == f"{project_dir}\\syscore\\tests\\file.csv"

    def test_resolve_package_module_combined(self, project_dir):
        actual = resolve_path_and_filename_for_package(
            "syscore.tests.pricetestdata.csv"
        )
        assert actual == f"{project_dir}\\syscore\\tests\\pricetestdata.csv"

    def test_resolve_package_module_combined_dotted_filename(self, project_dir):
        actual = resolve_path_and_filename_for_package(
            "syscore.tests.price.test.data.csv"
        )
        assert actual == f"{project_dir}\\syscore\\tests\\price.test.data.csv"

    def test_resolve_resolve_path_and_filename_for_package_with_dotted_dir_name(
        self, tmp_path
    ):
        directory = tmp_path / "dir.name.with.dots"
        directory.mkdir()
        file = directory / "hello.txt"
        file.write_text("content", encoding="utf-8")
        resolved_path = resolve_path_and_filename_for_package(
            f"{tmp_path}\\dir.name.with.dots", "hello.txt"
        )
        assert resolved_path == f"{tmp_path}\\dir.name.with.dots\\hello.txt"

    def test_resolve_resolve_path_and_filename_for_package_with_dotted_file_name(
        self, tmp_path
    ):
        directory = tmp_path / "dir_name"
        directory.mkdir()
        file = directory / "dotted.filename.txt"
        file.write_text("content", encoding="utf-8")
        resolved_path = resolve_path_and_filename_for_package(
            f"{tmp_path}\\dir_name\\dotted.filename.txt"
        )
        assert resolved_path == f"{tmp_path}\\dir_name\\dotted.filename.txt"
