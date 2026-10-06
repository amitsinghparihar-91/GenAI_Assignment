from __future__ import annotations

import html
import os
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from rag import answer, make_chain, make_retriever

load_dotenv(Path(__file__).parent / ".env")
st.set_page_config(
    page_title="Arcleo Assistant",
    page_icon="💬",
    layout="centered",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------------------------------------------
# Content you may want to edit
# --------------------------------------------------------------------------------------
SUGGESTIONS = [
    ("🏗️", "What architecture and AWS services are planned?"),
    ("💳", "How are payments and shipping handled?"),
    ("🔒", "What security protections are specified?"),
    ("💰", "What are the estimated monthly infrastructure costs?"),
]
# Extra ideas offered as "Related questions" after an answer (only ones not asked yet are shown).
EXTRA_QUESTIONS = [
    "How does the system handle traffic spikes and scaling?",
    "Which databases and storage are used?",
    "How is the application deployed and monitored?",
    "What are the main risks or open questions in the spec?",
]
ALL_QUESTIONS = [q for _, q in SUGGESTIONS] + EXTRA_QUESTIONS

# --------------------------------------------------------------------------------------
# Styling. Every colour is set explicitly (with !important) so text stays readable
# whether the browser/Streamlit theme is light or dark.
# --------------------------------------------------------------------------------------
st.markdown(
    """
<style>
:root {
  --ink:#18263a; --body:#2b3a52; --muted:#5b6b82; --blue:#356df3; --blue-dark:#1f4fc7;
  --line:#dfe6f1; --soft:#eef3ff; --card:#ffffff;
}
html, body, .stApp, [data-testid="stAppViewContainer"], [data-testid="stSidebar"] { color-scheme: light; }
html, body, [class*="css"] { font-family: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif; }

/* ---------- page ---------- */
.stApp { background: linear-gradient(180deg, #f4f7fd 0%, #ffffff 380px); color: var(--ink); }
[data-testid="stHeader"] { background: transparent; }
[data-testid="stHeader"] svg, [data-testid="stSidebarCollapsedControl"] svg,
[data-testid="stToolbar"] svg { color: var(--ink) !important; fill: currentColor; }
.block-container { max-width: 850px; padding-top: 2rem; padding-bottom: 6rem; }
footer { visibility: hidden; }

/* ---------- all normal text ---------- */
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] strong, [data-testid="stMarkdownContainer"] em,
[data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] h4,
[data-testid="stMarkdownContainer"] td, [data-testid="stMarkdownContainer"] th,
[data-testid="stMarkdownContainer"] a { color: var(--ink) !important; }
[data-testid="stMarkdownContainer"] a { color: var(--blue-dark) !important; }
[data-testid="stMarkdownContainer"] code { color: #7a1f4d !important; background: #f1f4fa !important; }
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * { color: var(--muted) !important; }
label, label p, [data-testid="stWidgetLabel"] p { color: var(--ink) !important; }

/* ---------- brand + hero ---------- */
@keyframes rise { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
@keyframes pulse { 0%,100% { box-shadow: 0 0 0 0 rgba(34,170,94,.45); } 50% { box-shadow: 0 0 0 6px rgba(34,170,94,0); } }
.brand-row { display:flex; align-items:center; justify-content:space-between; margin: 0 0 2rem; }
.brand-left { display:flex; align-items:center; gap:12px; }
.brand-mark { width:38px; height:38px; border-radius:12px; background:var(--soft); display:flex; align-items:center; justify-content:center; font-weight:800; font-size:20px; color:var(--blue) !important; }
.brand-name { font-weight:700; font-size:15px; letter-spacing:-.2px; color:#34435a !important; }
.pill { display:inline-flex; align-items:center; gap:7px; padding:5px 12px; border-radius:999px; font-size:12px; font-weight:600; background:#fff; border:1px solid var(--line); color:var(--body) !important; }
.dot { width:8px; height:8px; border-radius:50%; background:#22aa5e; animation:pulse 2s infinite; }
.dot.off { background:#d64545; animation:none; }
.hero { padding: 1rem 0 .5rem; animation: rise .5s ease both; }
.hero .eyebrow { color:var(--blue) !important; text-transform:uppercase; letter-spacing:1.5px; font-size:11px; font-weight:700; margin-bottom:12px; }
.hero h1 { font-size:clamp(2rem,5vw,3rem); letter-spacing:-1.6px; line-height:1.12; margin:0 0 14px; color:var(--ink) !important; }
.hero p.lead { color:var(--muted) !important; font-size:16px; line-height:1.65; max-width:560px; margin:0; }
.section-label { color:var(--muted) !important; font-size:12px; font-weight:700; letter-spacing:.7px; text-transform:uppercase; margin: 1.6rem 0 .7rem; }

/* ---------- buttons (suggestions, follow-ups, sidebar, download) ---------- */
.stButton > button, .stDownloadButton > button {
  border:1px solid var(--line); border-radius:14px; background:#fff !important; color:#34435a !important;
  padding:.75rem 1rem; min-height:60px; white-space:normal; line-height:1.35;
  box-shadow:0 4px 15px rgba(30,50,80,.04); transition:all .16s ease;
}
.stButton > button *, .stDownloadButton > button * { color:#34435a !important; text-align:left; }
.stButton > button > div, .stDownloadButton > button > div { justify-content:flex-start; text-align:left; }
.stButton > button:hover, .stDownloadButton > button:hover {
  border-color:#8fb0ff; background:#f5f8ff !important; transform:translateY(-2px);
  box-shadow:0 9px 24px rgba(53,109,243,.14);
}
.stButton > button:hover *, .stDownloadButton > button:hover * { color:var(--blue-dark) !important; }
.stButton > button:active { transform:translateY(0); }
.stButton > button:focus-visible { outline:2px solid var(--blue); outline-offset:2px; }
.stButton > button:disabled { opacity:.6; }
[class*="st-key-up_"] button, [class*="st-key-down_"] button { min-height:36px; padding:.25rem .7rem; border-radius:10px; }

/* ---------- chat ---------- */
[data-testid="stChatMessage"] {
  border:1px solid #e6ebf4; border-radius:18px; padding:.8rem 1.05rem; margin-bottom:.6rem;
  background:#fff !important; box-shadow:0 5px 18px rgba(30,50,80,.04); animation: rise .35s ease both;
}
[data-testid="stChatMessage"] * { color: var(--ink); }
[data-testid="stChatMessage"] a { color: var(--blue-dark) !important; }
[data-testid="stChatInput"], [data-testid="stChatInput"] > div {
  background:#fff !important; border-color:var(--line); border-radius:16px; box-shadow:0 8px 28px rgba(30,50,80,.08);
}
[data-testid="stChatInput"] textarea {
  color:var(--ink) !important; -webkit-text-fill-color:var(--ink) !important; caret-color:var(--blue);
  background:transparent !important; font-family:inherit;
}
[data-testid="stChatInput"] textarea::placeholder { color:#6b7a90 !important; -webkit-text-fill-color:#6b7a90 !important; opacity:1; }
[data-testid="stChatInput"] button svg { color:var(--blue) !important; fill:var(--blue) !important; }
[data-testid="stChatInput"]:focus-within { border-color:var(--blue); box-shadow:0 8px 28px rgba(53,109,243,.18); }

/* source chips + meta */
.chips { display:flex; flex-wrap:wrap; gap:8px; margin:.55rem 0 .15rem; }
.chip { display:inline-block; padding:5px 11px; border-radius:999px; font-size:12.5px; font-weight:600;
        background:var(--soft); border:1px solid #cddbff; color:var(--blue-dark) !important; }
.chip-label { font-size:12px; font-weight:700; letter-spacing:.6px; text-transform:uppercase; color:var(--muted) !important; margin-right:2px; align-self:center; }
.meta { color:var(--muted) !important; font-size:12px; margin-top:.2rem; }

/* ---------- expander, alerts, spinner, code ---------- */
[data-testid="stExpander"] { border:1px solid var(--line); border-radius:12px; background:#fff !important; }
[data-testid="stExpander"] summary, [data-testid="stExpander"] summary * { color: var(--ink) !important; }
[data-testid="stExpander"] svg { color: var(--ink) !important; }
[data-testid="stAlert"], [data-testid="stAlert"] * { color: var(--ink) !important; }
[data-testid="stSpinner"], [data-testid="stSpinner"] * { color: var(--muted) !important; }
[data-testid="stCode"], [data-testid="stCode"] pre { background:#f1f4fa !important; }
[data-testid="stCode"] *, pre, pre * { color: var(--ink) !important; }

/* ---------- sidebar ---------- */
[data-testid="stSidebar"] { background:#f1f5fc !important; border-right:1px solid var(--line); }
[data-testid="stSidebar"] * { color: var(--ink); }
[data-testid="stSidebar"] .stButton > button, [data-testid="stSidebar"] .stDownloadButton > button { min-height:48px; padding:.55rem .85rem; }
.side-title { font-size:17px; font-weight:800; letter-spacing:-.3px; color:var(--ink) !important; margin:.2rem 0 .1rem; }
.side-sub { font-size:12.5px; color:var(--muted) !important; margin-bottom:.9rem; }
.stat { display:flex; justify-content:space-between; font-size:13px; padding:.35rem 0; border-bottom:1px dashed #d4ddee; color:var(--body) !important; }
</style>
""",
    unsafe_allow_html=True,
)


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------
@st.cache_resource(show_spinner="Preparing the document search…")
def get_pipeline(api_key: str):
    return make_retriever(api_key), make_chain(api_key)


def stream_words(text: str):
    """Yield the answer word by word for a typing effect."""
    for token in text.split(" "):
        yield token + " "
        time.sleep(0.012)


def ask(question: str) -> None:
    st.session_state.pending_question = question


def reset_chat() -> None:
    st.session_state.messages = []
    st.session_state.pop("pending_question", None)


def set_feedback(index: int, value: str) -> None:
    st.session_state.messages[index]["feedback"] = value


def chips_html(refs: list[str]) -> str:
    chips = "".join(f'<span class="chip">📄 {html.escape(r)}</span>' for r in refs)
    return f'<div class="chips"><span class="chip-label">Sources</span>{chips}</div>'


def transcript_text() -> str:
    lines = ["Arcleo Assistant: conversation transcript", ""]
    for m in st.session_state.messages:
        who = "You" if m["role"] == "user" else "Assistant"
        lines.append(f"{who}: {m['content']}")
        if m.get("sources"):
            lines.append("Sources: " + "; ".join(m["sources"]))
        lines.append("")
    return "\n".join(lines)


def next_questions(limit: int = 3) -> list[str]:
    asked = {m["content"].strip().lower() for m in st.session_state.messages if m["role"] == "user"}
    return [q for q in ALL_QUESTIONS if q.lower() not in asked][:limit]


# --------------------------------------------------------------------------------------
# State
# --------------------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

api_key = os.getenv("GOOGLE_API_KEY")
# chat_input is always pinned to the bottom of the page, so it can be read here, before the header
typed_question = st.chat_input("Ask about the architecture spec…")
question = st.session_state.pop("pending_question", None) or typed_question
n_questions = sum(1 for m in st.session_state.messages if m["role"] == "user")

# --------------------------------------------------------------------------------------
# Sidebar
# --------------------------------------------------------------------------------------
with st.sidebar:
    st.markdown('<div class="side-title">Arcleo Assistant</div><div class="side-sub">Ask questions about the architecture spec</div>', unsafe_allow_html=True)
    st.button("➕  New conversation", on_click=reset_chat, use_container_width=True, disabled=not st.session_state.messages)

    st.markdown('<div class="section-label">Settings</div>', unsafe_allow_html=True)
    typing_effect = st.toggle("Typing effect", value=True, help="Show answers word by word")
    show_sources = st.toggle("Show sources", value=True, help="Show which spec sections each answer used")

    if st.session_state.messages:
        st.markdown('<div class="section-label">Quick questions</div>', unsafe_allow_html=True)
        for i, q in enumerate(ALL_QUESTIONS):
            st.button(q, key=f"side_q_{i}", on_click=ask, args=(q,), use_container_width=True)

        st.markdown('<div class="section-label">This chat</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="stat"><span>Questions asked</span><b>{n_questions}</b></div>', unsafe_allow_html=True)
        st.download_button("⬇️  Download transcript", transcript_text(), file_name="arcleo_chat.txt",
                           mime="text/plain", use_container_width=True)

# --------------------------------------------------------------------------------------
# Header + hero
# --------------------------------------------------------------------------------------
status = ('<span class="pill"><span class="dot"></span>Connected</span>' if api_key
          else '<span class="pill"><span class="dot off"></span>API key missing</span>')
st.markdown(
    f'<div class="brand-row"><div class="brand-left"><div class="brand-mark">A</div>'
    f'<div class="brand-name">ARCLEO&nbsp; / &nbsp;SPEC ASSISTANT</div></div>{status}</div>',
    unsafe_allow_html=True,
)

if st.session_state.messages or question:
    st.markdown("### Project assistant")
    st.caption("Gemini 2.5 Flash · grounded in your architecture spec")
else:
    st.markdown(
        """
        <div class="hero">
          <div class="eyebrow">Your project, at a glance</div>
          <h1>What would you like<br>to know?</h1>
          <p class="lead">Ask a question about the electronics store architecture. Answers are grounded in your spec and include source sections.</p>
        </div>
        <div class="section-label">Try asking · click a card or type below</div>
        """,
        unsafe_allow_html=True,
    )
    cols = st.columns(2, gap="medium")
    for i, (icon, text) in enumerate(SUGGESTIONS):
        cols[i % 2].button(f"{icon}  {text}", key=f"suggestion_{i}", on_click=ask, args=(text,), use_container_width=True)
    if not api_key:
        st.info("Add `GOOGLE_API_KEY=your-key` to a `.env` file next to app.py, then restart the app.")

# --------------------------------------------------------------------------------------
# History
# --------------------------------------------------------------------------------------
last_index = len(st.session_state.messages) - 1
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"], avatar="🧑" if msg["role"] == "user" else "🤖"):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            if show_sources and msg.get("sources"):
                st.markdown(chips_html(msg["sources"]), unsafe_allow_html=True)
            if msg.get("elapsed"):
                st.markdown(f'<div class="meta">Answered in {msg["elapsed"]:.1f}s</div>', unsafe_allow_html=True)
            if msg.get("feedback"):
                st.caption("Thanks for the feedback 👍" if msg["feedback"] == "up" else "Thanks, noted 👎")
            else:
                c1, c2, _ = st.columns([1, 1, 6])
                c1.button("👍", key=f"up_{idx}", on_click=set_feedback, args=(idx, "up"), help="Helpful")
                c2.button("👎", key=f"down_{idx}", on_click=set_feedback, args=(idx, "down"), help="Not helpful")

# Follow-up suggestions under the latest answer
if st.session_state.messages and not question and st.session_state.messages[last_index]["role"] == "assistant":
    follow_ups = next_questions()
    if follow_ups:
        st.markdown('<div class="section-label">Related questions</div>', unsafe_allow_html=True)
        fcols = st.columns(len(follow_ups), gap="small")
        for i, q in enumerate(follow_ups):
            fcols[i].button(q, key=f"follow_{last_index}_{i}", on_click=ask, args=(q,), use_container_width=True)

# --------------------------------------------------------------------------------------
# New question
# --------------------------------------------------------------------------------------
if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(question)

    response, matches, elapsed = "", [], None
    with st.chat_message("assistant", avatar="🤖"):
        if not api_key:
            response = "Add your Google API key to `.env` to start asking questions."
            st.info(response)
        else:
            try:
                retriever, chain = get_pipeline(api_key)
                started = time.time()
                with st.spinner("Searching the spec…"):
                    response, matches = answer(question, retriever, chain)
                elapsed = time.time() - started
                response = response or "I couldn't find an answer to that in the spec."
                if typing_effect and hasattr(st, "write_stream"):
                    st.write_stream(stream_words(response))
                else:
                    st.markdown(response)
            except Exception as exc:
                response, matches = "I couldn't reach Gemini. Check your API key and connection, then try again.", []
                st.error(response)
                with st.expander("Technical details"):
                    st.code(str(exc))

    refs = list(dict.fromkeys(doc.metadata["citation"] for doc in matches))
    st.session_state.messages.append({"role": "assistant", "content": response, "sources": refs, "elapsed": elapsed})
    st.rerun()  # redraw from saved state so sources, feedback and related questions appear