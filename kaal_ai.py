import streamlit as st
from authlib.integrations.requests_client import OAuth2Session
import google.generativeai as genai
import json
import os
import uuid
from datetime import datetime
import time

# --- 1) Google Login Integration ---

# Google OAuth details
CLIENT_ID = st.secrets["872182720005-9ube1btau24gpun9e85604alrtrho4ac.apps.googleusercontent.com"]
CLIENT_SECRET = st.secrets["GOOGLE_CLIENT_SECRET"]
REDIRECT_URI = "https://kaal-ai-qsqsqtwzpa4enxmzcde74g.streamlit.app/"  # Update with your Streamlit app URL
AUTHORIZATION_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
USERINFO_ENDPOINT = "https://openidconnect.googleapis.com/v1/userinfo"
SCOPES = "openid email profile"

# Create OAuth session
@st.cache_resource
def get_oauth():
    return OAuth2Session(
        CLIENT_ID,
        CLIENT_SECRET,
        scope=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
oauth = get_oauth()

# Check for callback code
params = st.query_params

if "token" not in st.session_state:
    if "code" in params:
        # User has been redirected back from Google
        code = params["code"]
        token = oauth.fetch_token(
            TOKEN_ENDPOINT,
            code=code,
            grant_type="authorization_code",
            include_client_id=True
        )
        st.session_state.token = token
        st.query_params.clear()  # clear code from URL
        st.experimental_rerun()
    else:
        # Show “Login with Google” link
        auth_url, _ = oauth.create_authorization_url(AUTHORIZATION_ENDPOINT)
        st.markdown(f"[👉 Login with Google]({auth_url})")
        st.stop()

# Fetch user info
token = st.session_state.token
resp = oauth.get(USERINFO_ENDPOINT, token=token)
user_info = resp.json()
st.session_state.username = user_info.get("email")

# --- 2) Setup for Chat and UI ---

# Page Config
st.set_page_config(page_title="Kaal AI - Desi GPT", page_icon="🧠", layout="wide")

# Inject futuristic background + custom font
st.markdown("""
    <style>
    .stApp {
        background-color: white;
    }

    video {
        position: fixed;
        right: 0;
        bottom: 0;
        min-width: 100vw;
        min-height: 100vh;
        z-index: -1;
        object-fit: cover;
        opacity: 0.2;
    }

    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Orbitron', sans-serif;
        color: #00ffe1;
        text-shadow: 0 0 8px #00ffe1;
    }

    .block-container {
        padding-top: 4rem;
    }

    .user-message {
        background-color: #3FE0D0;
        color: black;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
        max-width: 80%;
        margin-left: 10px;
    }

    .bot-message {
        background-color: #ADD8E6;
        color: black;
        padding: 10px;
        border-radius: 10px;
        margin: 5px 0;
        max-width: 80%;
        margin-right: 10px;
    }

    .typing-indicator {
        color: #00c8ff;
    }
    </style>

    <video autoplay loop muted>
        <source src="https://assets.mixkit.co/videos/preview/mixkit-digital-interface-with-data-9735-large.mp4" type="video/mp4">
    </video>
""", unsafe_allow_html=True)

# Configure Gemini API Key
genai.configure(api_key="AIzaSyD60S4qvkQM0cXVmYsZ1Slj5IrdoEpXtso")

# Create Unique User ID for Session
if "user_id" not in st.session_state:
    st.session_state.user_id = str(uuid.uuid4())

USER_ID = st.session_state.user_id
HISTORY_FILE = f"chat_history_{USER_ID}.json"

# Load Chat History
if os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        try:
            all_chats = json.load(f)
            if not isinstance(all_chats, dict):
                all_chats = {}
        except json.JSONDecodeError:
            all_chats = {}
else:
    all_chats = {}

# Today’s Key
today_key = datetime.now().strftime("%Y-%m-%d")
if today_key not in all_chats:
    all_chats[today_key] = []

# Sidebar – Past Conversations
with st.sidebar:
    st.header("📅 Past Conversations")
    for date in sorted(all_chats.keys(), reverse=True):
        with st.expander(date):
            for msg in all_chats[date]:
                st.markdown(f"👤 **You**: {msg['user']}")
                st.markdown(f"🤖 **Kaal AI**: {msg['bot']}")
                st.markdown("---")

# Main UI
st.title("🤖 Kaal AI - Desi GPT with Futuristic Vibes")
st.markdown("🚀 Hinglish mein baat karne wala AI saathi – upgraded to sci-fi mode!")

# Show Today’s Chat
if all_chats[today_key]:
    st.subheader("📌 Today’s Chat")
    for msg in all_chats[today_key]:
        st.markdown(f"<div class='user-message'>👤 **You**: {msg['user']}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='bot-message'>🤖 **Kaal AI**: {msg['bot']}</div>", unsafe_allow_html=True)
        st.markdown("---")

# Chat Input
user_input = st.chat_input("Pucho apna sawaal 💬")

# Chat Logic
if user_input:
    st.markdown(f"<div class='user-message'>👤 **You**: {user_input}</div>", unsafe_allow_html=True)

    history_messages = []
    for msg in all_chats[today_key]:
        history_messages.append({"role": "user", "parts": [msg["user"]]} )
        history_messages.append({"role": "model", "parts": [msg["bot"]]})

    if "chat_session" not in st.session_state:
        model = genai.GenerativeModel(model_name="models/gemini-1.5-pro-001")
        st.session_state.chat_session = model.start_chat(history=history_messages)

    try:
        # Typing animation
        st.markdown("<div class='typing-indicator'>🤖 **Kaal AI is typing...**</div>", unsafe_allow_html=True)
        time.sleep(1)

        # Get AI response
        chat = st.session_state.chat_session
        ai_response = chat.send_message(user_input).text

        # Show response
        st.markdown(f"<div class='bot-message'>🤖 **Kaal AI**: {ai_response}</div>", unsafe_allow_html=True)
        st.markdown("---")

        # Save chat history
        all_chats[today_key].append({"user": user_input, "bot": ai_response})
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(all_chats, f, indent=2, ensure_ascii=False)

        # Refresh page to show updated chat
        st.rerun()

    except Exception as e:
        st.error(f"⚠️ Error: {e}")

# --- 3) Logout Button (Optional) ---
if st.sidebar.button("🚪 Logout"):
    for k in ["token", "username", "user_id"]:
        st.session_state.pop(k, None)
    st.experimental_rerun()
