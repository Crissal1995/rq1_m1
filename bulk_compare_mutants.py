import argparse
import logging
import pathlib

import pandas as pd
from compare_mutants import main

from src.utility import subjects, tools


def set_logging(name: str = None):
    # FORMAT = "%(levelname)s :: %(asctime)s :: %(module)s, line %(lineno)d :: %(message)s"
    FORMAT = "%(levelname)s :: [%(module)s.%(lineno)d] :: %(message)s"

    file_handler = logging.FileHandler("bulk_compare_mutants.log")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(FORMAT))

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    stream_handler.setFormatter(logging.Formatter(FORMAT))

    _logger = logging.getLogger(name)
    _logger.addHandler(file_handler)
    _logger.addHandler(stream_handler)
    _logger.setLevel(logging.DEBUG)

    return _logger


if __name__ == "__main__":
    logger = set_logging()

    parser = argparse.ArgumentParser()

    # set one subject (cannot compare two different subjects)
    parser.add_argument("subject", choices=subjects)

    # set tool (cannot compare between two or more tools)
    parser.add_argument("tool", choices=tools)

    # set root for files
    parser.add_argument("--root")

    args = parser.parse_args()

    root = args.root
    if not root:
        root = f"data_cmp/{args.subject}/{args.tool}"
    root = pathlib.Path(root)

    directories = [dir_ for dir_ in root.iterdir() if dir_.is_dir()]
    basename = "_single_dev"
    base = [dir_ for dir_ in directories if dir_.name == basename]
    assert len(base) > 0, f"No {basename} found inside {root}"
    assert len(base) == 1, f"More than one {basename} found inside {root}"
    base = base.pop()
    directories.pop(directories.index(base))

    files1 = list(base.iterdir())
    series = []

    # set level to WARNING to exclude printing to stdout
    # except for severe problems
    logger.setLevel(logging.WARNING)
    logger.info(f"Base directory found: {base}")

    data_type = "original"
    index = True

    # compare to itself to gen first column - that is, single_dev live mutants
    comparer = main(
        root, args.subject, args.tool, files1, files1, args_absolute_path=True
    )
    series.append(
        comparer.get_series(
            name="single_dev", kind="first", data_type=data_type, index=index
        )
    )

    # restore level
    logger.setLevel(logging.INFO)
    for i, directory in enumerate(directories):
        if i > 0:
            logger.info("-" * 50)

        files2 = list(directory.iterdir())
        logger.info(f"Comparison with {directory}")

        comparer = main(
            root, args.subject, args.tool, files1, files2, args_absolute_path=True
        )
        series.append(
            comparer.get_series(name=directory.name, data_type=data_type, index=index)
        )

    df = pd.DataFrame(series)
    path = f"{root}/{args.subject}_{args.tool}.csv"
    path = pathlib.Path(path)
    df.to_csv(path)
    logger.info(f"Dataframe saved as csv in {path}")
    logger.info(f"Live Mutants count = {df.count(1)}")
