import streamlit as st
import openai
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import uuid
import re
import base64
import os
# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="SpeakUp",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}
.block-container {padding-top: 1.5rem; padding-bottom: 2rem; max-width: 700px;}

/* ── CARDS ── */
.welcome-banner {
    background: #E1F5EE; border: 1.5px solid #1D9E75;
    border-radius: 12px; padding: 16px 20px; margin-bottom: 1.5rem;
}
.welcome-banner h2 { color: #0F6E56; margin: 0 0 3px 0; font-size: 19px; }
.welcome-banner p  { color: #0F6E56; margin: 0; font-size: 13px; }

/* ── FEEDBACK CARD ── */
.fb-card {
    background: #fafaf8; border: 1px solid #e5e2da;
    border-radius: 12px; padding: 14px 18px; margin-top: 6px; font-size: 14px; line-height: 1.7;
}
.fb-sec { margin-bottom: 10px; }
.fb-sec:last-child { margin-bottom: 0; }
.fb-lbl { font-weight: 700; font-size: 11px; text-transform: uppercase;
          letter-spacing: 0.07em; margin-bottom: 3px; }
.lbl-said { color: #666; }
.lbl-q    { color: #1D9E75; }
.lbl-fb   { color: #E24B4A; }
.lbl-enh  { color: #534AB7; }

/* ── MIC BUTTON ── */
.mic-wrap { text-align: center; padding: 1.5rem 0 0.5rem; }
.mic-hint { font-size: 13px; color: #888; margin-top: 8px; }

/* Larger audio input mic button */
[data-testid="stAudioInput"] button {
    width: 72px !important;
    height: 72px !important;
    font-size: 28px !important;
}
[data-testid="stAudioInput"] {
    display: flex;
    justify-content: center;
    margin: 0.5rem 0;
}

/* ── CONVERSATION PICKER ── */
.conv-card {
    background: white; border: 1.5px solid #e0ddd6;
    border-radius: 10px; padding: 13px 16px; margin-bottom: 8px;
    cursor: pointer; transition: border-color 0.15s;
}
.conv-card:hover { border-color: #1D9E75; }
.conv-title { font-weight: 500; font-size: 14px; }
.conv-goal  { font-size: 12px; color: #888; margin-top: 3px; }

/* ── STATUS PILL ── */
.status-pill {
    display: inline-block; padding: 3px 10px; border-radius: 99px;
    font-size: 12px; font-weight: 500;
}
.pill-green { background: #E1F5EE; color: #0F6E56; }
.pill-red   { background: #FCEBEB; color: #C0392B; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# CURRICULUM — ages 13-17
# ─────────────────────────────────────────────
LEVELS = {
    9:  "Level 1 – Getting Started",
    10: "Level 2 – Building Confidence",
    11: "Level 3 – Everyday English",
    12: "Level 4 – Growing Fluency",
    13: "Level 7 – Functional English",
    14: "Level 8 – Confidence & Public Speaking",
    15: "Level 9 – Real-World English",
    16: "Level 10 – Advanced Speaking",
    17: "Level 10 – Advanced Speaking",
}

# Each module has conversations with full curriculum content
CURRICULUM = {
    "topic1": {
        "title": "First Impressions",
        "icon": "✨",
        "conversations": [
            {
                "id": "t1c1", "title": "Personal Choices",
                "goal": "Student talks about their own everyday preferences and habits using simple present tense.",
                "vocabulary": "prefer, usually, always, sometimes, favourite, choose, enjoy, hobby, free time, because, instead of",
                "structures": '"I prefer … because…" / "I usually … in my free time." / "My favourite … is … because…" / "I enjoy … more than…" / "I always/sometimes…"',
                "starter": "Let's start simple! Tell me one thing about yourself — maybe a food you love, something you do after school, or a hobby you enjoy. Anything at all!",
                "followups": ["Why do you prefer that?", "How often do you do that — every day, or only sometimes?", "Do you enjoy doing that alone or with friends?", "Is that your favourite thing to do, or is there something you enjoy more?", "What do you usually do on a Sunday?", "Do you prefer watching something or playing something in your free time?"]
            },
            {
                "id": "t1c2", "title": "Describe a Person on First Impressions",
                "goal": "Student uses adjectives to describe how a real person looks and comes across.",
                "vocabulary": "tall, short, curly, straight, dark, fair, friendly, quiet, confident, shy, serious, kind, neat, messy, young, older",
                "structures": '"He/She has … hair." / "He/She is … and …" / "He/She seems … because…" / "I think he/she is … because…" / "He/She is wearing…"',
                "starter": "Think of someone you see often — a classmate, a neighbour, a family friend. Don't say their name! Just describe what they look like. What is the first thing you notice about them?",
                "followups": ["What does their hair look like?", "Are they tall or short?", "Do they seem friendly or more quiet?", "What do they usually wear?", "What is one word you would use to describe their personality?", "Do they seem confident or a little shy?", "What is the first thing someone would notice about this person?"]
            },
            {
                "id": "t1c3", "title": "What People Notice About Each Other",
                "goal": "Student reflects on social perception — what they notice first about others and what others might notice about them.",
                "vocabulary": "notice, first impression, appearance, smile, clothes, attitude, confident, nervous, remember, judge, important, seem, think",
                "structures": '"I notice … first because…" / "I think people usually notice…" / "My first impression of … was…" / "I think I seem … to other people." / "When I meet someone, I always notice…"',
                "starter": "What do you notice first when you meet a new person? Their eyes? Their smile? Their clothes? Or something else? There is no wrong answer!",
                "followups": ["Why do you notice that first — is it important to you?", "Do you think most people notice the same thing, or is everyone different?", "What do you think people notice first about you?", "Has your first impression of someone ever been wrong?", "Do you think clothes tell you something about a person?", "Is there someone whose first impression really stayed with you? What did you notice?"]
            },
            {
                "id": "t1c4", "title": "Stories of Meeting Someone for the First Time",
                "goal": "Student narrates a simple real past experience of meeting someone new using basic past tense.",
                "vocabulary": "met, first time, thought, seemed, turned out, remember, nervous, excited, surprised, at first, then, after that, in the end",
                "structures": '"I met … when/at…" / "At first I thought he/she was…" / "He/She seemed … but then…" / "I remember feeling…" / "In the end, I found out that…"',
                "starter": "Can you tell me about a time you met someone new for the first time? Maybe a new classmate, a neighbour, or someone at a family function. Where were you, and what happened?",
                "followups": ["Where did you meet this person?", "What was your first impression of them?", "Were you nervous or excited?", "Did they seem friendly straight away?", "Did your impression of them change after you spoke?", "How did you feel after meeting them — happy, nervous, surprised?", "Do you still know this person today?"]
            },
        ]
    },
    "topic2": {
        "title": "Connecting Objects to People",
        "icon": "🎒",
        "conversations": [
            {
                "id": "t2c1", "title": "Ask and Answer Questions About Themselves",
                "goal": "Student practises asking and answering simple personal questions in a two-way exchange.",
                "vocabulary": "study, live, favourite, spend time, come from, interested in, good at, dream, hope, belong, neighbourhood, passion, background",
                "structures": '"I come from…" / "I am good at … because…" / "I spend most of my time…" / "I hope to … one day." / "What about you — do you…?" / "Can I ask you…?"',
                "starter": "Let's get to know each other a little better! Tell me — where do you live and what is one thing you are really good at?",
                "followups": ["How long have you lived there?", "Who do you live with?", "What subject are you best at in school and why?", "What do you spend most of your time doing after school?", "Is there something you really want to learn or get better at?", "What do you hope to do when you are older?", "Now can you ask me something — anything you want to know!"]
            },
            {
                "id": "t2c2", "title": "Connect Objects to Experiences",
                "goal": "Student picks a real everyday object and connects it to a specific memory, feeling, or experience.",
                "vocabulary": "remind, memory, belong, used to, special, represent, connected to, gift, treasure, meaningful, whenever, given by, bought, found, reminds me of",
                "structures": '"This object reminds me of…" / "It belonged to…" / "I got this when…" / "Whenever I see this, I think of…" / "This is special to me because…" / "It represents…"',
                "starter": "Think of one object that is important to you — it can be anything. A book, a trophy, a photo, a piece of clothing, a gift. Can you tell me what it is and why it matters to you?",
                "followups": ["Where did you get that object from?", "How long have you had it?", "Did someone give it to you or did you find or buy it yourself?", "What memory does it remind you of?", "How do you feel when you see or hold that object?", "Would you ever give it away? Why or why not?", "If your house was on fire and you could only save one object, would this be the one? Why?", "Does this object represent something about who you are?"]
            },
            {
                "id": "t2c3", "title": "Use Personal Objects to Introduce Themselves",
                "goal": "Student uses 2 or 3 objects or pictures to give a short structured self-introduction.",
                "vocabulary": "represent, symbol, hobby, interest, passion, identity, proud of, relates to, says a lot about, personality, describe, show, this one, the next one, finally",
                "structures": '"This object represents…" / "I brought this because…" / "This says a lot about me because…" / "The next object I want to show is…" / "Finally, I chose this because…" / "These three objects together show that I am…"',
                "starter": "Imagine you are introducing yourself to a new class using only objects — no words about your name or age! You have chosen 2 or 3 objects or pictures. Start with your first one — what is it and what does it say about you?",
                "followups": ["Why did you choose that specific object and not something else?", "What does that object say about your personality?", "How long has that been an important part of your life?", "What is your next object — and how is it different from the first one?", "Do these objects together tell a complete story about who you are?", "Is there anything important about you that these objects do NOT show?", "If you could only keep one of these objects, which would it be and why?", "What would someone think about you just from looking at these objects?"]
            },
        ]
    },
    "topic3": {
        "title": "Personal Identity",
        "icon": "🪞",
        "conversations": [
            {
                "id": "t3c1", "title": "Express How They Identify Themselves",
                "goal": "Student thinks about which aspects of their identity feel most important, choosing from concrete familiar categories.",
                "vocabulary": "identity, define, important, represent, belong to, proud of, describe, category, nationality, hometown, supporter, role, value, stands for, means to me",
                "structures": '"I would define myself as…" / "The most important part of my identity is… because…" / "I am proud to be…" / "I belong to…" / "Being … is important to me because…" / "I identify most with… because…"',
                "starter": "I am going to give you some categories — age, gender, nationality, hometown, hobbies, family, clothes, music, cricket team, the people you spend time with. Which THREE feel most like YOU? Take a moment to think and then tell me!",
                "followups": ["Why did you choose that one and not the others?", "Has that always been an important part of your identity or did it change as you grew up?", "Which category on the list feels the LEAST like you — and why?", "You mentioned your family — what is it about your family that feels like a big part of who you are?", "Do you think your identity will stay the same in 10 years or will it change?", "Is there something important about who you are that is NOT on the list at all?", "If you had to describe yourself in three words based on your choices, what would they be?"]
            },
            {
                "id": "t3c2", "title": "Talk About Their Future Identities",
                "goal": "Student imagines and describes who they want to become using simple future tense and aspiration language.",
                "vocabulary": "future, hope to, plan to, dream of, become, achieve, imagine, role, career, identity, change, grow, different, still, by the time, one day, goal, aspire",
                "structures": '"In the future I hope to…" / "I plan to become…" / "I think I will still be… but I will also…" / "By the time I am … years old, I want to…" / "One day I dream of…" / "I think my identity will change because…"',
                "starter": "You just told me three things that make you YOU right now. Now let's think about the future — who do you WANT to be in 10 years? What parts of yourself do you think will stay the same and what might change?",
                "followups": ["What do you hope to be doing for work or study?", "Which part of your identity from today do you think will always stay with you?", "Is there something about yourself that you want to change or improve?", "Do you think where you live will change — will you stay in your hometown or move somewhere new?", "What kind of person do you want people to say you are in the future?", "What is one thing you need to do NOW to become the person you want to be?", "If your future self could send you one piece of advice, what do you think it would say?"]
            },
        ]
    },
    "topic4": {
        "title": "Personal Preferences",
        "icon": "☕",
        "conversations": [
            {
                "id": "t4c1", "title": "Making Decisions",
                "goal": "Student talks through the small everyday decisions they make, practising language for explaining reasons and priorities.",
                "vocabulary": "decide, choice, routine, remember, required, prepare, morning, organised, forget, priority, prefer, usually, automatically, on time, responsible, plan ahead",
                "structures": '"Every morning I have to decide…" / "I usually choose … because…" / "I always remember to… because…" / "Sometimes I forget to…" / "I prefer to … first and then…" / "I had to think about … this morning."',
                "starter": "Think about this morning — from the moment you woke up. Did you have to decide what to eat for breakfast? What to wear? How to get to school? What did you have to remember to bring today? Tell me about the decisions you made!",
                "followups": ["Was that decision easy or did you have to think about it?", "Do you make that same choice every day or does it change?", "Did you forget anything this morning — or almost forget something?", "Do you plan your morning the night before or do you decide everything in the morning?", "Is there a decision you made today that you are happy about?", "What is the hardest small decision you make every day?", "Does anyone help you make decisions in the morning — like a parent or sibling?"]
            },
            {
                "id": "t4c2", "title": "Talk About Personal Preferences",
                "goal": "Student expresses clear personal preferences on simple everyday topics, giving reasons and using comparative language.",
                "vocabulary": "prefer, rather, instead, option, choice, reason, definitely, depends, comfortable, convenient, enjoyable, taste, opinion, both, neither, although, however",
                "structures": '"I prefer … because…" / "I would rather … than…" / "For me … is better because…" / "It depends on…" / "Although … is good, I prefer… because…" / "I definitely prefer … over…"',
                "starter": "Let's start with something simple — tea or coffee? Which do you prefer and why? There is no wrong answer!",
                "followups": ["Do you prefer travelling by car or bicycle — and does it depend on where you are going?", "Do you prefer mornings or evenings — why?", "Do you prefer studying alone or with friends?", "Hot food or cold food — which do you prefer?", "Do you prefer a busy day with lots to do or a quiet day with nothing planned?", "Movies or books — which do you prefer and why?", "Do you prefer giving gifts or receiving them?", "Is there something that most people your age like that you actually don't prefer?"]
            },
        ]
    },
    "topic5": {
        "title": "Learning Styles",
        "icon": "🧠",
        "conversations": [
            {
                "id": "t5c1", "title": "Discuss Different Learning Styles",
                "goal": "Student explores how they personally learn best, discussing ideal learning environments, emotions, creativity, and strategies.",
                "vocabulary": "learning style, visual, auditory, practical, environment, creative, technique, method, concentrate, remember, understand, challenge, enjoyable, stressed, bored, motivated, useful, design, ideal, integrate, routine, trick, tool",
                "structures": '"I learn best when…" / "For me the ideal classroom would…" / "I think creativity is important because…" / "When I feel … I find it hard to…" / "The most challenging thing I ever learned was…" / "If I had to teach someone, I would…"',
                "starter": "Let's think about how YOU learn best. If you could design your perfect classroom — the room, the way of teaching, everything — what would it look like? Would there be desks? Music? Colours? Tell me!",
                "followups": ["Do you think you learn better by reading, listening, watching, or actually doing something yourself?", "Does your mood affect how well you learn — if you are stressed or bored, does it change things?", "Do you think creativity plays a role in learning — can being creative help you study better?", "Can learning ever be fun? What is one way you make studying more enjoyable?", "What is the most challenging thing you have ever had to learn — and what helped you get through it?", "If you had to teach a younger student something new, what techniques would you use?", "Do you think it is better to stick to one learning style or mix different ones together?"]
            },
        ]
    },
    "topic6": {
        "title": "Friendships",
        "icon": "👥",
        "conversations": [
            {
                "id": "t6c1", "title": "Friendships from Different Perspectives",
                "goal": "Student explores their own friendships discussing intimacy, distance, conflict, and priorities using specific friendship vocabulary.",
                "vocabulary": "confidant, intimate, rapport, maintain, priority, setback, drift apart, backstab, two-faced, shoulder to cry on, fall out, long-distance, trust, loyal, support, BFF, bond, close, honest",
                "structures": '"I would describe … as my confidant because…" / "We maintain our friendship by…" / "One thing that can cause a setback in a friendship is…" / "Friends can deal with problems by…" / "We drifted apart because…" / "A two-faced friend is someone who…"',
                "starter": "Let's talk about friendships! Do you have a best friend — a BFF? Can you describe them? What makes them special to you?",
                "followups": ["Is there a friend you would call a confidant — someone you trust with your deepest secrets? What makes that friendship so close?", "Do you have any long-distance friendships — a friend who moved away or lives far from you? How do you keep in touch?", "Have you ever had a setback or problem in a friendship? What happened and how did you both deal with it?", "Would you say friendships are one of your top priorities in life?", "Have you ever had a two-faced friend or a backstabber?", "Have you ever given a friend a shoulder to cry on — been there for them when they were upset?", "Have you ever fallen out with a friend? What happened?", "Why do you think friends sometimes drift apart even when nothing bad happens?"]
            },
        ]
    },
    "topic7": {
        "title": "Food Preferences",
        "icon": "🍽️",
        "conversations": [
            {
                "id": "t7c1", "title": "Conversations About Food and Dishes",
                "goal": "Student discusses personal food preferences, seasonal eating habits, benefits of healthy eating, and food's effect on the body.",
                "vocabulary": "favourite, prefer, seasonal, vegetable, fruit, juice, grow, benefits, healthy, nutrition, energy, sleepy, influence, digest, diet, fresh, taste, sweet, sour, bitter, spicy, balanced, affect, meal",
                "structures": '"My favourite … is … because…" / "In summer I prefer … because…" / "I think eating … is good for you because…" / "I have noticed that after eating … I feel…" / "I would love to grow … at home because…" / "I think food affects sleep because…"',
                "starter": "Let's talk about food! Do you have a favourite fruit or vegetable — something you could eat every day? Tell me what it is and why you love it!",
                "followups": ["What is your favourite fruit to eat in summer? Does that change in winter?", "Do you like fruit or vegetable juices? Which ones do you enjoy most?", "Would you like to grow any fruits or vegetables at home? Which ones and why?", "Do you think eating the right food is important — what are some benefits of eating healthy?", "Have you ever felt very sleepy after eating a big meal or certain foods?", "Do you think the food you eat can affect how well you sleep at night?", "Is there a food that gives you a lot of energy? And one that makes you feel slow or tired?", "Is there a food that is healthy but you really dislike?"]
            },
        ]
    },
    "topic8": {
        "title": "Clarifications",
        "icon": "💬",
        "conversations": [
            {
                "id": "t8c1", "title": "Communication Issues and How to Clarify",
                "goal": "Student discusses situations where communication breaks down and practises the language of asking for clarification.",
                "vocabulary": "clarify, misunderstand, explain, repeat, communicate, distracted, background noise, international, language barrier, unclear, context, assume, confirm, follow, lost, accent, rephrase, check, make sure, in other words",
                "structures": '"I didn\'t understand because…" / "Can you explain that again please?" / "What I think you mean is…" / "Could you speak more slowly please?" / "I was confused because…" / "People misunderstand each other when…"',
                "starter": "Has there ever been a situation where you completely misunderstood someone — or they misunderstood you? What happened? Don't worry if it is funny or embarrassing, those are the best stories!",
                "followups": ["What do you find most difficult about speaking with someone from another state or country?", "When you don't understand something, do you usually ask them to explain or do you just pretend you understood?", "Why do you think people sometimes pretend to understand even when they don't?", "What happens when people speak too quickly or too quietly — how do you handle that?", "Have you ever been distracted during a conversation and missed something important?", "What are some polite ways to ask someone to repeat or explain something without making them feel bad?"]
            },
        ]
    },
    "topic9": {
        "title": "The Past",
        "icon": "⏪",
        "conversations": [
            {
                "id": "t9c1", "title": "A Day in the Past",
                "goal": "Student recalls and describes specific events from yesterday and childhood using simple past tense.",
                "vocabulary": "yesterday, last night, this morning, when I was young, used to, remember, ago, before, after, then, at that time, earlier, back then, enjoyed, preferred, went, ate, slept, came, felt",
                "structures": '"Yesterday I…" / "Last night I…" / "When I was younger I used to…" / "I went home by…" / "I had … for breakfast yesterday." / "I used to enjoy … but now…" / "I remember that when I was little…"',
                "starter": "Let's travel back to yesterday! Tell me — what did you have for breakfast yesterday morning? And what time did you go to bed last night?",
                "followups": ["Where did you eat lunch yesterday — at home, at school, somewhere else?", "How did you get home from school yesterday — by bus, by car, walking?", "Did you enjoy eating vegetables when you were younger — or did you refuse to eat them?", "Is there a food you loved as a child that you don't eat anymore?", "What were you doing at 3 o'clock last Saturday afternoon?", "What do you remember most about the pandemic — how did your daily life change?", "What was the name of your very first teacher? What were they like?"]
            },
            {
                "id": "t9c2", "title": "Interrupting Politely",
                "goal": "Student learns and practises the language of polite interruption — understanding when it is acceptable and how to do it without being rude.",
                "vocabulary": "interrupt, polite, rude, excuse me, sorry to interrupt, may I add, hold on, just a moment, cut off, jump in, wait, pause, mid-sentence, acceptable, appropriate, signal, turn, conversation, context",
                "structures": '"Sorry to interrupt but…" / "Excuse me, may I add something?" / "Can I just say…?" / "I just wanted to mention…" / "Going back to what you said…" / "I don\'t mean to cut you off but…"',
                "starter": "Has anyone ever stopped you in the middle of a sentence to say something? How did it feel? Was it polite or rude — and what made the difference?",
                "followups": ["Can you think of a situation where interrupting someone is actually okay or even necessary?", "What is the difference between a polite interruption and a rude one?", "If your teacher is explaining something and you have an important question, how would you politely interrupt?", "Have you ever interrupted someone and immediately felt bad about it?", "In your family, is it normal to interrupt each other — or do people wait their turn?", "Can you try to interrupt me politely right now while I am talking — just to practise?"]
            },
            {
                "id": "t9c3", "title": "Share Personal Stories",
                "goal": "Student narrates a personal story from their past with a clear beginning, middle, and end using past tense and sequencing language.",
                "vocabulary": "memorable, celebration, childhood, trouble, prize, went wrong, trip, journey, famous, once, suddenly, eventually, at first, after that, finally, I'll never forget, ended up, turned out, realised, luckily, unfortunately",
                "structures": '"This happened when I was…" / "It all started when…" / "At first I thought…" / "Suddenly…" / "After that…" / "Eventually…" / "In the end…" / "I will never forget…" / "Luckily / Unfortunately…"',
                "starter": "I have some story topics for you — pick the one that feels most interesting to you! A memorable celebration, a childhood pet, meeting a famous person, a time you got into trouble, a trip you'll never forget, a day when everything went wrong, or a prize you won. Which one do you want to tell me about?",
                "followups": ["When did this happen — how old were you?", "Where were you and who were you with?", "What happened first — how did it all start?", "Was there a moment when everything changed or went in a different direction?", "How did you feel at that moment?", "How did it end — was it a good ending or not?", "What did you learn from that experience?", "Is there one part of that story you will never forget?"]
            },
            {
                "id": "t9c4", "title": "Remembering the Past",
                "goal": "Student practises retrieving and describing specific past memories using past tense and memory language.",
                "vocabulary": "remember, recall, memory, childhood, earliest, vague, clear, back then, at that age, used to, first time, remind, forget, vivid, exactly, at the time, grew up, before, after",
                "structures": '"I remember that…" / "As far as I can remember…" / "I can\'t really remember but I think…" / "My earliest memory is…" / "I met … when I was…" / "I will never forget the time…"',
                "starter": "Let's test your memory! Can you remember anything that happened before you were three years old — any tiny memory at all, even just a feeling or an image?",
                "followups": ["What were you doing at 3 o'clock last Saturday afternoon — can you remember exactly?", "Where did you meet your best friend — what is the story of how you two first met?", "What was your first teacher's name and what do you remember about them?", "What was the first big word you ever learned in English?", "What did you have for breakfast the day before yesterday — can you remember?", "What do you remember about the pandemic — what changed in your daily life?", "What is your earliest happy memory? And your earliest memory of being scared or upset?"]
            },
        ]
    },
    "topic10": {
        "title": "The Future",
        "icon": "🔭",
        "conversations": [
            {
                "id": "t10c1", "title": "Making Predictions",
                "goal": "Student makes predictions about the world using future tense and opinion language, reflecting on positive and negative possible futures.",
                "vocabulary": "predict, prediction, future, come true, activist, improve, worse, better place, believe, imagine, possibility, climate, technology, peace, poverty, environment, generation, change, impact, hopeful, concerned",
                "structures": '"I think the world will…" / "I believe that in the future…" / "The world would be a better place if…" / "The world would be worse off if…" / "I predict that…" / "I am hopeful that… because…" / "I am worried that… because…"',
                "starter": "Has anyone ever predicted your future — maybe a family member, an astrologer, or even a friend? Did you believe them? Do you think it will come true?",
                "followups": ["What do you think about the world today — is it in a good place or are there big problems?", "Can you finish this sentence — the world would be a better place if…? Give me three ideas.", "Now the opposite — the world would be worse off if…? What worries you most?", "Do you think technology will make the future better or create new problems?", "What do you think will be the biggest change in the world in the next 20 years?", "Do you think young people today can make the world better — how?", "Is there something happening in India right now that you think will be very different in 20 years?"]
            },
            {
                "id": "t10c2", "title": "Making Plans",
                "goal": "Student talks about upcoming holiday plans using future tense structures, distinguishing definite plans from possibilities.",
                "vocabulary": "plan, holiday, definite, maybe, probably, going to, might, hoping to, looking forward to, trip, visit, stay, travel, relax, celebrate, spend time, arrange, confirm, excited about, uncertain",
                "structures": '"I am going to… during the holidays." / "I might … if…" / "I am planning to…" / "I am really looking forward to…" / "I hope to… but I am not sure yet." / "We have definitely decided to…" / "I predict the holidays will be…"',
                "starter": "Let's talk about your upcoming holidays! Do you have any special plans — anything you are definitely doing, or maybe just hoping to do? Tell me everything!",
                "followups": ["Is that a definite plan or just a hope — have you confirmed it?", "Who are you spending the holidays with?", "Is there something you are really looking forward to?", "Are you travelling anywhere or staying at home?", "What do you predict your holidays will be like — relaxing, busy, exciting, boring?", "Is there something you want to do this holiday that you have never done before?", "What will you definitely NOT be doing these holidays?"]
            },
            {
                "id": "t10c3", "title": "Future of Space Exploration",
                "goal": "Student discusses space exploration using knowledge about India's space programme then explores Mars and life beyond Earth imaginatively.",
                "vocabulary": "planet, solar system, astronaut, space agency, orbit, mission, launch, explore, galaxy, Mars, gravity, atmosphere, colonise, spacecraft, ticket, average day, survive, resources, settlement, SpaceX, ISRO",
                "structures": '"There are … planets in the solar system." / "A person who travels to space is called…" / "India\'s space agency is called…" / "I think many/few people will… because…" / "I would/would not like to… because…" / "An average day on Mars might include…"',
                "starter": "Let's start with some quick questions — how many planets are in the solar system? What do we call a person who travels to space? And do you know the name of India's space agency?",
                "followups": ["Have you heard of SpaceX? Do you know who Elon Musk is and what he is trying to do?", "Do you think many people will actually buy a ticket to Mars one day — why or why not?", "Would YOU like to travel to Mars and live there — what would make you say yes or no?", "What would be a good name for the very first city on Mars and why?", "What might an average day on Mars look like — what would people eat, what jobs would they do, what would they do for fun?", "What do you think would be the hardest thing about living on Mars?", "Do you think India will send people to Mars one day?"]
            },
        ]
    },
    "topic11": {
        "title": "Life Stages",
        "icon": "🌱",
        "conversations": [
            {
                "id": "t11c1", "title": "Stages of Life",
                "goal": "Student reflects on different life stages discussing memories, advantages and disadvantages of their current age, and thoughts on ageing.",
                "vocabulary": "stage, childhood, teenager, adult, elderly, old age, memory, advantage, disadvantage, society, treat, consider, current, forever, life expectancy, experience, wisdom, energy, responsibility, freedom, pressure, recall, vivid",
                "structures": '"I consider people to be old when…" / "My first memory as a child is…" / "I think the best age is… because…" / "One advantage of my age is…" / "One disadvantage of my age is…" / "Old people in society are treated…" / "I think people living forever would be… because…"',
                "starter": "Let's start with a big question — at what age do you think a person becomes old? Is it 50? 60? 80? Or does it depend on something else?",
                "followups": ["What is your very first memory as a child — even a small or vague one?", "What do you think is the best age to be and why?", "What are the advantages of being your age right now?", "What are the disadvantages — what is hard or frustrating about being your age?", "What do you think old people remember and miss most about being a teenager?", "Who is the oldest person you know? How is their daily life different from yours?", "How do you think society treats old people — with respect, or do they get ignored?", "Do you think in the future people might be able to live forever — and would you actually want that?"]
            },
            {
                "id": "t11c2", "title": "Different Treatment of Old People in Different Cultures",
                "goal": "Student explores how elderly people are treated differently across cultures and discusses programmes like Adopt a Grandparent.",
                "vocabulary": "life expectancy, culture, society, respect, ignore, lonely, alone, care home, adopt, benefit, programme, match, similar, tradition, value, generation, elderly, community, opinion, compare, treatment, family structure",
                "structures": '"Life expectancy means…" / "I think people are living longer because…" / "The oldest person in my family is… and they…" / "In my family old people are treated…" / "I think adopting a grandparent is… because…" / "My ideal grandparent would be…"',
                "starter": "Do you know what life expectancy means? People today are living much longer than before — why do you think that is?",
                "followups": ["Who is the oldest person in your family? Do they live with you or somewhere else?", "What is your relationship like with the older members of your family?", "In many countries old people live completely alone — how does that make you feel?", "Have you heard of programmes like Adopt a Grandparent — where families are matched with elderly people who have no family? What do you think of that idea?", "How do you think a family could benefit from adopting a grandparent?", "Is there anything similar to this that happens in India or in your community?", "Describe your ideal grandparent — what would they be like, what would you do together?"]
            },
        ]
    },
    "topic12": {
        "title": "Expressing Opinions",
        "icon": "💡",
        "conversations": [
            {"id": "t12c1", "title": "Celebrities earn too much money", "goal": "Student states and defends an opinion on wealth and fairness.", "vocabulary": "celebrity, earn, salary, deserve, talent, influence, compare, teacher, doctor, fair, unfair, wealth, fame, worth, contribute, society, overpaid", "structures": '"I think… because…" / "In my opinion…" / "I agree/disagree because…" / "On the other hand…" / "I understand that… but…"', "starter": "Here is a statement — Celebrities earn too much money. Do you agree or disagree? Tell me what you think and why!", "followups": ["How much do you think a celebrity earns compared to a teacher or a doctor?", "Do you think celebrities deserve their money because of their talent?", "Is there a type of celebrity you think earns too much — actors, cricketers, influencers?", "Should there be a limit on how much anyone can earn?", "Do you think fame and money always go together?"]},
            {"id": "t12c2", "title": "Holidays abroad vs. holidays at home", "goal": "Student compares travel experiences using comparative language.", "vocabulary": "abroad, domestic, travel, explore, culture, familiar, foreign, experience, local, tourist, discover, compare, prefer, comfortable, exciting, different", "structures": '"I think travelling in India is… because…" / "Going abroad is more… because…" / "I would rather… because…" / "Both have… but…"', "starter": "Do you agree — is a holiday in India just as interesting as going abroad, or even more interesting? What do you think?", "followups": ["Have you ever travelled to another state in India — what was it like?", "Is there somewhere in India you really want to visit?", "Is there a foreign country you dream of visiting?", "Do you think you learn more about yourself when you travel somewhere very different from home?", "What do you think is the best thing about travelling within India?"]},
            {"id": "t12c3", "title": "Exams are the best way to measure ability", "goal": "Student discusses education and assessment, challenging or defending exams.", "vocabulary": "exam, measure, ability, assess, pressure, fair, alternative, project, practical, memorise, knowledge, skills, stress, result, performance, judge, represent", "structures": '"I think exams are… because…" / "A better way to measure ability would be…" / "Exams don\'t show… because…" / "I feel… when I have an exam."', "starter": "Exams are the best way to measure how smart a student is — do you agree or disagree? Be honest!", "followups": ["How do you feel before an exam — nervous, confident, stressed?", "Do you think exams show everything a student knows or just what they can memorise?", "What would be a better way to test a student's real ability?", "Have you ever done really well in class but badly in an exam — or the other way around?", "Do you think all subjects should be tested the same way?"]},
            {"id": "t12c4", "title": "Arriving late to meet friends is rude", "goal": "Student discusses social etiquette and respect using opinion and justification language.", "vocabulary": "punctual, late, rude, respect, excuse, habit, culture, wait, appointment, acceptable, impression, reliable, considerate, rush, emergency, apologise", "structures": '"I think arriving late is… because…" / "It depends on…" / "In my experience…" / "I always try to… because…" / "I think it is acceptable when…"', "starter": "If your friend is always late when you plan to meet — is that rude or is it okay? What do you think?", "followups": ["Are you usually on time or do you tend to be late?", "Is being late more acceptable in some situations than others?", "How do you feel when you have been waiting a long time for someone?", "Do you think punctuality is taken seriously in India compared to other countries?", "What is a good excuse for being late — and what is not acceptable?"]},
            {"id": "t12c5", "title": "Social media is a waste of time", "goal": "Student discusses the benefits and risks of social media.", "vocabulary": "social media, platform, waste, dangerous, addictive, influence, cyberbullying, privacy, connect, trend, mental health, screen time, benefit, harmful, compare, content, opinion, post, share", "structures": '"I think social media is… because…" / "The biggest danger is…" / "One benefit is… but…" / "I spend … hours on social media and I think…" / "It can be dangerous when…"', "starter": "Do you think social media is a waste of time — or is it actually useful? And do you think it can be dangerous? Tell me your honest opinion!", "followups": ["How much time do you spend on social media every day?", "What platforms do you use most and why?", "Has social media ever made you feel bad about yourself — comparing yourself to others?", "Do you think cyberbullying is a serious problem for teenagers in India?", "Should there be rules about how much time teenagers spend on social media?"]},
            {"id": "t12c6", "title": "Dogs are better companions than cats", "goal": "Student practises lighthearted opinion and comparison language.", "vocabulary": "companion, loyal, independent, affectionate, playful, calm, energetic, require, attention, pet, prefer, personality, suit, lifestyle, advantage, disadvantage", "structures": '"I think dogs are… because…" / "Cats are better because…" / "It depends on your personality because…" / "A dog/cat suits someone who…" / "I prefer… because…"', "starter": "Big debate — dogs or cats? Which make better companions and why? Which side are you on?", "followups": ["Do you have a pet at home — or have you ever had one?", "What do you think is the best thing about dogs? And about cats?", "Which animal suits a busy person better?", "Do you think the pet you choose says something about your personality?", "If you could have any animal as a companion — not just dogs or cats — what would you choose?"]},
            {"id": "t12c7", "title": "Children should not eat fast food", "goal": "Student discusses health, parenting, and personal freedom using opinion language.", "vocabulary": "fast food, allowed, banned, healthy, nutrition, habit, occasional, addiction, childhood, obesity, choice, freedom, parent, restrict, balance, treat, junk food, consequence", "structures": '"I think children should/should not… because…" / "Fast food is harmful because…" / "It is okay to eat fast food if…" / "Parents should… because…" / "I think balance is important because…"', "starter": "Should children be completely banned from eating fast food — or is that too strict? What do you think?", "followups": ["How often do you eat fast food?", "Do your parents have any rules about what you can and cannot eat?", "Do you think fast food companies should be allowed to advertise to children?", "Is it the child's choice or the parent's responsibility to decide what they eat?", "What do you think is a healthy balance between eating well and having treats?"]},
            {"id": "t12c8", "title": "Teachers should stop giving homework", "goal": "Student debates the purpose of homework using personal experience.", "vocabulary": "homework, purpose, revision, burden, independent, reinforce, stress, balance, free time, necessary, ban, alternative, practice, effort, benefit, mental health, opinion", "structures": '"I think homework is… because…" / "Without homework students would…" / "The problem with homework is…" / "A better alternative would be…" / "I think teachers should… because…"', "starter": "If you could make one rule at school it would be — no more homework! Do you agree with that? Tell me why!", "followups": ["How much homework do you get every day — is it too much, too little, or about right?", "Do you think homework actually helps you learn or do you just do it to submit it?", "What would you do with your evenings if there was no homework?", "Do you think some subjects need homework more than others?", "What would be a better way to practise what you learn in school without traditional homework?"]},
            {"id": "t12c9", "title": "No smartphones before age 13", "goal": "Student discusses technology, childhood, and responsibility.", "vocabulary": "smartphone, age limit, responsible, access, social media, distraction, safety, appropriate, mature, monitor, screen time, benefit, danger, independent, childhood, addiction, permission", "structures": '"I think the right age for a smartphone is… because…" / "Children under 13 are not ready because…" / "A smartphone can be dangerous for young children because…" / "I got my first phone when I was… and I think…" / "Parents should… because…"', "starter": "When did you get your first smartphone — or when do you think you will? Do you think 13 is the right age or too late?", "followups": ["What do you think a child under 13 would use a smartphone for — is that a problem?", "Do you think having a smartphone too young can affect how children grow up?", "Should parents be able to monitor what their child does on their phone?", "Is there a difference between having a phone for safety versus having full access to the internet?", "Do you think you were or will be responsible enough at 13 to have a smartphone?"]},
            {"id": "t12c10", "title": "Animals should not be kept in zoos", "goal": "Student discusses animal rights and conservation forming a balanced opinion.", "vocabulary": "zoo, captivity, wild, conservation, endangered, habitat, welfare, rescue, breed, educate, natural, freedom, cruel, protect, species, extinction, opinion, benefit, argument", "structures": '"I think keeping animals in zoos is… because…" / "Animals deserve… because…" / "Zoos are important because…" / "On the other hand…" / "A better alternative to zoos would be…"', "starter": "Should animals be kept in zoos — or is it cruel to take them out of the wild? What is your opinion?", "followups": ["Have you ever been to a zoo — what was that experience like?", "Do you think animals are happy in zoos or do they suffer?", "Some zoos protect endangered animals — does that change your opinion?", "What do you think is the difference between a good zoo and a bad zoo?", "What would happen to endangered animals if there were no zoos at all?"]},
        ]
    },
    "topic13": {
        "title": "Teenage Stress",
        "icon": "😓",
        "conversations": [
            {
                "id": "t13c1", "title": "Stress Issues and Possible Solutions",
                "goal": "Student identifies teenage stressors, reflects on their own stress, and explores practical coping strategies.",
                "vocabulary": "stress, struggle, pressure, expectation, peer, cyberbullying, addiction, homework, exam, anxiety, cope, solution, distract, focus, shift, clear, mental health, dialogue, support, check in, overwhelmed, balance, handle, technique",
                "structures": '"I think the biggest stressor for teenagers is… because…" / "I sometimes feel stressed when…" / "One thing that helps me take my mind off things is…" / "To shift my focus from my mind to my body I…" / "When I can\'t sleep because of stress I…" / "When I have difficult thoughts I talk to…"',
                "starter": "Let's be honest — what do you think are the biggest things that stress teenagers out today? Think about school, home, friends, phones — everything. What comes to mind first?",
                "followups": ["Do you think there is enough conversation about teenage stress — in school, at home, in society?", "Who do you think should be checking on how students are doing mentally — parents, teachers, or friends?", "When you are stressed or overwhelmed, what do you do to take your mind off it?", "Is there anything physical you do — sport, walking, dancing — that helps you shift from thinking to just being in your body?", "When stress stops you from sleeping, what do you do — do you have any tricks that help you fall asleep?", "Is there a person you go to when you have difficult thoughts — someone you trust?", "Do you think phone addiction makes teenage stress better or worse?", "Is there a type of stress you think teenagers face today that adults do not take seriously enough?"]
            },
        ]
    },
    "topic14": {
        "title": "Giving Advice",
        "icon": "🤝",
        "conversations": [
            {
                "id": "t14c1", "title": "Asking for and Giving Advice",
                "goal": "Student discusses when and how they ask for and give advice, and practises giving practical advice using appropriate language.",
                "vocabulary": "advice, suggest, recommend, try, consider, helpful, useful, easy, difficult, follow, opinion, perspective, trust, experience, situation, solution, attempt, encourage, guide, support, benefit, worth trying",
                "structures": '"I think you should… because…" / "Have you tried…?" / "It might help to…" / "In my opinion the best thing to do is…" / "I would recommend… because…" / "I usually ask for advice when…" / "I give advice when…" / "I find it easy/difficult to follow advice because…"',
                "starter": "Do you find it easy to ask someone for advice when you have a problem — or do you prefer to figure things out alone? Tell me about a time you asked someone for advice or someone asked you!",
                "followups": ["Who do you usually go to for advice — a friend, a parent, a teacher?", "Is there a type of problem you would never ask for advice about — something you keep to yourself?", "Do you find it easy to actually follow the advice people give you — or do you listen but then do your own thing anyway?", "Has someone ever given you advice that turned out to be really wrong — what happened?", "When a friend comes to you with a problem, how do you decide what advice to give?", "Is there an activity — like exercise, journaling, or talking to someone — that you have never tried for stress but would like to?", "Do you think some people give advice too easily without really understanding the situation?", "If a younger student came to you stressed about exams, what three pieces of advice would you give them?"]
            },
        ]
    },
}

CURRICULUM_9_12 = {
    'y1topic1': {
        'title': 'Introducing Yourself',
        'icon': '👋',
        'conversations': [{'id': 'y1t1c1', 'title': 'All About Me', 'goal': 'Student introduces themselves with simple facts — name, class, family, likes.', 'vocabulary': 'name, class, family, like, favourite, live, brother, sister', 'structures': '"My name is…" / "I am in class…" / "I like…" / "I live with…" / "I have a brother/sister called…"', 'starter': "Hi! Let's get to know each other. What is your name and what class are you in?", 'followups': ['What do you like to eat?', 'Do you have any brothers or sisters?', 'What do you like to do after school?', 'What is one thing that makes you special?', 'Who do you live with?']}, {'id': 'y1t1c2', 'title': 'Asking About a Friend', 'goal': 'Student practises asking simple personal questions to learn about someone else.', 'vocabulary': 'ask, friend, hobby, food, dislike, favourite', 'structures': '"What\'s your name?" / "Where do you live?" / "What\'s your favourite…?" / "Do you like…?"', 'starter': 'Imagine you just met a new friend. What is the first question you would ask them?', 'followups': ['What would you ask about their favourite food?', 'What would you ask about their hobby?', "What is something you don't like?", 'What is a question you can ask to learn more about someone?']}],
    },
    'y1topic2': {
        'title': 'Asking Questions',
        'icon': '❓',
        'conversations': [{'id': 'y1t2c1', 'title': 'Yes/No and Wh Questions', 'goal': 'Student practises forming and using simple yes/no and wh- questions.', 'vocabulary': 'what, where, when, why, who, do, does, is, are', 'structures': '"Do you like…?" / "Is your name…?" / "What is your favourite…?" / "Where do you live?"', 'starter': "Let's practise asking questions. Can you ask me — do I like tea or coffee?", 'followups': ['Can you ask me what my favourite food is?', 'Can you ask me where I live?', 'Can you ask me why I like something?', "Can you think of a question starting with 'who'?"]}, {'id': 'y1t2c2', 'title': 'Reporter and Celebrity', 'goal': 'Student role-plays asking questions as a reporter interviewing a celebrity.', 'vocabulary': 'interview, reporter, famous, ask, answer, question', 'structures': '"Can I ask you a question?" / "What do you like to do?" / "Why are you famous?"', 'starter': "Let's play a game! I am a famous cricketer and you are a reporter. What is the first question you want to ask me?", 'followups': ['What do you want to know about my life?', 'What do you want to ask about my favourite sport?', 'Can you ask me one more question?', 'What was your favourite question to ask?']}],
    },
    'y1topic3': {
        'title': 'Likes and Dislikes',
        'icon': '❤️',
        'conversations': [{'id': 'y1t3c1', 'title': 'Talking About Likes', 'goal': 'Student expresses likes using simple structures and gives a reason.', 'vocabulary': 'like, love, enjoy, favourite, because, sport, food, hobby', 'structures': '"I like… because…" / "My favourite … is…" / "I love…" / "I enjoy…"', 'starter': 'Tell me — what is something you really like? It can be a food, a game, anything!', 'followups': ['Why do you like that?', 'What is your favourite sport?', 'What is your favourite food?', 'Is there a song you like?', 'What is your favourite TV show?']}, {'id': 'y1t3c2', 'title': 'Talking About Dislikes', 'goal': 'Student expresses dislikes politely using simple structures.', 'vocabulary': "don't like, hate, dislike, can't stand, because", 'structures': '"I don\'t like… because…" / "I hate…" / "I\'m not fond of…"', 'starter': "Now tell me something you don't like at all! It's okay, everyone has things they dislike.", 'followups': ["Why don't you like that?", "Is there a food you don't like?", "Is there a game you don't enjoy?", "What is something most people like but you don't?"]}],
    },
    'y1topic4': {
        'title': 'Interviews',
        'icon': '🎤',
        'conversations': [{'id': 'y1t4c1', 'title': 'Interview a Partner', 'goal': 'Student asks and answers simple personal questions in an interview format.', 'vocabulary': 'interview, question, answer, favourite, hobby, family', 'structures': '"What is your favourite…?" / "Do you like…?" / "Tell me about…"', 'starter': "Let's do an interview! I'll ask you questions like a reporter. What is your favourite thing to do after school?", 'followups': ['What is your favourite food?', 'What do you like to do on weekends?', 'Tell me about your family.', 'What is something you are good at?']}, {'id': 'y1t4c2', 'title': 'Talking About a Friend', 'goal': 'Student describes someone else using third person simple present.', 'vocabulary': 'he, she, likes, plays, lives, has', 'structures': '"He/She likes…" / "He/She is good at…" / "He/She has…" / "He/She lives in…"', 'starter': 'Think of a friend or someone in your family. Can you tell me one thing they like to do?', 'followups': ['What does this person like to eat?', 'What is this person good at?', 'Where does this person live?', 'What makes this person special?']}],
    },
    'y1topic5': {
        'title': 'Daily Routines',
        'icon': '⏰',
        'conversations': [{'id': 'y1t5c1', 'title': 'My Day', 'goal': 'Student describes their daily routine using simple present tense and time connectives.', 'vocabulary': 'wake up, brush, eat, go, school, homework, sleep, first, then, after that', 'structures': '"I wake up at…" / "First I…, then I…" / "After school I…" / "At night I…"', 'starter': 'Tell me about your day! What is the first thing you do when you wake up?', 'followups': ['What do you do after you wake up?', 'What time do you go to school?', 'What do you do after school?', 'What do you do before you sleep?']}, {'id': 'y1t5c2', 'title': "Someone Else's Routine", 'goal': "Student talks about another person's daily routine using third person.", 'vocabulary': 'he/she wakes up, goes, plays, eats, third person -s', 'structures': '"He/She wakes up at…" / "He/She goes to…" / "What does he/she do in the evening?"', 'starter': 'Think about your mother, father, or someone in your family. What is the first thing they do every morning?', 'followups': ['What does this person do during the day?', 'What does this person do in the evening?', 'Is their routine different from yours?', 'What time does this person sleep?']}],
    },
    'y1topic6': {
        'title': 'Describing People',
        'icon': '🧑',
        'conversations': [{'id': 'y1t6c1', 'title': 'What Does Someone Look Like', 'goal': "Student uses simple adjectives to describe a person's physical appearance.", 'vocabulary': 'tall, short, hair, eyes, wearing, has', 'structures': '"He/She is tall/short." / "He/She has … hair." / "He/She is wearing…"', 'starter': 'Think of someone you know well. Can you describe what they look like?', 'followups': ['What colour is their hair?', 'Are they tall or short?', 'What are they usually wearing?', 'What is the first thing people notice about them?']}, {'id': 'y1t6c2', 'title': 'What Is Someone Like', 'goal': 'Student uses simple personality adjectives to describe character.', 'vocabulary': 'kind, friendly, funny, shy, honest, helpful', 'structures': '"He/She is kind." / "He/She always…" / "He/She never…"', 'starter': "Now tell me about this person's personality. Are they kind, funny, shy, or something else?", 'followups': ['Why do you think they are kind/funny/shy?', 'Can you give an example of something they did?', 'Is there someone in your family who is very funny?', 'What is one word to describe your best friend?']}],
    },
    'y1topic7': {
        'title': 'Homes and Furniture',
        'icon': '🏠',
        'conversations': [{'id': 'y1t7c1', 'title': 'My Home', 'goal': 'Student describes their home using simple vocabulary for rooms and prepositions of place.', 'vocabulary': 'house, room, kitchen, bedroom, living room, bathroom, upstairs, downstairs', 'structures': '"I live in a…" / "There is a… in my house." / "My bedroom is…" / "The kitchen is…"', 'starter': 'Tell me about your home. How many rooms does it have?', 'followups': ['What room do you spend the most time in?', 'Is your kitchen upstairs or downstairs?', 'Do you share your room with someone?', 'What is your favourite room in the house?']}, {'id': 'y1t7c2', 'title': 'My Dream Room', 'goal': 'Student imagines and describes an ideal room using simple descriptive language.', 'vocabulary': 'would, colour, bed, table, window, want', 'structures': '"I would like a… room." / "My dream room would have…" / "The colour would be…"', 'starter': 'If you could design your own dream room, what would it look like?', 'followups': ['What colour would the walls be?', 'What furniture would you have?', 'Would you have a window?', 'What is one special thing you would add?']}],
    },
    'y1topic8': {
        'title': 'Favourite Places',
        'icon': '📍',
        'conversations': [{'id': 'y1t8c1', 'title': 'Places in My Town', 'goal': 'Student names and talks about places in their local area.', 'vocabulary': 'market, school, park, shop, temple, hospital, road', 'structures': '"There is a… near my house." / "I go to the… every…" / "My favourite place is…"', 'starter': 'What are some places near your house? Is there a market, a park, or a shop close by?', 'followups': ['What is your favourite place to go in your town?', 'Why do you like that place?', 'Is there a park near your house?', 'Where do you go on weekends?']}, {'id': 'y1t8c2', 'title': "A Place I'd Like to Visit", 'goal': 'Student talks about a place they would like to visit, real or imagined, using simple future language.', 'vocabulary': 'visit, would like, beach, mountain, city, village', 'structures': '"I would like to visit…" / "I want to go to… because…" / "I have never been to… but I want to."', 'starter': 'Is there a place you would really like to visit one day? It can be anywhere!', 'followups': ['Why do you want to go there?', 'What would you do there?', 'Have you ever been to a beach or a mountain?', 'Who would you take with you?']}],
    },
    'y1topic9': {
        'title': 'Nature and the World Around Us',
        'icon': '🌳',
        'conversations': [{'id': 'y1t9c1', 'title': 'Things I See in Nature', 'goal': 'Student describes things they notice in nature using simple sensory language.', 'vocabulary': 'tree, sky, flower, bird, sun, rain, colour, beautiful', 'structures': '"I see…" / "I like the colour of…" / "I hear… when…"', 'starter': 'Think about something beautiful you have seen in nature — a tree, the sky, a flower. Can you describe it?', 'followups': ['What colour was it?', 'Where did you see it?', 'Do you like the rain or the sun more?', 'What is your favourite thing about nature?']}, {'id': 'y1t9c2', 'title': 'My Favourite Season', 'goal': 'Student talks about their favourite season and weather using simple present tense.', 'vocabulary': 'summer, winter, monsoon, hot, cold, rain, sunny', 'structures': '"My favourite season is…" / "In summer it is…" / "I like… because…"', 'starter': 'Which season do you like best — summer, winter, or monsoon? Why?', 'followups': ['What do you do during that season?', "What do you wear when it's cold?", 'Do you like the rain?', 'What is the weather like today?']}],
    },
    'y1topic10': {
        'title': 'Keeping a Pet',
        'icon': '🐶',
        'conversations': [{'id': 'y1t10c1', 'title': 'Talking About Pets', 'goal': 'Student talks about pets they have or would like to have, using simple structures.', 'vocabulary': 'dog, cat, pet, name, feed, look after', 'structures': '"I have a…" / "My pet\'s name is…" / "I would like to have a…" / "I feed my pet…"', 'starter': 'Do you have a pet, or is there a pet you would love to have one day?', 'followups': ["What is your pet's name?", 'What do you feed your pet?', 'What pet would you like to have?', 'Have you ever had a pet before?']}, {'id': 'y1t10c2', 'title': 'Convince Your Parent', 'goal': 'Student practises persuasive simple language in a roleplay asking for a pet.', 'vocabulary': 'promise, take care, responsible, please', 'structures': '"I promise to…" / "I will take care of…" / "Can I please have a…?"', 'starter': 'Imagine you really want a pet but your parent says no. What would you say to convince them?', 'followups': ['What would you promise to do?', 'Why do you think a pet would be good for you?', 'What would you tell them if they say a pet is too much work?', 'Do you think you are responsible enough for a pet?']}],
    },
    'y1topic11': {
        'title': 'Story Time',
        'icon': '📖',
        'conversations': [{'id': 'y1t11c1', 'title': 'Tell Me a Story', 'goal': 'Student narrates a simple story with a beginning, middle, and end using past tense.', 'vocabulary': 'once, then, suddenly, after that, finally', 'structures': '"Once there was…" / "Then…" / "Suddenly…" / "In the end…"', 'starter': "Let's make up a story together! Once upon a time, there was a boy who found a dog. What happens next?", 'followups': ['What did the boy do next?', 'What happened suddenly?', 'How does the story end?', 'Do you want to tell me your own story now?']}, {'id': 'y1t11c2', 'title': 'My Favourite Story', 'goal': 'Student talks about a favourite story or fairy tale they know, retelling key parts.', 'vocabulary': 'story, character, beginning, end, favourite', 'structures': '"My favourite story is…" / "It is about…" / "In the end…" / "I like this story because…"', 'starter': 'What is your favourite story or fairy tale? Can you tell me what happens in it?', 'followups': ['Who is your favourite character in the story?', 'What happens at the end?', 'Why do you like this story?', 'Is there a lesson in the story?']}],
    },
    'y1topic12': {
        'title': 'Songs and Listening',
        'icon': '🎵',
        'conversations': [{'id': 'y1t12c1', 'title': 'My Favourite Song', 'goal': 'Student talks about a song they like and why, using simple opinion language.', 'vocabulary': 'song, sing, listen, favourite, like', 'structures': '"My favourite song is…" / "I like to listen to…" / "I like this song because…"', 'starter': 'Do you have a favourite song? What is it and why do you like it?', 'followups': ['Do you like to sing?', 'When do you listen to music?', 'What song makes you happy?', 'Is there a song your family likes?']}],
    },
    'y1topic13': {
        'title': 'More Questions',
        'icon': '💬',
        'conversations': [{'id': 'y1t13c1', 'title': 'Ask, Answer, Add', 'goal': 'Student practises extending a conversation by asking follow-up questions after answering.', 'vocabulary': 'favourite, often, why, what, more', 'structures': '"What\'s your favourite…?" / "I like… I also…" / "Do you…?"', 'starter': "Let's practise a longer conversation. What's your favourite food?", 'followups': ['How often do you eat that?', 'Do you cook it yourself or buy it?', 'What else do you like to eat?', 'Can you ask me a question now?']}],
    },
    'y1topic14': {
        'title': 'Mixed Practice',
        'icon': '🎲',
        'conversations': [{'id': 'y1t14c1', 'title': 'Correct the Mistake', 'goal': 'Student listens to an incorrect sentence and practises correcting it, building grammar awareness.', 'vocabulary': 'correct, wrong, fix, sentence', 'structures': '"That is not right, it should be…" / "I think the correct sentence is…"', 'starter': "I'm going to say a silly sentence and you tell me what's wrong with it. Ready? Elephants are very small animals.", 'followups': ['Can you fix this one — we eat breakfast in the evening?', 'What is wrong with this — the sun sets in the east?', 'Can you make up a funny wrong sentence for me to fix?', 'Why was that sentence wrong?']}, {'id': 'y1t14c2', 'title': 'Guess Who', 'goal': 'Student describes a well-known person using adjectives for the AI to guess, practising descriptive language.', 'vocabulary': 'famous, describe, guess, looks like, is like', 'structures': '"This person is…" / "This person looks like…" / "This person is famous for…"', 'starter': "Let's play a guessing game! Think of someone famous and describe them to me without saying their name.", 'followups': ['What do they look like?', 'What are they famous for?', 'Can you give me one more clue?', "Do you want to guess who I'm thinking of now?"]}],
    },
    'y1topic15': {
        'title': 'Describing Objects',
        'icon': '🔍',
        'conversations': [{'id': 'y1t15c1', 'title': 'What Is It Made Of', 'goal': 'Student describes everyday objects using adjectives, materials, and uses.', 'vocabulary': 'made of, wood, plastic, metal, used for, round, big, small', 'structures': '"It is made of…" / "It is used for…" / "It is…" (adjective)', 'starter': "Let's play I Spy! Think of an object near you and describe it without telling me what it is.", 'followups': ['What is it made of?', 'What is it used for?', 'Is it big or small?', 'Can I guess what it is?']}, {'id': 'y1t15c2', 'title': 'My Everyday Objects', 'goal': 'Student talks about objects they use every day and their importance.', 'vocabulary': 'always, carry, use, important, need', 'structures': '"I always carry…" / "I use… every day." / "I need… because…"', 'starter': 'What is something you always carry with you or use every day?', 'followups': ['Why is this object important to you?', 'What would you do without it?', 'Is there something in your kitchen you use every day?', 'What object would you like to get as a present?']}],
    },
    'y1topic16': {
        'title': 'My Favourite Things',
        'icon': '⭐',
        'conversations': [{'id': 'y1t16c1', 'title': 'Favourite Things and Why', 'goal': 'Student talks about favourite things across categories with simple reasons.', 'vocabulary': 'favourite, category, because, best', 'structures': '"My favourite … is … because…" / "I like this because…"', 'starter': "Let's talk about your favourite things! What is your favourite food, and what is your favourite game?", 'followups': ['What is your favourite animal?', 'What is your favourite school subject?', 'What is your favourite colour and why?', "What is something you really don't like?"]}],
    },
    'y1topic17': {
        'title': "Let's Go Shopping",
        'icon': '🛍️',
        'conversations': [{'id': 'y1t17c1', 'title': 'Asking About Prices', 'goal': 'Student practises asking and answering about prices using simple structures.', 'vocabulary': 'how much, rupees, expensive, cheap, price', 'structures': '"How much is/are…?" / "It is… rupees." / "That is expensive/cheap."', 'starter': 'Imagine you are in a shop. How would you ask the price of something?', 'followups': ['What would you say if something is too expensive?', 'What would you say if something is cheap?', 'What is something you would like to buy?', 'Have you ever bargained for something?']}, {'id': 'y1t17c2', 'title': 'At the Shop Roleplay', 'goal': 'Student roleplays a simple shopping conversation as customer or shopkeeper.', 'vocabulary': 'size, colour, looking for, help, buy', 'structures': '"I\'m looking for…" / "Can I help you?" / "Do you have this in…?" / "I\'ll take it."', 'starter': "Let's do a roleplay. I am the shopkeeper. You are looking for a pair of shoes. What do you say to me?", 'followups': ['What colour would you like?', 'What size do you need?', 'Do you want to try it on?', 'How would you ask the price?']}],
    },
    'y1topic18': {
        'title': 'Buying Presents',
        'icon': '🎁',
        'conversations': [{'id': 'y1t18c1', 'title': 'Choosing a Gift', 'goal': 'Student talks about choosing presents for people they know using simple reasoning.', 'vocabulary': 'gift, present, would, because, like', 'structures': '"I would gift… a… because…" / "For my…, I would buy…"', 'starter': 'If you could buy a present for someone in your family, what would you get them and why?', 'followups': ['Why would you choose that gift?', 'What is the best present you have ever received?', 'What occasion do people give presents on?', 'What present would you like to receive?']}],
    },
    'y1topic19': {
        'title': 'Family',
        'icon': '👨\u200d👩\u200d👧\u200d👦',
        'conversations': [{'id': 'y1t19c1', 'title': 'My Family', 'goal': 'Student talks about family members using simple vocabulary and structures.', 'vocabulary': 'mother, father, brother, sister, grandmother, grandfather, family', 'structures': '"I have a…" / "My … is called…" / "I live with…"', 'starter': 'Tell me about your family. Who do you live with?', 'followups': ['How many people are in your family?', 'Do you have brothers or sisters?', 'Who is the oldest person in your family?', 'Who do you spend the most time with?']}, {'id': 'y1t19c2', 'title': 'Describing a Family Member', 'goal': 'Student describes one family member in more detail using simple descriptive language.', 'vocabulary': 'oldest, youngest, kind, works, lives', 'structures': '"My… is…" / "He/She works as…" / "He/She is very…"', 'starter': 'Pick one person in your family. Can you tell me about them?', 'followups': ['What does this person do?', 'What is this person like?', 'Do you look like this person?', 'What do you like doing together?']}],
    },
    'y1topic20': {
        'title': 'Friends',
        'icon': '👫',
        'conversations': [{'id': 'y1t20c1', 'title': 'My Best Friend', 'goal': 'Student describes their best friend using vocabulary for friendship and personality.', 'vocabulary': 'best friend, kind, funny, honest, since when', 'structures': '"My best friend is…" / "He/She is…" / "We have been friends since…"', 'starter': 'Do you have a best friend? Tell me about them!', 'followups': ['How did you become friends?', 'What do you like to do together?', 'What makes them a good friend?', 'How long have you been friends?']}, {'id': 'y1t20c2', 'title': 'What Makes a Good Friend', 'goal': 'Student reflects on qualities of friendship using simple opinion language.', 'vocabulary': 'kind, share, listen, trust, help', 'structures': '"A good friend is…" / "A good friend always…" / "I think… because…"', 'starter': 'What do you think makes someone a good friend?', 'followups': ['Have you ever helped a friend?', 'Has a friend ever helped you?', 'What do good friends do together?', 'How many close friends do you have?']}],
    },
    'y1topic21': {
        'title': 'Describing Actions',
        'icon': '🏃',
        'conversations': [{'id': 'y1t21c1', 'title': 'How Do You Do Things', 'goal': 'Student uses simple adverbs to describe how actions are performed.', 'vocabulary': 'quickly, slowly, loudly, quietly, happily', 'structures': '"I … quickly/slowly." / "He/She … loudly." / "I do this… because…"', 'starter': 'Tell me — do you walk to school quickly or slowly?', 'followups': ['Do you eat your food quickly or slowly?', 'Do you talk loudly or quietly?', 'How do you do your homework — carefully or quickly?', 'How does your friend laugh — loudly or softly?']}],
    },
    'y1topic22': {
        'title': 'How Often Do You',
        'icon': '🔁',
        'conversations': [{'id': 'y1t22c1', 'title': 'Talking About Frequency', 'goal': 'Student talks about how often they do activities using simple frequency words.', 'vocabulary': 'always, sometimes, never, often, every day, once a week', 'structures': '"I always…" / "I sometimes…" / "I never…" / "How often do you…?"', 'starter': 'How often do you play outside — every day, sometimes, or never?', 'followups': ['How often do you watch TV?', 'How often do you help at home?', 'How often do you read books?', 'Is there something you never do?']}],
    },
    'y1topic23': {
        'title': 'Food Choices',
        'icon': '🍛',
        'conversations': [{'id': 'y1t23c1', 'title': 'Food I Eat', 'goal': 'Student talks about food they eat and like using simple present tense.', 'vocabulary': 'eat, drink, cook, favourite, healthy', 'structures': '"I eat… for breakfast/lunch/dinner." / "I like to eat…" / "I don\'t like…"', 'starter': 'What do you usually eat for breakfast?', 'followups': ['What is your favourite food to eat at home?', 'Do you like spicy food?', 'What do you drink most often?', 'Is there a food you have never tried but want to?']}, {'id': 'y1t23c2', 'title': 'Healthy or Unhealthy', 'goal': 'Student reflects on healthy vs unhealthy eating habits using simple comparative language.', 'vocabulary': 'healthy, unhealthy, fruit, vegetable, sweet, junk food', 'structures': '"I think… is healthy because…" / "I eat… every day." / "I should eat more…"', 'starter': 'Do you think you are a healthy eater? Tell me what you eat in a normal day.', 'followups': ['What fruits or vegetables do you like?', 'Do you eat sweets often?', 'What is one food you should eat more of?', 'What is your favourite healthy food?']}],
    },
}


def get_curriculum_for_age(age: int) -> dict:
    """Returns the right curriculum set based on student age."""
    if age is not None and 9 <= age <= 12:
        return CURRICULUM_9_12
    return CURRICULUM

GLOBAL_RULES = """
GLOBAL RULES — apply to every single response without exception:
- Keep vocabulary appropriate for the student's age — do not use overly complex words
- Ask only ONE follow-up question per response — never two at once
- Accept incomplete sentences — model the correct version warmly, never harshly
- Correct only the MOST IMPORTANT single error per response, not every mistake at once
- If the student gives a one-word answer, gently prompt for a full sentence using a simple example
- Keep responses concise — the student needs to speak more than you do
- ALWAYS stay on the module topic — never drift into unrelated subjects
- Use examples grounded in an underprivileged Indian student's daily life — local market, school, cricket on the street, family, festivals. NEVER assume access to malls, imported goods, tablets, foreign travel, or other costly/unfamiliar things
- Your tone must always be warm, patient, and encouraging
- Never make the student feel embarrassed or judged for errors
- For younger students (under 13), use extremely short, simple sentences and celebrate every small success enthusiastically
"""

def build_system_prompt(age: int, conv: dict) -> str:
    level = LEVELS.get(age, LEVELS[17])
    if age <= 10:
        lang = "Use VERY simple words and VERY short sentences (5-8 words max). Speak like a kind teacher talking to a young beginner. Repeat key words often. Be extremely encouraging and patient — this student has limited English exposure."
    elif age <= 12:
        lang = "Use simple, everyday words and short sentences. Avoid idioms or complex grammar. Be warm, patient, and very encouraging — this student is still building basic confidence in English."
    elif age <= 14:
        lang = "Use clear everyday vocabulary and natural sentences. Be warm and encouraging. Avoid complex grammar explanations."
    elif age <= 16:
        lang = "Use natural conversational language. Occasionally use idioms. Be engaging and gently challenging."
    else:
        lang = "Use rich, natural language. Challenge the student with varied vocabulary, idioms, and complex ideas."

    return f"""You are a warm, supportive English conversation tutor for a {age}-year-old Indian student ({level}).

TODAY'S CONVERSATION: {conv['title']}
GOAL: {conv['goal']}
KEY VOCABULARY to introduce naturally: {conv['vocabulary']}
TARGET SENTENCE STRUCTURES to model and encourage: {conv['structures']}
FOLLOW-UP QUESTIONS you can draw from (use one at a time, naturally):
{chr(10).join('- ' + q for q in conv['followups'])}

LANGUAGE LEVEL GUIDANCE: {lang}

{GLOBAL_RULES}

RESPONSE FORMAT — you must ALWAYS respond in exactly these 4 sections with these exact emoji labels. Never skip a section. Never add extra sections.

🗣 What you said:
[Repeat the student's exact words, including any errors. Nothing else here.]

❓ Next question:
[Ask exactly ONE natural follow-up question. Keep it simple and easy to answer. Assume what the student said is correct.]

✅ Feedback:
[Correct the single most important grammar or sentence structure error. Explain it simply and kindly. If there are no errors write: "Great job — no corrections needed!"]

✨ Enhancements:
[Suggest one better word or phrase from the key vocabulary list if relevant. Phrase it as: "Instead of \\"...\\" you could say \\"...\\"". If nothing needs enhancing write: "Your vocabulary was great!"]"""


# ─────────────────────────────────────────────
# FIREBASE
# ─────────────────────────────────────────────
def init_firebase():
    if firebase_admin._apps:
        return firestore.client()
    try:
        fb = {
            "type":                        st.secrets["firebase"]["type"],
            "project_id":                  st.secrets["firebase"]["project_id"],
            "private_key_id":              st.secrets["firebase"]["private_key_id"],
            "private_key":                 st.secrets["firebase"]["private_key"].replace("\\n", "\n"),
            "client_email":                st.secrets["firebase"]["client_email"],
            "client_id":                   st.secrets["firebase"]["client_id"],
            "auth_uri":                    st.secrets["firebase"]["auth_uri"],
            "token_uri":                   st.secrets["firebase"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url":        st.secrets["firebase"]["client_x509_cert_url"],
        }
        cred = credentials.Certificate(fb)
        firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"Firebase connection failed: {e}")
        return None

db = init_firebase()

def get_or_create_student(name: str, age: int) -> dict:
    if db is None:
        return {"name": name, "age": age, "level": LEVELS.get(age, LEVELS[17])}
    doc_ref = db.collection("students").document(name.lower().replace(" ", "_"))
    doc = doc_ref.get()
    if doc.exists:
        doc_ref.update({"age": age, "level": LEVELS.get(age, LEVELS[17])})
        return doc.to_dict()
    student = {"name": name, "age": age, "level": LEVELS.get(age, LEVELS[17]),
               "created_at": datetime.utcnow().isoformat(), "total_sessions": 0, "total_messages": 0}
    doc_ref.set(student)
    return student

def save_session(student_name: str, session: dict):
    if db is None: return
    try:
        sid = student_name.lower().replace(" ", "_")
        db.collection("students").document(sid)\
          .collection("sessions").document(session["id"]).set(session)
        db.collection("students").document(sid).update({
            "total_sessions": firestore.INCREMENT(1),
            "total_messages": firestore.INCREMENT(session.get("message_count", 0)),
        })
    except Exception as e:
        st.warning(f"Could not save session: {e}")

def log_message(student_name: str, session_id: str, msg: dict):
    if db is None: return
    try:
        sid = student_name.lower().replace(" ", "_")
        db.collection("students").document(sid)\
          .collection("sessions").document(session_id)\
          .collection("messages").add(msg)
    except: pass

def get_past_sessions(student_name: str) -> list:
    if db is None: return []
    try:
        sid = student_name.lower().replace(" ", "_")
        docs = db.collection("students").document(sid)\
                 .collection("sessions").order_by("started_at", direction=firestore.Query.DESCENDING)\
                 .limit(50).stream()
        return [d.to_dict() for d in docs]
    except: return []

def get_session_messages(student_name: str, session_id: str) -> list:
    if db is None: return []
    try:
        sid = student_name.lower().replace(" ", "_")
        docs = db.collection("students").document(sid)\
                 .collection("sessions").document(session_id)\
                 .collection("messages").order_by("timestamp").stream()
        return [d.to_dict() for d in docs]
    except: return []

def get_completed_conv_ids(student_name: str) -> dict:
    """Returns {conv_id: session_date_str} for all completed conversations."""
    sessions = get_past_sessions(student_name)
    done = {}
    for s in sessions:
        cid = s.get("conversation")
        if cid and cid not in done:
            done[cid] = s.get("started_at", "")[:10]
    return done


# ─────────────────────────────────────────────
# TEACHER FIRESTORE HELPERS
# ─────────────────────────────────────────────
def get_teacher_password() -> str:
    if db is None: return ""
    try:
        doc = db.collection("config").document("teacher").get()
        if doc.exists:
            return doc.to_dict().get("password", "")
    except: pass
    return ""

def set_teacher_password(new_pw: str):
    if db is None: return
    db.collection("config").document("teacher").set({"password": new_pw})

def get_all_students() -> list:
    if db is None: return []
    try:
        docs = db.collection("students").stream()
        return sorted([d.to_dict() for d in docs], key=lambda x: x.get("name","").lower())
    except: return []

def get_curriculum_overrides() -> dict:
    """Returns {conv_id: {field: value}} overrides stored by teacher."""
    if db is None: return {}
    try:
        docs = db.collection("curriculum_overrides").stream()
        return {d.id: d.to_dict() for d in docs}
    except: return {}

def save_curriculum_override(conv_id: str, data: dict):
    if db is None: return
    db.collection("curriculum_overrides").document(conv_id).set(data)

def apply_curriculum_overrides(curriculum: dict, overrides: dict) -> dict:
    """Merge Firestore overrides into the hardcoded curriculum dict."""
    import copy
    cur = copy.deepcopy(curriculum)
    for topic_key, topic in cur.items():
        for conv in topic["conversations"]:
            if conv["id"] in overrides:
                conv.update(overrides[conv["id"]])
    return cur


# ─────────────────────────────────────────────
# ASSIGNMENT + PROGRESS REPORT HELPERS
# ─────────────────────────────────────────────
def get_student_assignment(student_name: str) -> dict:
    """Returns {mode: 'free'|'assigned', conv_ids: []} or None."""
    if db is None: return None
    try:
        sid = student_name.lower().replace(" ", "_")
        doc = db.collection("students").document(sid).collection("meta").document("assignment").get()
        return doc.to_dict() if doc.exists else None
    except: return None

def set_student_assignment(student_name: str, mode: str, conv_ids: list):
    if db is None: return
    sid = student_name.lower().replace(" ", "_")
    db.collection("students").document(sid).collection("meta").document("assignment").set({
        "mode": mode, "conv_ids": conv_ids
    })

def get_progress_report(student_name: str) -> dict:
    if db is None: return {}
    try:
        sid = student_name.lower().replace(" ", "_")
        doc = db.collection("students").document(sid).collection("meta").document("progress_report").get()
        return doc.to_dict() if doc.exists else {}
    except: return {}

def save_progress_report(student_name: str, report: dict):
    if db is None: return
    sid = student_name.lower().replace(" ", "_")
    db.collection("students").document(sid).collection("meta").document("progress_report").set(report)

def get_new_sessions_since_report(student_name: str, existing_report: dict) -> list:
    """Returns sessions that occurred after the last report was generated."""
    last_generated = existing_report.get("generated_at", "") if existing_report else ""
    all_sessions = get_past_sessions(student_name)
    if not last_generated:
        return all_sessions
    return [s for s in all_sessions if s.get("started_at","") > last_generated]

def has_new_sessions_since_report(student_name: str, existing_report: dict) -> bool:
    return len(get_new_sessions_since_report(student_name, existing_report)) > 0

def generate_progress_report(student_name: str, existing_report: dict = None,
                              force_full: bool = False) -> dict:
    """
    Incremental report generation:
    - First time (no existing_report): analyses all sessions, creates report from scratch.
    - Subsequent times: only analyses NEW sessions since last report, merges with existing.
    - force_full=True (teacher only): regenerates entirely from scratch.
    """
    all_sessions = get_past_sessions(student_name)
    if not all_sessions:
        return {"error": "No sessions found."}

    is_first = not existing_report or not existing_report.get("text") or force_full

    if is_first:
        sessions_to_analyse = all_sessions[:20]
        mode = "full"
    else:
        sessions_to_analyse = get_new_sessions_since_report(student_name, existing_report)[:10]
        if not sessions_to_analyse:
            return {"error": "No new sessions since last report."}
        mode = "incremental"

    # Collect student messages from chosen sessions
    new_msgs = []
    for sess in sessions_to_analyse:
        msgs = get_session_messages(student_name, sess["id"])
        for m in msgs:
            if m.get("role") == "user":
                new_msgs.append(m.get("content",""))

    if not new_msgs:
        return {"error": "No student messages found in these sessions."}

    combined = "\n".join(f"- {m}" for m in new_msgs[:60])
    client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    if is_first:
        # Full report from scratch
        prompt = f"""You are an English language teacher reviewing a student's spoken English practice.
Below are the student's spoken responses collected over several sessions:

{combined}

Produce a structured progress report with these exact sections:

## Summary
A 2-3 sentence overall assessment of the student's English level and main strengths.

## Grammar errors by category
List the most common grammar error types with a specific example and corrected version:
**Error type**: [name]
Example: "[what they said]" → "[correct version]"
Explanation: [brief explanation]

## Vocabulary observations
Note patterns in vocabulary — overused words, missing vocabulary, or good choices.

## Specific strategies to improve
List 3-5 concrete, actionable strategies tailored to this student's specific errors.

Keep the tone encouraging. Focus on patterns, not one-off errors."""

        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        report_text = resp.choices[0].message.content
        return {
            "text": report_text,
            "generated_at": datetime.utcnow().isoformat(),
            "session_count": len(all_sessions),
            "message_count": len(new_msgs),
            "last_session_date": all_sessions[0].get("started_at","")[:10] if all_sessions else "",
        }

    else:
        # Incremental: extract new patterns and merge with existing report
        existing_text = existing_report.get("text","")
        prompt = f"""You are an English language teacher updating a student's progress report.

EXISTING REPORT:
{existing_text}

NEW RESPONSES from {len(sessions_to_analyse)} new session(s) since the last report:
{combined}

Update the existing report by:
1. Updating the Summary to reflect any improvement or new patterns.
2. Adding any NEW grammar error types seen in the new responses (do not repeat existing ones unless they are still occurring frequently).
3. Updating Vocabulary observations if new patterns appear.
4. Revising the Specific strategies if new priorities have emerged, or confirming existing ones still apply.

Return the COMPLETE updated report using the same section headings. Be concise — do not pad.
Keep the tone encouraging."""

        resp = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )
        merged_text = resp.choices[0].message.content
        prev_count = existing_report.get("message_count", 0)
        prev_sessions = existing_report.get("session_count", 0)
        return {
            "text": merged_text,
            "generated_at": datetime.utcnow().isoformat(),
            "session_count": prev_sessions + len(sessions_to_analyse),
            "message_count": prev_count + len(new_msgs),
            "last_session_date": all_sessions[0].get("started_at","")[:10] if all_sessions else "",
        }


# ─────────────────────────────────────────────
# OPENAI HELPERS
# ─────────────────────────────────────────────
def get_openai_client():
    return openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def get_ai_response(user_text: str) -> str:
    client = get_openai_client()
    conv = st.session_state.current_conv
    # Apply any teacher overrides to this conversation's content
    overrides = get_curriculum_overrides()
    if conv["id"] in overrides:
        conv = {**conv, **overrides[conv["id"]]}
    system = build_system_prompt(st.session_state.student["age"], conv)
    messages = [{"role": "system", "content": system}]
    for m in st.session_state.chat_history:
        messages.append({"role": m["role"], "content": m["content"]})
    messages.append({"role": "user", "content": user_text})
    resp = client.chat.completions.create(model="gpt-3.5-turbo", messages=messages, temperature=0.7)
    return resp.choices[0].message.content

def transcribe(audio_bytes: bytes) -> str:
    client = get_openai_client()
    with open("/tmp/student_audio.wav", "wb") as f:
        f.write(audio_bytes)
    with open("/tmp/student_audio.wav", "rb") as f:
        result = client.audio.transcriptions.create(model="whisper-1", file=f)
    return result.text

def text_to_speech(text: str) -> bytes:
    client = get_openai_client()
    # Extract only the Next question for speaking — cleaner for the student
    try:
        spoken = text.split("❓ Next question:")[1].split("✅ Feedback:")[0].strip()
    except:
        spoken = text
    resp = client.audio.speech.create(model="tts-1", voice="shimmer", input=spoken)
    return resp.content

def autoplay_audio(audio_bytes: bytes):
    b64 = base64.b64encode(audio_bytes).decode()
    st.markdown(
        f'<audio autoplay style="display:none"><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>',
        unsafe_allow_html=True
    )


# ─────────────────────────────────────────────
# PARSE + RENDER 4-SECTION RESPONSE
# ─────────────────────────────────────────────
def parse_response(text: str) -> dict:
    s = {"said": "", "question": "", "feedback": "", "enhancement": "", "raw": text}
    patterns = {
        "said":        r"🗣\s*What you said:(.*?)(?=❓|✅|✨|$)",
        "question":    r"❓\s*Next question:(.*?)(?=🗣|✅|✨|$)",
        "feedback":    r"✅\s*Feedback:(.*?)(?=🗣|❓|✨|$)",
        "enhancement": r"✨\s*Enhancements:(.*?)(?=🗣|❓|✅|$)",
    }
    for k, p in patterns.items():
        m = re.search(p, text, re.DOTALL | re.IGNORECASE)
        if m: s[k] = m.group(1).strip()
    return s

def render_response(s: dict):
    if not any([s["question"], s["feedback"], s["enhancement"]]):
        st.markdown(s["raw"]); return
    html = '<div class="fb-card">'
    if s["question"]:
        html += f'<div class="fb-sec"><div class="fb-lbl lbl-q">❓ Next question</div><div><strong>{s["question"]}</strong></div></div>'
    if s["feedback"]:
        html += f'<div class="fb-sec"><div class="fb-lbl lbl-fb">✅ Feedback</div><div>{s["feedback"]}</div></div>'
    if s["enhancement"]:
        html += f'<div class="fb-sec"><div class="fb-lbl lbl-enh">✨ Enhancement</div><div>{s["enhancement"]}</div></div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
for k, v in {
    "screen": "login", "student": None,
    "selected_topic": None, "current_conv": None,
    "chat_history": [], "session_id": None,
    "message_count": 0, "session_start": None,
    "last_audio_key": None, "pending_audio": None,
    "mic_key": 0,
    "processing": False,
    "editing_index": None,
    "view_session": None,
    "is_teacher": False,
    "teacher_view_student": None,   # student dict teacher is browsing
    "teacher_view_session": None,   # session dict teacher is reading
    "teacher_edit_conv": None,      # conv being edited in curriculum editor
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────
# SCREEN: LOGIN
# ─────────────────────────────────────────────
def screen_login():
    st.markdown("## 🎙️ SpeakUp")
    st.markdown("##### AI English conversation practice · Ages 9–17")
    st.info("🔊 Make sure your speaker volume is turned up — the AI will speak its questions aloud.")
    st.divider()

    tab_student, tab_teacher = st.tabs(["👤 Student login", "🏫 Teacher login"])

    with tab_student:
        with st.form("login_student"):
            name = st.text_input("Full name", placeholder="e.g. Aanya Sharma")
            age  = st.selectbox("Age", [""] + list(range(9, 18)),
                                format_func=lambda x: "Select age…" if x == "" else str(x))
            if st.form_submit_button("Start learning →", use_container_width=True):
                if not name.strip(): st.error("Please enter your full name.")
                elif age == "": st.error("Please select your age.")
                else:
                    st.session_state.student = get_or_create_student(name.strip(), int(age))
                    st.session_state.is_teacher = False
                    st.session_state.screen = "home"
                    st.rerun()
        st.caption("Already used SpeakUp before? Enter your name and age — your progress loads automatically.")

    with tab_teacher:
        with st.form("login_teacher"):
            pw = st.text_input("Teacher password", type="password")
            if st.form_submit_button("Sign in as teacher →", use_container_width=True):
                correct = get_teacher_password()
                if not correct:
                    st.error("No teacher password has been set up yet. Please contact the app administrator.")
                elif pw == correct:
                    st.session_state.is_teacher = True
                    st.session_state.screen = "teacher_home"
                    st.rerun()
                else:
                    st.error("Incorrect password.")


# ─────────────────────────────────────────────
# SCREEN: HOME — topic + conversation picker
# ─────────────────────────────────────────────
def screen_home():
    s = st.session_state.student
    col_w, col_so = st.columns([5, 1])
    with col_w:
        st.markdown(
            f'<div class="welcome-banner"><h2>Hello, {s["name"]} 👋</h2>'
            f'<p>Age {s["age"]}</p></div>',
            unsafe_allow_html=True
        )
    with col_so:
        st.markdown("<div style='padding-top:1.1rem'></div>", unsafe_allow_html=True)
        if st.button("Sign out", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

    # Tab: Practice vs History
    tab_practice, tab_history = st.tabs(["📚 Practice", "📋 Past sessions"])

    with tab_practice:
        assignment = get_student_assignment(s["name"])
        completed  = get_completed_conv_ids(s["name"])
        overrides  = get_curriculum_overrides()

        if assignment and assignment.get("mode") == "assigned":
            # ── ASSIGNED MODE: only show the teacher-assigned conversations ──
            assigned_ids = assignment.get("conv_ids", [])
            st.info("📌 Your teacher has assigned specific conversations for you to practise.")

            # Build a flat lookup of all convs across all topics (age-appropriate set)
            curric = get_curriculum_for_age(s["age"])
            all_conv_lookup = {}
            for tk, tv in curric.items():
                for c in tv["conversations"]:
                    all_conv_lookup[c["id"]] = (tk, c)
            # also check extra_conversations
            if db:
                try:
                    for d in db.collection("extra_conversations").stream():
                        dc = d.to_dict()
                        all_conv_lookup[dc["id"]] = (dc.get("topic_key",""), dc)
                except: pass

            convs_to_show = []
            for cid in assigned_ids:
                if cid in all_conv_lookup:
                    topic_key, conv = all_conv_lookup[cid]
                    merged = {**conv, **overrides.get(cid, {})}
                    if not merged.get("hidden"):
                        convs_to_show.append((topic_key, merged))

            if not convs_to_show:
                st.warning("No conversations assigned yet — check back soon.")
            else:
                for i, (topic_key, conv) in enumerate(convs_to_show):
                    topic_icon = curric.get(topic_key, {}).get("icon", "📖")
                    already_done = conv["id"] in completed
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{topic_icon} {conv['title']}**{'  ✅' if already_done else ''}")
                        st.caption(conv.get("goal",""))
                        if already_done:
                            st.caption(f"Done on {completed[conv['id']]}")
                    with col2:
                        btn_label = "Redo →" if already_done else "Start →"
                        if st.button(btn_label, key=f"conv_{conv['id']}", use_container_width=True):
                            if already_done:
                                st.session_state.pending_already_done = {"conv": conv, "date": completed[conv["id"]]}
                                st.session_state.screen = "already_done"
                                st.rerun()
                            else:
                                st.session_state.selected_topic = topic_key
                                launch_session(conv)
                    if i < len(convs_to_show) - 1:
                        st.divider()

        else:
            # ── FREE MODE: full topic + conversation picker (age-appropriate set) ──
            curric = get_curriculum_for_age(s["age"])
            st.markdown("#### Choose a topic")
            topic_options = {f'{v["icon"]} {v["title"]}': k for k, v in curric.items()}
            chosen_label = st.selectbox("Topic", list(topic_options.keys()), label_visibility="collapsed")
            chosen_key   = topic_options[chosen_label]
            topic        = curric[chosen_key]
            st.session_state.selected_topic = chosen_key

            # Get any teacher-added extra conversations for this topic
            try:
                extra_docs = db.collection("extra_conversations").where("topic_key","==",chosen_key).stream() if db else []
                extra_convs = [d.to_dict() for d in extra_docs]
            except: extra_convs = []

            st.markdown("#### Choose a conversation")
            all_convs = topic["conversations"] + extra_convs
            convs = [c for c in all_convs if not overrides.get(c["id"],{}).get("hidden", False)]
            for i, conv in enumerate(convs):
                already_done = conv["id"] in completed
                col1, col2 = st.columns([4, 1])
                with col1:
                    if already_done:
                        st.markdown(f"**{conv['title']}** ✅")
                        st.caption(f"{conv['goal']} · Done on {completed[conv['id']]}")
                    else:
                        st.markdown(f"**{conv['title']}**")
                        st.caption(conv["goal"])
                with col2:
                    btn_label = "Redo →" if already_done else "Start →"
                    if st.button(btn_label, key=f"conv_{conv['id']}", use_container_width=True):
                        if already_done:
                            st.session_state.pending_already_done = {"conv": conv, "date": completed[conv["id"]]}
                            st.session_state.screen = "already_done"
                            st.rerun()
                        else:
                            launch_session(conv)
                if i < len(convs) - 1:
                    st.divider()

    with tab_history:
        screen_history_tab(s)


def delete_student_session(student_name: str, session_id: str):
    if db is None: return
    try:
        sid = student_name.lower().replace(" ", "_")
        sess_ref = db.collection("students").document(sid).collection("sessions").document(session_id)
        # delete subcollection messages first
        msgs = sess_ref.collection("messages").stream()
        for m in msgs:
            m.reference.delete()
        sess_ref.delete()
        # decrement totals
        db.collection("students").document(sid).update({
            "total_sessions": firestore.INCREMENT(-1),
        })
    except Exception as e:
        st.error(f"Could not delete session: {e}")

def render_progress_report(report: dict, editable: bool = False, student_name: str = ""):
    """Renders the progress report. If editable=True, shows an edit form (teacher only)."""
    if not report or "text" not in report:
        return
    st.caption(f"Generated {report.get('generated_at','')[:10]} · Based on {report.get('session_count',0)} sessions · {report.get('message_count',0)} messages")
    if editable and student_name:
        with st.form("edit_report_form"):
            edited = st.text_area("Edit report", value=report["text"], height=500)
            if st.form_submit_button("💾 Save edited report", use_container_width=True):
                report["text"] = edited
                report["edited_by_teacher"] = True
                save_progress_report(student_name, report)
                st.success("Report saved.")
                st.rerun()
    else:
        st.markdown(report["text"])


def screen_history_tab(s):
    sessions = get_past_sessions(s["name"])
    if not sessions:
        st.caption("No sessions yet — complete your first conversation to see it here.")
        return
    st.markdown(f"**{len(sessions)} sessions completed**")

    # ── Progress report button ──
    existing_report = get_progress_report(s["name"])
    has_new = has_new_sessions_since_report(s["name"], existing_report)

    rcol1, rcol2 = st.columns([3,1])
    with rcol1:
        if existing_report:
            st.caption(f"📊 Report last updated {existing_report.get('generated_at','')[:10]}")
            if has_new:
                st.caption("🆕 You have new sessions since your last report.")
        else:
            st.caption("No report yet — complete some sessions and generate one.")
    with rcol2:
        if not existing_report:
            # First time — always show button
            if st.button("📊 Generate report", use_container_width=True):
                with st.spinner("Analysing your sessions…"):
                    try:
                        report = generate_progress_report(s["name"])
                        if "error" not in report:
                            save_progress_report(s["name"], report)
                            st.success("Report ready!")
                            st.rerun()
                        else:
                            st.error(report["error"])
                    except Exception as e:
                        st.error(f"Could not generate report: {e}")
        elif has_new:
            # New sessions available — update existing
            if st.button("🆕 Update report", use_container_width=True):
                with st.spinner("Adding new sessions to your report…"):
                    try:
                        report = generate_progress_report(s["name"], existing_report=existing_report)
                        if "error" not in report:
                            save_progress_report(s["name"], report)
                            st.success("Report updated!")
                            st.rerun()
                        else:
                            st.error(report["error"])
                    except Exception as e:
                        st.error(f"Could not update report: {e}")
        else:
            st.caption("Up to date ✓")

    if existing_report and existing_report.get("text"):
        with st.expander("📊 View my progress report", expanded=False):
            render_progress_report(existing_report, editable=False)

    st.divider()
    for sess in sessions:
        date_str   = sess.get("started_at", "")[:10]
        msgs       = sess.get("message_count", 0)
        title      = sess.get("conv_title", sess.get("conversation", "Session"))
        topic_id   = sess.get("topic", "")
        topic_icon = get_curriculum_for_age(s["age"]).get(topic_id, {}).get("icon", "📖")
        col1, col2, col3 = st.columns([4, 1, 1])
        with col1:
            st.markdown(f"**{topic_icon} {title}**")
            st.caption(f"{date_str} · {msgs} messages")
        with col2:
            if st.button("View →", key=f"view_{sess['id']}", use_container_width=True):
                st.session_state.view_session = sess
                st.session_state.screen = "transcript"
                st.rerun()
        with col3:
            if st.button("🗑️", key=f"del_{sess['id']}", use_container_width=True,
                         help="Delete this session"):
                delete_student_session(s["name"], sess["id"])
                st.rerun()
        st.divider()


def launch_session(conv):
    st.session_state.current_conv   = conv
    st.session_state.session_id     = str(uuid.uuid4())
    st.session_state.chat_history   = []
    st.session_state.message_count  = 0
    st.session_state.session_start  = datetime.utcnow().isoformat()
    st.session_state.last_audio_key = None
    st.session_state.editing_index  = None
    st.session_state.screen         = "chat"
    st.rerun()


# ─────────────────────────────────────────────
# SCREEN: CHAT
# ─────────────────────────────────────────────
def screen_chat():
    s    = st.session_state.student
    conv = st.session_state.current_conv

    # Header
    col1, col2 = st.columns([4, 1])
    with col1:
        topic = get_curriculum_for_age(s["age"])[st.session_state.selected_topic]
        st.markdown(f"**{topic['icon']} {topic['title']}** — {conv['title']}")
        st.caption(f"Age {s['age']}")
    with col2:
        if st.button("End session", use_container_width=True):
            end_session(); return

    st.divider()

    # ── AI opener (first turn only) ──
    if not st.session_state.chat_history:
        with st.spinner("Starting conversation…"):
            # Opener is just a plain greeting + starter question — no 4-section format
            opener_prompt = (
                f"Ask this exact starter question to open the conversation: \"{conv['starter']}\" "
                f"Do not greet by name. Do not say hello or hi first. "
                f"Just ask the question naturally and warmly. Do NOT use the 4-section format."
            )
            try:
                ai_text = get_ai_response(opener_prompt)
                # Generate TTS for the full opener
                client = get_openai_client()
                tts_resp = client.audio.speech.create(model="tts-1", voice="shimmer", input=ai_text)
                audio_b64 = base64.b64encode(tts_resp.content).decode()
                st.session_state.chat_history.append({
                    "role": "assistant", "content": ai_text,
                    "sections": None, "is_opener": True
                })
                # Store audio to play during render, not during processing
                st.session_state.pending_audio = audio_b64
                log_message(s["name"], st.session_state.session_id,
                            {"role": "assistant", "content": ai_text,
                             "timestamp": datetime.utcnow().isoformat()})
            except Exception as e:
                st.error(f"Error starting conversation: {e}"); return

    # ── Play any pending audio BEFORE rendering (survives the rerun) ──
    if st.session_state.get("pending_audio"):
        b64 = st.session_state.pending_audio
        st.session_state.pending_audio = None
        st.markdown(
            f'<audio autoplay><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>',
            unsafe_allow_html=True
        )

    # ── Render chat history ──
    last_ai_idx  = max((i for i, m in enumerate(st.session_state.chat_history) if m["role"] == "assistant"), default=None)
    last_usr_idx = max((i for i, m in enumerate(st.session_state.chat_history) if m["role"] == "user"), default=None)

    for idx, msg in enumerate(st.session_state.chat_history):
        if msg["role"] == "user":
            with st.chat_message("user"):
                # Edit mode for this message
                if st.session_state.editing_index == idx:
                    edited = st.text_input("Edit your response:", value=msg["content"],
                                           key=f"edit_input_{idx}")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✅ Send edited", key=f"send_edit_{idx}", use_container_width=True):
                            # Remove everything after this user message and re-send
                            st.session_state.chat_history = st.session_state.chat_history[:idx]
                            st.session_state.editing_index = None
                            st.session_state.processing = True
                            st.session_state.mic_key += 1
                            process_message(edited.strip())
                    with c2:
                        if st.button("✖ Cancel", key=f"cancel_edit_{idx}", use_container_width=True):
                            st.session_state.editing_index = None
                            st.rerun()
                else:
                    st.markdown(f"🎤 *{msg['content']}*")
                    # Show edit button only on the last user message
                    if idx == last_usr_idx and not st.session_state.get("processing"):
                        if st.button("✏️ Edit", key=f"edit_btn_{idx}"):
                            st.session_state.editing_index = idx
                            st.rerun()
        else:
            with st.chat_message("assistant", avatar="🎙️"):
                if msg.get("is_opener"):
                    st.markdown(msg["content"])
                else:
                    render_response(msg.get("sections", {
                        "raw": msg["content"],
                        "said": "", "question": "", "feedback": "", "enhancement": ""
                    }))
                    # Regenerate button only on the last AI message
                    if idx == last_ai_idx and not st.session_state.get("processing"):
                        if st.button("🔄 Ask a different question", key=f"redo_{idx}"):
                            st.session_state.processing = True
                            st.session_state.mic_key += 1
                            with st.spinner("Getting a new question…"):
                                try:
                                    regen_text = get_ai_response(
                                        "Ask me a different follow-up question about the same topic. "
                                        "Do not repeat the previous question. Use the 4-section format."
                                    )
                                    regen_sections = parse_response(regen_text)
                                    try:
                                        spoken = regen_text.split("❓ Next question:")[1].split("✅ Feedback:")[0].strip()
                                    except:
                                        spoken = regen_sections.get("question", regen_text)
                                    client = get_openai_client()
                                    tts_resp = client.audio.speech.create(model="tts-1", voice="shimmer", input=spoken)
                                    audio_b64 = base64.b64encode(tts_resp.content).decode()
                                    st.session_state.chat_history[idx] = {
                                        "role": "assistant", "content": regen_text,
                                        "sections": regen_sections, "is_opener": False
                                    }
                                    st.session_state.pending_audio = audio_b64
                                except Exception as e:
                                    st.error(f"Could not regenerate: {e}")
                            st.session_state.processing = False
                            st.rerun()

    st.divider()

    # ── Mic input — st.audio_input (built-in, no library needed) ──
    if st.session_state.get("processing"):
        st.info("⏳ Processing your answer…")
    else:
        st.markdown("**🎤 Tap to record your answer:**")
        audio = st.audio_input(
            "Record",
            label_visibility="collapsed",
            key=f"audio_{st.session_state.get('mic_key', 0)}"
        )
        if audio is not None:
            audio_bytes = audio.read()
            audio_key = hash(audio_bytes)
            if audio_key != st.session_state.last_audio_key:
                st.session_state.last_audio_key = audio_key
                st.session_state.processing = True
                st.session_state.mic_key = st.session_state.get("mic_key", 0) + 1
                with st.spinner("Transcribing your answer…"):
                    try:
                        user_text = transcribe(audio_bytes)
                    except Exception as e:
                        st.session_state.processing = False
                        st.error(f"Transcription failed: {e}"); return
                if user_text.strip():
                    process_message(user_text.strip())
                else:
                    st.session_state.processing = False
                    st.warning("Couldn't hear that clearly — please try again.")
        st.caption("Tap the mic button, speak, then tap stop. The AI will respond automatically.")




def process_message(user_text: str):
    s = st.session_state.student
    st.session_state.chat_history.append({"role": "user", "content": user_text, "sections": None})
    st.session_state.message_count += 1
    log_message(s["name"], st.session_state.session_id,
                {"role": "user", "content": user_text, "timestamp": datetime.utcnow().isoformat()})

    with st.spinner("Thinking…"):
        try:
            ai_text  = get_ai_response(user_text)
            sections = parse_response(ai_text)
            # Get spoken text (next question only) and generate audio
            try:
                spoken = ai_text.split("❓ Next question:")[1].split("✅ Feedback:")[0].strip()
            except:
                spoken = ai_text
            client = get_openai_client()
            tts_resp = client.audio.speech.create(model="tts-1", voice="shimmer", input=spoken)
            audio_b64 = base64.b64encode(tts_resp.content).decode()
        except Exception as e:
            st.error(f"Error getting response: {e}"); return

    st.session_state.chat_history.append({
        "role": "assistant", "content": ai_text,
        "sections": sections, "is_opener": False
    })
    log_message(s["name"], st.session_state.session_id,
                {"role": "assistant", "content": ai_text, "timestamp": datetime.utcnow().isoformat()})
    # Store audio in session state — it plays at the top of the next render pass
    st.session_state.pending_audio = audio_b64
    st.session_state.processing = False  # re-enable mic before rerun
    st.rerun()

def end_session():
    s = st.session_state.student
    save_session(s["name"], {
        "id":            st.session_state.session_id,
        "student_name":  s["name"],
        "topic":         st.session_state.selected_topic,
        "conversation":  st.session_state.current_conv["id"],
        "conv_title":    st.session_state.current_conv["title"],
        "started_at":    st.session_state.session_start,
        "ended_at":      datetime.utcnow().isoformat(),
        "message_count": st.session_state.message_count,
    })
    for k in ["chat_history", "session_id", "message_count", "session_start",
              "current_conv", "selected_topic", "last_audio_key"]:
        st.session_state[k] = [] if k == "chat_history" else None
    st.session_state.screen = "home"
    st.rerun()


# ─────────────────────────────────────────────
# SCREEN: ALREADY DONE WARNING
# ─────────────────────────────────────────────
def screen_already_done():
    data = st.session_state.get("pending_already_done", {})
    conv = data.get("conv", {})
    date = data.get("date", "")
    st.markdown("## ✅ You've done this before")
    st.markdown(
        f"You already completed **{conv.get('title', 'this conversation')}** on **{date}**."
    )
    st.markdown("Would you like to do it again?")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("▶️ Do it again", use_container_width=True, type="primary"):
            st.session_state.pending_already_done = None
            launch_session(conv)
    with col2:
        if st.button("← Back", use_container_width=True):
            st.session_state.pending_already_done = None
            st.session_state.screen = "home"
            st.rerun()


# ─────────────────────────────────────────────
# SCREEN: TRANSCRIPT VIEWER
# ─────────────────────────────────────────────
def screen_transcript():
    sess = st.session_state.view_session
    if not sess:
        st.session_state.screen = "home"; st.rerun(); return

    if st.button("← Back to sessions"):
        st.session_state.view_session = None
        st.session_state.screen = "home"
        st.rerun()

    st.markdown(f"## 📋 {sess.get('conv_title', 'Session')}")
    date_str = sess.get("started_at", "")[:10]
    msgs_count = sess.get("message_count", 0)
    st.caption(f"{date_str} · {msgs_count} messages")
    st.divider()

    messages = get_session_messages(
        st.session_state.student["name"], sess["id"]
    )
    if not messages:
        st.info("No messages saved for this session.")
        return

    for msg in messages:
        role = msg.get("role", "user")
        text = msg.get("content", "")
        if role == "user":
            with st.chat_message("user"):
                st.markdown(f"🎤 *{text}*")
        else:
            with st.chat_message("assistant", avatar="🎙️"):
                sections = parse_response(text)
                if any([sections["said"], sections["question"],
                        sections["feedback"], sections["enhancement"]]):
                    render_response(sections)
                else:
                    st.markdown(text)


# ─────────────────────────────────────────────
# TEACHER: HOME — all students
# ─────────────────────────────────────────────
def screen_teacher_home():
    col1, col2 = st.columns([4,1])
    with col1:
        st.markdown("## 🏫 Teacher dashboard")
    with col2:
        if st.button("Sign out"):
            st.session_state.is_teacher = False
            st.session_state.screen = "login"
            st.rerun()

    tab_students, tab_curriculum, tab_settings = st.tabs(
        ["👥 Students", "📚 Curriculum editor", "⚙️ Settings"]
    )

    with tab_students:
        students = get_all_students()
        if not students:
            st.caption("No students have logged in yet.")
        else:
            st.markdown(f"**{len(students)} students registered**")
            st.divider()
            for stu in students:
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.markdown(f"**{stu['name']}**")
                    st.caption(f"Age {stu.get('age','')} · {stu.get('total_sessions',0)} sessions · {stu.get('total_messages',0)} messages")
                with col2:
                    if st.button("View sessions →", key=f"t_stu_{stu['name']}", use_container_width=True):
                        st.session_state.teacher_view_student = stu
                        st.session_state.screen = "teacher_student"
                        st.rerun()
                st.divider()

    with tab_curriculum:
        screen_teacher_curriculum()

    with tab_settings:
        screen_teacher_settings()


# ─────────────────────────────────────────────
# TEACHER: STUDENT SESSION LIST
# ─────────────────────────────────────────────
def screen_teacher_student():
    stu = st.session_state.teacher_view_student
    if not stu:
        st.session_state.screen = "teacher_home"; st.rerun(); return

    if st.button("← Back to students"):
        st.session_state.teacher_view_student = None
        st.session_state.screen = "teacher_home"
        st.rerun()

    st.markdown(f"## {stu['name']}")
    st.caption(f"Age {stu.get('age','')} · {stu.get('total_sessions',0)} sessions")
    st.divider()

    tab_sess, tab_assign, tab_report = st.tabs(["📋 Sessions", "📌 Assignment", "📊 Progress report"])

    # ── Sessions tab ──
    with tab_sess:
        sessions = get_past_sessions(stu["name"])
        if not sessions:
            st.info("This student has no sessions yet.")
        else:
            for sess in sessions:
                date_str  = sess.get("started_at","")[:10]
                msgs      = sess.get("message_count", 0)
                title     = sess.get("conv_title", sess.get("conversation","Session"))
                topic_id  = sess.get("topic","")
                icon      = get_curriculum_for_age(stu.get("age")).get(topic_id, {}).get("icon","📖")
                col1, col2, col3 = st.columns([4,1,1])
                with col1:
                    st.markdown(f"**{icon} {title}**")
                    st.caption(f"{date_str} · {msgs} messages")
                with col2:
                    if st.button("View →", key=f"t_sess_{sess['id']}", use_container_width=True):
                        st.session_state.teacher_view_session = {"sess": sess, "student": stu}
                        st.session_state.screen = "teacher_transcript"
                        st.rerun()
                with col3:
                    if st.button("🗑️", key=f"t_del_{sess['id']}", use_container_width=True,
                                 help="Delete this session"):
                        delete_student_session(stu["name"], sess["id"])
                        st.rerun()
                st.divider()

    # ── Assignment tab ──
    with tab_assign:
        st.markdown("### Assign conversations")
        st.caption("Choose whether this student can pick any conversation freely, or is restricted to specific ones you assign.")

        current = get_student_assignment(stu["name"]) or {"mode": "free", "conv_ids": []}
        current_mode = current.get("mode", "free")
        current_ids  = current.get("conv_ids", [])

        mode = st.radio(
            "Practice mode",
            ["free", "assigned"],
            index=0 if current_mode == "free" else 1,
            format_func=lambda x: "🆓 Free practice — student can choose any conversation" if x == "free"
                                  else "📌 Assigned — student only sees the conversations you choose",
            key="assign_mode_radio"
        )

        selected_ids = current_ids.copy()
        if mode == "assigned":
            st.markdown("**Select conversations to assign:**")
            # Build flat list of all conversations across all topics for this student's age group
            stu_curric = get_curriculum_for_age(stu.get("age"))
            for topic_key, topic_val in stu_curric.items():
                with st.expander(f"{topic_val['icon']} {topic_val['title']}"):
                    for conv in topic_val["conversations"]:
                        checked = conv["id"] in selected_ids
                        if st.checkbox(conv["title"], value=checked, key=f"asgn_{conv['id']}"):
                            if conv["id"] not in selected_ids:
                                selected_ids.append(conv["id"])
                        else:
                            if conv["id"] in selected_ids:
                                selected_ids.remove(conv["id"])

        if st.button("💾 Save assignment", use_container_width=True, type="primary"):
            set_student_assignment(stu["name"], mode, selected_ids if mode == "assigned" else [])
            st.success(f"Assignment saved — student is now in {'assigned' if mode == 'assigned' else 'free'} mode.")
            st.rerun()

    # ── Progress report tab ──
    with tab_report:
        st.markdown("### Progress report")
        existing = get_progress_report(stu["name"])
        has_new  = has_new_sessions_since_report(stu["name"], existing)

        col1, col2, col3 = st.columns(3)
        with col1:
            btn_first = "📊 Generate report" if not existing else None
            if btn_first and st.button(btn_first, use_container_width=True):
                with st.spinner("Analysing sessions…"):
                    try:
                        report = generate_progress_report(stu["name"])
                        if "error" not in report:
                            save_progress_report(stu["name"], report)
                            st.success("Report generated!")
                            st.rerun()
                        else:
                            st.error(report["error"])
                    except Exception as e:
                        st.error(f"Could not generate: {e}")
        with col2:
            if existing and has_new:
                if st.button("🆕 Update with new sessions", use_container_width=True):
                    with st.spinner("Adding new sessions…"):
                        try:
                            report = generate_progress_report(stu["name"], existing_report=existing)
                            if "error" not in report:
                                save_progress_report(stu["name"], report)
                                st.success("Report updated!")
                                st.rerun()
                            else:
                                st.error(report["error"])
                        except Exception as e:
                            st.error(f"Could not update: {e}")
            elif existing and not has_new:
                st.caption("✓ Up to date")
        with col3:
            if existing:
                if st.button("🔄 Regenerate from scratch", use_container_width=True):
                    with st.spinner("Regenerating full report…"):
                        try:
                            report = generate_progress_report(stu["name"], force_full=True)
                            if "error" not in report:
                                save_progress_report(stu["name"], report)
                                st.success("Report regenerated!")
                                st.rerun()
                            else:
                                st.error(report["error"])
                        except Exception as e:
                            st.error(f"Could not regenerate: {e}")

        if existing and existing.get("text"):
            st.divider()
            render_progress_report(existing, editable=True, student_name=stu["name"])
        elif not existing:
            st.info("No report yet — click Generate to create one.")


# ─────────────────────────────────────────────
# TEACHER: TRANSCRIPT VIEWER
# ─────────────────────────────────────────────
def screen_teacher_transcript():
    data = st.session_state.teacher_view_session
    if not data:
        st.session_state.screen = "teacher_home"; st.rerun(); return

    sess = data["sess"]
    stu  = data["student"]

    if st.button(f"← Back to {stu['name']}'s sessions"):
        st.session_state.teacher_view_session = None
        st.session_state.screen = "teacher_student"
        st.rerun()

    st.markdown(f"## 📋 {sess.get('conv_title','Session')}")
    st.caption(f"{stu['name']} · {sess.get('started_at','')[:10]} · {sess.get('message_count',0)} messages")
    st.divider()

    messages = get_session_messages(stu["name"], sess["id"])
    if not messages:
        st.info("No messages saved for this session.")
        return

    for msg in messages:
        role = msg.get("role","user")
        text = msg.get("content","")
        if role == "user":
            with st.chat_message("user"):
                st.markdown(f"🎤 *{text}*")
        else:
            with st.chat_message("assistant", avatar="🎙️"):
                sections = parse_response(text)
                if any([sections["said"], sections["question"],
                        sections["feedback"], sections["enhancement"]]):
                    render_response(sections)
                else:
                    st.markdown(text)


# ─────────────────────────────────────────────
# TEACHER: CURRICULUM EDITOR
# ─────────────────────────────────────────────
def get_extra_topics() -> dict:
    """Custom topics added by teacher, stored in Firestore."""
    if db is None: return {}
    try:
        docs = db.collection("custom_topics").stream()
        return {d.id: d.to_dict() for d in docs}
    except: return {}

def get_extra_convs(topic_key: str) -> list:
    """Extra conversations added by teacher for a topic."""
    if db is None: return []
    try:
        docs = db.collection("extra_conversations").where("topic_key", "==", topic_key).stream()
        return [d.to_dict() for d in docs]
    except: return []

def delete_conv_override(conv_id: str):
    if db is None: return
    try:
        db.collection("curriculum_overrides").document(conv_id).delete()
    except: pass

def delete_extra_conv(conv_id: str):
    if db is None: return
    try:
        db.collection("extra_conversations").document(conv_id).delete()
    except: pass

def delete_custom_topic(topic_id: str):
    if db is None: return
    try:
        db.collection("custom_topics").document(topic_id).delete()
        # also delete any extra convs for this topic
        docs = db.collection("extra_conversations").where("topic_key","==",topic_id).stream()
        for d in docs: d.reference.delete()
    except: pass

def screen_teacher_curriculum():
    st.markdown("### Edit curriculum")
    st.caption("Changes apply immediately for all students.")

    age_group = st.radio(
        "Age group",
        ["9-12", "13-17"],
        horizontal=True,
        key="teacher_curric_age_group"
    )
    base_curriculum = CURRICULUM_9_12 if age_group == "9-12" else CURRICULUM

    overrides    = get_curriculum_overrides()
    extra_topics = get_extra_topics()

    # Build combined topic list: hardcoded (for selected age group) + custom
    # Custom topics are tagged with an age_group field; only show matching ones
    all_topics = {**base_curriculum}
    for tid, td in extra_topics.items():
        if td.get("age_group", "13-17") == age_group:
            all_topics[tid] = td

    topic_options = {f'{v.get("icon","📘")} {v["title"]}': k for k, v in all_topics.items()}
    chosen_label  = st.selectbox("Topic", list(topic_options.keys()),
                                 key="teacher_topic_sel", label_visibility="collapsed")
    chosen_key    = topic_options[chosen_label]
    topic         = all_topics[chosen_key]
    is_custom_topic = chosen_key in extra_topics

    # ── Delete / info for topic ──
    tcol1, tcol2 = st.columns([4,1])
    with tcol1:
        if is_custom_topic:
            st.caption("⚡ Custom topic")
    with tcol2:
        if is_custom_topic:
            if st.button("🗑️ Delete topic", key="del_topic", use_container_width=True):
                delete_custom_topic(chosen_key)
                st.success("Topic deleted.")
                st.rerun()

    st.divider()

    # ── Existing conversations ──
    convs       = topic.get("conversations", [])
    extra_convs = get_extra_convs(chosen_key)
    all_convs   = convs + extra_convs

    for conv in all_convs:
        merged    = {**conv, **overrides.get(conv["id"], {})}
        is_edited = conv["id"] in overrides
        is_extra  = conv in extra_convs
        badge     = "✏️ " if is_edited else ("➕ " if is_extra else "")
        label     = f"{badge}{merged['title']}"

        with st.expander(label, expanded=False):
            with st.form(key=f"edit_form_{conv['id']}"):
                new_title    = st.text_input("Title",           value=merged["title"])
                new_goal     = st.text_area("Goal",             value=merged.get("goal",""),     height=80)
                new_starter  = st.text_area("Starter question", value=merged.get("starter",""),  height=80)
                new_vocab    = st.text_area("Vocabulary",       value=merged.get("vocabulary",""),height=60)
                new_struct   = st.text_area("Target structures",value=merged.get("structures",""),height=80)
                new_followups= st.text_area(
                    "Follow-up questions (one per line)",
                    value="\n".join(merged.get("followups", [])),
                    height=160
                )
                c1, c2, c3 = st.columns(3)
                with c1:
                    saved = st.form_submit_button("💾 Save", use_container_width=True)
                with c2:
                    reset = st.form_submit_button("↩️ Reset", use_container_width=True)
                with c3:
                    delete = st.form_submit_button("🗑️ Delete", use_container_width=True)

                if saved:
                    followups_list = [q.strip() for q in new_followups.split("\n") if q.strip()]
                    save_curriculum_override(conv["id"], {
                        "title": new_title, "goal": new_goal,
                        "starter": new_starter, "vocabulary": new_vocab,
                        "structures": new_struct, "followups": followups_list,
                    })
                    st.success("Saved!")
                    st.rerun()

                if reset:
                    delete_conv_override(conv["id"])
                    st.success("Reset to original.")
                    st.rerun()

                if delete:
                    if is_extra:
                        delete_extra_conv(conv["id"])
                        st.success("Conversation deleted.")
                    else:
                        # Hide built-in conv by marking it hidden in overrides
                        save_curriculum_override(conv["id"], {**merged, "hidden": True})
                        st.success("Conversation hidden from students.")
                    st.rerun()

    # ── Add new conversation ──
    st.divider()
    with st.expander("➕ Add a new conversation to this topic"):
        with st.form("add_conv_form"):
            nc_title    = st.text_input("Title")
            nc_goal     = st.text_area("Goal", height=70)
            nc_starter  = st.text_area("Starter question", height=70)
            nc_vocab    = st.text_input("Vocabulary (comma-separated)")
            nc_struct   = st.text_area("Target structures", height=70)
            nc_followups= st.text_area("Follow-up questions (one per line)", height=120)
            if st.form_submit_button("Add conversation", use_container_width=True):
                if not nc_title.strip():
                    st.error("Title is required.")
                else:
                    new_id = f"custom_{uuid.uuid4().hex[:8]}"
                    db.collection("extra_conversations").document(new_id).set({
                        "id": new_id, "topic_key": chosen_key,
                        "title": nc_title, "goal": nc_goal,
                        "starter": nc_starter, "vocabulary": nc_vocab,
                        "structures": nc_struct,
                        "followups": [q.strip() for q in nc_followups.split("\n") if q.strip()],
                        "age_group": age_group,
                    })
                    st.success("Conversation added!")
                    st.rerun()

    # ── Add new topic ──
    st.divider()
    with st.expander("➕ Add a completely new topic"):
        with st.form("add_topic_form"):
            nt_icon  = st.text_input("Icon (emoji)", value="📘")
            nt_title = st.text_input("Topic title")
            if st.form_submit_button("Create topic", use_container_width=True):
                if not nt_title.strip():
                    st.error("Title is required.")
                else:
                    new_tid = f"custom_topic_{uuid.uuid4().hex[:8]}"
                    db.collection("custom_topics").document(new_tid).set({
                        "title": nt_title, "icon": nt_icon,
                        "conversations": [],
                        "age_group": age_group,
                    })
                    st.success(f"Topic '{nt_title}' created! Now add conversations to it above.")
                    st.rerun()


# ─────────────────────────────────────────────
# TEACHER: SETTINGS
# ─────────────────────────────────────────────
def screen_teacher_settings():
    st.markdown("### Change teacher password")
    with st.form("change_pw"):
        current = st.text_input("Current password", type="password")
        new_pw  = st.text_input("New password",     type="password")
        confirm = st.text_input("Confirm new password", type="password")
        if st.form_submit_button("Update password", use_container_width=True):
            correct = get_teacher_password()
            if current != correct:
                st.error("Current password is wrong.")
            elif not new_pw:
                st.error("New password cannot be empty.")
            elif new_pw != confirm:
                st.error("Passwords do not match.")
            else:
                set_teacher_password(new_pw)
                st.success("Password updated.")


# ─────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────
if st.session_state.screen == "login":
    screen_login()
elif st.session_state.screen == "home":
    screen_home()
elif st.session_state.screen == "chat":
    screen_chat()
elif st.session_state.screen == "already_done":
    screen_already_done()
elif st.session_state.screen == "transcript":
    screen_transcript()
elif st.session_state.screen == "teacher_home":
    screen_teacher_home()
elif st.session_state.screen == "teacher_student":
    screen_teacher_student()
elif st.session_state.screen == "teacher_transcript":
    screen_teacher_transcript()
