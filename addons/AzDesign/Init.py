# SPDX-License-Identifier: LGPL-2.1-or-later
"""Make saved feature proxies importable before a document is restored."""

import os
import sys

_az_root = os.path.dirname(__file__)
if _az_root not in sys.path:
    sys.path.insert(0, _az_root)
