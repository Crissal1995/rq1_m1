import datetime
import json
import os
import re
import xml.etree.ElementTree as ET
from abc import ABC
from collections import Counter
from typing import List, Sequence, Set, Union

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
    killed_mutants: List[Mutant] = None
    live_mutants: List[Mutant] = None
    _killed_mutants_count: int = None
    _live_mutants_count: int = None

    _created_at = datetime.datetime.now()

    def summary(self, mutants: bool = False) -> str:
        buffer = [
            f"Report created at {self._created_at}",
            f"Killed mutants count: {self.killed_mutants_count}",
            f"Live mutants count: {self.live_mutants_count}",
        ]

        for mutants_arr, mutants_str in zip(
            [self.killed_mutants, self.live_mutants], ["Killed", "Live"]
        ):
            if mutants_arr:
                buffer.append(f"{mutants_str} mutants report:")
                if mutants:
                    buffer.append("\n".join(str(m) for m in mutants_arr))
                else:
                    buffer.append("< SNIP >")
            else:
                buffer.append(f"Cannot report {mutants_str} mutants")

        return "\n".join(buffer)

    @staticmethod
    def find_overlapping_mutants(mutants: Sequence[Mutant]) -> Set[Mutant]:
        """This brief algorithm finds the mutants that are duplicates,
        i.e. their hash value is equal."""
        counter = Counter([hash(mutant) for mutant in mutants])
        duplicates = [h for (h, c) in counter.items() if c > 1]
        return set([m for m in mutants if hash(m) in duplicates])

    def sanity_check(self):
        """Check for overlapping mutants"""
        if self.killed_mutants:
            set_killed = self.find_overlapping_mutants(self.killed_mutants)
            if set_killed:
                raise OverlappingMutantsError(set_killed)

        if self.live_mutants:
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
    def __init__(self, filepath: Union[str, os.PathLike], **kwargs):
        super(ReportSingleFile, self).__init__()

        self.filepath = filepath
        self.extract(**kwargs)

        self.sanity_check()

    def extract(self, **kwargs):
        raise NotImplementedError

    def summary(self, mutants: bool = False) -> str:
        summary = super(ReportSingleFile, self).summary()
        fp = str(self.filepath)
        return f"{summary}\nFilepath: {fp}"


class ReportMultipleFiles(Report):
    def __init__(self, *filepaths: Union[str, os.PathLike], **kwargs):
        super(ReportMultipleFiles, self).__init__()

        self.filepaths = list(filepaths)
        self.extract_multiple(**kwargs)

        self.sanity_check()

    def extract_multiple(self, **kwargs):
        raise NotImplementedError

    def summary(self, mutants: bool = False) -> str:
        summary = super(ReportMultipleFiles, self).summary()
        fps = [str(fp) for fp in self.filepaths]
        return f"{summary}\nFilepaths: {fps}"


class JudyReport(ReportSingleFile):
    class_under_mutation: str

    def __init__(self, filepath: Union[str, os.PathLike], class_under_mutation: str):
        self.class_under_mutation = class_under_mutation
        super(JudyReport, self).__init__(
            filepath, class_under_mutation=class_under_mutation
        )

    def __repr__(self):
        return "Judy" + super(JudyReport, self).__repr__()

    def extract(self, **kwargs):
        judy_dict = json.loads(open(self.filepath).read())

        thedict = [
            adict
            for adict in judy_dict["classes"]
            if adict["name"] == self.class_under_mutation
        ]

        if len(thedict) == 0:
            raise MissingClassFromJudyReportError(
                f"{self.class_under_mutation} not found!"
            )
        elif len(thedict) > 1:
            raise MultipleClassFromJudyReportError(
                f"{self.class_under_mutation} found multiple times!"
            )
        else:
            thedict = thedict[0]

        self._killed_mutants_count = thedict["mutantsKilledCount"]
        self.live_mutants = [
            JudyMutant.from_dict(mdict) for mdict in thedict["notKilledMutant"]
        ]


class JumbleReport(ReportSingleFile):
    def __repr__(self):
        return "Jumble" + super(JumbleReport, self).__repr__()

    def extract(self, **kwargs):
        content = open(self.filepath).read()

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

        self._killed_mutants_count = killed_mutants_count

        self.live_mutants = [
            JumbleMutant.from_tuple(atuple) for atuple in fail_pattern.findall(text)
        ]
        assert self.live_mutants_count == live_mutants_count


class MajorReport(ReportMultipleFiles):
    def __init__(
        self,
        mutation_log_fp: Union[str, os.PathLike],
        kill_csv_fp: Union[str, os.PathLike],
    ):
        super(MajorReport, self).__init__(mutation_log_fp, kill_csv_fp)

    def __repr__(self):
        return "Major" + super(MajorReport, self).__repr__()

    def extract_multiple(self, **kwargs):
        if len(self.filepaths) != 2:
            raise MajorReportError(
                "Two files must be provided! kill.csv and mutants.log"
            )

        first_fp, second_fp = self.filepaths
        first_fp_first_line = open(first_fp).read().splitlines()[0]

        # if we find the colon in first file, this is mutants.log file
        if ":" in first_fp_first_line:
            logfile, csvfile = first_fp, second_fp
        # otherwise mutants.log is the second file
        else:
            logfile, csvfile = second_fp, first_fp

        columns = ["MutantNo", "Status"]
        kill_df = pd.read_csv(csvfile, header=0, names=columns).set_index(columns[0])

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
            logfile, delimiter=":", header=None, names=columns
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

        self.live_mutants = []
        self.killed_mutants = []

        for index, row in df.iterrows():
            mutant = MajorMutant.from_series(row)
            if mutant.status == "LIVE":
                self.live_mutants.append(mutant)
            else:
                self.killed_mutants.append(mutant)


class PitReport(ReportSingleFile):
    def __repr__(self):
        return "Pit" + super(PitReport, self).__repr__()

    def extract(self, **kwargs):
        tree = ET.parse(self.filepath)
        root = tree.getroot()
        elements = list(root)

        self.live_mutants = []
        self.killed_mutants = []

        for element in elements:
            mutant = PitMutant.from_xml_element(element)
            if mutant.detected:
                self.killed_mutants.append(mutant)
            else:
                self.live_mutants.append(mutant)
