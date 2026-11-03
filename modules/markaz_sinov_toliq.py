"""REV280: Milliy sertifikat (multilevel) uslubidagi TO'LIQ sinov — ingliz tili, 1-variant.
Listening 35 va Reading 35 topshiriq, imtihondagi kabi qismlarga bo'lingan: tanlash (A/B/C/D), bo'sh joy to'ldirish (so'z/son),
True/False/Not Given, sarlavha moslashtirish. Hamma matn va savollar o'zimiz yozgan."""
def _m(i, savol, var, j): return {"id": i, "tur": "tanlash", "savol": savol, "variantlar": var, "javob": j}
def _g(i, savol, javoblar): return {"id": i, "tur": "yozish", "savol": savol, "javob": javoblar}   # javoblar: qabul qilinadigan variantlar
TFN = ["True", "False", "Not Given"]
# sarlavhalar aralash tartibda (javob paragraf tartibiga mos kelmasin)
_SARL = ["Better health", "The hidden costs", "Cooler streets", "Choosing wisely", "Help from residents", "Mistakes of the past", "Cleaner air", "Higher property values"]

LISTENING = [
 {"id": "LP1", "qism": "Part 1 — Short conversations (1–8)", "izoh": "You will hear eight short conversations. Choose the correct answer.",
  "audio": [
   ("Woman: Are you coming to the meeting at three? Man: I can't, my train is at half past two. Can you tell me about it later?", _m("L01", "Why can't the man go to the meeting?", ["He is ill", "He has a train to catch", "He has another meeting"], 1)),
   ("Man: How was the new restaurant? Woman: The food was lovely, but we waited almost an hour for it.", _m("L02", "What was the problem with the restaurant?", ["The food", "The price", "The service was slow"], 2)),
   ("Woman: Is the bank open on Saturday? Man: Only in the morning, until one o'clock.", _m("L03", "When is the bank open on Saturday?", ["All day", "Until 1 p.m.", "It is closed"], 1)),
   ("Man: Did you buy the blue jacket? Woman: No, it was too big, so I got the black one in a smaller size.", _m("L04", "Which jacket did the woman buy?", ["The blue one", "The black one", "Neither"], 1)),
   ("Woman: How do you usually get to work? Man: I used to drive, but now I cycle. It's cheaper and healthier.", _m("L05", "How does the man travel to work now?", ["By car", "By bicycle", "By bus"], 1)),
   ("Man: When is your sister's wedding? Woman: It was going to be in June, but they moved it to September.", _m("L06", "When is the wedding now?", ["In June", "In July", "In September"], 2)),
   ("Woman: Shall we watch the film at home? Man: Let's go to the cinema instead — the screen is much better.", _m("L07", "What does the man suggest?", ["Watching at home", "Going to the cinema", "Reading a book"], 1)),
   ("Man: I'd like to book a table for four for Friday. Woman: Sorry, Friday is full. We have a table on Saturday.", _m("L08", "What is the problem?", ["No tables on Friday", "The restaurant is closed", "The table is too small"], 0)),
  ]},
 {"id": "LP2", "qism": "Part 2 — Note completion (9–14)", "izoh": "Listen to information about a sports centre. Write ONE word or a number for each gap.",
  "matn": "Welcome to Riverside Sports Centre. We are open every day from six in the morning until ten at night. The swimming pool is "
          "on the ground floor, and the gym is on the first floor. Membership costs forty dollars a month, or four hundred dollars for a whole year. "
          "New members get a free personal training session. Yoga classes take place every Tuesday and Thursday evening. To join, please bring "
          "a photo and your passport to reception.",
  "savollar": [_g("L09", "The centre closes at ___ p.m.", ["10", "ten"]), _g("L10", "The gym is on the ___ floor.", ["first", "1st"]),
               _g("L11", "Monthly membership: ___ dollars.", ["40", "forty"]), _g("L12", "New members get a free ___ training session.", ["personal"]),
               _g("L13", "Yoga is on Tuesday and ___ .", ["thursday"]), _g("L14", "Bring a photo and your ___ .", ["passport"])]},
 {"id": "LP3", "qism": "Part 3 — Speakers (15–20)", "izoh": "Listen to six people talking about learning a language. Choose the correct answer for each speaker.",
  "audio": [
   ("Speaker 1: I learned most of my English from songs. I listened to the same song again and again until I understood every word.", _m("L15", "Speaker 1 mainly learned through…", ["music", "films", "a teacher"], 0)),
   ("Speaker 2: For me, the hardest part was speaking. I knew the grammar, but I was afraid of making mistakes.", _m("L16", "Speaker 2 found it difficult to…", ["read", "speak", "write"], 1)),
   ("Speaker 3: I moved to London for work and had no choice. After six months I was dreaming in English!", _m("L17", "Speaker 3 learned because…", ["of a job abroad", "of school", "of a friend"], 0)),
   ("Speaker 4: I use an app every morning for fifteen minutes. Little and often is the secret.", _m("L18", "Speaker 4 studies…", ["once a week", "a little every day", "only at weekends"], 1)),
   ("Speaker 5: My teacher made every lesson a game. I never felt bored, even with difficult topics.", _m("L19", "Speaker 5 liked lessons because they were…", ["short", "fun", "free"], 1)),
   ("Speaker 6: I watched TV series with subtitles. First in my language, then in English, and finally with none.", _m("L20", "Speaker 6 used…", ["TV series", "books", "podcasts"], 0)),
  ]},
 {"id": "LP4", "qism": "Part 4 — Interview (21–28)", "izoh": "Listen to an interview with a young chef. Choose the correct answer.",
  "matn": "Interviewer: Laylo, you opened your own café at only twenty-four. How did it start? Laylo: I always loved cooking with my grandmother. "
          "At university I studied economics, but I spent every weekend working in a restaurant kitchen. Interviewer: Was it hard to open a café? "
          "Laylo: Very. The bank refused to give me a loan twice. In the end my family helped me, and I promised to pay them back in three years. "
          "Interviewer: What makes your café different? Laylo: We use only local vegetables and fruit, and the menu changes every season. "
          "We also teach free cooking classes for children on Sundays. Interviewer: What is the most difficult part of the job? Laylo: Honestly, "
          "the long hours. I start at six and often finish after ten. But when customers say the food reminds them of home, I forget I'm tired. "
          "Interviewer: Any advice for young people? Laylo: Get experience first. Work in a real kitchen before you open your own place.",
  "savollar": [_m("L21", "Who first taught Laylo to cook?", ["Her mother", "Her grandmother", "A chef"], 1),
               _m("L22", "What did she study at university?", ["Cooking", "Economics", "Languages"], 1),
               _m("L23", "Who helped her to open the café?", ["The bank", "Her family", "A friend"], 1),
               _m("L24", "She promised to return the money in…", ["one year", "two years", "three years"], 2),
               _m("L25", "What is special about the menu?", ["It never changes", "It changes every season", "It has only desserts"], 1),
               _m("L26", "On Sundays the café…", ["is closed", "teaches children to cook", "has live music"], 1),
               _m("L27", "What does she find most difficult?", ["The customers", "The long hours", "The prices"], 1),
               _m("L28", "Her advice is to…", ["get experience first", "borrow money", "study abroad"], 0)]},
 {"id": "LP5", "qism": "Part 5 — Talk (29–35)", "izoh": "Listen to a short talk about sleep. Choose the correct answer.",
  "matn": "Most adults need between seven and nine hours of sleep a night, but many people sleep much less. Scientists say that poor sleep affects "
          "our memory, our mood and even our immune system. Teenagers are a special case: their body clock changes, so they naturally feel sleepy later "
          "in the evening. That is why some schools now start lessons at nine instead of eight. Screens are another problem. The light from phones tells "
          "the brain that it is still daytime, so experts recommend stopping using them an hour before bed. A short nap of twenty minutes can help, "
          "but longer naps may make it harder to sleep at night. Finally, going to bed and waking up at the same time every day — even at weekends — "
          "is one of the simplest ways to sleep better.",
  "savollar": [_m("L29", "How much sleep do most adults need?", ["5–6 hours", "7–9 hours", "10–11 hours"], 1),
               _m("L30", "Poor sleep affects memory, mood and…", ["the immune system", "eyesight", "height"], 0),
               _m("L31", "Teenagers feel sleepy later because…", ["they drink coffee", "their body clock changes", "they study more"], 1),
               _m("L32", "Some schools now start lessons at…", ["8 o'clock", "9 o'clock", "10 o'clock"], 1),
               _m("L33", "Experts recommend stopping using phones…", ["at midnight", "an hour before bed", "after dinner"], 1),
               _m("L34", "A helpful nap is about…", ["twenty minutes", "one hour", "two hours"], 0),
               _m("L35", "One of the simplest ways to sleep better is to…", ["sleep longer at weekends", "keep the same times every day", "exercise at night"], 1)]},
]

READING = [
 {"id": "RP1", "qism": "Part 1 — Gap filling (1–6)", "izoh": "Choose the best word for each gap.",
  "matn": "Dear Mr Karimov, I am writing to (1) ___ about the course I booked. The website said the classes would (2) ___ at 6 p.m., "
          "but they actually start at 5 p.m., which is too early for me (3) ___ I finish work at 5:30. Could you please (4) ___ me to the evening group? "
          "I would also like to know (5) ___ the books are included in the price. I look (6) ___ to hearing from you. Yours sincerely, Dilnoza Rahimova",
  "savollar": [_m("R01", "(1)", ["complain", "explain", "remain", "obtain"], 0), _m("R02", "(2)", ["begin", "began", "begun", "beginning"], 0),
               _m("R03", "(3)", ["so", "because", "but", "although"], 1), _m("R04", "(4)", ["move", "make", "take", "bring"], 0),
               _m("R05", "(5)", ["what", "whether", "which", "who"], 1), _m("R06", "(6)", ["forward", "ahead", "after", "up"], 0)]},
 {"id": "RP2", "qism": "Part 2 — Headings (7–14)", "izoh": "Choose the best heading for each paragraph.",
  "matn": "A. Many cities are planting trees on their streets. Trees give shade, so streets stay cooler in hot summers. "
          "B. Trees also clean the air by taking in dust and harmful gases from cars. "
          "C. However, planting a tree is the easy part. Young trees need water and care for several years, which costs money. "
          "D. Some cities ask local people to adopt a tree and water it during dry weeks. "
          "E. Research shows that people who live near green areas visit the doctor less often. "
          "F. Trees can also increase the price of nearby houses by up to ten percent. "
          "G. In the past, some cities cut down trees to make roads wider, and many now regret it. "
          "H. Experts say the best results come when the right type of tree is chosen for the local climate.",
  "sarlavhalar": _SARL,
  "savollar": [_m(f"R{7+i:02d}", f"Paragraph {'ABCDEFGH'[i]}", _SARL, _SARL.index(t))
               for i, t in enumerate(["Cooler streets", "Cleaner air", "The hidden costs", "Help from residents", "Better health", "Higher property values", "Mistakes of the past", "Choosing wisely"])]},
 {"id": "RP3", "qism": "Part 3 — True / False / Not Given (15–22)", "izoh": "Read the text. Are the statements True, False or Not Given?",
  "matn": "The Silk Road was not a single road but a network of routes connecting China with the Mediterranean. For more than a thousand years, "
          "merchants carried silk, spices, paper and ideas along these routes. Samarkand and Bukhara became rich trading centres where travellers "
          "rested and exchanged goods. Most merchants did not travel the whole distance; instead, goods passed from one trader to another. "
          "The routes were also dangerous: travellers faced deserts, mountains and sometimes robbers. With the growth of sea trade in the fifteenth century, "
          "the land routes slowly became less important. Today, many of the old cities attract tourists from all over the world.",
  "savollar": [_m("R15", "The Silk Road was one single road.", TFN, 1), _m("R16", "Ideas were exchanged as well as goods.", TFN, 0),
               _m("R17", "Samarkand was a trading centre.", TFN, 0), _m("R18", "Most merchants travelled from China to the Mediterranean.", TFN, 1),
               _m("R19", "Silk was the most expensive product.", TFN, 2), _m("R20", "Travelling on the routes could be dangerous.", TFN, 0),
               _m("R21", "Sea trade became more important in the fifteenth century.", TFN, 0), _m("R22", "Tourism is now the main industry of Bukhara.", TFN, 2)]},
 {"id": "RP4", "qism": "Part 4 — Longer text (23–29)", "izoh": "Read the article and choose the correct answer.",
  "matn": "When Sherzod started working from home, he thought it would be easy. No traffic, no expensive lunches, and more time with his children. "
          "But after a few weeks he noticed problems. He worked longer hours because the office was always 'open', he moved much less, and he missed his colleagues. "
          "So he made some rules. First, he created a separate work corner and stopped working on the sofa. Second, he started and finished at fixed times. "
          "Third, he went for a twenty-minute walk every lunchtime. He also arranged a weekly video call with his team that was only for chatting, not for work. "
          "'The first month was a mess,' he says. 'Now I am more productive than in the office — but only because I treat home working seriously.'",
  "savollar": [_m("R23", "At first Sherzod expected working from home to be…", ["difficult", "easy", "boring", "expensive"], 1),
               _m("R24", "One problem was that he…", ["earned less", "worked longer hours", "lost his job", "travelled more"], 1),
               _m("R25", "He also felt…", ["lonely without colleagues", "happier with colleagues", "tired of his children", "too busy to eat"], 0),
               _m("R26", "His first rule was to…", ["work on the sofa", "have a separate work place", "work at night", "buy a new computer"], 1),
               _m("R27", "Every lunchtime he…", ["sleeps", "goes for a walk", "calls his boss", "cooks for the family"], 1),
               _m("R28", "The weekly video call is for…", ["planning projects", "chatting", "training", "reports"], 1),
               _m("R29", "Now he says he is more productive because he…", ["works more hours", "treats home working seriously", "has a bigger office", "never takes breaks"], 1)]},
 {"id": "RP5", "qism": "Part 5 — Summary completion (30–35)", "izoh": "Complete the summary with ONE word from the text in Part 4.",
  "savollar": [_g("R30", "Working from home meant no ___ on the way to work.", ["traffic"]), _g("R31", "Sherzod stopped working on the ___ .", ["sofa"]),
               _g("R32", "He started and finished at ___ times.", ["fixed"]), _g("R33", "His walk lasted twenty ___ .", ["minutes"]),
               _g("R34", "The video call was with his ___ .", ["team"]), _g("R35", "He says the first ___ was a mess.", ["month"])]},
]

def _norm(t): return " ".join(str(t or "").strip().lower().replace(".", "").split())

def ochiq():
    def toza(q):
        return {k: v for k, v in q.items() if k != "javob"}
    def bolim(B):
        out = []
        for b in B:
            x = {k: v for k, v in b.items() if k not in ("audio", "savollar")}
            if "audio" in b:
                x["audio"] = [{"matn": m, "savol": toza(q)} for m, q in b["audio"]]
            if "savollar" in b:
                x["savollar"] = [toza(q) for q in b["savollar"]]
            out.append(x)
        return out
    return {"listening": bolim(LISTENING), "reading": bolim(READING), "turi": "toliq", "variant": 1}

def baholash(javoblar):
    from modules.markaz_sertifikat import chegaralar
    out = {}
    for nom, B in (("listening", LISTENING), ("reading", READING)):
        togri = jami = 0; xatolar = []
        for b in B:
            qs = [q for _, q in b.get("audio", [])] + b.get("savollar", [])
            for q in qs:
                jami += 1
                v = javoblar.get(q["id"], "")
                ok = (q["tur"] == "tanlash" and str(v) != "" and str(v).lstrip("-").isdigit() and int(v) == q["javob"]) or \
                     (q["tur"] == "yozish" and _norm(v) in [_norm(x) for x in q["javob"]])
                if ok: togri += 1
                else: xatolar.append({"id": q["id"], "savol": q["savol"], "togri": q["variantlar"][q["javob"]] if q["tur"] == "tanlash" else q["javob"][0]})
        # rasmiy imtihonda 35 savol → 75 ball (Rasch o'rniga proporsional yaqinlashuv)
        b75 = round(75 * togri / jami) if jami else 0
        out[nom] = {"togri": togri, "jami": jami, "ball": b75, "daraja": chegaralar(b75), "xatolar": xatolar}
    return out
