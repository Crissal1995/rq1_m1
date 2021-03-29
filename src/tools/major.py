import os

from src import model


class Mutant(model.Mutant):
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

    def __repr__(self):
        if self.line != self.original_line:
            org = f" (original: {self.original_line})"
        else:
            org = ""
        return (
            f"Mutant at line {self.line}{org} ({self.method_signature})\n"
            f"{self.mutator} - from {self.source_operand} "
            f"to {self.destination_operand} - {self.description}"
        )


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
        # reads "mutants.log", containing a list of all mutants generated
        with open(self.mutants_log_filepath) as f:
            lines = [line.split(":") for line in f.readlines()]

        mutants = []
        for line in lines:
            mut_id = int(line[0])
            mutants.append((mut_id, Mutant(mutation_list=line)))

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

        # mut_id will be also the key of mutants arr
        for mut_id, mut_status in lines:
            # fix first row (header)
            if not mut_id.isnumeric():
                continue
            mut_id = int(mut_id)
            pos = mut_id - 1  # from 1..N to 0..N-1
            mutant = mutants[pos]

            if mut_status.strip() == "LIVE":
                self.live_mutants.append(mutant)
            else:
                self.killed_mutants.append(mutant)

        self.mutants = self.killed_mutants + self.live_mutants
