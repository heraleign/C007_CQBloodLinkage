"""ID generation utilities."""

from __future__ import annotations

import uuid
from datetime import datetime


def generate_node_id() -> str:
    return uuid.uuid4().hex[:16]


def generate_edge_id() -> str:
    return uuid.uuid4().hex[:16]


def generate_parse_id() -> str:
    return f"PARSE_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4]}"
