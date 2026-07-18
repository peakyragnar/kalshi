from kalshi_data.analysis import full_suite


def test_full_suite_rebuilds_snapshots_before_registered_families(monkeypatch):
    calls = []
    monkeypatch.setattr(full_suite, "metadata_backfill_complete", lambda: True)
    for name in (
        "derive",
        "corpus_audit",
        "research_panel",
        "atlas",
        "mechanism_suite",
        "metadata_suite",
        "survivor_audit",
    ):
        module = getattr(full_suite, name)
        monkeypatch.setattr(module, "run", lambda name=name: calls.append(name))

    full_suite.run()

    assert calls == [
        "derive",
        "corpus_audit",
        "research_panel",
        "atlas",
        "mechanism_suite",
        "metadata_suite",
        "survivor_audit",
    ]
