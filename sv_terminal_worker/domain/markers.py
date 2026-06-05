from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Mapping


MARKER_RE = re.compile(r"^\[(?P<kind>SV_[A-Z_]+)\s+(?P<attrs>.+)\]$")
ATTR_RE = re.compile(r"(?P<key>[A-Za-z_][A-Za-z0-9_]*)=(?P<value><[^>]*>|\"[^\"]*\"|'[^']*'|[^\s]+)")


@dataclass(frozen=True)
class Marker:
    kind: str
    attrs: Mapping[str, str]
    raw: str

    def get(self, key: str, default: str | None = None) -> str | None:
        return self.attrs.get(key, default)


def parse_marker(line: str) -> Marker:
    stripped = line.strip()
    match = MARKER_RE.match(stripped)
    if not match:
        raise ValueError(f"invalid marker: {line}")

    attrs = {m.group("key"): _clean_value(m.group("value")) for m in ATTR_RE.finditer(match.group("attrs"))}
    if not attrs:
        raise ValueError(f"marker has no attributes: {line}")

    return Marker(kind=match.group("kind"), attrs=attrs, raw=stripped)


def find_markers(text: str) -> list[Marker]:
    markers: list[Marker] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("[SV_") and stripped.endswith("]"):
            markers.append(parse_marker(stripped))
    return markers


def is_proposal_approval(marker: Marker) -> bool:
    return (
        marker.kind == "SV_APPROVAL"
        and marker.get("decision") == "approved"
        and (marker.get("target") or "").startswith("proposal:")
    )


def _clean_value(value: str) -> str:
    if len(value) >= 2 and ((value[0] == value[-1] == '"') or (value[0] == value[-1] == "'")):
        return value[1:-1]
    return value
