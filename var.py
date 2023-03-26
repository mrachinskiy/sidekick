# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright 2020-2023 Mikhail Rachinskiy

from pathlib import Path

from . import report


Report = report.Scan()


# Paths
# --------------------------------


ADDON_ID = __package__
ADDON_DIR = Path(__file__).parent
CONFIG_DIR = ADDON_DIR / ".config"
