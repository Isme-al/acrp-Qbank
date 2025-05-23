import streamlit as st
import pandas as pd
import random
import time

# ── 1) Page config & hide Streamlit chrome ────────────────────────
st.set_page_config(
    page_title="ACRP QBank",
    layout="wide",
    initial_sidebar_state="collapsed"
)
st.markdown("""
    <style>
      /* hide menu and footer */
      #MainMenu, footer { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# ── 2) UWorld-style CSS overrides ─────────────────────────────────
st.markdown("""
<style>
/* Top navbar styling */
.navbar {
  background-color: #1f77b4;
  padding: .75rem 1rem;
  color: white;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.navbar-title { font-size: 1.5rem; font-weight: 600; }
/* Render page-nav buttons as links */
.navbar-nav button {
  background: transparent;
  border: none;
  color: white;
  margin-left: 1rem;
  font-size: 1rem;
  cursor: pointer;
}
.navbar-nav button:hover { text-decoration: underline; }
/* Style any Streamlit radio as a “card” */
div.stRadio > label {
  display: block;
  background: #f8f9fa;
  padding: 1rem;
  margin: .3rem 0;
  border-radius: .5rem;
  cursor: pointer;
  font-size: 1.1rem;
}
div.stRadio > label:hover { background: #e9ecef; }
/* Highlight selected card */
div.stRadio > label > div[aria-checked="true"] {
  border: 2px solid #1f77b4 !important;
  background: #e1ecf9 !important;
}
/* Make buttons full-width, UWorld blue */
div.stButton > button {
  width: 100%;
  padding: .75rem;
  font-size: 1rem;
  color: white;
  background-color: #1f77b4;
  border: none;
  border-radius: .375rem;
}
div.stButton > button:hover {
  background-color: #0e5c99;
}
</style>
""", unsafe_allow_html=True)

# ── 3) Top navigation bar (HTML) ─────────────────────────────────
pages = ["Dashboard", "Create Test", "Clinical Research Library"]
nav_buttons = "".join(
    f"<button onclick=\"window.location.hash='{p}'\">{p}</button>"
    for p in pages
)
st.markdown(f"""
<div class="navbar">
  <div class="navbar-title">ACRP QBank</div>
  <div class="navbar-nav">
    {nav_buttons}
  </div>
</div>
""", unsafe_allow_html=True)

# Use URL hash for page routing
current_hash = st.experimental_get_query_params().get("hash", [pages[0]])[0]
page = current_hash if current_hash in pages else pages[0]


# ── 4) Load questions ─────────────────────────────────────────────
@st.cache_data
def load_questions():
    df = pd.read_csv("questions_extracted.csv", encoding="utf-8-sig", dtype=str)
    qs = []
    for _, r in df.iterrows():
        qs.append({
            "question":    r["question"],
            "options":     [r["option_A"], r["option_B"], r["option_C"], r["option_D"]],
            "answer":      ["A","B","C","D"].index(r["answer"].strip().upper()),
            "explanation": r.get("explanation", ""),
            "topic":       r.get("topic", "")
        })
    return qs

QUESTION_BANK = load_questions()


# ── 5) Session state defaults ─────────────────────────────────────
if 'test_questions' not in st.session_state:
    st.session_state.update({
        'test_questions': [], 'test_index': 0,
        'test_answers': {}, 'test_submitted': False, 'test_start': None
    })


# ── 6) Page definitions ───────────────────────────────────────────
def dashboard_page():
    st.markdown("### Dashboard")
    st.write("Welcome! Use 'Create Test' to generate a new question set.")


def create_test_page():
    st.markdown("### Create Test")

    total = len(QUESTION_BANK)
    attempted = set(st.session_state['test_answers'].keys())
    count_unused  = total - len(attempted)
    count_corr    = sum(
        i in attempted and st.session_state['test_answers'][i] == q['options'][q['answer']]
        for i, q in enumerate(QUESTION_BANK)
    )
    count_incorr  = sum(
        i in attempted and st.session_state['test_answers'][i] != q['options'][q['answer']]
        for i, q in enumerate(QUESTION_BANK)
    )

    cols = st.columns(5)
    unused    = cols[0].checkbox(f"Unused ({count_unused})", True)
    incorrect = cols[1].checkbox(f"Incorrect ({count_incorr})")
    marked    = cols[2].checkbox("Marked (0)")
    omitted   = cols[3].checkbox("Omitted (0)")
    correct   = cols[4].checkbox(f"Correct ({count_corr})")
    st.markdown("---")

    # Topics filter
    st.subheader("Subjects")
    topics = sorted({q['topic'] for q in QUESTION_BANK})
    cols_subj = st.columns(2)
    topic_sel = {}
    for idx_t, topic in enumerate(topics):
        col = cols_subj[idx_t % 2]
        cnt = sum(1 for q in QUESTION_BANK if q['topic'] == topic)
        topic_sel[topic] = col.checkbox(f"{topic} ({cnt})", True)
    st.markdown("---")

    # Number of questions
    st.subheader("No. of Questions")
    max_q = st.number_input("Max per block", 1, total, min(40, total), 1)
    st.markdown("---")

    if st.button("Generate Test"):
        filt = []
        for i, q in enumerate(QUESTION_BANK):
            ok = True
            if not unused    and i not in attempted: ok = False
            if not incorrect and i in attempted and st.session_state['test_answers'][i] != q['options'][q['answer']]: ok=False
            if not correct   and i in attempted and st.session_state['test_answers'][i] == q['options'][q['answer']]: ok=False
            if not topic_sel.get(q['topic'], False): ok=False
            if ok: filt.append(q)
        n = min(max_q, len(filt))
        st.session_state.update({
            'test_questions': random.sample(filt, n),
            'test_index':     0,
            'test_answers':   {},
            'test_submitted': False,
            'test_start':     time.time()
        })
        st.rerun()

    if st.session_state['test_questions']:
        idx   = st.session_state['test_index']
        total = len(st.session_state['test_questions'])
        q     = st.session_state['test_questions'][idx]

        st.markdown(f"#### Question {idx+1} of {total}   _(Topic: {q['topic']})_")
        choice = st.radio("", q['options'], key=f"ans{idx}")

        c1, c2 = st.columns(2)
        with c1:
            if idx > 0 and st.button("← Previous"):
                st.session_state['test_index'] -= 1; st.rerun()
        with c2:
            if idx < total-1 and st.button("Next →"):
                st.session_state['test_index'] += 1; st.rerun()

        if st.button("Submit Answer"):
            st.session_state['test_answers'][idx] = choice

        if idx in st.session_state['test_answers']:
            sel  = st.session_state['test_answers'][idx]
            corr = q['options'][q['answer']]
            if sel == corr:
                st.success("Correct!")
            else:
                st.error(f"Incorrect. Correct: {corr}")
            with st.expander("Explanation"):
                st.write(q['explanation'])

    if st.session_state['test_questions'] and st.session_state['test_index'] == len(st.session_state['test_questions']) - 1:
        if st.button("Submit Test"):
            st.session_state['test_submitted'] = True
        if st.session_state['test_submitted']:
            score = sum(
                1 for i, q in enumerate(st.session_state['test_questions'])
                if st.session_state['test_answers'].get(i) == q['options'][q['answer']]
            )
            st.markdown("---")
            st.success(f"Final Score: {score} / {len(st.session_state['test_questions'])}")


def library_page():
    st.markdown("### Clinical Research Library")
    st.write("Browse study resources here.")


# ── 7) Render the selected page ────────────────────────────────────
if page == "Dashboard":
    dashboard_page()
elif page == "Create Test":
    create_test_page()
else:
    library_page()
