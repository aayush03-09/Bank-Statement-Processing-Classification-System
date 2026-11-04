import sys
import os

test_dir = os.path.dirname(os.path.abspath(__file__))
pkg_dir = os.path.dirname(test_dir)
parent_dir = os.path.dirname(pkg_dir)

for path in [pkg_dir, parent_dir]:
    if path not in sys.path:
        sys.path.insert(0, path)
