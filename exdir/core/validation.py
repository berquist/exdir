from enum import Enum
import os
import sys
from pathlib import Path, WindowsPath
from unicodedata import category
from . import constants as exob

# `ntpath.isreserved` forbids ASCII control characters
# (https://github.com/python/cpython/blob/7c016deae62308dd1b4e2767fc6abf04857c7843/Lib/ntpath.py#L325)
# while `pathlib.PureWindowsPath.is_reserved` does not, so it is easiest to
# forbid all control characters.
if sys.version_info.minor < 13:
    from pathlib import PureWindowsPath

    def _is_reserved(path):
        return PureWindowsPath(path).is_reserved() or _contains_control_character(path)
else:
    from ntpath import isreserved

    def _is_reserved(path):
        return isreserved(path) or _contains_control_character(path)

VALID_CHARACTERS = ("abcdefghijklmnopqrstuvwxyz1234567890_-.")


class NamingRule(Enum):
    SIMPLE = 1
    STRICT = 2
    THOROUGH = 3
    NONE = 4


def _contains_control_character(s):
    return any(ch for ch in s if category(ch)[0] == "C")


def _assert_unique(parent_path, name):
    try:
        name_str = str(name)
    except UnicodeEncodeError:
        name = name.encode('utf8')

    if (parent_path / name).exists():
        raise RuntimeError(
            "'{}' already exists in '{}'".format(name, parent_path)
        )


def _assert_nonempty(parent_path, name):
    try:
        name_str = str(name)
    except UnicodeEncodeError:
        name_str = name.encode('utf8')

    if len(name_str) < 1:
        raise NameError("Name cannot be empty.")


def _assert_nonreserved(name):
    # NOTE ignore unicode errors, they are not reserved
    try:
        name_str = str(name)
    except UnicodeEncodeError:
        name_str = name.encode('utf8')

    reserved_names = [
        exob.META_FILENAME,
        exob.ATTRIBUTES_FILENAME,
        exob.RAW_FOLDER_NAME
    ]

    if name_str in reserved_names:
        raise NameError(
            "Name cannot be '{}' because it is a reserved filename in Exdir.".format(name_str)
        )

    if _is_reserved(name_str):
        raise NameError(
            "Name cannot be '{}' because it is a reserved filename in Windows.".format(name_str)
        )

def _assert_valid_characters(name):
    try:
        name_str = str(name)
    except UnicodeEncodeError:
        name_str = name.encode('utf8')

    for char in name_str:
        if char not in VALID_CHARACTERS:
            raise NameError(
                "Name '{}' contains invalid character '{}'.\n"
                "Valid characters are:\n{}".format(name_str, char, VALID_CHARACTERS)
            )

def unique(parent_path, name):
    _assert_nonempty(parent_path, name)
    _assert_unique(parent_path, name)


def minimal(parent_path, name):
    _assert_nonempty(parent_path, name)
    _assert_nonreserved(name)
    _assert_unique(parent_path, name)


def strict(parent_path, name):
    _assert_nonreserved(name)
    _assert_unique(parent_path, name)
    _assert_valid_characters(name)

def thorough(parent_path, name):
    _assert_nonempty(parent_path, name)
    _assert_nonreserved(name)
    try:
        name_str = str(name)
    except UnicodeEncodeError:
        name_str = name.encode('utf8')
    name_lower = name_str.lower()
    _assert_valid_characters(name_lower)

    if isinstance(Path(parent_path), WindowsPath):
        # use _assert_unique if we're already on Windows, because it is much faster
        # than the test below
        _assert_unique(parent_path, name)
        return

    # os.listdir is much faster here than os.walk or parent_path.iterdir
    for item in os.listdir(str(parent_path)):
        if name_lower == item.lower():
            raise RuntimeError(
                "A directory with name (case independent) '{}' already exists "
                " and cannot be made according to the naming rule 'thorough'.".format(name)
            )


def none(parent_path, name):
    pass
