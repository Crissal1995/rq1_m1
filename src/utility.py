import os
import pathlib

from src import model
from src.tools import judy, jumble, major, pit

tools = ["judy", "jumble", "major", "pit"]
subjects = {"cli": "cli32", "lang": "lang53", "gson": "gson15"}
classnames = {
    "cli": "org.apache.commons.cli.HelpFormatter",
    "gson": "com.google.gson.stream.JsonWriter",
    "lang": "org.apache.commons.lang.time.DateUtils",
}


def get_root_dir(tool, subject):
    assert subject in subjects
    return pathlib.Path("data") / subjects[subject] / tool


def get_class_name(subject: str):
    assert subject in classnames
    return classnames[subject]


class ReportFactory:
    def __init__(self, tool: str, subject: str):
        assert tool in tools
        self.tool = tool

        assert subject in subjects
        self.subject = subject

        self.root_dir = get_root_dir(tool, subject)

        all_reports = {
            "judy": {
                "buggy": judy.Report(
                    self.root_dir / "buggy_result.json", classnames[subject]
                ),
                "fixed": judy.Report(
                    self.root_dir / "fixed_result.json", classnames[subject]
                ),
            },
            "jumble": {
                "buggy": jumble.Report(self.root_dir / "buggy_out.txt"),
                "fixed": jumble.Report(self.root_dir / "fixed_out.txt"),
            },
            "major": {
                "buggy": major.Report(
                    self.root_dir / "buggy_mutants.log",
                    self.root_dir / "buggy_kill.csv",
                ),
                "fixed": major.Report(
                    self.root_dir / "fixed_mutants.log",
                    self.root_dir / "fixed_kill.csv",
                ),
            },
            "pit": {
                "buggy": pit.Report(self.root_dir / "buggy_mutations.xml"),
                "fixed": pit.Report(self.root_dir / "fixed_mutations.xml"),
            },
        }
        self.reports = all_reports[tool]
        self.buggy_report = self.get_buggy_report()
        self.fixed_report = self.get_fixed_report()

    def is_valid(self):
        return not any(report is None for report in self.reports.values())

    def get_buggy_report(self):
        report = self.reports["buggy"]
        if report:
            report.makeit()
        return report

    def get_fixed_report(self):
        report = self.reports["fixed"]
        if report:
            report.makeit()
        return report

    def get_difference_set(self):
        comparer = model.MutantsComparer(
            buggy_mutants=self.buggy_report.get_live_mutants(),
            fixed_mutants=self.fixed_report.get_live_mutants(),
            buggy_filepath=self.buggy_filepath(),
            fixed_filepath=self.fixed_filepath(),
        )

        return comparer.get_difference_set()

    def buggy_filepath(self):
        return self.root_dir / ".." / "buggy.java"

    def fixed_filepath(self):
        return self.root_dir / ".." / "fixed.java"

    def write_mutants(self):
        buggy_muts = self.buggy_report.get_live_mutants()
        fixed_muts = self.fixed_report.get_live_mutants()
        diff_muts = self.get_difference_set()

        # sort buggy and fixed for output clarity
        buggy_muts = sorted(buggy_muts, key=lambda m: m.line)
        fixed_muts = sorted(fixed_muts, key=lambda m: m.line)

        output = self.root_dir / "output"
        os.makedirs(output, exist_ok=True)

        for name, mutants in zip(
            ("buggy", "fixed", "diff"), (buggy_muts, fixed_muts, diff_muts)
        ):
            filename = name + ".txt"
            with open(output / filename, "w") as f:
                s = f"{name} set, counting {len(mutants)} mutants\n\n"
                s += "\n".join([str(mutant) for mutant in mutants])
                f.write(s)
