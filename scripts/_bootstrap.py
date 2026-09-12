"""Make ``src/`` importable when a script is run from a clone without installing.

``pip install -e .`` is the supported path, but a reviewer who clones the repo
and immediately runs a script should not hit an ImportError. Importing this
module first fixes that and is a no-op once the package is installed.
"""

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))
