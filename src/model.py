import datetime
import difflib
import logging
import os
import pathlib
from abc import ABC
from collections import Counter
from typing import Sequence

import pandas as pd

from src.exception import OverlappingMutantError


class Mutant(ABC):
    def __init__(self, line: int):
        # assert line >= 0
        self.line = line
        self.original_line = line

    @property
    def hash_tuple(self) -> tuple:
        raise NotImplementedError

    def __hash__(self):
        return hash(self.hash_tuple)

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        return all(el1 == el2 for (el1, el2) in zip(self.hash_tuple, other.hash_tuple))

    def __repr__(self):
        return f"Mutant{self.hash_tuple}"


class GitDiff:
    def __init__(
        self,
        source_line: int,
        source_count: int,
        destination_line: int,
        destination_count: int,
        lines: [str],
    ):
        self.source_line = source_line
        self.source_count = source_count
        self.destination_line = destination_line
        self.destination_count = destination_count
        self.lines = lines

    @property
    def delta(self):
        return self.source_count - self.destination_count

    def __repr__(self):
        return (
            f"GitDiff({self.source_line}, {self.source_count}, "
            f"{self.destination_line}, {self.destination_count}); delta={self.delta}"
        )

    def __str__(self):
        return "".join(self.lines)

    @classmethod
    def gen_diffs(cls, src: str, dst: str):
        """Get a generator of GitDiff elements"""
        src = pathlib.Path(src)
        dst = pathlib.Path(dst)

        src_lines = open(src).readlines()
        dst_lines = open(dst).readlines()

        diffs_gen = difflib.unified_diff(src_lines, dst_lines, n=0)
        differences = list(diffs_gen)

        start_indices = [
            i for i, line in enumerate(differences) if line.startswith("@@")
        ]

        for i, index in enumerate(start_indices):
            diffline = differences[index]
            lines = diffline.split()[1:3]

            source_line_list = lines[0].split(",")
            if len(source_line_list) == 2:
                source_count = int(source_line_list[1])
            else:
                source_count = 1
            source_line = int(source_line_list[0].replace("-", ""))

            dest_line_list = lines[1].split(",")
            if len(dest_line_list) == 2:
                dest_count = int(dest_line_list[1])
            else:
                dest_count = 1
            dest_line = int(dest_line_list[0].replace("+", ""))

            if i != len(start_indices) - 1:
                limit = start_indices[i + 1]
            else:
                limit = len(differences)
            block_diffs = differences[index:limit]
            assert len(block_diffs) == source_count + dest_count + 1
            yield cls(
                source_line=source_line,
                source_count=source_count,
                destination_line=dest_line,
                destination_count=dest_count,
                lines=block_diffs,
            )


class MutantsComparerSets:
    def __init__(self, first_seq: Sequence[Mutant], second_seq: Sequence[Mutant]):
        self.first_seq = first_seq
        self.first_set = set(first_seq)
        assert len(self.first_set) == len(self.first_seq)

        self.second_seq = second_seq
        self.second_set = set(second_seq)
        assert len(self.second_set) == len(self.second_seq)

    @staticmethod
    def correct_lines(mutants: Sequence[Mutant], src_filepath: str, dst_filepath: str):
        """This function should be called if a mutants set should be corrected
        because of mismatching lines (e.g. a buggy and a fixed version of the same Java file)."""

        # sort mutants based on their mutation line
        sorted_mutants = sorted(mutants, key=lambda mutant: mutant.line)

        for diff in GitDiff.gen_diffs(src_filepath, dst_filepath):
            logging.info(f"Difference found: {repr(diff)}")

            # skip empty deltas
            if diff.delta == 0:
                logging.info("Empty difference delta, skip it")
                continue
            # else get mutants that will be affected by this change
            affected_mutants = [
                mutation
                for mutation in sorted_mutants
                if mutation.line >= diff.source_line
            ]
            logging.info(
                f"Changing the 'line' attribute of {len(affected_mutants)} mutants"
            )

            for mutation in affected_mutants:
                logging.debug(
                    f"From line {mutation.line} to line "
                    f"{mutation.line + diff.delta} - {repr(mutation)}"
                )
                mutation.line += diff.delta

        return sorted_mutants

    @staticmethod
    def find_duplicate_mutants(mutants: Sequence[Mutant]):
        counter = Counter([hash(mutant) for mutant in mutants])
        return [
            mutant
            for (mutant, (hash_, count)) in zip(mutants, counter.items())
            if count > 1
        ]

    def summary(self, dirname: str = None):
        """Print a summary and write on files the output"""
        now = str(datetime.datetime.now()).replace(":", ".").replace(".", "-")
        path = pathlib.Path("result")
        thedir = f"{dirname} {now}" if dirname else now
        path /= thedir

        l1_seq = len(self.first_seq)
        l1_set = len(self.first_set)

        l2_seq = len(self.second_seq)
        l2_set = len(self.second_set)

        # mismatch is a binary flag variable
        mismatch = 0

        # set bits
        if l1_set != l1_seq:
            mismatch |= 1
        if l2_set != l2_seq:
            mismatch |= 2

        # if any of these bit is high, error found
        if mismatch & 3:
            path = pathlib.Path("overlapping") / now
            os.makedirs(path, exist_ok=True)

            msg = ""
            if mismatch & 1:
                mutants = self.find_duplicate_mutants(self.first_seq)
                with open(path / "seq1.txt", "w") as f:
                    f.write("\n\n".join(mutants))
                msg += "Written overlapping mutants on seq1.txt\n"

            if mismatch & 2:
                mutants = self.find_duplicate_mutants(self.second_seq)
                with open(path / "seq2.txt", "w") as f:
                    f.write("\n\n".join(mutants))
                msg += "Written overlapping mutants on seq2.txt\n"

            raise OverlappingMutantError(msg)

        os.makedirs(path)

        # original
        # first set
        with open(path / "first_set.txt", "w") as f:
            f.write("\n\n".join([str(m) for m in self.first_seq]))

        # second set
        with open(path / "second_set.txt", "w") as f:
            f.write("\n\n".join([str(m) for m in self.second_seq]))

        # intersection
        intersection = list(self.first_set & self.second_set)
        with open(path / "intersection.txt", "w") as f:
            f.write("\n\n".join([str(m) for m in intersection]))

        # union
        union = list(self.first_set | self.second_set)
        with open(path / "union.txt", "w") as f:
            f.write("\n\n".join([str(m) for m in union]))

        # diff 1-2
        first_diff = list(self.first_set - self.second_set)
        with open(path / "first_diff.txt", "w") as f:
            f.write("\n\n".join([str(m) for m in first_diff]))

        # diff 2-1
        second_diff = list(self.second_set - self.first_set)
        with open(path / "second_diff.txt", "w") as f:
            f.write("\n\n".join([str(m) for m in second_diff]))

        # xor
        xor = list(self.first_set ^ self.second_set)
        with open(path / "xor.txt", "w") as f:
            f.write("\n\n".join([str(m) for m in xor]))

        msg = (
            f"SUMMARY LIVE MUTANTS - lengths:\n"
            f"First set: {len(self.first_seq)}\n"
            f"Second set: {len(self.second_seq)}\n"
            f"Intersection: {len(intersection)}\n"
            f"Union: {len(union)}\n"
            f"First - Second: {len(first_diff)}\n"
            f"Second - First: {len(second_diff)}\n"
            f"Xor: {len(xor)}\n"
            f"(now: {now})"
        )
        logging.info(msg)

    def get_series(
        self, name: str = None, *, kind: str = "first_diff", data_type: str = "original"
    ) -> pd.Series:
        kind = kind.lower()
        kinds = (
            "first",
            "second",
            "union",
            "intersection",
            "first_diff",
            "second_diff",
            "xor",
        )
        kinds = sorted(kinds)
        if kind not in kinds:
            raise ValueError(f"Kind '{kind}' must be one of {kinds}")

        data_type = data_type.lower()
        data_types = ("original", "hash")
        data_types = sorted(data_types)
        if data_type not in data_types:
            raise ValueError(f"Data type '{data_type}' must be one of {data_types}")

        data_dict = {
            "first": self.first_seq,
            "second": self.second_seq,
            "intersection": list(self.first_set & self.second_set),
            "union": list(self.first_set | self.second_set),
            "xor": list(self.first_set ^ self.second_set),
            "first_diff": list(self.first_set - self.second_set),
            "second_diff": list(self.second_set - self.first_set),
        }

        original_data = data_dict[kind]
        hash_data = [hash(mutant) for mutant in original_data]

        if data_type == "original":
            data = original_data
        elif data_type == "hash":
            data = hash_data
        else:
            raise AssertionError("Should not reach this LoC")

        return pd.Series(data=data, name=name or kind, index=hash_data)


class MutantsComparer:
    def __init__(
        self,
        buggy_mutants: [Mutant],
        fixed_mutants: [Mutant],
        buggy_filepath: [str, os.PathLike],
        fixed_filepath: [str, os.PathLike],
        subject: str = None,
        tool: str = None,
    ):
        self.buggy_mutants: [Mutant] = buggy_mutants
        self.fixed_mutants: [Mutant] = fixed_mutants

        self.buggy_filepath = buggy_filepath
        self.fixed_filepath = fixed_filepath

        self.subject = subject
        self.tool = tool

    def get_git_diffs_gen(self):
        # check for user errors
        buggy_filepath = pathlib.Path(self.buggy_filepath)
        fixed_filepath = pathlib.Path(self.fixed_filepath)

        if not all(
            path.exists() and path.is_file()
            for path in (buggy_filepath, fixed_filepath)
        ):
            err = "Missing source java files!"
            if self.subject:
                err += f" Subject: {self.subject}"
            raise FileNotFoundError(err)

        buggy_lines = open(buggy_filepath).readlines()
        fixed_lines = open(fixed_filepath).readlines()

        differences = list(
            difflib.unified_diff(
                buggy_lines,
                fixed_lines,
                n=0,
            )
        )

        start_indices = [
            i for i, line in enumerate(differences) if line.startswith("@@")
        ]

        for i, index in enumerate(start_indices):
            diffline = differences[index]
            lines = diffline.split()[1:3]

            source_line_list = lines[0].split(",")
            if len(source_line_list) == 2:
                source_count = int(source_line_list[1])
            else:
                source_count = 1
            source_line = int(source_line_list[0].replace("-", ""))

            dest_line_list = lines[1].split(",")
            if len(dest_line_list) == 2:
                dest_count = int(dest_line_list[1])
            else:
                dest_count = 1
            dest_line = int(dest_line_list[0].replace("+", ""))

            if i != len(start_indices) - 1:
                limit = start_indices[i + 1]
            else:
                limit = len(differences)
            block_diffs = differences[index:limit]
            assert len(block_diffs) == source_count + dest_count + 1
            yield GitDiff(
                source_line=source_line,
                source_count=source_count,
                destination_line=dest_line,
                destination_count=dest_count,
                lines=block_diffs,
            )

    @staticmethod
    def find_duplicate_mutants(mutants_list):
        counter = Counter([hash(mutant) for mutant in mutants_list])
        return [
            hash_
            for (mutant, (hash_, count)) in zip(mutants_list, counter.items())
            if count > 1
        ]

    def write_duplicate_mutants(self, subject_type: str, mutant_list: list):
        assert subject_type in ("buggy", "fixed")
        assert self.subject
        assert self.tool

        root = pathlib.Path(self.buggy_filepath).parent / "hash"
        os.makedirs(root, exist_ok=True)
        fp = root / f"hash_{self.subject}_{subject_type}_{self.tool}.txt"

        with open(fp, "w") as f:
            # m is mutant, h is its hash
            s = self.pprint_list(
                [
                    (h, m)
                    for (h, m) in [(hash(mutant), mutant) for mutant in mutant_list]
                ]
            )
            f.write(s)

    @staticmethod
    def pprint_list(alist: list):
        return "\n".join(str(elem) for elem in alist)

    def get_difference_set(self):
        # make a tmp copy of fixed mutants
        fixed_mutants = sorted(
            self.fixed_mutants.copy(), key=lambda mutant: mutant.line
        )

        for diff in self.get_git_diffs_gen():
            logging.info(f"Difference found: {repr(diff)}")

            # skip empty deltas
            if diff.delta == 0:
                logging.info("Empty difference delta, skip it")
                continue
            # else get mutants that will be affected by this change
            affected_mutants = [
                mutation
                for mutation in fixed_mutants
                if mutation.line >= diff.source_line
            ]
            logging.info(
                f"Changing the 'line' attribute of {len(affected_mutants)} mutants"
            )

            for mutation in affected_mutants:
                logging.debug(
                    f"From line {mutation.line} to line "
                    f"{mutation.line + diff.delta} - {repr(mutation)}"
                )
                mutation.line += diff.delta

        logging.debug(f"Buggy mutants: {self.buggy_mutants}")
        logging.debug(f"Fixed mutants: {fixed_mutants}")

        logging.info(f"Buggy mutants length: {len(self.buggy_mutants)}")
        logging.info(f"Fixed mutants length: {len(fixed_mutants)}")

        buggy_set = set(self.buggy_mutants)
        fixed_set = set(fixed_mutants)

        logging.debug(f"Buggy set: {buggy_set}")
        logging.debug(f"Fixed set: {fixed_set}")

        logging.info(f"Buggy set length: {len(buggy_set)}")
        logging.info(f"Fixed set length: {len(fixed_set)}")

        self.write_duplicate_mutants("buggy", self.buggy_mutants)
        self.write_duplicate_mutants("fixed", fixed_mutants)

        overlapping = False

        if len(buggy_set) != len(self.buggy_mutants):
            overlapping = True
            overlapped = self.find_duplicate_mutants(self.buggy_mutants)
            logging.error(f"Duplicate mutants hash (buggy set): {overlapped}")

        if len(fixed_set) != len(fixed_mutants):
            overlapping = True
            overlapped = self.find_duplicate_mutants(fixed_mutants)
            logging.error(f"Duplicate mutants hash (fixed set): {overlapped}")

        if overlapping:
            raise OverlappingMutantError(
                "One or more mutants were deleted when set() applied! Fix your hash-tuple"
            )

        difference_set = buggy_set - fixed_set

        logging.debug(f"M1 difference set: {difference_set}")
        logging.info(f"M1 difference set length: {len(difference_set)}")

        return difference_set


class Report(ABC):
    def makeit(self):
        raise NotImplementedError

    def get_mutants(self) -> list:
        return self.get_live_mutants() + self.get_killed_mutants()

    def get_killed_mutants(self) -> list:
        raise NotImplementedError

    def get_live_mutants(self) -> list:
        raise NotImplementedError

    def get_mutants_count(self):
        return len(self.get_mutants())

    def get_killed_mutants_count(self):
        return len(self.get_killed_mutants())

    def get_live_mutants_count(self):
        return len(self.get_live_mutants())

    def __str__(self):
        return (
            f"Total mutants generated: {self.get_mutants_count()} -- "
            f"killed: {self.get_killed_mutants_count()}, live: {self.get_live_mutants_count()}"
        )
