"""Confirms embed_text normalises before doing anything else, and that it's
currently the only way in (no model wired up yet)."""

import pytest

from retrieval.embed import embed_text


def test_embed_text_normalises_before_raising():
    with pytest.raises(NotImplementedError) as exc_info:
        embed_text("حَيض   جِي")
    # the harakat and extra whitespace must already be gone in the message,
    # proving normalize_sd ran before the NotImplementedError was raised
    assert "حيض جي" in str(exc_info.value)
    assert "َ" not in str(exc_info.value)
