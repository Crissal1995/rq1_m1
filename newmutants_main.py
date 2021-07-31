import pathlib

from reports.reports import JudyReport, JumbleReport, MajorReport, PitReport

projects = ["cli", "gson", "lang"]
classes = [
    "org.apache.commons.cli.HelpFormatter",
    "com.google.gson.stream.JsonWriter",
    "org.apache.commons.lang.time.DateUtils",
]


for project, cls in zip(projects, classes):
    print(f"WORKING WITH {project}")

    p = pathlib.Path(f"data_cmp/{project}/judy/_single_dev/result.json")
    report = JudyReport(p, cls)
    print(report.summary(), "\n")

    p = pathlib.Path(f"data_cmp/{project}/jumble/_single_dev/jumble_output.txt")
    report = JumbleReport(p)
    print(report.summary(), "\n")

    p1 = pathlib.Path(f"data_cmp/{project}/major/_single_dev/kill.csv")
    p2 = pathlib.Path(f"data_cmp/{project}/major/_single_dev/mutants.log")
    report = MajorReport(p2, p1)
    print(report.summary(), "\n")

    p = pathlib.Path(f"data_cmp/{project}/pit/_single_dev/mutations.xml")
    report = PitReport(p)
    print(report.summary(), "\n")

    print("-" * 60)
