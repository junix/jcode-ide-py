from __future__ import annotations

from jcode_ide.client import _position_from_dict, _range_from_dict


def test_position_from_dict_reads_line_and_character() -> None:
    pos = _position_from_dict({"line": 7, "character": 3})

    assert pos.line == 7
    assert pos.character == 3


def test_position_from_dict_defaults_missing_fields_to_zero() -> None:
    assert _position_from_dict({}).line == 0
    assert _position_from_dict({}).character == 0
    assert _position_from_dict({"line": 5}).character == 0


def test_position_from_dict_handles_none() -> None:
    pos = _position_from_dict(None)

    assert pos.line == 0
    assert pos.character == 0


def test_range_from_dict_reads_start_and_end() -> None:
    rng = _range_from_dict({"start": {"line": 1, "character": 0}, "end": {"line": 2, "character": 5}})

    assert rng.start.line == 1
    assert rng.start.character == 0
    assert rng.end.line == 2
    assert rng.end.character == 5


def test_range_from_dict_defaults_missing_endpoints_to_zero() -> None:
    rng = _range_from_dict({})

    assert rng.start.line == 0
    assert rng.start.character == 0
    assert rng.end.line == 0
    assert rng.end.character == 0


def test_range_from_dict_partial_dict_preserves_defaults() -> None:
    rng = _range_from_dict({"start": {"line": 4}})

    assert rng.start.line == 4
    assert rng.start.character == 0
    assert rng.end.line == 0
    assert rng.end.character == 0


def test_range_from_dict_handles_none() -> None:
    rng = _range_from_dict(None)

    assert rng.start.line == 0
    assert rng.end.line == 0
