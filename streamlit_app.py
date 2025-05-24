import streamlit as st
import pandas as pd
import random

# Load question data
@st.cache_data
def load_questions():
    df = pd.read_csv("questions_extracted.csv")
    return df

df = load_questions()

# Define valid subjects
valid_subjects = [
    "Ethical and Participant Safety Considerations",
    "Clinical Research Standards and Guidelines",
    "Clinical Trial Operations (GCPs)",
    "Study and Site Management",
    "Research Design and Data Management"
]

# Filter available subjects from the dataframe
subject_options = sorted(list(set(df['topic']) & set(valid_subjects)))

st.title("ACRP Exam Prep")

# Sidebar: Subject selection
st.sidebar.header("Select Subjects")
selected_subjects = []
cols = st.sidebar.columns(2)
for i, subject in enumerate(subject_options):
    col = cols[i % 2]
    with col:
        if st.checkbox(subject, key=f"subject_{subject}", value=True):
            selected_subjects.append(subject)

# Number of questions
num_questions = st.sidebar.number_input("Number of Questions", min_value=1, max_value=100, value=5)

# Filter and generate test
if st.sidebar.button("Generate Test"):
    filtered_df = df[df['topic'].isin(selected_subjects)]
    if not filtered_df.empty:
        questions = filtered_df.sample(min(num_questions, len(filtered_df))).reset_index(drop=True)
        st.session_state['questions'] = questions
        st.session_state['current'] = 0
        st.session_state['answers'] = []
        st.experimental_rerun()

# Test Interface
if 'questions' in st.session_state and st.session_state['current'] < len(st.session_state['questions']):
    q = st.session_state['questions'].iloc[st.session_state['current']]
    st.write(f"**Question {st.session_state['current'] + 1} of {len(st.session_state['questions'])}:**")
    st.write(q['question'])
    
    options = [q['option_A'], q['option_B'], q['option_C'], q['option_D']]
    answer = st.radio("Select an answer:", options, key=f"answer_{st.session_state['current']}")

    if st.button("Next"):
        st.session_state['answers'].append(answer)
        st.session_state['current'] += 1
        st.experimental_rerun()

elif 'questions' in st.session_state and st.session_state['current'] >= len(st.session_state['questions']):
    st.success("Test Completed!")
    score = 0
    for i, row in st.session_state['questions'].iterrows():
        if st.session_state['answers'][i] == row['answer']:
            score += 1
    
    st.write(f"Your score: {score} out of {len(st.session_state['questions'])}")

    if st.button("Start Over"):
        del st.session_state['questions']
        del st.session_state['answers']
        del st.session_state['current']
        st.experimental_rerun()
