from __future__ import annotations

from pathlib import Path

from jcode_ide.client import DiffResult
from jcode_ide.discovery import IDEServerDiscovery
from jcode_ide.fallback import suffix_to_language


def test_suffix_to_language_returns_known_and_unknown_values() -> None:
    assert suffix_to_language("py") == "python"
    assert suffix_to_language("unknown") == "text"


def test_diff_result_helpers_reflect_status() -> None:
    accepted = DiffResult(status="accepted")
    rejected = DiffResult(status="rejected")

    assert accepted.accepted is True
    assert accepted.rejected is False
    assert rejected.accepted is False
    assert rejected.rejected is True


def test_parse_port_file(tmp_path: Path) -> None:
    port_file = tmp_path / "letta-ide-server-test-8123.json"
    port_file.write_text(
        '{"port":8123,"authToken":"token","workspacePath":"/tmp/ws","pid":123,"createdAt":456,"instanceNonce":"abc"}',
        encoding="utf-8",
    )

    server = IDEServerDiscovery._parse_port_file(port_file)

    assert server.port == 8123
    assert server.auth_token == "token"
    assert server.base_url == "http://localhost:8123"
