from app.privacy.pii import pseudonymize, rehydrate


def test_pseudonymize_masks_and_rehydrates():
    text = (
        "Bitte kontaktieren Sie max.mustermann@stadt.de oder telefonisch 0211 123456. "
        "IBAN: DE89 3704 0044 0532 0130 00."
    )
    masked, mapping = pseudonymize(text)

    assert "max.mustermann@stadt.de" not in masked
    assert "[EMAIL_1]" in masked
    assert any(tok.startswith("[IBAN_") for tok in mapping)
    assert any(tok.startswith("[PHONE_") for tok in mapping)

    assert rehydrate(masked, mapping) == text


def test_pseudonymize_noop_when_clean():
    text = "Allgemeine Information ohne personenbezogene Daten."
    masked, mapping = pseudonymize(text)
    assert masked == text
    assert mapping == {}
