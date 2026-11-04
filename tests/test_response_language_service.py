
import pytest

from services.response_language_service import (
    validate_response_language,
)


def test_english_response_passes():
    validate_response_language(
        "English",
        "Dear Customer, please share your order ID.",
    )


def test_tamil_response_passes():
    validate_response_language(
        "Tamil",
        "வணக்கம், உங்கள் ஆர்டர் விவரங்களை வழங்கவும். நன்றி.",
    )


def test_tamil_response_rejected_for_english():
    with pytest.raises(
        ValueError,
        match="Response language mismatch",
    ):
        validate_response_language(
            "English",
            "வணக்கம், உங்கள் ஆர்டர் விவரங்களை வழங்கவும்.",
        )


def test_english_response_rejected_for_tamil():
    with pytest.raises(
        ValueError,
        match="Response language mismatch",
    ):
        validate_response_language(
            "Tamil",
            "Dear Customer, please share your order ID.",
        )


def test_unknown_language_is_not_blocked():
    validate_response_language(
        "French",
        "Bonjour, comment pouvons-nous vous aider?",
    )


def test_empty_response_rejected():
    with pytest.raises(
        ValueError,
        match="contains no letters",
    ):
        validate_response_language(
            "English",
            "12345",
        )
