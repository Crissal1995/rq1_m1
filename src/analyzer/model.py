import abc
import enum
import logging
import os
import pathlib
import re
import shutil
from typing import Union

logger = logging.getLogger(__file__)

FILES = pathlib.Path(__file__).parent / "files"


class Tool(abc.ABC):
    """Interface for mutation tools"""

    name = None

    bash_script = None
    other = []
    output = []

    @property
    def files(self):
        return [self.bash_script] + self.other

    def setup(self, project_dir, **kwargs):
        """Setup tool files, copying them into the project dir"""
        project_dir = pathlib.Path(project_dir)
        for file in self.files:
            src = os.fspath(FILES / file)
            dst = os.fspath(project_dir / file)
            shutil.copy(src, dst)

    def replace(self, project_dir, mapping: dict):
        """Overwrite tool flags with actual values"""
        project_dir = pathlib.Path(project_dir)
        file = project_dir / self.bash_script

        # read file
        with open(file) as f:
            content = f.read()

        # change its content (flags)
        fixed = content.replace(
            mapping["tests"]["original"], mapping["tests"]["replacement"]
        ).replace(mapping["class"]["original"], mapping["class"]["replacement"])

        # write to file
        with open(file, "w") as f:
            f.write(fixed)


class Judy(Tool):
    """Judy tool"""

    name = "judy"

    bash_script = "judy.sh"
    output = ["result.json"]


class Jumble(Tool):
    """Jumble tool"""

    name = "jumble"

    bash_script = "jumble.sh"
    other = [".jumble_parser.sh", ".test_extract.sh"]
    output = ["jumble_output.txt"]

    def setup(self, project_dir, **kwargs):
        super(Jumble, self).setup(project_dir)
        mapping = {
            "tests": {"original": "<REPLACE_TESTS>", "replacement": kwargs["tests"]},
            "class": {"original": "<REPLACE_CLASS>", "replacement": kwargs["class"]},
        }
        self.replace(project_dir, mapping=mapping)


class Major(Tool):
    """Major tool"""

    name = "major"

    output = ["kill.csv", "mutants.log"]


class Pit(Tool):
    """Pit tool"""

    name = "pit"

    bash_script = "pit.sh"
    output = ["pit_report/mutations.xml"]

    def setup(self, project_dir, **kwargs):
        super(Pit, self).setup(project_dir)
        mapping = {
            "tests": {"original": "<TEST_REGEXP>", "replacement": kwargs["tests"]},
            "class": {"original": "<CLASS_REGEXP>", "replacement": kwargs["class"]},
        }
        self.replace(project_dir, mapping=mapping)


class BugStatus(enum.Enum):
    BUGGY = "b"
    FIXED = "f"


class Project:
    default_backup_tests = "dev_backup"

    def __init__(self, filepath: Union[str, os.PathLike]):
        """Create a (Defects4j compatible) Project"""
        self.filepath = pathlib.Path(filepath)

        config = self.read_defects4j_config()
        self.name = config["pid"]
        assert (
            self.is_compatible_project()
        ), "Incompatible project! Use only Cli, Gson or Lang"

        self.bug, bug_status = re.match(r"(\d+)(\w+)", config["vid"]).groups()
        if bug_status == "b":
            self.bug_status = BugStatus.BUGGY
        elif bug_status == "f":
            self.bug_status = BugStatus.FIXED
        else:
            raise ValueError(f"Invalid bug status found in config ({bug_status})")

        properties = self.read_defects4j_build_properties()
        self.relevant_class = properties["d4j.classes.relevant"]
        self.test_dir = self.filepath / properties["d4j.dir.src.tests"]
        self.package = ".".join(self.relevant_class.split(".")[:-1])
        package_path = self.package.replace(".", "/")
        self.full_test_dir = self.test_dir / package_path

    def is_compatible_project(self):
        return self.name in ("Cli", "Gson", "Lang")

    def __repr__(self):
        return f"{self.name} {self.bug}{self.bug_status.value} [fp: {self.filepath}]"

    @staticmethod
    def _read_config(filepath, separator="=") -> dict:
        """Utility method to read config files"""
        with open(filepath) as f:
            content = f.read()

        result = dict()
        for line in content.splitlines(keepends=False):
            splitted = line.strip().split(separator, maxsplit=1)
            if len(splitted) < 2:
                continue
            else:
                key, value = splitted
                result[key] = value
        return result

    def read_defects4j_build_properties(self) -> dict:
        """Read defects4j.build.properties as key-value dictionary"""
        return self._read_config(self.filepath / "defects4j.build.properties")

    def read_defects4j_config(self) -> dict:
        """Read .defects4j.config as key-value dictionary"""
        return self._read_config(self.filepath / ".defects4j.config")

    def backup_tests(self, name=default_backup_tests):
        """Backup original/dev tests"""
        src = os.fspath(self.test_dir)
        dst = os.fspath(self.test_dir.with_name(name))
        shutil.move(src, dst)

    def restore_tests(self, name=default_backup_tests):
        """Restore original/dev tests"""
        src = os.fspath(self.test_dir.with_name(name))
        dst = os.fspath(self.test_dir)
        shutil.move(src, dst)

    def _set_dir_as_tests(self, dirpath):
        """Set a directory of java files as the project testsuite"""
        dirpath = pathlib.Path(dirpath)
        src = os.fspath(dirpath)
        dst = os.fspath(self.full_test_dir)
        shutil.rmtree(self.test_dir, ignore_errors=True)
        shutil.copytree(src, dst)

    def project_tests_root(self):
        tests = dict(
            Cli="cli_tests",
            Gson="gson_tests",
            Lang="lang_tests",
        )
        return FILES / tests[self.name]

    def set_dummy_as_tests(self):
        root = self.project_tests_root()
        return self._set_dir_as_tests(root / "dummy")

    def set_tool_as_tests(self, tool: Tool):
        root = self.project_tests_root()
        return self._set_dir_as_tests(root / tool.name)
