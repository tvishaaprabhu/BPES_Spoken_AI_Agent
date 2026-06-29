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

GLOBAL_RULES = """
GLOBAL RULES — apply to every single response without exception:
- Keep vocabulary appropriate for the student's age — do not use overly complex words
- Ask only ONE follow-up question per response — never two at once
- Accept incomplete sentences — model the correct version warmly, never harshly
- Correct only the MOST IMPORTANT single error per response, not every mistake at once
- If the student gives a one-word answer, gently prompt for a full sentence using a simple example
- Keep responses concise — the student needs to speak more than you do
- ALWAYS stay on the module topic — never drift into unrelated subjects
- Use examples from Indian daily life — school, cricket, festivals, local markets, family
- Your tone must always be warm, patient, and encouraging
- Never make the student feel embarrassed or judged for errors
"""

def build_system_prompt(age: int, conv: dict) -> str:
    level = LEVELS.get(age, LEVELS[17])
    if age <= 14:
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
# OPENAI HELPERS
# ─────────────────────────────────────────────
def get_openai_client():
    return openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

def get_ai_response(user_text: str) -> str:
    client = get_openai_client()
    conv = st.session_state.current_conv
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
    if not any([s["said"], s["question"], s["feedback"], s["enhancement"]]):
        st.markdown(s["raw"]); return
    html = '<div class="fb-card">'
    if s["said"]:
        html += f'<div class="fb-sec"><div class="fb-lbl lbl-said">🗣 What you said</div><div>{s["said"]}</div></div>'
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
    "editing_index": None,   # index of user message being edited
    "view_session": None,    # session dict being viewed in history
}.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────
# SCREEN: LOGIN
# ─────────────────────────────────────────────
def screen_login():
    st.markdown("## 🎙️ SpeakUp")
    st.markdown("##### AI English conversation practice · Ages 13–17")
    st.info("🔊 Make sure your speaker volume is turned up — the AI will speak its questions aloud.")
    st.divider()
    with st.form("login"):
        name = st.text_input("Full name", placeholder="e.g. Aanya Sharma")
        age  = st.selectbox("Age", [""] + list(range(13, 18)),
                            format_func=lambda x: "Select age…" if x == "" else str(x))
        if st.form_submit_button("Start learning →", use_container_width=True):
            if not name.strip(): st.error("Please enter your full name.")
            elif age == "": st.error("Please select your age.")
            else:
                st.session_state.student = get_or_create_student(name.strip(), int(age))
                st.session_state.screen = "home"
                st.rerun()
    st.caption("Already used SpeakUp before? Enter your name and age — your progress loads automatically.")


# ─────────────────────────────────────────────
# SCREEN: HOME — topic + conversation picker
# ─────────────────────────────────────────────
def screen_home():
    s = st.session_state.student
    st.markdown(
        f'<div class="welcome-banner"><h2>Hello, {s["name"]} 👋</h2>'
        f'<p>Age {s["age"]}</p></div>',
        unsafe_allow_html=True
    )

    # Tab: Practice vs History
    tab_practice, tab_history = st.tabs(["📚 Practice", "📋 Past sessions"])

    with tab_practice:
        st.markdown("#### Choose a topic")
        topic_options = {f'{v["icon"]} {v["title"]}': k for k, v in CURRICULUM.items()}
        chosen_label = st.selectbox("Topic", list(topic_options.keys()), label_visibility="collapsed")
        chosen_key   = topic_options[chosen_label]
        topic        = CURRICULUM[chosen_key]
        st.session_state.selected_topic = chosen_key

        # Load completed conversations for this student
        completed = get_completed_conv_ids(s["name"])

        st.markdown("#### Choose a conversation")
        convs = topic["conversations"]
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
                        st.session_state.pending_already_done = {
                            "conv": conv,
                            "date": completed[conv["id"]]
                        }
                        st.session_state.screen = "already_done"
                        st.rerun()
                    else:
                        launch_session(conv)
            if i < len(convs) - 1:
                st.divider()

    with tab_history:
        screen_history_tab(s)


def screen_history_tab(s):
    sessions = get_past_sessions(s["name"])
    if not sessions:
        st.caption("No sessions yet — complete your first conversation to see it here.")
        return
    st.markdown(f"**{len(sessions)} sessions completed**")
    for sess in sessions:
        date_str = sess.get("started_at", "")[:10]
        msgs     = sess.get("message_count", 0)
        title    = sess.get("conv_title", sess.get("conversation", "Session"))
        topic_id = sess.get("topic", "")
        topic_icon = CURRICULUM.get(topic_id, {}).get("icon", "📖")
        col1, col2 = st.columns([4, 1])
        with col1:
            st.markdown(f"**{topic_icon} {title}**")
            st.caption(f"{date_str} · {msgs} messages")
        with col2:
            if st.button("View →", key=f"view_{sess['id']}", use_container_width=True):
                st.session_state.view_session = sess
                st.session_state.screen = "transcript"
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
        topic = CURRICULUM[st.session_state.selected_topic]
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
