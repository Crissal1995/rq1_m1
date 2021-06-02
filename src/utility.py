import logging
import os
import pathlib

from src import model
from src.tools import JudyReport, JumbleReport, MajorReport, PitReport

tools = ["judy", "jumble", "major", "pit"]
subjects = {"cli": "cli32", "gson": "gson15", "lang": "lang53"}
classnames = {
    "cli": "org.apache.commons.cli.HelpFormatter",
    "gson": "com.google.gson.stream.JsonWriter",
    "lang": "org.apache.commons.lang.time.DateUtils",
}


def get_root_dir(tool, subject, base_dir):
    assert subject in subjects
    assert pathlib.Path(base_dir).exists()
    return pathlib.Path(base_dir) / subjects[subject] / tool


def get_class_name(subject: str):
    assert subject in classnames
    return classnames[subject]


class ReportFactory:
    def __init__(
        self,
        tool: str,
        subject: str,
        *,
        make_buggy_report=True,
        make_fixed_report=True,
        base_dir="data",
    ):
        assert tool in tools
        self.tool = tool

        assert subject in subjects
        self.subject = subject

        self.root_dir = get_root_dir(tool, subject, base_dir=base_dir)

        logging.debug(f"Root dir is {self.root_dir}")

        all_reports = {
            "judy": {
                "buggy": JudyReport(
                    self.root_dir / "buggy_result.json", get_class_name(subject)
                ),
                "fixed": JudyReport(
                    self.root_dir / "fixed_result.json", get_class_name(subject)
                ),
            },
            "jumble": {
                "buggy": JumbleReport(self.root_dir / "buggy_jumble_output.txt"),
                "fixed": JumbleReport(self.root_dir / "fixed_jumble_output.txt"),
            },
            "major": {
                "buggy": MajorReport(
                    self.root_dir / "buggy_mutants.log",
                    self.root_dir / "buggy_kill.csv",
                ),
                "fixed": MajorReport(
                    self.root_dir / "fixed_mutants.log",
                    self.root_dir / "fixed_kill.csv",
                ),
            },
            "pit": {
                "buggy": PitReport(self.root_dir / "buggy_mutations.xml"),
                "fixed": PitReport(self.root_dir / "fixed_mutations.xml"),
            },
        }
        reports = all_reports[tool]

        self.buggy_report = reports["buggy"]
        if make_buggy_report:
            self.buggy_report.makeit()
            logging.info(str(self.buggy_report))

        self.fixed_report = reports["fixed"]
        if make_fixed_report:
            self.fixed_report.makeit()
            logging.info(str(self.fixed_report))

    def get_difference_set(self):
        comparer = model.MutantsComparer(
            buggy_mutants=self.buggy_report.get_live_mutants(),
            fixed_mutants=self.fixed_report.get_live_mutants(),
            buggy_filepath=self.buggy_filepath(),
            fixed_filepath=self.fixed_filepath(),
            subject=self.subject,
            tool=self.tool,
        )

        return comparer.get_difference_set()

    def buggy_filepath(self):
        return self.root_dir.parent / "buggy.java"

    def fixed_filepath(self):
        return self.root_dir.parent / "fixed.java"

    def write_mutants(self, mutants_type: str):
        if mutants_type == "buggy":
            mutants = self.buggy_report.get_live_mutants()
        elif mutants_type == "fixed":
            mutants = self.fixed_report.get_live_mutants()
        else:
            raise ValueError("Invalid mutants type provided!")

        mutants = sorted(mutants, key=lambda m: m.line)

        output = self.root_dir / "output"
        os.makedirs(output, exist_ok=True)

        name = mutants_type
        filename = name + ".txt"
        outfile = output / filename
        with open(outfile, "w") as f:
            s = f"{name} set, counting {len(mutants)} mutants\n\n"
            s += "\n".join([str(mutant) for mutant in mutants])
            f.write(s)
        logging.info(f"Logged {len(mutants)} mutants on {outfile}")

    def write_all_mutants(self):
        buggy_muts = self.buggy_report.get_live_mutants()
        fixed_muts = self.fixed_report.get_live_mutants()
        diff_muts = self.get_difference_set()

        # sort buggy and fixed for output clarity
        buggy_muts = sorted(buggy_muts, key=lambda m: m.line)
        fixed_muts = sorted(fixed_muts, key=lambda m: m.line)
        diff_muts = sorted(diff_muts, key=lambda m: m.line)

        output = self.root_dir / "output"
        os.makedirs(output, exist_ok=True)

        for name, mutants in zip(
            ("buggy", "fixed", "diff"), (buggy_muts, fixed_muts, diff_muts)
        ):
            filename = name + ".txt"
            outfile = output / filename
            with open(outfile, "w") as f:
                s = f"{name} set, counting {len(mutants)} mutants\n\n"
                s += "\n".join([str(mutant) for mutant in mutants])
                f.write(s)
            logging.info(f"Logged {len(mutants)} mutants on {outfile}")


def get_report(subject: str, tool: str, *args, root: str) -> model.Report:
    root = get_root_dir(tool=tool, subject=subject, base_dir=root)

    # fix files' paths
    args = [root / arg for arg in args]

    subject = subject.lower()
    tool = tool.lower()

    if subject not in subjects:
        raise ValueError(f"{subject} not valid! Valid values are: {subjects}")

    if tool not in tools:
        raise ValueError(f"{tool} not valid! Valid values are: {tools}")

    if not 1 <= len(args) <= 2:
        raise ValueError(
            "Invalid args! Must be at least one element and at most two elements"
        )

    reports = dict(
        judy=JudyReport,
        jumble=JumbleReport,
        major=MajorReport,
        pit=PitReport,
    )

    # specify another argument to judy constructor
    # that is, the classname
    if tool == "judy":
        classname = get_class_name(subject)
        args = args + [classname]

    if tool == "major":
        assert len(args) == 2
        arg1, arg2 = args

        # arg1 must be log file
        # if it's not, then swap them
        if isinstance(arg1, str) and not arg1.lower().endswith(".log"):
            args = (arg2, arg1)

    return reports[tool](*args)
