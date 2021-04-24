import logging

from src.analyzer.utility import test_environment

# assure we're in an env with defects4j correctly set in PATH
test_environment()

# set logging format
FORMAT = "%(levelname)s :: [%(module)s.%(funcName)s.%(lineno)d] :: %(message)s"

# set format in logging
logging.basicConfig(format=FORMAT)
