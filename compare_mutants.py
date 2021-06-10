import argparse
import logging

from src.model import MutantsComparerSets
from src.utility import get_report, subjects, tools


def set_logging():
    # FORMAT = "%(levelname)s :: %(asctime)s :: %(module)s, line %(lineno)d :: %(message)s"
    FORMAT = "%(levelname)s :: [%(module)s.%(lineno)d] :: %(message)s"

    file_handler = logging.FileHandler("compare_mutants.log", mode="w")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(FORMAT))

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter(FORMAT))

    logger = logging.getLogger()
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)
    logger.setLevel(logging.DEBUG)
    return logger


def main(
    root: str,
    subject: str,
    tool: str,
    files1: [str],
    files2: [str],
    compare: str = "live",
    dirname: str = None,
    args_absolute_path: bool = False,
):
    valid_compare_values = "live", "killed", "all"
    if compare not in valid_compare_values:
        raise ValueError(
            f"Invalid compare value provided ({compare})"
            f"\nValid compare values are {valid_compare_values}"
        )

    max_files_length = 2

    if len(files1) > max_files_length:
        raise ValueError(f"files1 can hold up to {max_files_length} arguments")

    if len(files2) > max_files_length:
        raise ValueError(f"files2 can hold up to {max_files_length} arguments")

    report1 = get_report(
        subject, tool, *files1, root=root, args_absolute_path=args_absolute_path
    )
    report1.makeit()

    report2 = get_report(
        subject, tool, *files2, root=root, args_absolute_path=args_absolute_path
    )
    report2.makeit()

    mutants = list()
    if compare == "live":
        mutants = report1.get_live_mutants(), report2.get_live_mutants()
    elif compare == "killed":
        mutants = report1.get_killed_mutants(), report2.get_killed_mutants()
    elif compare == "all":
        mutants = report1.get_mutants(), report2.get_mutants()

    comparer = MutantsComparerSets(*mutants)

    dirname = dirname or f"{subject} {tool}"
    comparer.summary(dirname=dirname)


if __name__ == "__main__":
    logger = set_logging()

    parser = argparse.ArgumentParser()

    # set one subject (cannot compare two different subjects)
    parser.add_argument("subject", choices=subjects)

    # set tool (cannot compare between two or more tools)
    parser.add_argument("tool", choices=tools)

    # set first and second files arguments
    parser.add_argument("-f1", "--files1", nargs="+")
    parser.add_argument("-f2", "--files2", nargs="+")

    # set root for files
    parser.add_argument("--root", default="data")

    args = parser.parse_args()
    main(args.root, args.subject, args.tool, args.files1, args.files2)
