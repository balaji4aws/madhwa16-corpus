"""Tests for corpus passage retrieval rules."""
from app.main import passages_for, retrieve, tokenize


def test_tokenize_preserves_unicode_words():
    assert "ಕೃಷ್ಣನ" in tokenize("ಕೃಷ್ಣನ ಬಾಲ್ಯದಲ್ಲಿ")


def test_masked_sanskrit_is_never_a_passage():
    record = {
        "metadata": {"title": "Test", "source_url": "https://example.com",
                     "status": "machine-draft", "slug": "test"},
        "manifest": {"title": "Test", "source_url": "https://example.com"},
        "transcript": (
            "[00:01] [unverified Sanskrit verse recited — masked pending human validation]\n"
            "[00:09] ಕೃಷ್ಣನ ಬಾಲ್ಯದಲ್ಲಿ ಒಬ್ಬಳು ಗೆಳತಿ ಇದ್ದಳು"
        ),
    }
    passages = passages_for(record)
    assert len(passages) == 1
    assert "unverified Sanskrit" not in passages[0]["text"]


def test_empty_or_unrelated_query_does_not_return_evidence():
    assert retrieve("zzzxxyy unrelated hypothetical topic") == []
