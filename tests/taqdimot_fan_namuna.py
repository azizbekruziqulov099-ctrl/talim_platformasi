SL = lambda sar, *els: {"sarlavha": sar, "elementlar": list(els)}
TEST = {"meta": {"mavzu": "Barcha slayd turlari sinovi", "fan": "Umumiy", "sinf": "5-sinf"}, "bolimlar": [
 {"nom": "Tillar", "slaydlar": [
  SL("Mevalar (Fruits)", {"tur": "lugat", "sozlar": [{"soz": "apple", "oqilishi": "[ˈæp.əl]", "tarjima": "olma", "misol": "I eat an apple every day.", "rasm": "olma_savat"},
      {"soz": "pizza", "oqilishi": "[ˈpiːt.sə]", "tarjima": "pitsa", "rasm": "pitsa_bolaklar", "misol": "We share a pizza."},
      {"soz": "cake", "oqilishi": "[keɪk]", "tarjima": "tort", "rasm": "tort_bolaklar", "misol": "Happy birthday cake!"}]}),
  SL("Lug‘at: 6 so‘z", {"tur": "lugat", "sozlar": [{"soz": "book", "tarjima": "kitob"}, {"soz": "pen", "tarjima": "ruchka"}, {"soz": "desk", "tarjima": "parta"},
      {"soz": "school", "tarjima": "maktab"}, {"soz": "teacher", "tarjima": "o‘qituvchi", "rasm": "oqituvchi_doska"}, {"soz": "friend", "tarjima": "do‘st", "rasm": "dostlik"}]}),
  SL("Tanishuv", {"tur": "dialog", "qatorlar": [{"kim": "Ali", "matn": "Hello! My name is Ali. What is your name?", "tarjima": "Salom! Mening ismim Ali. Ismingiz nima?"},
      {"kim": "Malika", "matn": "Hi, Ali! I am Malika. Nice to meet you.", "tarjima": "Salom, Ali! Men Malikaman. Tanishganimdan xursandman."},
      {"kim": "Ali", "matn": "Nice to meet you too!", "tarjima": "Men ham xursandman!"},
      {"kim": "Malika", "matn": "Where are you from?", "tarjima": "Qayerdansiz?"}]}),
 ]},
 {"nom": "Adabiyot va tarix", "slaydlar": [
  SL("She‘rdan parcha", {"tur": "parcha", "sarlavha": "Alisher Navoiy", "matn": "Ilm hosil qilmoqqa tirishgil, ey o‘g‘il,\nKim jahonda yo‘q ilmdan yaxshiroq.\nIlm — insonning ko‘zidagi nur,\nIlmsiz kishi — qorong‘ida yurur.", "muallif": "namuna matn", "belgilar": ["Ilm", "nur"]}),
  SL("Temuriylar davri", {"tur": "vaqt_chizigi", "voqealar": [{"sana": "1336", "nom": "Amir Temur tug‘ildi", "matn": "Kesh (Shahrisabz) yaqinida.", "rasm": "amir_temur"},
      {"sana": "1370", "nom": "Davlatga asos", "matn": "Poytaxt — Samarqand."}, {"sana": "1404", "nom": "Bibixonim masjidi", "matn": "Qurilish yakunlandi.", "rasm": "bibixonim"},
      {"sana": "1420", "nom": "Ulug‘bek rasadxonasi", "matn": "Samarqandda qurildi.", "rasm": "ulugbek"}, {"sana": "1441", "nom": "Navoiy tug‘ildi", "matn": "Hirotda.", "rasm": "alisher_navoiy"}]}),
  SL("O‘zbekiston viloyatlari", {"tur": "xarita", "hudud": "ozbekiston", "belgilash": ["Samarqand", "Buxoro", "Xorazm"], "joylar": [{"nom": "Toshkent"}, {"nom": "Samarqand", "matn": "Registon"}, {"nom": "Buxoro"}, {"nom": "Xiva"}, {"nom": "Nukus"}, {"nom": "Termiz"}]}),
  SL("Dunyo xaritasi", {"tur": "xarita", "hudud": "dunyo", "belgilash": ["O‘zbekiston", "Misr", "Gretsiya"], "joylar": [{"nom": "Qohira", "lat": 30.04, "lon": 31.24}, {"nom": "Afina", "lat": 37.98, "lon": 23.73}, {"nom": "Toshkent"}]}),
 ]},
 {"nom": "Tabiiy fanlar", "slaydlar": [
  SL("Suvning qaynashi", {"tur": "tajriba", "maqsad": "Suv qanday haroratda qaynashini kuzatish", "jihozlar": [{"nom": "Konussimon kolba", "rasm": "kolba_konus"}, {"nom": "Spirtovka", "rasm": "spirtovka"}, "Termometr", "Shtativ"],
      "bosqichlar": ["Kolbaga 100 ml suv quying.", "Kolbani shtativga mahkamlang.", "Spirtovkani yoqib, suvni isiting.", "Har daqiqada haroratni yozing."], "natija": "Suv 100 °C da qaynaydi (dengiz sathida).", "xavfsizlik": "Issiq kolbani qo‘l bilan ushlamang."}),
  SL("Suvning aylanishi", {"tur": "jarayon", "shakl": "aylana", "sarlavha": "Suv aylanishi", "bosqichlar": [{"nom": "Bug‘lanish", "matn": "Quyosh suvni isitadi"}, {"nom": "Bulut", "matn": "Bug‘ sovib bulut bo‘ladi", "rasm": "bulut_turlari"}, {"nom": "Yomg‘ir", "matn": "Tomchilar yerga tushadi"}, {"nom": "Oqim", "matn": "Suv daryo va dengizga qaytadi"}]}),
  SL("Oziq zanjiri", {"tur": "jarayon", "shakl": "zanjir", "bosqichlar": [{"nom": "O‘t", "matn": "Quyosh energiyasi"}, {"nom": "Quyon", "rasm": "quyon", "matn": "O‘t yeydi"}, {"nom": "Tulki", "matn": "Quyonni ovlaydi"}, {"nom": "Bakteriyalar", "matn": "Qoldiqlarni parchalaydi"}]}),
  SL("Ertalabki badantarbiya", {"tur": "jarayon", "shakl": "qadam", "bosqichlar": [{"nom": "Cho‘zilish", "matn": "Qo‘llarni yuqoriga", "rasm": "ertalabki_badantarbiya"}, {"nom": "Yugurish", "matn": "Joyida 1 daqiqa", "rasm": "yugurish"}, {"nom": "Sakrash", "matn": "10 marta", "rasm": "arqon_sakrash"}, {"nom": "Nafas", "matn": "Chuqur nafas oling"}]}),
 ]},
 {"nom": "San'at va o'yinlar", "slaydlar": [
  SL("O‘zbek cholg‘ulari", {"tur": "galereya", "rasmlar": [{"rasm": "dutor", "izoh": "Dutor"}, {"rasm": "doira", "izoh": "Doira"}, {"rasm": "nay", "izoh": "Nay"}, {"rasm": "rubob", "izoh": "Rubob"}]}),
  SL("Cholg‘ularni guruhlang", {"tur": "guruhlash", "guruhlar": [{"nom": "Torli", "bandlar": ["Dutor", "Tanbur", "Rubob", "Gitara"]}, {"nom": "Urma", "bandlar": ["Doira", "Baraban"]}, {"nom": "Puflama", "bandlar": ["Nay", "Karnay", "Surnay"]}]}),
  SL("Juftini toping", {"tur": "moslash", "juftlar": [{"chap": "apple", "ong": "olma"}, {"chap": "book", "ong": "kitob"}, {"chap": "cat", "ong": "mushuk"}, {"chap": "sun", "ong": "quyosh"}]}),
  SL("To‘g‘rimi?", {"tur": "togri_notogri", "fikrlar": [{"matn": "Yer Quyosh atrofida aylanadi.", "javob": True, "izoh": "Bir marta aylanishi — 1 yil."}, {"matn": "Suv 50 °C da qaynaydi.", "javob": False, "izoh": "Dengiz sathida 100 °C da."}, {"matn": "O‘simliklar fotosintezda kislorod chiqaradi.", "javob": True}, {"matn": "Kit — baliq.", "javob": False, "izoh": "Kit — sutemizuvchi."}]}),
  SL("Bo‘sh joyni to‘ldiring", {"tur": "bosh_joy", "gaplar": [{"matn": "I ___ a student.", "javob": "am"}, {"matn": "She ___ to school every day.", "javob": "goes"}, {"matn": "They ___ playing football.", "javob": "are"}]}),
  SL("Raqamlarda", {"tur": "raqamlar", "bandlar": [{"raqam": "72%", "nom": "O‘quvchilar", "matn": "yordam bilan vazifani bajardi"}, {"raqam": "1934", "nom": "Yil", "matn": "«Tafakkur va nutq»"}, {"raqam": "3×", "nom": "Tezlik"}]}),
  SL("Olim fikri", {"tur": "iqtibos", "matn": "Bola bugun hamkorlikda qila oladigan ishni ertaga mustaqil bajara oladi.", "muallif": "L.S. Vygotskiy", "manba": "Tafakkur va nutq, 1934"}),
  SL("Rasmda nima?", {"tur": "rasmda_nima", "rasm": "registon", "savol": "Bu qaysi obida?", "variantlar": ["Registon", "Ichan qal’a", "Ark", "Shohizinda"], "javob": 0}),
 ]}]}
