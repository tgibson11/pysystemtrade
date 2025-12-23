import glob
import datetime
import time

# from importlib import import_module
# from array import array
from importlib.util import find_spec

# import inspect
import os
from pathlib import Path
from typing import List, Tuple

from syscore.dateutils import SECONDS_PER_DAY


"""

    FILE RENAMING AND DELETING

"""


def rename_files_with_extension_in_pathname_as_archive_files(
    pathname: str, extension: str = ".txt", archive_extension: str = ".arch"
):
    """
    Find all the files with a particular extension in a directory, and rename them
     eg thing.txt will become thing_yyyymmdd.txt where yyyymmdd is todays date

    """

    resolved_pathname = get_resolved_pathname(pathname)
    list_of_files = files_with_extension_in_resolved_pathname(
        resolved_pathname, extension=extension
    )

    for filename in list_of_files:
        full_filename = os.path.join(resolved_pathname, filename)
        rename_file_as_archive(
            full_filename, old_extension=extension, archive_extension=archive_extension
        )


def rename_file_as_archive(
    full_filename: str, old_extension: str = ".txt", archive_extension: str = ".arch"
):
    """
    Rename a file with archive suffix and extension
     eg thing.txt will become thing_yyyymmdd.arch where yyyymmdd is todays date

    """

    old_filename = "%s%s" % (full_filename, old_extension)
    date_label = datetime.datetime.now().strftime("%Y%m%d")
    new_filename = "%s_%s%s" % (full_filename, date_label, archive_extension)

    os.rename(old_filename, new_filename)


def delete_old_files_with_extension_in_pathname(
    pathname: str, days_old=30, extension=".arch"
):
    """
    Find all the files with a particular extension in a directory, and delete them
    if older than x days

    """

    resolved_pathname = get_resolved_pathname(pathname)
    list_of_files = glob.glob(resolved_pathname + "/**/*" + extension, recursive=True)

    for filename in list_of_files:
        delete_file_if_too_old(filename, days_old=days_old)


def delete_file_if_too_old(full_filename_with_ext: str, days_old: int = 30):
    file_age = get_file_or_folder_age_in_days(full_filename_with_ext)
    if file_age > days_old:
        print("Deleting %s" % full_filename_with_ext)
        os.remove(full_filename_with_ext)


def get_file_or_folder_age_in_days(full_filename_with_ext: str) -> float:
    # time will be in UNIX seconds
    file_time = os.stat(full_filename_with_ext).st_ctime
    time_now = time.time()

    age_seconds = time_now - file_time
    age_days = age_seconds / SECONDS_PER_DAY

    return age_days


"""

    FILENAME RESOLUTION

"""


def resolve_path_and_filename_for_package(
    path_and_filename: str, separate_filename=None
) -> str:
    """
    A way of resolving relative and absolute filenames
    """

    resolved = get_resolved_pathname(path_and_filename)
    if separate_filename is None:
        path = Path(resolved)
    else:
        path = Path(resolved, separate_filename)

    return str(path)


def get_resolved_pathname(pathname: str) -> str:
    """
    TODO
    """
    if isinstance(pathname, Path):
        # special case when already a Path
        pathname = str(pathname.absolute())

    if "@" in pathname or "::" in pathname:
        # This is an ssh address for rsync - don't change
        return pathname

    path = Path(pathname)
    if path.is_absolute():
        return str(path)
    else:
        return _get_path_for_module(pathname)


def _get_path_for_module(module_name: str) -> str:
    module_spec = find_spec(module_name)
    if module_spec is None:
        raise ModuleNotFoundError(f"Module {module_name} not found")
    path = Path(module_spec.origin)
    return str(path.parent)


"""

    HTML

"""


def write_list_of_lists_as_html_table_in_file(file, list_of_lists: list):
    file.write("<table>")
    for sublist in list_of_lists:
        file.write("  <tr><td>")
        file.write("    </td><td>".join(sublist))
        file.write("  </td></tr>")

    file.write("</table>")


"""

    FILES IN DIRECTORIES

"""


def files_with_extension_in_pathname(pathname: str, extension=".csv") -> List[str]:
    """
    Find all the files with a particular extension in a directory

    """
    resolved_pathname = get_resolved_pathname(pathname)

    return files_with_extension_in_resolved_pathname(
        resolved_pathname, extension=extension
    )


def files_with_extension_in_resolved_pathname(
    resolved_pathname: str, extension=".csv"
) -> List[str]:
    """
    Find all the files with a particular extension in a directory
    """

    file_list = [
        os.path.basename(f) for f in glob.glob(f"{resolved_pathname}/*{extension}")
    ]
    file_list_no_extension = [filename.split(".")[0] for filename in file_list]

    return file_list_no_extension


def full_filename_for_file_in_home_dir(filename: str) -> str:
    pathname = os.path.expanduser("~")

    return os.path.join(pathname, filename)


def does_filename_exist(filename: str) -> bool:
    resolved_filename = resolve_path_and_filename_for_package(filename)
    file_exists = does_resolved_filename_exist(resolved_filename)
    return file_exists


def does_resolved_filename_exist(resolved_filename: str) -> bool:
    file_exists = os.path.isfile(resolved_filename)
    return file_exists
