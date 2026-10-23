"""REV158: pulli kurs — o'qituvchi rekvizitlari (Click havolasi, Paynet, karta) va o'quvchi tanlagan usul."""
import pytest
from fastapi import HTTPException

from modules.academy_payments import details_view, payment_details_clean


def test_valid_details_and_methods():
    d = payment_details_clean({"click_url": "https://my.click.uz/services/pay?service_id=1", "paynet": "+998 90 123 45 67",
                               "card_number": "8600 1234 5678 9012", "card_holder": "Aziz Ahmadov", "note": "Izohga ismingizni yozing"})
    assert d["card_number"] == "8600123456789012"
    assert details_view(d)["methods"] == ["click", "paynet", "karta"]
    assert details_view(None)["methods"] == []


@pytest.mark.parametrize("bad", [
    {"click_url": "http://my.click.uz/x"},
    {"click_url": "https://evil.example/click.uz"},
    {"card_number": "8600123456789016", "card_holder": "A"},   # Luhn xato
    {"card_number": "8600123456789012"},                       # egasi yo'q
    {"paynet": "https://paynet.uz.evil.com/x"},
])
def test_invalid_details_rejected(bad):
    with pytest.raises(HTTPException):
        payment_details_clean(bad)
