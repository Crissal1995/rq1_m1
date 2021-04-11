import logging

from src import MutantError, ReportFactory, subjects, tools

# FORMAT = "%(levelname)s :: %(asctime)s :: %(module)s, line %(lineno)d :: %(message)s"
FORMAT = "%(levelname)s :: %(module)s, line %(lineno)d :: %(message)s"

file_handler = logging.FileHandler("get_mutants.log", mode="w")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(logging.Formatter(FORMAT))

stream_handler = logging.StreamHandler()
stream_handler.setLevel(logging.INFO)
stream_handler.setFormatter(logging.Formatter(FORMAT))

logger = logging.getLogger()
logger.addHandler(file_handler)
logger.addHandler(stream_handler)
logger.setLevel(logging.DEBUG)

tools.remove("judy")
logging.warning(
    "Removed Judy from tools, because it doesn't generate mutants with a dummy test suite"
)

for subject in subjects:
    for tool in tools:
        logging.warning(f"Working on subject {subject} and tool {tool}")
        try:
            factory = ReportFactory(tool=tool, subject=subject, base_dir="data_dummy")
            factory.write_mutants("buggy")
            factory.write_mutants("fixed")
        except MutantError as e:
            logging.error(f"Mutant error caught: {e}")
        except Exception as e:
            logging.error(f"Exception caught: {e}")
