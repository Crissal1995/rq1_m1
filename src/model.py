import difflib
import os
import pathlib
from abc import ABC


class Mutant(ABC):
    def __init__(self, line: int):
        assert line >= 0
        self.line = line

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
        return f"Mutant(line={self.line})"


class Diff:
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
            f"Diff({self.source_line}, {self.source_count}, "
            f"{self.destination_line}, {self.destination_count}); delta={self.delta}"
        )

    def __str__(self):
        src_count = f",{self.source_count}" if self.source_count != 1 else ""
        dst_count = f",{self.destination_count}" if self.destination_count != 1 else ""
        s = f"@@ -{self.source_line}{src_count} +{self.destination_line}{dst_count} @@\n"
        s += "\n".join(self.lines)
        return s


class MutantsComparer:
    def __init__(
        self,
        buggy_mutants: [Mutant],
        fixed_mutants: [Mutant],
        buggy_filepath: [str, os.PathLike],
        fixed_filepath: [str, os.PathLike],
    ):
        self.buggy_mutants: [Mutant] = buggy_mutants
        self.fixed_mutants: [Mutant] = fixed_mutants

        self.buggy_filepath = buggy_filepath
        self.fixed_filepath = fixed_filepath

    def generate_diffs(self):
        # check for user errors
        buggy_filepath = pathlib.Path(self.buggy_filepath)
        fixed_filepath = pathlib.Path(self.fixed_filepath)

        assert all(
            path.exists() and path.is_file()
            for path in (buggy_filepath, fixed_filepath)
        )

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
            block_diffs = differences[index + 1 : limit]
            assert len(block_diffs) == source_count + dest_count
            yield Diff(
                source_line=source_line,
                source_count=source_count,
                destination_line=dest_line,
                destination_count=dest_count,
                lines=block_diffs,
            )

    def get_difference_set(self, ordered=True):
        # make a tmp copy of fixed mutants
        fixed_mutants = sorted(
            self.fixed_mutants.copy(), key=lambda mutant: mutant.line
        )

        for diff in self.generate_diffs():
            for mutation in [
                mutation
                for mutation in fixed_mutants
                if mutation.line >= diff.source_line
            ]:
                mutation.line += diff.delta

        buggy_set = set(self.buggy_mutants)
        fixed_set = set(fixed_mutants)

        difference_set = buggy_set - fixed_set

        if not ordered:
            return difference_set
        else:
            return sorted(difference_set, key=lambda mutant: mutant.line)


class PitMutant(Mutant):
    def __init__(self, line: int):
        super().__init__(line)

    @property
    def hash_tuple(self) -> tuple:
        return (self.line,)


if __name__ == "__main__":
    _buggy_mutants = list(PitMutant(line=i) for i in range(930, 943))
    _fixed_mutants = list(PitMutant(line=i) for i in range(930, 943))

    home = pathlib.Path(__file__) / ".." / ".." / "data" / "cli32"
    buggy_fp = home / "buggy_helpformatter.java"
    fixed_fp = home / "fixed_helpformatter.java"

    comparer = MutantsComparer(
        buggy_mutants=_buggy_mutants,
        fixed_mutants=_fixed_mutants,
        buggy_filepath=buggy_fp,
        fixed_filepath=fixed_fp,
    )

    diff_set = comparer.get_difference_set()
    print(diff_set)
