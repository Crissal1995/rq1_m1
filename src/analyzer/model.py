import abc
import enum
import logging
import os
import pathlib
import re
import shutil
from typing import Generator, Sequence, Union

from src.analyzer import utility

logger = logging.getLogger(__file__)

FILES = pathlib.Path(__file__).parent / "files"


class Tool(abc.ABC):
    """Interface for mutation tools"""

    name: str = ""

    bash_script = None
    output = []

    def __repr__(self):
        return f"{self.name.capitalize()}Tool"

    def __init__(self, project_dir: Union[str, os.PathLike]):
        self.project_dir = pathlib.Path(project_dir)

    def setup(self, **kwargs):
        """Setup tool files, copying them into the project dir"""
        if self.bash_script:
            src = os.fspath(FILES / self.bash_script)
            dst = os.fspath(self.project_dir / self.bash_script)
            shutil.copy(src, dst)

    def run(self, **kwargs):
        """Run the tool via its bash script"""
        script = self.project_dir / self.bash_script

        capture_out = kwargs.get("stdout", False)
        capture_err = kwargs.get("stderr", False)
        utility.bash_script(script, capture_out, capture_err)

    def replace(self, mapping: dict):
        """Overwrite tool flags with actual values"""
        file = self.project_dir / self.bash_script

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
    output = ["jumble_output.txt"]

    def setup(self, **kwargs):
        super(Jumble, self).setup()
        mapping = {
            "tests": {"original": "<REPLACE_TESTS>", "replacement": kwargs["tests"]},
            "class": {"original": "<REPLACE_CLASS>", "replacement": kwargs["class"]},
        }
        self.replace(mapping=mapping)


class Major(Tool):
    """Major tool"""

    name = "major"

    output = ["kill.csv", "mutants.log"]

    def run(self, **kwargs):
        return utility.defects4j_cmd_dirpath(self.project_dir, "mutation")


class Pit(Tool):
    """Pit tool"""

    name = "pit"

    bash_script = "pit.sh"
    output = ["pit_report/mutations.xml"]

    def setup(self, **kwargs):
        super(Pit, self).setup()
        mapping = {
            "tests": {"original": "<TEST_REGEXP>", "replacement": kwargs["tests"]},
            "class": {"original": "<CLASS_REGEXP>", "replacement": kwargs["class"]},
        }
        self.replace(mapping=mapping)


def get_tool(tool_name: str, project_dir: Union[str, os.PathLike]):
    """Utility function to retrieve a tool from a name and a project dir"""
    valid_tools = {
        Judy.name: Judy(project_dir),
        Jumble.name: Jumble(project_dir),
        Major.name: Major(project_dir),
        Pit.name: Pit(project_dir),
    }
    if tool_name not in valid_tools.keys():
        msg = f"Invalid tool provided: {tool_name}. Valid tools are {list(valid_tools.keys())}"
        logger.error(msg)
        raise ValueError(msg)

    return valid_tools[tool_name]


class BugStatus(enum.Enum):
    """Status of a checkout project's bug"""

    BUGGY = "b"
    FIXED = "f"


class Project:
    """Interface of a Defects4j Project"""

    default_backup_tests = "dev_backup"

    def __init__(self, filepath: Union[str, os.PathLike]):
        """Create a (Defects4j compatible) Project"""
        self.filepath = pathlib.Path(filepath)

        config = self.read_defects4j_config()
        self.name = config["pid"]

        if not self.is_compatible_project():
            msg = "Incompatible project! Use only Cli, Gson or Lang"
            logger.error(msg)
            raise ValueError(msg)

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

    def read_defects4j_build_properties(self) -> dict:
        """Read defects4j.build.properties as key-value dictionary"""
        return utility.read_config(self.filepath / "defects4j.build.properties")

    def read_defects4j_config(self) -> dict:
        """Read .defects4j.config as key-value dictionary"""
        return utility.read_config(self.filepath / ".defects4j.config")

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

    def _set_dir_testsuite(self, dirpath: Union[str, os.PathLike]):
        """Set a directory of java files as the project testsuite"""
        src = os.fspath(dirpath)
        dst = os.fspath(self.full_test_dir)
        shutil.rmtree(self.test_dir, ignore_errors=True)
        shutil.copytree(src, dst)

    def project_tests_root(self):
        """Get the root of project tests, based on project name"""
        tests = dict(
            Cli="cli_tests",
            Gson="gson_tests",
            Lang="lang_tests",
        )
        return FILES / tests[self.name]

    def set_dummy_testsuite(self):
        """Set dummy as project testsuite"""
        root = self.project_tests_root()
        return self._set_dir_testsuite(root / "dummy")

    def set_tool_testsuite(self, tool: Tool):
        """Set <tool_name> as project testsuite"""
        root = self.project_tests_root()
        return self._set_dir_testsuite(root / tool.name)

    def get_student_names(self, tool: Tool) -> Generator:
        """Get students' names from formatted java-filename"""
        root = self.project_tests_root()
        tool_dir = root / tool.name
        logger.debug(f"Parsing java files from {tool_dir}")

        pattern = re.compile(r"^([a-zA-Z]+)_([a-zA-Z]+)_([a-zA-Z]\d+)")
        for file in tool_dir.glob("*.java"):
            match = pattern.match(file.name)
            if not match:
                logger.warning(f"Invalid filename found: {file.name}")
                continue
            else:
                logger.debug(f"Match found: {match.groups()}")
                yield match.group(3)

    def _execute_defects4j_cmd(self, command: str, *args, **kwargs):
        """Execute Defects4j command in the right folder"""
        return utility.defects4j_cmd_dirpath(self.filepath, command, *args, **kwargs)

    def execute_tests(self):
        """Execute defects4j test"""
        return self._execute_defects4j_cmd("test")

    def clean(self):
        """Remove compiled files (both src and tests)"""
        target = self.filepath / "target"
        if target.exists():
            shutil.rmtree(os.fspath(target))
            logger.debug("Cleaned project")
        else:
            logger.debug("Project was already clean")

    def compile(self):
        """Execute defects4j compile"""
        return self._execute_defects4j_cmd("compile")

    def execute_coverage(self):
        """Execute defects4j coverage"""
        return self._execute_defects4j_cmd("coverage")

    def coverage(self, tools: Union[Tool, Sequence[Tool]] = None):
        """Execute coverage for selected tools.
        If 'tools' is None, every tool will be selected.
        """

        # if None, take every tool
        if tools is None:
            tools = [
                Judy(self.filepath),
                Jumble(self.filepath),
                Major(self.filepath),
                Pit(self.filepath),
            ]

        # if one tool is given, create list
        if isinstance(tools, Tool):
            tools = [tools]

        logger.info(f"Executing coverage on tools {tools}")

        for tool in tools:
            logger.info(f"Start coverage of tool {tool}")

            # set tool tests for project
            self.set_tool_testsuite(tool)

            # execute defects4j coverage
            # produces coverage.xml
            self.execute_coverage()

            # get student names
            names = list(self.get_student_names(tool))
            str_names = "_".join(names)

            # rename coverage.xml
            fname = "coverage.xml"
            src = self.filepath / fname
            dst = src.with_name(f"{tool.name}_{str_names}_{fname}")
            if src.exists():
                logger.debug(f"Generated {fname}")
                shutil.move(src, dst)
                logger.info(f"Generated {dst.name}")
            else:
                msg = f"Skipping {tool} because {fname} wasn't found - maybe there was an error?"
                logger.warning(msg)

    def get_mutants(self, tools: Union[Tool, Sequence[Tool]] = None, **kwargs):
        """Get all mutants generated by the selected tools.
        If 'tools' is None, every tool will be selected.

        Judy doesn't generate any mutant at all with the dummy test,
        so it will be removed if included.
        """

        # if None, take every tool (except for Judy)
        if tools is None:
            tools = [Jumble(self.filepath), Major(self.filepath), Pit(self.filepath)]

        # if one tool is given, create list
        if isinstance(tools, Tool):
            tools = [tools]

        # remove judy from tools
        if any(isinstance(tool, Judy) for tool in tools):
            logger.warning(
                "Judy doesn't work with this dummy test, so it will be removed!"
            )
            tools = [tool for tool in tools if not isinstance(tool, Judy)]

        logger.info(f"Executing get_mutants on tools {tools}")

        if not tools:
            logger.warning("Empty toolset, exit...")
            return

        # set the testsuite as dummy (empty test class)
        self.set_dummy_testsuite()

        # clean compiled and compile again
        self.clean()
        self.compile()
        logger.info("Project cleaned and compiled")

        # get dummy test name
        dummy_test_name = f"{self.name.upper()}_DUMMY_TEST"
        dummy_test = ".".join([self.package, dummy_test_name])

        # and also class under mutation name
        class_under_mutation = self.relevant_class

        # cycle over tools
        for tool in tools:
            # must specify tests and class for replacement of dummy text
            # inside bash scripts
            if isinstance(tool, (Jumble, Pit)):
                kwargs.update(
                    {
                        "tests": dummy_test,
                        "class": class_under_mutation,
                    }
                )

            logger.debug(f"{tool} kwargs: {kwargs}")

            logger.info(f"Setupping {tool}...")
            tool.setup(**kwargs)
            logger.info(f"Setup of {tool} completed")

            logger.info(f"Running {tool}...")
            # must modify kwargs to don't interfere
            tool.run(**kwargs)
            logger.info(f"Execution of {tool} completed")
