import io
import json
import os
import re
import xml.etree.ElementTree as ET
from abc import ABC
from collections import Counter
from typing import Sequence, Set, Union

import pandas as pd

from src.mutants.mutants import JudyMutant, JumbleMutant, MajorMutant, Mutant, PitMutant


class ReportError(Exception):
    """Base report error"""


class MissingMutantListException(ReportError):
    """Exception when a mutant list is missing,
    so it's None. This can happen if it's impossible
    to extract information about that particular
    kind of mutants from a report"""


class OverlappingMutantsError(ReportError):
    """Exception raised when there are two
    or more mutants in a sequence that shares the same
    hash key; because collisions are unlikely with SHA256,
    this means that the Mutant interface needs a counter"""


class JudyReportError(ReportError):
    """Judy specialized report error"""


class MissingClassFromJudyReportError(JudyReportError):
    """Exception when the desired class is
    missing from a report"""


class MultipleClassFromJudyReportError(JudyReportError):
    """Error when the desired class is found
    multiple times in a report"""


class JumbleReportError(ReportError):
    """Jumble specialized report error"""


class MajorReportError(ReportError):
    """Major specialized report error"""


class PitReportError(ReportError):
    """Pit specialized report error"""


class WrongTagInPitReportError(PitReportError):
    """Error raised when a non-mutation element is
    encountered parsing an XML Pit report"""


class Report(ABC):
    killed_mutants: Sequence[Mutant] = None
    live_mutants: Sequence[Mutant] = None
    _killed_mutants_count: int = None
    _live_mutants_count: int = None

    @staticmethod
    def find_overlapping_mutants(mutants: Sequence[Mutant]) -> Set[Mutant]:
        """This brief algorithm finds the mutants that are duplicates,
        i.e. their hash value is equal."""
        counter = Counter([hash(mutant) for mutant in mutants])
        duplicates = [h for (h, c) in counter.items() if c > 1]
        return set([m for m in mutants if hash(m) in duplicates])

    def sanity_check(self):
        """Check for overlapping mutants"""
        if self.killed_mutants is not None:
            set_killed = self.find_overlapping_mutants(self.killed_mutants)
            if set_killed:
                raise OverlappingMutantsError(set_killed)

        if self.live_mutants is not None:
            set_live = self.find_overlapping_mutants(self.live_mutants)
            if set_live:
                raise OverlappingMutantsError(set_live)

    @staticmethod
    def _mutant_seq_length(theseq: Sequence):
        if theseq is not None:
            return len(theseq)
        else:
            raise MissingMutantListException()

    @property
    def killed_mutants_count(self) -> int:
        if self._killed_mutants_count is not None:
            return self._killed_mutants_count
        else:
            return self._mutant_seq_length(self.killed_mutants)

    @property
    def live_mutants_count(self) -> int:
        if self._live_mutants_count is not None:
            return self._live_mutants_count
        else:
            return self._mutant_seq_length(self.live_mutants)

    @property
    def total_mutants_count(self) -> int:
        return self.killed_mutants_count + self.live_mutants_count

    def __repr__(self):
        return (
            f"Report(killed_count={self.killed_mutants_count},"
            f" live_count={self.live_mutants_count})"
        )


class ReportSingleFile(Report):
    @classmethod
    def from_file(cls, filepath: Union[str, os.PathLike], **kwargs) -> "Report":
        content = open(filepath).read()
        return cls.extract(content, **kwargs)

    @classmethod
    def extract(cls, content: str, **kwargs) -> "Report":
        raise NotImplementedError


class ReportMultipleFiles(Report):
    @classmethod
    def from_files(
        cls, filepaths: Sequence[Union[str, os.PathLike]], **kwargs
    ) -> "Report":
        contents = [open(fp).read() for fp in filepaths]
        return cls.extract_multiple(contents, **kwargs)

    @classmethod
    def extract_multiple(cls, contents: Sequence[str], **kwargs) -> "Report":
        raise NotImplementedError


class JudyReport(ReportSingleFile):
    def __repr__(self):
        return "Judy" + super(JudyReport, self).__repr__()

    @classmethod
    def extract(cls, content: str, **kwargs) -> "Report":
        class_under_mutation = kwargs["class_under_mutation"]
        judy_dict = json.loads(content)

        thedict = [
            adict
            for adict in judy_dict["classes"]
            if adict["name"] == class_under_mutation
        ]

        if len(thedict) == 0:
            raise MissingClassFromJudyReportError(f"{class_under_mutation} not found!")
        elif len(thedict) > 1:
            raise MultipleClassFromJudyReportError(
                f"{class_under_mutation} found multiple times!"
            )
        else:
            thedict = thedict[0]

        report = cls()
        report._killed_mutants_count = thedict["mutantsKilledCount"]
        report.live_mutants = [
            JudyMutant.from_dict(mdict) for mdict in thedict["notKilledMutant"]
        ]
        report.sanity_check()
        return report


class JumbleReport(ReportSingleFile):
    def __repr__(self):
        return "Jumble" + super(JumbleReport, self).__repr__()

    @classmethod
    def extract(cls, content: str, **kwargs) -> "Report":
        fail_pattern = re.compile(r"M FAIL:\s*([a-zA-Z.]+):(\d+):\s*(.+)")
        start_pattern = re.compile(
            r"Mutation points = \d+, unit test time limit \d+\.\d+s"
        )
        end_pattern = re.compile(r"Jumbling took \d+\.\d+s")
        error_pattern = re.compile(r"Score: \d+%\s*\(?([\w ]+)?")

        # check if there were some errors with Jumble
        errmsg = error_pattern.search(content).group(1)
        if errmsg:
            raise JumbleReportError(errmsg)

        i = start_pattern.search(content).end()
        j = end_pattern.search(content[i:]).start() + i

        # this is the actual text regarding mutations
        text = content[i:j]

        # subtract from text all the fails + get count of them
        killed_text, live_mutants_count = fail_pattern.subn("", text)
        killed_mutants_count = len(re.sub(r"\s+", "", killed_text))

        report = cls()
        report._killed_mutants_count = killed_mutants_count

        report.live_mutants = [
            JumbleMutant.from_tuple(atuple) for atuple in fail_pattern.findall(text)
        ]
        assert report.live_mutants_count == live_mutants_count
        report.sanity_check()

        return report


class MajorReport(ReportMultipleFiles):
    def __repr__(self):
        return "Major" + super(MajorReport, self).__repr__()

    @classmethod
    def extract_multiple(cls, contents: Sequence[str], **kwargs) -> "Report":
        if len(contents) != 2:
            raise MajorReportError(
                "Two files must be provided! kill.csv and mutants.log"
            )

        # if we find the colon, we've found the mutants.log file
        if ":" in contents[0].splitlines()[0]:
            logfile, csvfile = contents
        else:
            csvfile, logfile = contents

        columns = ["MutantNo", "Status"]
        kill_df = pd.read_csv(io.StringIO(csvfile), header=0, names=columns).set_index(
            columns[0]
        )

        columns = [
            "MutantNo",
            "Operator",
            "From",
            "To",
            "Signature",
            "LineNumber",
            "Description",
        ]
        mutants_df = pd.read_csv(
            io.StringIO(logfile), delimiter=":", header=None, names=columns
        ).set_index(columns[0])

        # fix mismatch in length
        if kill_df.empty or len(kill_df) == 0:
            # empty kill csv -> all mutants are live
            kill_df = pd.DataFrame(["LIVE"] * len(mutants_df), columns=["Status"])
            kill_df.index.name = "MutantNo"

        df = mutants_df.join(kill_df)
        live_mutants = df.loc[df.Status == "LIVE"]
        killed_mutants = df.loc[df.index.difference(live_mutants.index)]
        live_count = len(live_mutants)
        killed_count = len(killed_mutants)
        assert len(df) == live_count + killed_count

        report = cls()
        report.live_mutants = []
        report.killed_mutants = []

        for index, row in df.iterrows():
            mutant = MajorMutant.from_series(row)
            if mutant.status == "LIVE":
                report.live_mutants.append(mutant)
            else:
                report.killed_mutants.append(mutant)

        report.sanity_check()
        return report


class PitReport(ReportSingleFile):
    def __repr__(self):
        return "Pit" + super(PitReport, self).__repr__()

    @classmethod
    def extract(cls, content: str, **kwargs) -> "Report":
        root = ET.fromstring(content)
        elements = list(root)

        report = cls()
        report.live_mutants = []
        report.killed_mutants = []

        for element in elements:
            mutant = PitMutant.from_xml_element(element)
            if mutant.detected:
                report.killed_mutants.append(mutant)
            else:
                report.live_mutants.append(mutant)

        report.sanity_check()
        return report
