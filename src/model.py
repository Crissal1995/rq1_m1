import difflib
import logging
import os
import pathlib
from abc import ABC
from collections import Counter

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
