import os
import sys

# Repo root on sys.path so flat modules (launcher, input_remap, ...) and the
# joypad package are both importable during the migration.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)
