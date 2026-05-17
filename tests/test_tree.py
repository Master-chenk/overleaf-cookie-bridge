
from overleaf_cookie_bridge.tree import Entity, find_entity, flatten_tree


def test_flatten_tree_preserves_doc_and_file_types():
    root = Entity(id="root", name="", type="folder", children=[
        Entity(id="d1", name="main.tex", type="doc"),
        Entity(id="f1", name="image.png", type="file"),
        Entity(id="folder", name="sections", type="folder", children=[
            Entity(id="d2", name="intro.tex", type="doc"),
        ]),
    ])

    flattened = {path: entity for path, entity in flatten_tree(root)}

    assert flattened["main.tex"].type == "doc"
    assert flattened["image.png"].type == "file"
    assert flattened["sections/intro.tex"].id == "d2"


def test_find_entity_returns_nested_path():
    root = Entity(id="root", name="", type="folder", children=[
        Entity(id="folder", name="sections", type="folder", children=[
            Entity(id="d2", name="intro.tex", type="doc"),
        ]),
    ])

    entity = find_entity(root, "sections/intro.tex")

    assert entity is not None
    assert entity.id == "d2"
