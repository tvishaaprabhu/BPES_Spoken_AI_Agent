import streamlit as st
import openai
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import uuid
import json
import re

st.write(list(st.secrets.keys()))

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="SpeakUp",
    page_icon="🎙️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ─────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* Hide default Streamlit chrome */
#MainMenu, footer, header {visibility: hidden;}
.block-container {padding-top: 2rem; padding-bottom: 2rem; max-width: 720px;}

/* Feedback card styling */
.fb-card {
    background: #f8f8f6;
    border: 1px solid #e0ddd6;
    border-radius: 10px;
    padding: 12px 16px;
    margin-top: 6px;
    font-size: 14px;
    line-height: 1.6;
}
.fb-section { margin-bottom: 10px; }
.fb-section:last-child { margin-bottom: 0; }
.fb-label { font-weight: 600; font-size: 12px; text-transform: uppercase;
            letter-spacing: 0.06em; margin-bottom: 4px; }
.label-said  { color: #555; }
.label-q     { color: #1D9E75; }
.label-fb    { color: #E24B4A; }
.label-enh   { color: #534AB7; }

/* Module card grid */
.module-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 1rem; }
.module-card {
    background: white; border: 1.5px solid #e0ddd6; border-radius: 10px;
    padding: 14px; cursor: pointer; transition: border-color 0.15s;
}
.module-card:hover { border-color: #1D9E75; }
.module-card.selected { border-color: #1D9E75; background: #E1F5EE; }
.module-title { font-weight: 500; font-size: 14px; margin-bottom: 2px; }
.module-desc  { font-size: 12px; color: #888; }

/* Welcome banner */
.welcome-banner {
    background: #E1F5EE; border: 1px solid #1D9E75;
    border-radius: 10px; padding: 14px 18px; margin-bottom: 1.5rem;
}
.welcome-banner h3 { color: #0F6E56; margin: 0 0 2px 0; font-size: 17px; }
.welcome-banner p  { color: #0F6E56; margin: 0; font-size: 13px; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
# FIREBASE INIT
# ─────────────────────────────────────────────
# ⚠️ Add your Firebase service account JSON to Streamlit secrets.
# In your .streamlit/secrets.toml add a [firebase] section with your key fields.
# See README for full instructions.

@st.cache_resource
def init_firebase():
    if firebase_admin._apps:
        return firestore.client()
    try:
        fb = dict(st.secrets["firebase"])
        # private_key newlines are escaped in toml — fix them
        fb["private_key"] = fb["private_key"].replace("\\n", "\n")
        cred = credentials.Certificate(fb)
        firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"Firebase connection failed: {e}")
        return None

db = init_firebase()


# ─────────────────────────────────────────────
# OPENAI CLIENT
# ─────────────────────────────────────────────
# Add OPENAI_API_KEY to .streamlit/secrets.toml
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


# ─────────────────────────────────────────────
# CURRICULUM DATA
# ─────────────────────────────────────────────
LEVELS = {
    7: "Level 1 – Foundations",
    8: "Level 2 – Basic Sentences",
    9: "Level 3 – Real-Life Contexts",
    10: "Level 4 – Practical Communication",
    11: "Level 5 – Stories & Description",
    12: "Level 6 – Grammar through Speaking",
    13: "Level 7 – Functional English",
    14: "Level 8 – Confidence & Public Speaking",
    15: "Level 9 – Real-World English",
    16: "Level 10 – Advanced Speaking",
    17: "Level 10 – Advanced Speaking",
}

MODULES = {
    7: [
        {"id": "greetings",  "icon": "👋", "title": "Greetings & introductions", "desc": "Hello, bye, your name and age"},
        {"id": "classroom",  "icon": "🏫", "title": "Classroom English",         "desc": "Sit, stand, open, close, listen"},
        {"id": "numbers",    "icon": "🔢", "title": "Numbers, colours & shapes", "desc": "Count to 50, basic shapes"},
        {"id": "family",     "icon": "👨‍👩‍👧", "title": "Family & home",           "desc": "Mother, father, rooms"},
        {"id": "feelings",   "icon": "😊", "title": "Feelings",                  "desc": "Happy, sad, scared, excited"},
    ],
    8: [
        {"id": "intro-others",   "icon": "🤝", "title": "Introducing others",    "desc": "Meet my friend, she is…"},
        {"id": "daily-routine",  "icon": "⏰", "title": "Daily routines",        "desc": "Wake up, brush, eat, play"},
        {"id": "weather",        "icon": "🌤", "title": "Weather & seasons",     "desc": "Sunny, rainy, hot, cold"},
        {"id": "food",           "icon": "🍎", "title": "Food vocabulary",       "desc": "Fruits, vegetables, favourites"},
        {"id": "questions",      "icon": "❓", "title": "Simple questions",      "desc": "What is this? Where is…?"},
    ],
    9: [
        {"id": "my-school", "icon": "📚", "title": "My school & class",      "desc": "Subjects, teachers, friends"},
        {"id": "places",    "icon": "🏘", "title": "Places in neighbourhood", "desc": "Market, park, hospital"},
        {"id": "objects",   "icon": "🎒", "title": "Describing objects",      "desc": "Size, colour, shape"},
        {"id": "likes",     "icon": "❤️", "title": "Likes & dislikes",       "desc": "I love…, I don't like…"},
        {"id": "friends",   "icon": "👫", "title": "My best friend",          "desc": "Describe a friend"},
    ],
    10: [
        {"id": "shopping", "icon": "🛍️", "title": "Shopping conversations", "desc": "Prices, items, bargaining"},
        {"id": "travel",   "icon": "🚌", "title": "Travel basics",           "desc": "Bus, train, directions"},
        {"id": "health",   "icon": "🏥", "title": "Health & body",           "desc": "Doctor visit vocabulary"},
        {"id": "polite",   "icon": "🙏", "title": "Polite language",         "desc": "Could you…? May I…?"},
        {"id": "verbs",    "icon": "🏃", "title": "Action verbs",            "desc": "Run, walk, eat, jump"},
    ],
    11: [
        {"id": "storytelling",    "icon": "📖", "title": "Storytelling basics",      "desc": "Beginning, middle, end"},
        {"id": "festivals",       "icon": "🎉", "title": "Festivals & celebrations", "desc": "Describe a festival"},
        {"id": "describe-people", "icon": "👗", "title": "Describing people",        "desc": "Height, hair, clothing"},
        {"id": "short-speech",    "icon": "🎤", "title": "Short speeches",           "desc": "A day I remember"},
        {"id": "asking-help",     "icon": "🙋", "title": "Asking for help",          "desc": "Excuse me, can you…?"},
    ],
    12: [
        {"id": "tenses",          "icon": "⏳", "title": "Present, past & future", "desc": "Spoken tense practice"},
        {"id": "comparisons",     "icon": "⚖️", "title": "Comparisons",            "desc": "Bigger, faster, better than"},
        {"id": "opinions",        "icon": "💭", "title": "Expressing opinions",     "desc": "I think… because…"},
        {"id": "hobbies",         "icon": "🎨", "title": "Hobbies & talents",      "desc": "What I love to do"},
        {"id": "feelings-reasons","icon": "💛", "title": "Feelings + reasons",      "desc": "I feel… because…"},
    ],
    13: [
        {"id": "first-impressions", "icon": "✨", "title": "First impressions",     "desc": "Personal choices, describing people"},
        {"id": "objects-identity",  "icon": "🎒", "title": "Objects & identity",    "desc": "Connect objects to experiences"},
        {"id": "personal-identity", "icon": "🪞", "title": "Personal identity",     "desc": "How you define yourself"},
        {"id": "preferences",       "icon": "☕", "title": "Personal preferences",  "desc": "Decisions, choices, likes"},
        {"id": "learning-styles",   "icon": "🧠", "title": "Learning styles",       "desc": "How you learn best"},
    ],
    14: [
        {"id": "friendships",   "icon": "👥", "title": "Friendships",         "desc": "Different perspectives on friendship"},
        {"id": "food-prefs",    "icon": "🍽️", "title": "Food preferences",   "desc": "Dishes, health, and food habits"},
        {"id": "clarifications","icon": "💬", "title": "Clarifications",      "desc": "Communication issues and solutions"},
        {"id": "the-past",      "icon": "⏪", "title": "The past",            "desc": "Stories, memories, past tense"},
        {"id": "debate",        "icon": "🗣️", "title": "Debate basics",      "desc": "For & against, agreeing/disagreeing"},
    ],
    15: [
        {"id": "the-future",    "icon": "🔭", "title": "The future",          "desc": "Predictions, plans, space"},
        {"id": "life-stages",   "icon": "🌱", "title": "Life stages",         "desc": "Ageing, culture, growing up"},
        {"id": "opinions-adv",  "icon": "💡", "title": "Expressing opinions", "desc": "Debate topics, opinion language"},
        {"id": "teen-stress",   "icon": "😓", "title": "Teenage stress",      "desc": "Stress issues and solutions"},
        {"id": "giving-advice", "icon": "🤝", "title": "Giving advice",       "desc": "Asking for and giving advice"},
    ],
    16: [
        {"id": "advanced-conv",    "icon": "🌐", "title": "Advanced conversation", "desc": "Complex topics, debates"},
        {"id": "presentations",    "icon": "📊", "title": "Presentations",         "desc": "Structure & delivery"},
        {"id": "formal-interview", "icon": "🎓", "title": "Formal interviews",     "desc": "Scholarships, university"},
        {"id": "persuasive",       "icon": "🏆", "title": "Persuasive speaking",   "desc": "Argue, convince, pitch"},
        {"id": "digital-english",  "icon": "💻", "title": "English for digital life","desc": "Emails, messages, online"},
    ],
}
MODULES[17] = MODULES[16]


# ─────────────────────────────────────────────
# SYSTEM PROMPT
# ─────────────────────────────────────────────
GLOBAL_AVOID = """
GLOBAL RULES — apply to every single response:
- Never use complex or advanced vocabulary unless the student is age 15+
- Never ask two questions at once — one follow-up question only
- Accept incomplete sentences — model the correct version warmly, never harshly
- Correct only the most important error per response, not every mistake
- If the student gives a one-word answer, gently prompt for a full sentence
- Keep your responses short and encouraging — never overwhelming
- Always stay on the module topic — do not drift into unrelated subjects
- Use examples from Indian daily life — school, family, cricket, festivals, local market
- Your tone must always be warm, patient, and motivational
"""

def build_system_prompt(age: int, module_id: str, module_title: str, module_desc: str) -> str:
    level = LEVELS.get(age, LEVELS[16])

    if age <= 9:
        level_guidance = "Use very simple words and very short sentences. Speak like a kind teacher talking to a young child."
    elif age <= 11:
        level_guidance = "Use simple everyday vocabulary and short sentences. Be warm and encouraging."
    elif age <= 13:
        level_guidance = "Use clear everyday vocabulary. Occasionally introduce slightly more advanced words. Be friendly."
    elif age <= 15:
        level_guidance = "Use natural conversational language. Occasionally use idioms. Be engaging and slightly more challenging."
    else:
        level_guidance = "Use rich, natural language. Challenge the student with complex sentences, idioms, and varied vocabulary."

    return f"""You are a warm, supportive English conversation tutor for a {age}-year-old Indian student ({level}).

TODAY'S MODULE: {module_title} — {module_desc}
You must keep the entire conversation focused on this module topic only.

LANGUAGE LEVEL: {level_guidance}

{GLOBAL_AVOID}

RESPONSE FORMAT — you must always respond in exactly these 4 sections with these exact emoji labels:

🗣 What you said:
[Repeat the student's sentence exactly as they said it, including any errors. Nothing else in this section.]

❓ Next question:
[Ask one natural follow-up question relevant to the module. Assume what the student said is correct. Keep it simple and easy to answer.]

✅ Feedback:
[Correct the most important grammar or sentence structure error. Explain it simply and kindly. If there are no errors, say "Great job — no corrections needed!" ]

✨ Enhancements:
[Suggest one better word or phrase the student could use. Phrase it as: "Instead of \\"...\\" you could say \\"...\\"". Do not rewrite their sentence. If nothing to enhance, say "Your vocabulary was spot on!"]

Never add extra sections. Never break this structure."""


# ─────────────────────────────────────────────
# FIREBASE HELPERS
# ─────────────────────────────────────────────
def get_or_create_student(name: str, age: int) -> dict:
    if db is None:
        return {"name": name, "age": age, "level": LEVELS.get(age, LEVELS[16])}
    doc_ref = db.collection("students").document(name.lower().replace(" ", "_"))
    doc = doc_ref.get()
    if doc.exists:
        data = doc.to_dict()
        # update age in case it changed
        doc_ref.update({"age": age, "level": LEVELS.get(age, LEVELS[16])})
        return data
    else:
        student = {
            "name": name,
            "age": age,
            "level": LEVELS.get(age, LEVELS[16]),
            "created_at": datetime.utcnow().isoformat(),
            "total_sessions": 0,
            "total_messages": 0,
        }
        doc_ref.set(student)
        return student


def save_session_to_firebase(student_name: str, session: dict):
    if db is None:
        return
    try:
        student_id = student_name.lower().replace(" ", "_")
        session_ref = (
            db.collection("students")
            .document(student_id)
            .collection("sessions")
            .document(session["id"])
        )
        session_ref.set(session)
        # update student totals
        db.collection("students").document(student_id).update({
            "total_sessions": firestore.INCREMENT(1),
            "total_messages": firestore.INCREMENT(session.get("message_count", 0)),
        })
    except Exception as e:
        st.warning(f"Could not save session: {e}")


def save_message_to_firebase(student_name: str, session_id: str, message: dict):
    if db is None:
        return
    try:
        student_id = student_name.lower().replace(" ", "_")
        db.collection("students").document(student_id)\
          .collection("sessions").document(session_id)\
          .collection("messages").add(message)
    except Exception as e:
        pass  # non-critical, don't surface


# ─────────────────────────────────────────────
# PARSE 4-SECTION RESPONSE
# ─────────────────────────────────────────────
def parse_response(text: str) -> dict:
    """Split AI response into its 4 labelled sections."""
    sections = {
        "said":        "",
        "question":    "",
        "feedback":    "",
        "enhancement": "",
        "raw":         text,
    }
    patterns = {
        "said":        r"🗣\s*What you said:(.*?)(?=❓|✅|✨|$)",
        "question":    r"❓\s*Next question:(.*?)(?=🗣|✅|✨|$)",
        "feedback":    r"✅\s*Feedback:(.*?)(?=🗣|❓|✨|$)",
        "enhancement": r"✨\s*Enhancements:(.*?)(?=🗣|❓|✅|$)",
    }
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            sections[key] = match.group(1).strip()
    return sections


def render_ai_response(sections: dict):
    """Render the 4-section response as a clean feedback card."""
    if not any([sections["said"], sections["question"],
                sections["feedback"], sections["enhancement"]]):
        st.markdown(sections["raw"])
        return

    html = '<div class="fb-card">'

    if sections["said"]:
        html += f'''<div class="fb-section">
            <div class="fb-label label-said">🗣 What you said</div>
            <div>{sections["said"]}</div>
        </div>'''

    if sections["question"]:
        html += f'''<div class="fb-section">
            <div class="fb-label label-q">❓ Next question</div>
            <div><strong>{sections["question"]}</strong></div>
        </div>'''

    if sections["feedback"]:
        html += f'''<div class="fb-section">
            <div class="fb-label label-fb">✅ Feedback</div>
            <div>{sections["feedback"]}</div>
        </div>'''

    if sections["enhancement"]:
        html += f'''<div class="fb-section">
            <div class="fb-label label-enh">✨ Enhancements</div>
            <div>{sections["enhancement"]}</div>
        </div>'''

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
def init_state():
    defaults = {
        "screen":          "login",   # login | home | chat
        "student":         None,
        "selected_module": None,
        "chat_history":    [],        # list of {role, content, sections}
        "session_id":      None,
        "message_count":   0,
        "session_start":   None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ─────────────────────────────────────────────
# SCREEN: LOGIN
# ─────────────────────────────────────────────
def screen_login():
    st.markdown("## 🎙️ SpeakUp")
    st.markdown("##### Practice English conversation with an AI tutor")
    st.divider()

    with st.form("login_form"):
        name = st.text_input("Full name", placeholder="e.g. Aanya Sharma")
        age  = st.selectbox("Age", options=[""] + list(range(7, 18)),
                            format_func=lambda x: "Select age…" if x == "" else str(x))
        submitted = st.form_submit_button("Start learning →", use_container_width=True)

        if submitted:
            if not name.strip():
                st.error("Please enter your full name.")
            elif age == "":
                st.error("Please select your age.")
            else:
                student = get_or_create_student(name.strip(), int(age))
                st.session_state.student = student
                st.session_state.screen  = "home"
                st.rerun()

    st.caption("Already used SpeakUp? Enter your name and age to continue — your progress will load automatically.")


# ─────────────────────────────────────────────
# SCREEN: HOME / MODULE PICKER
# ─────────────────────────────────────────────
def screen_home():
    student = st.session_state.student
    age     = student["age"]
    level   = student.get("level", LEVELS.get(age, LEVELS[16]))

    st.markdown(
        f'<div class="welcome-banner"><h3>Hello, {student["name"]} 👋</h3>'
        f'<p>{level} · Age {age}</p></div>',
        unsafe_allow_html=True
    )

    st.markdown("#### Choose a module to practise")
    modules = MODULES.get(age, MODULES[16])

    # Show modules as radio buttons styled cleanly
    module_options = {f'{m["icon"]} {m["title"]}': m for m in modules}
    choice = st.radio(
        "Module",
        options=list(module_options.keys()),
        label_visibility="collapsed"
    )
    selected_mod = module_options[choice]
    st.caption(selected_mod["desc"])
    st.session_state.selected_module = selected_mod

    st.divider()
    if st.button("Start session →", use_container_width=True, type="primary"):
        # initialise new session
        st.session_state.session_id    = str(uuid.uuid4())
        st.session_state.chat_history  = []
        st.session_state.message_count = 0
        st.session_state.session_start = datetime.utcnow().isoformat()
        st.session_state.screen        = "chat"
        st.rerun()


# ─────────────────────────────────────────────
# SEND TO GPT
# ─────────────────────────────────────────────
def get_ai_response(user_text: str) -> str:
    student = st.session_state.student
    mod     = st.session_state.selected_module
    system  = build_system_prompt(
        age          = student["age"],
        module_id    = mod["id"],
        module_title = mod["title"],
        module_desc  = mod["desc"],
    )

    # Build message list — only role/content for the API
    messages = [{"role": "system", "content": system}]
    for msg in st.session_state.chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": user_text})

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.7,
    )
    return response.choices[0].message.content


# ─────────────────────────────────────────────
# TRANSCRIBE AUDIO
# ─────────────────────────────────────────────
def transcribe_audio(audio_bytes: bytes) -> str:
    with open("temp_audio.wav", "wb") as f:
        f.write(audio_bytes)
    with open("temp_audio.wav", "rb") as f:
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=f,
        )
    return transcript.text


# ─────────────────────────────────────────────
# SCREEN: CHAT
# ─────────────────────────────────────────────
def screen_chat():
    student = st.session_state.student
    mod     = st.session_state.selected_module

    # Header row
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**{mod['icon']} {mod['title']}** · {student['name']}")
    with col2:
        if st.button("End session", use_container_width=True):
            end_session()

    st.divider()

    # ── Opener — sent once at session start ──────────────────────────────
    if not st.session_state.chat_history:
        with st.spinner("Starting conversation…"):
            opener_prompt = (
                f"Start the conversation now. Greet the student warmly and ask your "
                f"first question about today's topic: {mod['title']}. "
                f"Use the 4-section format."
            )
            opener = get_ai_response(opener_prompt)
            sections = parse_response(opener)
            st.session_state.chat_history.append({
                "role":     "assistant",
                "content":  opener,
                "sections": sections,
            })
            save_message_to_firebase(student["name"], st.session_state.session_id, {
                "role": "assistant", "content": opener,
                "timestamp": datetime.utcnow().isoformat(),
            })

    # ── Render chat history ───────────────────────────────────────────────
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            with st.chat_message("user"):
                st.markdown(msg["content"])
        else:
            with st.chat_message("assistant", avatar="🎙️"):
                render_ai_response(msg.get("sections", {"raw": msg["content"],
                                   "said":"","question":"","feedback":"","enhancement":""}))

    st.divider()

    # ── Input area ───────────────────────────────────────────────────────
    st.markdown("**Your turn — type or record:**")

    # Audio recorder
    try:
        from audio_recorder_streamlit import audio_recorder
        audio_bytes = audio_recorder(
            text="",
            recording_color="#E24B4A",
            neutral_color="#1D9E75",
            icon_name="microphone",
            icon_size="2x",
            pause_threshold=2.5,
            key="mic"
        )
        if audio_bytes and len(audio_bytes) > 1000:
            # Only process if it's new audio (not the same as last turn)
            audio_key = hash(audio_bytes)
            if audio_key != st.session_state.get("last_audio_key"):
                st.session_state.last_audio_key = audio_key
                with st.spinner("Transcribing…"):
                    user_text = transcribe_audio(audio_bytes)
                if user_text.strip():
                    st.info(f"🎤 You said: *{user_text}*")
                    process_user_message(user_text)
    except ImportError:
        st.caption("🎤 Mic not available — install `audio-recorder-streamlit`")

    # Text input
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_input(
            "Type your message",
            placeholder="Type here and press Enter…",
            label_visibility="collapsed"
        )
        send = st.form_submit_button("Send →", use_container_width=True)
        if send and user_input.strip():
            process_user_message(user_input.strip())


def process_user_message(user_text: str):
    student = st.session_state.student

    # Add user message to history
    st.session_state.chat_history.append({
        "role": "user", "content": user_text, "sections": None
    })
    st.session_state.message_count += 1

    save_message_to_firebase(student["name"], st.session_state.session_id, {
        "role": "user", "content": user_text,
        "timestamp": datetime.utcnow().isoformat(),
    })

    # Get AI response
    with st.spinner("Thinking…"):
        ai_text  = get_ai_response(user_text)
        sections = parse_response(ai_text)

    st.session_state.chat_history.append({
        "role": "assistant", "content": ai_text, "sections": sections
    })

    save_message_to_firebase(student["name"], st.session_state.session_id, {
        "role": "assistant", "content": ai_text,
        "timestamp": datetime.utcnow().isoformat(),
    })

    st.rerun()


def end_session():
    student = st.session_state.student
    session = {
        "id":            st.session_state.session_id,
        "student_name":  student["name"],
        "module_id":     st.session_state.selected_module["id"],
        "module_title":  st.session_state.selected_module["title"],
        "started_at":    st.session_state.session_start,
        "ended_at":      datetime.utcnow().isoformat(),
        "message_count": st.session_state.message_count,
    }
    save_session_to_firebase(student["name"], session)
    # Reset chat state
    st.session_state.screen        = "home"
    st.session_state.chat_history  = []
    st.session_state.session_id    = None
    st.session_state.message_count = 0
    st.session_state.selected_module = None
    st.rerun()


# ─────────────────────────────────────────────
# ROUTER
# ─────────────────────────────────────────────
screen = st.session_state.screen

if screen == "login":
    screen_login()
elif screen == "home":
    screen_home()
elif screen == "chat":
    screen_chat()
