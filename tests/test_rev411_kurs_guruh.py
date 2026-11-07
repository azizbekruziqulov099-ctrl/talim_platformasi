from modules import kurs_guruh as kg

def test_holat_qoidasi():
    assert kg.holat_of(None, None, 20, 0) == "boshlamagan"
    assert kg.holat_of(3, "faol", 20, 5) == "yechmoqda"
    assert kg.holat_of(40, "faol", 20, 5) == "chiqdi"
    assert kg.holat_of(2, "chiqdi", 20, 5) == "chiqdi"
    assert kg.holat_of(2, "faol", 20, 20) == "tugatdi"
    assert kg.kod_norm(" ab-c9 ") == "ABC9" and len(kg.kod_yasa()) == 6
