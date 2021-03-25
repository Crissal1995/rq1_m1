import pathlib

# file.py -> src dir -> root dir
HOME = pathlib.Path(__file__).parent.parent

subjects = {'cli': 'cli32', 'lang': 'lang53', 'gson': 'gson15'}
tools = ["judy", "jumble", "major", "pit"]


def get_root_dir(subject: str, tool: str):
    assert subject in subjects
    assert tool in tools
    return HOME / "data" / subjects[subject] / tool
