"""Smoke tests: the entrypoint imports, and a migration suggestion can be built.

Both failed before #3: main.py imported a missing ssh_connect, and
suggest_migrations read cpu_score/memory_score, which were locals of
evaluate_migration_target. No SSH is opened here.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import main  # noqa: E402  (the import itself is the first check)


def _host(cpu, mem_used, mem_total, free_memory, free_cores, balance):
    return {
        "cpu": f"{cpu} 0 0",
        "memory": f"{mem_used} {mem_total}",
        "cpu_threshold": 2.0,
        "memory_threshold": 0.8,
        "free_memory": free_memory,
        "free_cores": free_cores,
        "balance_score": balance,
    }


def test_entrypoint_has_ssh_connect():
    assert callable(main.ssh_connect)


def test_suggest_migrations_builds_the_detail(monkeypatch):
    hosts = {
        "busy": _host(3.5, 7000, 8000, 500, 0, 2.0),
        "idle": _host(0.2, 1000, 8000, 6000, 6, 0.3),
    }
    candidate = {
        "container_id": 101,
        "source_host": "busy",
        "container_cpu_load": 0.5,
        "container_memory": 1024,
        "container_cores": 1,
    }
    monkeypatch.setattr(main, "get_migration_candidates", lambda h, p: ([candidate], [("busy", hosts["busy"])]))

    suggestions = main.suggest_migrations(hosts, {})

    assert [s["target_host"] for s in suggestions] == ["idle"]
    detail = suggestions[0]["detailed_calc"]
    assert "Target CPU Score: 0.35" in detail
    assert "Target Memory Score: 0.25" in detail
