"""MemoGarden Soil - Compatibility Wrapper.

DEPRECATED: This package is deprecated. Use 'system.soil' instead.

This module provides backward compatibility by re-exporting from system.soil.
The email importers (email_importer.py, email_parser.py, import_mbox.py)
remain in this package temporarily and will be migrated to /providers/ in Phase 6.

Migration guide:
- Old: from soil import Soil, Item
- New: from system.soil import Soil, Item
"""

from __future__ import annotations

import warnings

# Re-export everything from system.soil
from system.soil import (
    Item,
    Evidence,
    SystemRelation,
    Soil,
    generate_soil_uuid,
    SOIL_UUID_PREFIX,
    current_day,
    get_soil,
    create_email_item,
)

__all__ = [
    "Item",
    "Evidence",
    "SystemRelation",
    "Soil",
    "generate_soil_uuid",
    "SOIL_UUID_PREFIX",
    "current_day",
    "get_soil",
    "create_email_item",
]

# Issue deprecation warning
warnings.warn(
    "Importing from 'soil' package is deprecated. "
    "Use 'from system.soil import ...' instead. "
    "The soil package will be removed after Phase 6 (Provider Refactoring).",
    DeprecationWarning,
    stacklevel=2
)
