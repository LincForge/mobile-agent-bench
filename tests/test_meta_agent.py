import json
import sys
from pathlib import Path
from typing import Any

from mobile_agent_bench.agent import final_answer_text, run_agent, transcript_assistant_text
from mobile_agent_bench.meta_agent import (
    build_replay_items,
    execute_read_tool,
    is_meta_model,
    is_read_blocked,
    normalize_usage,
    run_muse_agent,
)
from mobile_agent_bench.schema import Task, Tool, Verify
from mobile_agent_bench.tokens import TokenReport, _usage_fields


def _make_task(timeout_s: int = 30) -> Task:
    return Task(
        id="a1_launch",
        tier="A",
        name="Launch and read channel",
        prompt="Find the build channel.",
        app_package="dev.lincforge.benchtarget",
        app_apk="target-app/app/build/outputs/apk/stock/debug/app-stock-debug.apk",
        reset=("force-stop",),
        verify=Verify(
            type="answer",
            pattern="BENCH-STABLE",
            match_samples=("is BENCH-STABLE",),
            reject_samples=("is BENCH-DEV",),
        ),
        timeout_s=timeout_s,
    )


def _write_fake_mcp_server(tmp_path: Path) -> Path:
    """Create a real stdio JSON-RPC 2.0 MCP server script for integration tests."""
    srv_script = tmp_path / "fake_mcp_server.py"
    srv_script.write_text(
        """import json, sys

for raw in sys.stdin:
    raw = raw.strip()
    if not raw:
        continue
    msg = json.loads(raw)
    req_id = msg.get("id")
    method = msg.get("method")
    if req_id is None:
        continue
    if method == "initialize":
        res = {"protocolVersion": "2024-11-05", "capabilities": {}, "serverInfo": {"name": "fake"}}
    elif method == "tools/list":
        res = {
            "tools": [
                {
                    "name": "nerve_elements",
                    "description": "Read interactive elements on screen",
                    "inputSchema": {
                        "$schema": "http://json-schema.org/draft-07/schema#",
                        "type": "object",
                        "properties": {"device": {"type": "string"}},
                    },
                }
            ]
        }
    elif method == "tools/call":
        params = msg.get("params") or {}
        res = {
            "content": [
                {"type": "text", "text": json.dumps({"channel": "BENCH-STABLE", "args": params.get("arguments")})}
            ],
            "isError": False,
        }
    else:
        res = {}
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": req_id, "result": res}) + "\\n")
    sys.stdout.flush()
""",
        encoding="utf-8",
    )
    mcp_cfg = tmp_path / "fake.mcp.json"
    mcp_cfg.write_text(
        json.dumps(
            {
                "mcpServers": {
                    "fake-nerve": {
                        "command": sys.executable,
                        "args": [str(srv_script)],
                    }
                }
            }
        ),
        encoding="utf-8",
    )
    return mcp_cfg


def test_is_meta_model_routing():
    assert is_meta_model("muse-spark-1.3")
    assert is_meta_model("muse-spark-1.3-contributor")
    assert is_meta_model("muse-wonder-1.0")
    assert is_meta_model("meta-models/muse-spark-open-1026")
    assert is_meta_model("meta-models/Muse-Glimmer-30B")
    assert not is_meta_model("claude-sonnet-4-6")
    assert not is_meta_model("")
    assert not is_meta_model(None)  # type: ignore[arg-type]


def test_contract_read_guard_parity_and_multimodal_png(tmp_path):
    """[contract] Read-guard blocks benchmark source/SPEC and base64-encodes allowed PNGs."""
    assert is_read_blocked(
        "/Users/somebody/projects/mobile-agent-bench/target-app/app/src/main/java/CheckoutViewModel.kt"
    )
    assert is_read_blocked("/anywhere/SPEC.md")
    assert is_read_blocked("/tmp/Foo.java")
    assert is_read_blocked("")
    assert not is_read_blocked("/tmp/nerve_screenshot_001.png")

    msg, imgs = execute_read_tool("/anywhere/SPEC.md")
    assert "Read blocked" in msg
    assert imgs == []

    png_path = tmp_path / "screen.png"
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
    png_path.write_bytes(png_bytes)
    msg, imgs = execute_read_tool(str(png_path))
    assert "Loaded image" in msg
    assert len(imgs) == 1
    assert imgs[0].startswith("data:image/png;base64,")


def test_contract_normalize_usage_preserves_token_accounting_invariants():
    """[contract] Raw `/v1/responses` input_tokens includes cached_tokens;
    normalized usage must satisfy total_billed == raw_input + raw_output and
    total_uncached == (raw_input - cached) + raw_output."""
    u = normalize_usage(
        {
            "input_tokens": 1500,
            "input_tokens_details": {"cached_tokens": 1200},
            "output_tokens": 300,
            "output_tokens_details": {"reasoning_tokens": 220},
        }
    )
    inp, out, cc, cr = _usage_fields(u)
    report = TokenReport(inp, out, cc, cr, 1, None, "result-record")
    assert report.input_tokens == 300
    assert report.cache_read_tokens == 1200
    assert report.output_tokens == 300
    assert report.total_billed == 1800
    assert report.total_uncached == 600
    assert u["reasoning_tokens"] == 220

    # Hostile inputs: cached > input, negative values, NaN, booleans, None
    hostile = normalize_usage(
        {
            "input_tokens": 100,
            "input_tokens_details": {"cached_tokens": 999},
            "output_tokens": -50,
            "output_tokens_details": {"reasoning_tokens": float("nan")},
        }
    )
    assert hostile["input_tokens"] == 0
    assert hostile["cache_read_input_tokens"] == 100
    assert hostile["output_tokens"] == 0
    assert hostile["reasoning_tokens"] == 0
    assert normalize_usage(None)["input_tokens"] == 0


def test_contract_build_replay_items_preserves_encrypted_reasoning_and_order():
    """[contract] Multi-turn `/v1/responses` replay must preserve item order and encrypted_content."""
    output = [
        {
            "id": "rs_1",
            "type": "reasoning",
            "encrypted_content": "gAAAAABp...",
            "summary": [],
        },
        {
            "id": "msg_1",
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "Checking screen"}],
        },
        {
            "id": "fc_1",
            "type": "function_call",
            "call_id": "call_abc",
            "name": "nerve_elements",
            "arguments": '{"device":"serial1"}',
        },
    ]
    replayed = build_replay_items(output)
    assert [r["type"] for r in replayed] == ["reasoning", "message", "function_call"]
    assert replayed[0]["encrypted_content"] == "gAAAAABp..."
    assert replayed[2]["call_id"] == "call_abc"


def test_run_muse_agent_end_to_end_with_stdio_mcp(tmp_path, monkeypatch):
    """Full 2-turn `/v1/responses` loop over a real stdio MCP server subprocess."""
    monkeypatch.setenv("META_AI_API_KEY", "test-placeholder-key")
    mcp_cfg = _write_fake_mcp_server(tmp_path)
    tool = Tool(id="linc", name="LINC", mcp_config=str(mcp_cfg))
    task = _make_task()

    png_path = tmp_path / "shot.png"
    png_path.write_bytes(b"\x89PNG\r\n\x1a\nfake")

    captured_requests: list[dict[str, Any]] = []

    def fake_post(url: str, api_key: str, payload: dict[str, Any], timeout_s: float) -> dict[str, Any]:
        captured_requests.append({"url": url, "payload": json.loads(json.dumps(payload))})
        turn = len(captured_requests)
        if turn == 1:
            return {
                "output": [
                    {
                        "id": "rs_t1",
                        "type": "reasoning",
                        "encrypted_content": "enc_turn_1",
                        "summary": [],
                    },
                    {
                        "type": "function_call",
                        "call_id": "call_1",
                        "name": "nerve_elements",
                        "arguments": '{"device": "dev1"}',
                    },
                    {
                        "type": "function_call",
                        "call_id": "call_2",
                        "name": "Read",
                        "arguments": json.dumps({"file_path": str(png_path)}),
                    },
                    {
                        "type": "function_call",
                        "call_id": "call_bad_json",
                        "name": "nerve_elements",
                        "arguments": "{not-valid-json",
                    },
                ],
                "usage": {
                    "input_tokens": 500,
                    "input_tokens_details": {"cached_tokens": 0},
                    "output_tokens": 120,
                    "output_tokens_details": {"reasoning_tokens": 80},
                },
            }
        return {
            "output": [
                {
                    "id": "rs_t2",
                    "type": "reasoning",
                    "encrypted_content": "enc_turn_2",
                    "summary": [],
                },
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "The channel is BENCH-STABLE."}],
                },
            ],
            "usage": {
                "input_tokens": 900,
                "input_tokens_details": {"cached_tokens": 450},
                "output_tokens": 60,
                "output_tokens_details": {"reasoning_tokens": 30},
            },
        }

    out_dir = tmp_path / "run-1"
    run = run_muse_agent(task, tool, "muse-spark-1.3-contributor", out_dir, http_post=fake_post)

    assert run.exit_code == 0
    assert not run.timed_out
    assert run.tokens.source == "result-record"
    assert run.tokens.num_turns == 2
    assert run.tokens.input_tokens == 500 + (900 - 450)
    assert run.tokens.cache_read_tokens == 450
    assert run.tokens.output_tokens == 180
    assert run.tokens.total_billed == 500 + 900 + 180
    assert run.tokens.total_uncached == 950 + 180
    assert final_answer_text(run.transcript_path) == "The channel is BENCH-STABLE."
    assert "BENCH-STABLE" in transcript_assistant_text(run.transcript_path)

    # Verify Turn 1 and Turn 2 shared the exact same prompt_cache_key and replayed encrypted_content
    req1 = captured_requests[0]["payload"]
    req2 = captured_requests[1]["payload"]
    assert req1["prompt_cache_key"] == req2["prompt_cache_key"]
    assert req1["store"] is False
    assert req1["include"] == ["reasoning.encrypted_content"]
    replayed_types = [item.get("type") for item in req2["input"] if isinstance(item, dict)]
    assert "reasoning" in replayed_types
    assert "function_call" in replayed_types
    assert "function_call_output" in replayed_types
    # And the PNG from Read was attached as an input_image block
    user_img_items = [
        item for item in req2["input"]
        if isinstance(item, dict) and item.get("role") == "user" and isinstance(item.get("content"), list)
    ]
    assert len(user_img_items) == 1
    assert user_img_items[0]["content"][0]["type"] == "input_image"


def test_run_agent_dispatches_open_weight_meta_models(tmp_path, monkeypatch):
    """Open-weight `meta-models/*` models route through `/v1/chat/completions` with temperature=1.0, top_p=0.95."""
    monkeypatch.setenv("BASETEN_API_KEY", "test-baseten-key")
    mcp_cfg = _write_fake_mcp_server(tmp_path)
    tool = Tool(id="linc", name="LINC", mcp_config=str(mcp_cfg))
    task = _make_task()

    seen: list[dict[str, Any]] = []

    def fake_post(url: str, api_key: str, payload: dict[str, Any], timeout_s: float) -> dict[str, Any]:
        seen.append({"url": url, "payload": payload})
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Open-weight result: BENCH-STABLE",
                    }
                }
            ],
            "usage": {"prompt_tokens": 400, "completion_tokens": 50},
        }

    out_dir = tmp_path / "run-open"
    run = run_muse_agent(
        task,
        tool,
        "meta-models/muse-spark-open-1026",
        out_dir,
        http_post=fake_post,
    )
    assert run.exit_code == 0
    assert seen[0]["url"].endswith("/chat/completions")
    assert seen[0]["payload"]["temperature"] == 1.0
    assert seen[0]["payload"]["top_p"] == 0.95
    assert final_answer_text(run.transcript_path) == "Open-weight result: BENCH-STABLE"


def test_contract_turn_cap_defaults_above_baseline_and_rejects_hostile_override():
    """[contract] The wall-clock timeout_s is the binding budget, as for the Claude
    baseline cells (c9 used up to 165 turns); BENCH_META_MAX_TURNS only overrides
    with a positive int."""
    from mobile_agent_bench.meta_agent import DEFAULT_MAX_TURNS, resolve_max_turns

    assert DEFAULT_MAX_TURNS >= 300
    assert resolve_max_turns({}) == DEFAULT_MAX_TURNS
    assert resolve_max_turns({"BENCH_META_MAX_TURNS": "7"}) == 7
    for hostile in ("", "0", "-3", "abc", "1e9", "nan", " 5\n"):
        assert resolve_max_turns({"BENCH_META_MAX_TURNS": hostile}) == DEFAULT_MAX_TURNS


def test_contract_turn_cap_exhaustion_is_not_a_clean_finish(tmp_path, monkeypatch):
    """[contract] A run cut off by the turn cap must not write a result record or
    exit 0 (the 2026-10-27 c9 cell was graded on a mid-task sentence)."""
    monkeypatch.setenv("META_AI_API_KEY", "test-placeholder-key")
    monkeypatch.setenv("BENCH_META_MAX_TURNS", "3")
    mcp_cfg = _write_fake_mcp_server(tmp_path)
    tool = Tool(id="linc", name="LINC", mcp_config=str(mcp_cfg))
    task = _make_task()
    calls: list[int] = []

    def fake_post(url: str, api_key: str, payload: dict[str, Any], timeout_s: float) -> dict[str, Any]:
        calls.append(1)
        return {
            "output": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "Moving on to the next section."}],
                },
                {
                    "type": "function_call",
                    "call_id": f"call_{len(calls)}",
                    "name": "nerve_elements",
                    "arguments": '{"device": "dev1"}',
                },
            ],
            "usage": {"input_tokens": 10, "output_tokens": 5},
        }

    out_dir = tmp_path / "run-1"
    run = run_muse_agent(task, tool, "muse-spark-1.3-contributor", out_dir, http_post=fake_post)

    assert len(calls) == 3
    assert run.exit_code == 2
    assert not run.timed_out
    records = [json.loads(line) for line in run.transcript_path.read_text().splitlines() if line]
    assert not any(r.get("type") == "result" for r in records)
    assert "max turns (3) reached" in (out_dir / "stderr.txt").read_text()
