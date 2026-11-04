
import pytest

from services.response_language_service import (
    validate_response_language,
)


@pytest.mark.parametrize(
    "language,response",
    [
        ("English", "Your refund request is under review."),
        ("Tamil", "உங்கள் கோரிக்கை பரிசீலனையில் உள்ளது."),
        ("Hindi", "आपका अनुरोध समीक्षा के अधीन है।"),
        ("Telugu", "మీ అభ్యర్థన పరిశీలనలో ఉంది."),
        ("Kannada", "ನಿಮ್ಮ ವಿನಂತಿಯನ್ನು ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ."),
        ("Malayalam", "നിങ്ങളുടെ അഭ്യർത്ഥന പരിശോധിക്കുന്നു."),
        ("French", "Votre demande est en cours d'examen."),
        ("Spanish", "Su solicitud está siendo revisada."),
    ],
)
def test_valid_language_response(language, response):
    validate_response_language(language, response)


@pytest.mark.parametrize(
    "language,response",
    [
        ("English", "உங்கள் கோரிக்கை பரிசீலனையில் உள்ளது."),
        ("English", "आपका अनुरोध समीक्षा के अधीन है।"),
        ("Tamil", "Your request is being reviewed."),
        ("Hindi", "Your request is being reviewed."),
        ("Telugu", "உங்கள் கோரிக்கை பரிசீலனையில் உள்ளது."),
        ("Kannada", "మీ అభ్యర్థన పరిశీలనలో ఉంది."),
        ("Malayalam", "ನಿಮ್ಮ ವಿನಂತಿಯನ್ನು ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ."),
        ("French", "आपका अनुरोध समीक्षा के अधीन है।"),
        ("Spanish", "உங்கள் கோரிக்கை பரிசீலனையில் உள்ளது."),
    ],
)
def test_language_mismatch_rejected(language, response):
    with pytest.raises(ValueError):
        validate_response_language(language, response)


@pytest.mark.parametrize(
    "language,response",
    [
        ("en", "Your request is being reviewed."),
        ("ta", "உங்கள் கோரிக்கை பரிசீலனையில் உள்ளது."),
        ("hi", "आपका अनुरोध समीक्षा के अधीन है।"),
        ("te", "మీ అభ్యర్థన పరిశీలనలో ఉంది."),
        ("kn", "ನಿಮ್ಮ ವಿನಂತಿಯನ್ನು ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ."),
        ("ml", "നിങ്ങളുടെ അഭ്യർത്ഥന പരിശോധിക്കുന്നു."),
        ("fr", "Votre demande est en cours d'examen."),
        ("es", "Su solicitud está siendo revisada."),
    ],
)
def test_iso_language_codes(language, response):
    validate_response_language(language, response)
