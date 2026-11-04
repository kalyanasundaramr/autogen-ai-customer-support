
import unicodedata


# Unicode ranges for languages with distinctive scripts.
LANGUAGE_SCRIPTS = {
    "tamil": (0x0B80, 0x0BFF),
    "telugu": (0x0C00, 0x0C7F),
    "kannada": (0x0C80, 0x0CFF),
    "malayalam": (0x0D00, 0x0D7F),
    "hindi": (0x0900, 0x097F),
}

LANGUAGE_ALIASES = {
    "en": "english",
    "ta": "tamil",
    "te": "telugu",
    "kn": "kannada",
    "ml": "malayalam",
    "hi": "hindi",
    "fr": "french",
    "es": "spanish",
}


def validate_response_language(
    language: str,
    response: str,
) -> None:
    """
    Validate clear response-script mismatches.

    This is a script-level safeguard, not a
    complete multilingual language detector.

    Languages sharing a script, such as English,
    French, and Spanish, require additional
    language identification.
    """

    if not isinstance(language, str):
        raise ValueError("Language must be a string.")

    if not isinstance(response, str):
        raise ValueError("Response must be a string.")

    expected = language.strip().casefold()
    expected = LANGUAGE_ALIASES.get(expected, expected)

    letters = [
        char for char in response
        if unicodedata.category(char).startswith("L")
    ]

    if not letters:
        raise ValueError(
            "Customer response contains no letters."
        )

    total_letters = len(letters)

    script_counts = {}

    for script, (start, end) in LANGUAGE_SCRIPTS.items():
        script_counts[script] = sum(
            start <= ord(char) <= end
            for char in letters
        )

    if expected in LANGUAGE_SCRIPTS:
        expected_ratio = (
            script_counts[expected] / total_letters
        )

        if expected_ratio < 0.20:
            raise ValueError(
                "Response language mismatch: "
                f"{expected.title()} expected, "
                "but insufficient matching-script "
                "text was generated."
            )

        other_script_count = sum(
            count
            for script, count in script_counts.items()
            if script != expected
        )

        if other_script_count / total_letters > 0.20:
            raise ValueError(
                "Response contains substantial text "
                "from another Indian-language script."
            )

    elif expected in {
        "english",
        "french",
        "spanish",
    }:
        indian_script_count = sum(
            script_counts.values()
        )

        if indian_script_count / total_letters > 0.20:
            raise ValueError(
                "Response language mismatch: "
                f"{expected.title()} expected, "
                "but substantial Indian-script "
                "text was generated."
            )

    # Unknown languages are not rejected solely
    # because this validator lacks their script.
    # They require a separate language check.
