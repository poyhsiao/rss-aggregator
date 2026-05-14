"""Tests for Alembic migration integrity."""

import pytest


@pytest.mark.unit
def test_alembic_heads_single_head():
    """Verify only one head revision exists.
    
    When Alembic reports "Multiple head revisions", it means migrations
    have branched and not been properly merged. This test ensures CI
    fails fast with a clear message rather than cryptic Alembic errors.
    """
    import subprocess
    result = subprocess.run(
        ["uv", "run", "alembic", "heads"],
        capture_output=True,
        text=True,
    )
    output = result.stdout + result.stderr
    
    # Alembic should report exactly one head
    lines = [line.strip() for line in output.strip().split("\n") if line.strip()]

    # Count head lines - format is "<rev> (head)"
    head_count = sum(1 for line in lines if "(head)" in line)
    
    assert head_count == 1, (
        f"Expected single Alembic head, found {head_count}. "
        f"Run 'uv run alembic heads' to see current heads. "
        f"Output: {output}"
    )
