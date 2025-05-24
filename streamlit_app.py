import streamlit as st
import pandas as pd
import random
import time

# ── Page config ──
st.set_page_config(page_title="Clinical Research QBank", layout="wide")

# ── Load questions from CSV ──
@st.cache_data
def load_questions():
    df = pd.read_csv("questions_extracted.csv", encoding="utf-8-sig", dtype=str)
    questions = []
    for _, r in df.iterrows():
        questions.append({
            "question":    r["question"],
            "options":     [r["option_A"], r["option_B"], r["option_C"], r["option_D"]],
            "answer":      ["A","B","C","D"].index(r["answer"].strip().upper()),
            "explanation": r.get("explanation", ""),
            "topic":       r.get("topic", "")
        })
    return questions

QUESTION_BANK = load_questions()

# ── Session state defaults ──
if 'test_questions' not in st.session_state:
    st.session_state.update({
        'test_questions': [],
        'test_index': 0,
        'test_answers': {},
        'test_submitted': False,
        'test_start': None
    })

# ── Sidebar navigation ──
with st.sidebar:
    st.title("Clinical Research QBank")
    page = st.radio("Navigate", ["Dashboard", "Create Test", "Clinical Research Library"] )

# ── Pages ──
def dashboard_page():
    st.header("Dashboard")
    st.write("Welcome! Use 'Create Test' to generate a new test.")


def create_test_page():
    st.header("Create Test")
    total = len(QUESTION_BANK)
    attempted = set(st.session_state['test_answers'].keys())
    count_unused = total - len(attempted)
    count_correct = sum(
        1 for i,q in enumerate(QUESTION_BANK)
        if i in attempted and st.session_state['test_answers'][i] == q['options'][q['answer']]
    )
    count_incorrect = sum(
        1 for i,q in enumerate(QUESTION_BANK)
        if i in attempted and st.session_state['test_answers'][i] != q['options'][q['answer']]
    )

    # Question Mode filters
    cols = st.columns(5)
    unused = cols[0].checkbox(f"Unused ({count_unused})", value=True)
    incorrect = cols[1].checkbox(f"Incorrect ({count_incorrect})")
    marked = cols[2].checkbox("Marked (0)")
    omitted = cols[3].checkbox("Omitted (0)")
    correct = cols[4].checkbox(f"Correct ({count_correct})")
    st.markdown("---")

    # Subject filters
    st.subheader("Subjects")
    topics = sorted({q['topic'] for q in QUESTION_BANK})
    cols_subj = st.columns(2)
    topic_selection = {}
    for idx, topic in enumerate(topics):
        col = cols_subj[idx % 2]
        cnt = sum(1 for q in QUESTION_BANK if q['topic'] == topic)
        topic_selection[topic] = col.checkbox(f"{topic} ({cnt})", value=True)
    st.markdown("---")

    # Number of questions
    st.subheader("No. of Questions")
    max_q = st.number_input(
        "Max allowed per block",
        min_value=1, max_value=total,
        value=min(10, total), step=1
    )
    st.markdown("---")

    # Generate Test
    if st.button("Generate Test"):
        filtered = []
        for i, q in enumerate(QUESTION_BANK):
            ok = True
            if not unused and i not in attempted:
                ok = False
            if not incorrect and i in attempted and st.session_state['test_answers'][i] != q['options'][q['answer']]:
                ok = False
            if not correct and i in attempted and st.session_state['test_answers'][i] == q['options'][q['answer']]:
                ok = False
            if not topic_selection.get(q['topic'], False):
                ok = False
            if ok:
                filtered.append(q)
        n = min(max_q, len(filtered))
        st.session_state['test_questions'] = random.sample(filtered, n)
        st.session_state['test_index'] = 0
        st.session_state['test_answers'] = {}
        st.session_state['test_submitted'] = False
        st.session_state['test_start'] = time.time()
        st.rerun()

    # If a test has been generated, render the questions
    if st.session_state['test_questions']:
        idx = st.session_state['test_index']
        q = st.session_state['test_questions'][idx]
        st.subheader(f"Question {idx+1} of {len(st.session_state['test_questions'])}   Topic: {q['topic']}")
        st.write(q['question'])
        choice = st.radio("Select an answer:", q['options'], key=f"ans{idx}")

        # Navigation buttons
        c1, c2 = st.columns(2)
        with c1:
            if idx > 0 and st.button("Previous"):
                st.session_state['test_index'] -= 1
                st.rerun()
        with c2:
            if idx < len(st.session_state['test_questions']) - 1 and st.button("Next"):
                st.session_state['test_index'] += 1
                st.rerun()

        # Record answer
        if st.button("Submit Answer"):
            st.session_state['test_answers'][idx] = choice

        # Immediate feedback
        if idx in st.session_state['test_answers']:
            sel = st.session_state['test_answers'][idx]
            corr = q['options'][q['answer']]
            if sel == corr:
                st.success("Correct!")
            else:
                st.error(f"Incorrect. Correct answer: {corr}")
            with st.expander("Explanation"):
                st.write(q['explanation'])

        # Final score once all are answered
        total_q = len(st.session_state['test_questions'])
        if len(st.session_state['test_answers']) == total_q:
            if st.button("Submit Test"):
                st.session_state['test_submitted'] = True
            if st.session_state['test_submitted']:
                score = sum(
                    1 for i, q in enumerate(st.session_state['test_questions'])
                    if st.session_state['test_answers'].get(i) == q['options'][q['answer']]
                )
                pct = round(score/total_q * 100)
                st.markdown("---")
                st.success(f"🎉 You scored **{score} / {total_q}**  ({pct}%)")


def library_page():
    st.header("Clinical Research Library")
    st.write("Browse study resources here.")

# ── Router ──
if page == "Dashboard":
    dashboard_page()
elif page == "Create Test":
    create_test_page()
elif page == "Clinical Research Library":
    library_page()
