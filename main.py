from src import utility

for tool in ("judy", "jumble", "major", "pit"):
    factory = utility.ReportFactory(tool=tool, subject="cli")

    if not factory.is_valid():
        continue

    factory.write_mutants()
