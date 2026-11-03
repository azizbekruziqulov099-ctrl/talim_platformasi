"""REV271: Daraja aniqlash testi (placement) — CEFR A1–C1. Savollar o'zimiz yozgan (mualliflik huquqi toza).
Har daraja 8 savol (grammatika, so'z boyligi, kontekstda tushunish). Natija: pastdan yuqoriga — har darajada
kamida 60% to'g'ri bo'lsa o'sha daraja «o'zlashtirilgan»; birinchi yiqilgan darajada to'xtaydi."""
DARAJALAR = ["A1", "A2", "B1", "B2", "C1"]
CHEGARA = 0.6

def _q(i, d, tur, savol, v, j):
    return {"id": f"en{i:03d}", "daraja": d, "tur": tur, "savol": savol, "variantlar": v, "javob": j}

EN = [
    # A1
    _q(1, "A1", "grammatika", "She ___ a teacher.", ["am", "is", "are", "be"], 1),
    _q(2, "A1", "grammatika", "I ___ two brothers.", ["has", "have", "am", "having"], 1),
    _q(3, "A1", "so'z", "Which word is a colour?", ["table", "green", "happy", "run"], 1),
    _q(4, "A1", "grammatika", "___ you like apples?", ["Does", "Are", "Do", "Is"], 2),
    _q(5, "A1", "so'z", "The opposite of 'big' is ___.", ["tall", "small", "long", "old"], 1),
    _q(6, "A1", "tushunish", "'Where is the bank?' — 'It's ___ the school.' (yonida)", ["next to", "under", "in", "on"], 0),
    _q(7, "A1", "grammatika", "There ___ three cats in the garden.", ["is", "be", "are", "am"], 2),
    _q(8, "A1", "so'z", "We eat breakfast in the ___.", ["night", "morning", "evening", "afternoon tea"], 1),
    # A2
    _q(9, "A2", "grammatika", "Yesterday I ___ to the market.", ["go", "goes", "went", "gone"], 2),
    _q(10, "A2", "grammatika", "This bag is ___ than that one.", ["heavy", "heavier", "heaviest", "more heavy"], 1),
    _q(11, "A2", "grammatika", "Look! It ___ outside.", ["rains", "is raining", "rained", "rain"], 1),
    _q(12, "A2", "so'z", "I'm hungry. Let's ___ lunch now.", ["do", "have", "take", "go"], 1),
    _q(13, "A2", "grammatika", "We ___ to Samarkand next weekend.", ["are going", "went", "go to", "have gone"], 0),
    _q(14, "A2", "tushunish", "'Could you pass the salt?' — The speaker wants to ___.", ["buy salt", "get the salt", "cook", "leave"], 1),
    _q(15, "A2", "grammatika", "There isn't ___ milk in the fridge.", ["some", "many", "any", "a"], 2),
    _q(16, "A2", "so'z", "A person who treats sick animals is a ___.", ["vet", "nurse", "pilot", "chef"], 0),
    # B1
    _q(17, "B1", "grammatika", "I ___ here since 2020.", ["live", "am living", "have lived", "lived"], 2),
    _q(18, "B1", "grammatika", "If it rains tomorrow, we ___ at home.", ["stay", "will stay", "would stay", "stayed"], 1),
    _q(19, "B1", "grammatika", "The book ___ by millions of people.", ["has read", "has been read", "is reading", "reads"], 1),
    _q(20, "B1", "so'z", "She was so tired that she ___ asleep on the bus.", ["fell", "felt", "dropped", "went down"], 0),
    _q(21, "B1", "grammatika", "He asked me where I ___.", ["work", "worked", "am working", "will work"], 1),
    _q(22, "B1", "so'z", "Can you ___ after my plants while I'm away?", ["look", "see", "watch", "care"], 0),
    _q(23, "B1", "tushunish", "'I'd rather not go out tonight.' — The speaker ___.", ["wants to go out", "prefers to stay in", "is going out later", "has already gone out"], 1),
    _q(24, "B1", "grammatika", "You ___ wear a uniform at our school. It's a rule.", ["might", "can", "have to", "would"], 2),
    # B2
    _q(25, "B2", "grammatika", "If I ___ about the traffic, I would have left earlier.", ["knew", "had known", "would know", "have known"], 1),
    _q(26, "B2", "grammatika", "By the time we arrived, the film ___.", ["already started", "has already started", "had already started", "was already starting"], 2),
    _q(27, "B2", "so'z", "The company decided to ___ the meeting until next week.", ["put off", "put on", "put up", "put out"], 0),
    _q(28, "B2", "grammatika", "She denied ___ the window.", ["to break", "breaking", "break", "broken"], 1),
    _q(29, "B2", "so'z", "His argument was very ___; everyone agreed with him.", ["persuasive", "pervasive", "permissive", "perceptive"], 0),
    _q(30, "B2", "grammatika", "Not only ___ late, but he also forgot the documents.", ["he was", "was he", "he is", "did he"], 1),
    _q(31, "B2", "tushunish", "'The results were far from satisfactory.' — The results were ___.", ["excellent", "quite good", "poor", "far away"], 2),
    _q(32, "B2", "so'z", "Recycling helps to ___ waste.", ["reduce", "remove off", "lessen up", "decline"], 0),
    # C1
    _q(33, "C1", "grammatika", "___ had she entered the room than the phone rang.", ["No sooner", "Hardly", "As soon", "Barely"], 0),
    _q(34, "C1", "so'z", "The new policy has been widely ___ for its lack of transparency.", ["criticised", "critiqued off", "condemned to", "blamed on"], 0),
    _q(35, "C1", "grammatika", "It's high time we ___ a decision.", ["make", "made", "will make", "have made"], 1),
    _q(36, "C1", "so'z", "The author's style is so ___ that every sentence must be read twice.", ["dense", "dull", "dim", "dire"], 0),
    _q(37, "C1", "tushunish", "'Her remarks were somewhat tongue-in-cheek.' — Her remarks were ___.", ["serious and angry", "not meant entirely seriously", "rude", "difficult to hear"], 1),
    _q(38, "C1", "grammatika", "Were the government ___ taxes, prices would rise.", ["to raise", "raising", "raised", "raise"], 0),
    _q(39, "C1", "so'z", "The findings ___ doubt on earlier theories.", ["cast", "threw up", "put", "made"], 0),
    _q(40, "C1", "tushunish", "'The plan is, by and large, sound.' — The plan is ___.", ["completely wrong", "generally good", "too large", "very noisy"], 1),
]
SAVOLLAR = {"en": EN}


def savollar(til):
    """Javobsiz savollar (brauzerga)."""
    return [{k: v for k, v in s.items() if k != "javob"} for s in SAVOLLAR.get(til, [])]


def baholash(til, javoblar, ui="uz"):
    """javoblar: {savol_id: tanlangan_index}. Natija: daraja, har daraja foizi, tavsiya."""
    bank = SAVOLLAR.get(til, [])
    hisob = {d: [0, 0] for d in DARAJALAR}
    for s in bank:
        hisob[s["daraja"]][1] += 1
        if str(s["id"]) in javoblar and int(javoblar[str(s["id"])]) == s["javob"]:
            hisob[s["daraja"]][0] += 1
    foiz = {d: round(100 * a / b) if b else 0 for d, (a, b) in hisob.items()}
    daraja = "A0"
    for d in DARAJALAR:
        if hisob[d][1] and hisob[d][0] / hisob[d][1] >= CHEGARA:
            daraja = d
        else:
            break
    keyingi = DARAJALAR[DARAJALAR.index(daraja) + 1] if daraja in DARAJALAR[:-1] else ("A1" if daraja == "A0" else None)
    t = ui if ui in ("ru", "en") else "uz"
    if daraja == "A0":
        tavsiya = {"uz": "Siz boshlang'ich bosqichdasiz — A1 darajasidan, eng oddiy hayotiy vaziyatlardan boshlaymiz.",
                   "ru": "Вы в самом начале — начнём с уровня A1, с самых простых жизненных ситуаций.",
                   "en": "You are at the very start — we begin at A1 with the simplest everyday situations."}[t]
    elif keyingi:
        tavsiya = {"uz": f"Darajangiz: {daraja}. Kursni {keyingi} darajasidan boshlaysiz.", "ru": f"Ваш уровень: {daraja}. Вы начнёте курс с уровня {keyingi}.",
                   "en": f"Your level: {daraja}. You will start the course at {keyingi}."}[t]
    else:
        tavsiya = {"uz": "Darajangiz: C1 va undan yuqori. Imtihon formatidagi sinov testlari va murakkab yozish/gapirish mashqlaridan boshlaysiz.",
                   "ru": "Ваш уровень: C1 и выше. Начнёте с пробных тестов в формате экзамена и сложных заданий по письму и говорению.",
                   "en": "Your level: C1 or higher. You will start with exam-format mock tests and advanced writing and speaking tasks."}[t]
    return {"daraja": daraja, "foiz": foiz, "keyingi": keyingi, "tavsiya": tavsiya}
