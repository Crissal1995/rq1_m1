import logging

from src import utility

FORMAT = "%(levelname)s :: %(asctime)s :: %(module)s, line %(lineno)d :: %(message)s"

file_handler = logging.FileHandler("main.log", mode="w")
file_handler.setFormatter(logging.Formatter(FORMAT))

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter(FORMAT))

logging.getLogger().addHandler(file_handler)
logging.getLogger().addHandler(stream_handler)

logging.getLogger().setLevel(logging.DEBUG)

for subject in utility.subjects:
    for tool in utility.tools:
        logging.warning(f"Working on subject {subject} and tool {tool}")
        try:
            factory = utility.ReportFactory(tool=tool, subject=subject)
        except Exception as e:
            logging.error(f"TOOL: {tool}, SUBJECT: {subject}, ERROR: {e}")
        else:
            factory.write_mutants()
