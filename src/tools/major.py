import io
import os
from collections import defaultdict

import pandas as pd

from src import model


class OldMutant(model.Mutant):
    @property
    def hash_tuple(self) -> tuple:
        return (
            self.line,
            self.mutator,
            self.description,
            self.source_operand,
            self.destination_operand,
            self.method_signature,
        )

    def __init__(self, mutation_list: list):
        assert len(mutation_list) >= 7

        # if there was a ":" inside the description, then
        # description is a list holding these splitted values
        if len(mutation_list) > 7:
            description = ":".join(mutation_list[6:])
        else:
            description = mutation_list[6]

        mut_id, mutator, from_, to_, method_signature, line_number = mutation_list[:6]

        super().__init__(line=int(line_number))
        self.mutation_id = mut_id
        self.mutator = mutator
        self.source_operand = from_
        self.destination_operand = to_
        self.method_signature = method_signature
        self.description = description

    def __str__(self):
        if self.line != self.original_line:
            org = f" (original: {self.original_line})"
        else:
            org = ""
        return (
            f"Mutant at line {self.line}{org} ({self.method_signature})\n"
            f"{self.mutator} - from {self.source_operand} "
            f"to {self.destination_operand} - {self.description}"
        )


class Mutant(model.Mutant):
    counter_hashkey = defaultdict(int)

    def __init__(self, mutation_series: pd.Series):
        self.status = mutation_series.Status
        self.operator = mutation_series.Operator
        self.from_ = mutation_series.From
        self.to = mutation_series.To
        self.signature = mutation_series.Signature
        self.line = mutation_series.LineNumber
        self.original_line = self.line
        self.description = mutation_series.Description

        self._series = mutation_series

        thehash = hash((mutation_series[k] for k in self._hash_tuple))
        self._counter = self.counter_hashkey[thehash]
        self.counter_hashkey[thehash] += 1

    @property
    def _hash_tuple(self) -> tuple:
        return (
            self.operator,
            self.from_,
            self.to,
            self.signature,
            self.line,
            self.description,
        )

    @property
    def hash_tuple(self) -> tuple:
        return self._hash_tuple + (self._counter,)

    def __str__(self):
        if self.line != self.original_line:
            org = f" (original: {self.original_line})"
        else:
            org = ""
        return f"Mutant at line {self.line}{org}\n" f"{str(self._series)}"


class Report(model.Report):
    def __init__(
        self,
        mutants_log_filepath: [str, os.PathLike],
        kill_csv_filepath: [str, os.PathLike],
    ):
        self.mutants_log_filepath = mutants_log_filepath
        self.kill_csv_filepath = kill_csv_filepath

        # attrs to instantiate in the makeit()
        self.mutants = []
        self.killed_mutants = []
        self.live_mutants = []

    def get_killed_mutants(self) -> list:
        return self.killed_mutants

    def get_live_mutants(self) -> list:
        return self.live_mutants

    def makeit(self):
        with open(self.kill_csv_filepath) as f:
            kill_csv_stream = io.StringIO(f.read())
        columns = ["MutantNo", "Status"]
        kill_df = pd.read_csv(kill_csv_stream, header=0, names=columns).set_index(
            "MutantNo"
        )

        with open(self.mutants_log_filepath) as f:
            stream = io.StringIO(f.read())
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
            stream, delimiter=":", header=None, names=columns
        ).set_index("MutantNo")

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

        for index, row in df.iterrows():
            mutant = Mutant(row)
            if mutant.status == "LIVE":
                self.live_mutants.append(mutant)
            else:
                self.killed_mutants.append(mutant)

        self.mutants = self.killed_mutants + self.live_mutants

    def _old_makeit(self):
        # reads "mutants.log", containing a list of all mutants generated
        with open(self.mutants_log_filepath) as f:
            lines = [line.split(":") for line in f.readlines()]

        mutants = []
        for line in lines:
            mut_id = int(line[0])
            mutants.append((mut_id, OldMutant(mutation_list=line)))

        # should be sorted, but better safe than sorry ;)
        mutants.sort(key=lambda el: el[0])

        # and to ensure that, the length of mutants arr
        # must be equal to last mutant's id
        assert len(mutants) == mutants[-1][0]

        # now remove first attribute
        mutants = [mutant for mut_id, mutant in mutants]

        # now read "kill.csv" which contains mut id and mut status
        with open(self.kill_csv_filepath) as f:
            lines = [line.split(",") for line in f.readlines()]

        # hack for empty kill.csv (all live mutants)
        if len(lines) < 2:
            self.live_mutants = mutants

        # mut_id will be also the key of mutants arr
        for i, (mut_id, mut_status) in enumerate(lines):
            # skip first row (header)
            if i == 0:
                continue
            mut_id = int(mut_id)
            pos = mut_id - 1  # from 1..N to 0..N-1
            mutant = mutants[pos]

            if mut_status.strip() == "LIVE":
                self.live_mutants.append(mutant)
            else:
                self.killed_mutants.append(mutant)

        self.mutants = self.killed_mutants + self.live_mutants
