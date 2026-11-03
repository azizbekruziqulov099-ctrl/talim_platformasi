"""REV278: Milliy sertifikat (CEFR, multilevel) uslubidagi SINOV imtihoni — ingliz tili, B1–B2 darajasi.
Hamma matn, audio-skript va savollar o'zimiz yozgan (rasmiy imtihon materiallari ko'chirilmagan).
«Mini» sinov: Listening 10, Reading 10, Writing 2 topshiriq, Speaking 3 qism; ball har bo'limda 0–75 ga keltiriladi
(rasmiy shkala: B1 38–50, B2 51–64, C1 65–75). To'liq sinov (35+35) keyingi bosqichda."""

LISTENING = [
    {"id": "L1", "matn": "Woman: Excuse me, does the number twelve bus go to the city library? Man: No, you need the number seven. "
                         "It stops right outside the library, and it comes every fifteen minutes. Woman: Thank you. Where is the bus stop? "
                         "Man: Just across the road, next to the pharmacy.",
     "savollar": [{"id": "L1a", "savol": "Which bus goes to the library?", "variantlar": ["Number twelve", "Number seven", "Number fifteen"], "javob": 1},
                  {"id": "L1b", "savol": "How often does the bus come?", "variantlar": ["Every five minutes", "Every twelve minutes", "Every fifteen minutes"], "javob": 2},
                  {"id": "L1c", "savol": "Where is the bus stop?", "variantlar": ["Next to the pharmacy", "Outside the library", "Behind the bank"], "javob": 0}]},
    {"id": "L2", "matn": "Good morning, everyone. Before we start the tour, a few important points. The museum closes at five today, "
                         "not six, because of a private event. Photography is allowed in all rooms except the gold collection on the second floor. "
                         "If you would like an audio guide, they cost three dollars and you can collect one at the information desk. "
                         "Our café is on the ground floor and offers a ten percent discount to students.",
     "savollar": [{"id": "L2a", "savol": "What time does the museum close today?", "variantlar": ["At four", "At five", "At six"], "javob": 1},
                  {"id": "L2b", "savol": "Where are visitors NOT allowed to take photos?", "variantlar": ["In the café", "On the ground floor", "In the gold collection"], "javob": 2},
                  {"id": "L2c", "savol": "Where can you get an audio guide?", "variantlar": ["At the information desk", "In the café", "On the second floor"], "javob": 0},
                  {"id": "L2d", "savol": "Who gets a discount in the café?", "variantlar": ["Teachers", "Students", "Families"], "javob": 1}]},
    {"id": "L3", "matn": "Man: Have you decided where to go on holiday this summer? Woman: I was thinking about the mountains, but my sister "
                         "wants to go to the seaside. Man: Why not do both? You could spend a week in the mountains and then travel to the coast. "
                         "Woman: That's a good idea, but it might be too expensive. I'll check train prices tonight. Man: Book early — "
                         "tickets get much cheaper if you buy them a month before.",
     "savollar": [{"id": "L3a", "savol": "Where does the woman's sister want to go?", "variantlar": ["To the mountains", "To the seaside", "To the city"], "javob": 1},
                  {"id": "L3b", "savol": "What is the woman worried about?", "variantlar": ["The weather", "The cost", "Her job"], "javob": 1},
                  {"id": "L3c", "savol": "What does the man advise her to do?", "variantlar": ["Travel by plane", "Stay at home", "Buy tickets early"], "javob": 2}]},
]

READING = [
    {"id": "R1", "sarlavha": "Learning a language outdoors",
     "matn": "Many people believe that languages are best learned in a classroom. However, a growing number of teachers are taking their "
             "lessons outside. In one school in Samarkand, students practise English while visiting local markets, parks and museums. "
             "They ask sellers questions, describe what they see and record short videos for their classmates. Their teacher says that "
             "students remember new words much better when they use them in real situations. At first, some parents were unsure, because "
             "they thought the trips were only for fun. But after one term, the students' speaking test results improved by almost twenty percent. "
             "The school now plans to organise one outdoor lesson every week.",
     "savollar": [{"id": "R1a", "savol": "Where do the students practise English?", "variantlar": ["Only in the classroom", "In real places around the city", "At home online"], "javob": 1},
                  {"id": "R1b", "savol": "According to the teacher, why do students remember words better?", "variantlar": ["They use them in real situations", "They have more homework", "They watch films"], "javob": 0},
                  {"id": "R1c", "savol": "How did some parents feel at first?", "variantlar": ["Excited", "Unsure", "Angry"], "javob": 1},
                  {"id": "R1d", "savol": "What happened after one term?", "variantlar": ["Speaking results improved", "The trips stopped", "Parents complained"], "javob": 0},
                  {"id": "R1e", "savol": "The school will have outdoor lessons…", "variantlar": ["every day", "every month", "every week"], "javob": 2}]},
    {"id": "R2", "sarlavha": "Notice: Changes to the city swimming pool",
     "matn": "From 1 March, the city swimming pool will open at 6:30 a.m. instead of 7:00 a.m. on weekdays. Weekend hours stay the same. "
             "Monthly cards can now be bought online, and card holders may bring one guest free of charge on Sundays. "
             "Please note that children under ten must be accompanied by an adult at all times. The small pool will be closed for repairs "
             "during the first two weeks of March.",
     "savollar": [{"id": "R2a", "savol": "What changes on weekdays?", "variantlar": ["The pool opens earlier", "The pool closes earlier", "Nothing changes"], "javob": 0},
                  {"id": "R2b", "savol": "Card holders can bring a free guest…", "variantlar": ["every day", "on Sundays", "on Saturdays"], "javob": 1},
                  {"id": "R2c", "savol": "Who must be with an adult?", "variantlar": ["Children under ten", "All guests", "Card holders"], "javob": 0},
                  {"id": "R2d", "savol": "Monthly cards can be bought…", "variantlar": ["only at the pool", "online", "at school"], "javob": 1},
                  {"id": "R2e", "savol": "The small pool will be closed…", "variantlar": ["all of March", "for two weeks", "on Sundays"], "javob": 1}]},
]

WRITING = [
    {"id": "W1", "nom": "Task 1 (letter)", "soz": "120–150",
     "topshiriq": "Your English friend is going to visit your city for the first time. Write a letter to your friend. "
                  "Tell them about the best time to visit, what they should see, and what food they must try."},
    {"id": "W2", "nom": "Task 2 (essay)", "soz": "180–220",
     "topshiriq": "Some people think that students should learn at least one foreign language at school from the age of six. "
                  "Do you agree or disagree? Give reasons and examples from your own experience."},
]

SPEAKING = [
    {"id": "S1", "nom": "Part 1 — Interview", "savollar": ["Where do you live, and what do you like about it?", "What do you usually do at the weekend?", "Why are you learning English?"]},
    {"id": "S2", "nom": "Part 2 — Describe", "savollar": ["Describe a place you visited that you really enjoyed. Say where it was, who you went with, what you did there and why you liked it. (Speak for about one minute.)"]},
    {"id": "S3", "nom": "Part 3 — Discussion", "savollar": ["Some people say that travelling is the best way to learn about the world. Do you agree? Why or why not?"]},
]

def chegaralar(ball75):
    return "C1" if ball75 >= 65 else "B2" if ball75 >= 51 else "B1" if ball75 >= 38 else "B1 dan past"

def sinov_ochiq():
    """Javobsiz (brauzerga)."""
    def toza(qism):
        return [{**b, "savollar": [{k: v for k, v in s.items() if k != "javob"} for s in b["savollar"]]} for b in qism]
    return {"listening": toza(LISTENING), "reading": toza(READING), "writing": WRITING, "speaking": SPEAKING,
            "shkala": "har bo'lim 0–75; B1 38–50, B2 51–64, C1 65–75", "turi": "mini"}

def obyektiv_ball(javoblar):
    """Listening va Reading: to'g'ri javoblar → 0–75 shkala (mini sinovda proporsional)."""
    out = {}
    for nom, qism in (("listening", LISTENING), ("reading", READING)):
        jami = togri = 0; xatolar = []
        for b in qism:
            for s in b["savollar"]:
                jami += 1
                t = str(javoblar.get(s["id"], ""))
                if t != "" and int(t) == s["javob"]:
                    togri += 1
                else:
                    xatolar.append({"id": s["id"], "savol": s["savol"], "togri": s["variantlar"][s["javob"]]})
        b75 = round(75 * togri / jami) if jami else 0
        out[nom] = {"togri": togri, "jami": jami, "ball": b75, "daraja": chegaralar(b75), "xatolar": xatolar}
    return out
