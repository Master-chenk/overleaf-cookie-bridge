from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import Literal

EntityType = Literal["folder", "doc", "file"]


@dataclass
class Entity:
    id: str
    name: str
    type: EntityType
    children: list[Entity] = field(default_factory=list)


def flatten_tree(root: Entity, prefix: str = "") -> Iterable[tuple[str, Entity]]:
    for child in root.children:
        path = f"{prefix}/{child.name}" if prefix else child.name
        yield path, child
        if child.type == "folder":
            yield from flatten_tree(child, path)


def find_entity(root: Entity, path: str) -> Entity | None:
    normalized = path.strip("/")
    for candidate_path, entity in flatten_tree(root):
        if candidate_path == normalized:
            return entity
    return None
