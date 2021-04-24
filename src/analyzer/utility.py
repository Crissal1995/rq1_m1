import logging
import subprocess

logger = logging.getLogger(__file__)


def defects4j_cmd(cmd: str = "", *args, **kwargs):
    """Utility function to call Defects4j"""
    possible_cmds = (
        "bids",
        "checkout",
        "compile",
        "coverage",
        "env",
        "export",
        "info",
        "monitor.test",
        "mutation",
        "pids",
        "query",
        "test",
    )
    if cmd:
        assert cmd in possible_cmds, "Invalid command provided for defects4j!"
        cmd = ["defects4j", cmd] + list(args)
    logger.debug(f"Running {cmd}")
    subprocess.run(cmd, **kwargs)


def test_environment():
    """Tests if the environment is correctly set,
    i.e. that Defects4j is installed into PATH"""
    try:
        subprocess.run(["defects4j"], stdout=subprocess.DEVNULL)
    except FileNotFoundError:
        raise EnvironmentError("defects4j not found in PATH!")
