import pathlib
import sys

cur_dir = pathlib.Path(__file__).parent.resolve()
proj_dir = str(cur_dir.parent)

if proj_dir not in sys.path:
    sys.path.insert(0, proj_dir)
