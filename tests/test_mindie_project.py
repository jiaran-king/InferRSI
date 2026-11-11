import hashlib
import json
from pathlib import Path

from inferrsi import mindie_mcp, mindie_project
from inferrsi.cli import main


def test_project_enable_discover_read_and_revoke(tmp_path, monkeypatch, capsys):
    enabled, disabled = tmp_path / "enabled", tmp_path / "disabled"
    for checkout in (enabled, disabled):
        (checkout / ".git").mkdir(parents=True)
    monkeypatch.setattr(Path, "home", lambda: tmp_path / "local-user")
    monkeypatch.chdir(enabled)
    engine = tmp_path / "engine.json"
    engine.write_text("{}")
    adapter = tmp_path / "adapter.json"
    adapter.write_text(json.dumps({
        "python": str(tmp_path / "python"), "engine_config": str(engine),
    }))
    reads = []

    def worker(grant, operation, raw):
        assert grant["domain"] == "operators"
        if operation == "describe":
            return b'{"domain":"operators","component_version":"0.13.13"}\n'
        reads.append((operation, json.loads(raw)))
        return b'{"results":[]}\n'

    monkeypatch.setattr(mindie_project, "_worker", worker)
    assert main(["mindie", "enable", "--adapter-config", str(adapter)]) == 0
    assert json.loads(capsys.readouterr().out)["available"]
    assert main(["mindie", "describe"]) == 0
    assert json.loads(capsys.readouterr().out)["tools"] == ["knowledge_query", "knowledge_explain"]
    assert {tool["name"] for tool in mindie_mcp._reply("tools/list", {})["tools"]} == {
        "knowledge_query", "knowledge_explain",
    }
    result = mindie_mcp._reply("tools/call", {
        "name": "knowledge_query", "arguments": {"query": "vector tail"},
        "_meta": {"threadId": "fresh-thread",
                  "x-codex-turn-metadata": {"thread_id": "fresh-thread"}},
    })
    assert not result["isError"]
    directory = Path(result["structuredContent"]["receipt_directory"])
    assert json.loads((directory / "input.json").read_text()) == {"query": "vector tail"}
    assert (directory / "result.json").read_bytes() == b'{"results":[]}\n'
    assert json.loads((directory / "receipt.json").read_text())["session_sha256"] == (
        hashlib.sha256(b"fresh-thread").hexdigest()
    )
    for name, args in (
        ("knowledge_distill", {}),
        ("knowledge_query", {"query": "vector tail", "domain": "unapproved"}),
        ("knowledge_query", {"query": "vector tail", "_session_verified": True}),
        ("knowledge_explain", {"refs": ["mindie://other/units/tail@1"]}),
        ("knowledge_explain", {"refs": ["mindie://operators/units/tail"]}),
    ):
        assert mindie_mcp._reply("tools/call", {"name": name, "arguments": args})["isError"]

    monkeypatch.chdir(disabled)
    assert mindie_mcp._reply("tools/list", {}) == {"tools": []}
    assert mindie_mcp._reply("tools/call", {
        "name": "knowledge_query", "arguments": {"query": "vector tail"},
    })["isError"]
    monkeypatch.chdir(enabled)
    assert main(["mindie", "disable"]) == 0
    assert mindie_mcp._reply("tools/list", {}) == {"tools": []}
    assert directory.is_dir()
    assert reads == [("query", {"query": "vector tail"})]
