# SPDX-FileCopyrightText: 2020-2024 Mikhail Rachinskiy
# SPDX-License-Identifier: GPL-3.0-or-later

from pathlib import Path

from . import report


ADDON_ID = __package__
ADDON_DIR = Path(__file__).parent

Report = report.Scan()
