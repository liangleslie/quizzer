import json
import random
import re
import streamlit as st

# Attempt to load the drag-and-drop component
try:
    from streamlit_sortables import sort_items
    HAS_SORTABLES = True
except ImportError:
    HAS_SORTABLES = False

QUESTION_SETS = {
    "AIGP 2024": "question_bank_2024.json",
    "Straits Interactive": "question_bank_straits_interactive.json",
    "Online Sourced": "question_bank_online_sourced.json"
}

def render_copyable_prompt(prompt_text: str):
    prompt_json = json.dumps(prompt_text)

    copy_button_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                margin: 0;
                padding: 0;
                background: transparent;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }}
            .container {{
                display: flex;
                align-items: center;
                gap: 12px;
                padding: 4px 0;
            }}
            #copy-btn {{
                background-color: #ff4b4b;
                color: white;
                border: none;
                padding: 8px 18px;
                font-size: 0.95rem;
                font-weight: 600;
                border-radius: 6px;
                cursor: pointer;
                display: inline-flex;
                align-items: center;
                gap: 6px;
                transition: all 0.2s ease;
            }}
            #copy-btn:hover {{
                opacity: 0.9;
            }}
            #copy-msg {{
                font-size: 0.9rem;
                color: #28a745;
                font-weight: 500;
                display: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <button id="copy-btn" onclick="copyPrompt()">
                📋 Copy Prompt to Clipboard
            </button>
            <span id="copy-msg">
                ✓ Copied to clipboard!
            </span>
        </div>

        <script>
        function copyPrompt() {{
            const text = {prompt_json};

            if (navigator.clipboard && window.isSecureContext) {{
                navigator.clipboard.writeText(text).then(showSuccess).catch(fallbackCopy);
            }} else {{
                fallbackCopy();
            }}

            function fallbackCopy() {{
                const textarea = document.createElement("textarea");
                textarea.value = text;
                textarea.style.position = "fixed";
                textarea.style.left = "-999999px";
                textarea.style.top = "-999999px";
                document.body.appendChild(textarea);
                textarea.focus();
                textarea.select();
                try {{
                    document.execCommand('copy');
                    showSuccess();
                }} catch (err) {{
                    console.error('Fallback copy failed', err);
                }}
                document.body.removeChild(textarea);
            }}

            function showSuccess() {{
                const btn = document.getElementById("copy-btn");
                const msg = document.getElementById("copy-msg");
                btn.style.backgroundColor = "#28a745";
                btn.innerText = "✓ Copied!";
                msg.style.display = "inline";
                setTimeout(() => {{
                    btn.style.backgroundColor = "#ff4b4b";
                    btn.innerText = "📋 Copy Prompt to Clipboard";
                    msg.style.display = "none";
                }}, 2500);
            }}
        }}
        </script>
    </body>
    </html>
    """
    st.components.v1.html(copy_button_html, height=55)


# --- Configuration & Styling ---
st.set_page_config(
    page_title="AI Governance Assessment", page_icon="📝", layout="centered"
)

st.markdown(
    """
    <style>
    header[data-testid="stHeader"] { display: none !important; }
    .block-container {
        max-width: 860px !important;
        padding-top: 3rem !important;
        padding-bottom: 4rem !important;
        margin: 0 auto !important;
    }
    .stMarkdown h3 {
        font-size: 1.45rem !important;
        line-height: 1.5 !important;
        font-weight: 600 !important;
        margin-top: 0.5rem !important;
        margin-bottom: 1.25rem !important;
    }
    [data-testid="stCaptionContainer"] {
        font-size: 0.95rem !important;
        font-weight: 500 !important;
        letter-spacing: 0.02em;
    }
    div[data-testid="stRadio"] label, div[data-testid="stCheckbox"] label {
        font-size: 1.15rem !important;
        line-height: 1.5 !important;
        padding: 4px 8px !important;
        border-radius: 8px;
        transition: background-color 0.15s ease;
    }
    div[data-testid="stRadio"] label:hover, div[data-testid="stCheckbox"] label:hover {
        background-color: rgba(125, 125, 125, 0.08);
    }

    /* Main Button Styling */
    .stButton button {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        padding: 0.55rem 1.2rem !important;
        border-radius: 8px !important;
    }

    /* Popover History Button Override */
    div[data-testid="stPopoverBody"] .stButton button {
        padding: 0.4rem 0.2rem !important;
        width: 100% !important;
    }
    div[data-testid="stPopoverBody"] .stButton button p {
        font-size: 0.95rem !important;
        white-space: nowrap !important;
        text-overflow: unset !important;
        overflow: visible !important;
    }

    [data-testid="stAlert"] {
        font-size: 1.05rem !important;
        line-height: 1.55 !important;
    }
    .review-item {
        font-size: 1.15rem;
        line-height: 1.5;
        padding: 10px 14px;
        border-radius: 6px;
        margin-bottom: 8px;
    }
    .review-correct {
        background-color: rgba(40, 167, 69, 0.15);
        border-left: 4px solid #28a745;
    }
    .review-incorrect {
        background-color: rgba(220, 53, 69, 0.15);
        border-left: 4px solid #dc3545;
    }
    .review-neutral {
        background-color: rgba(125, 125, 125, 0.05);
        border-left: 4px solid transparent;
    }
    .submitted-order-box {
        background-color: rgba(125, 125, 125, 0.05);
        border-left: 4px solid #007bff;
        padding: 12px 18px;
        border-radius: 6px;
        margin-bottom: 1rem;
        font-size: 1.1rem;
        line-height: 1.6;
    }
    </style>
""",
    unsafe_allow_html=True,
)


# --- State Initialization ---
def load_bank(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

if "selected_set" not in st.session_state:
    st.session_state.selected_set = list(QUESTION_SETS.keys())[0]
    st.session_state.question_bank = load_bank(QUESTION_SETS[st.session_state.selected_set])

if "order" not in st.session_state:
    st.session_state.order = list(range(len(st.session_state.question_bank)))

if "current_pos" not in st.session_state:
    st.session_state.current_pos = 0

if "attempts" not in st.session_state:
    st.session_state.attempts = {}

if "review_index" not in st.session_state:
    st.session_state.review_index = None

if "current_answered" not in st.session_state:
    st.session_state.current_answered = False

if "jump_widget" not in st.session_state:
    st.session_state.jump_widget = 1


# --- Button Callbacks ---
def handle_jump():
    st.session_state.current_pos = st.session_state.jump_widget - 1
    st.session_state.current_answered = False
    st.session_state.review_index = None

def cb_next_question():
    st.session_state.current_pos += 1
    st.session_state.current_answered = False
    if st.session_state.current_pos < len(st.session_state.order):
        st.session_state.jump_widget = st.session_state.current_pos + 1

def cb_randomize():
    st.session_state.order = list(range(len(st.session_state.question_bank)))
    random.shuffle(st.session_state.order)
    st.session_state.current_pos = 0
    st.session_state.attempts = {}
    st.session_state.review_index = None
    st.session_state.current_answered = False
    st.session_state.jump_widget = 1

def cb_restart():
    st.session_state.order = list(range(len(st.session_state.question_bank)))
    st.session_state.current_pos = 0
    st.session_state.attempts = {}
    st.session_state.review_index = None
    st.session_state.current_answered = False
    st.session_state.jump_widget = 1

def cb_back_to_quiz():
    st.session_state.review_index = None
    st.session_state.jump_widget = st.session_state.current_pos + 1

def cb_review(order_idx):
    st.session_state.review_index = order_idx


# --- Header & Navigation ---
st.markdown("### 📝 AI Governance Practice")

nav_col1, nav_col2 = st.columns([2.5, 1], vertical_alignment="bottom")

with nav_col1:
    selected_set = st.selectbox(
        "Select Question Bank",
        list(QUESTION_SETS.keys()),
        index=list(QUESTION_SETS.keys()).index(st.session_state.selected_set)
    )

# Safely handle switching banks *before* rendering the jump_widget
if selected_set != st.session_state.selected_set:
    st.session_state.selected_set = selected_set
    st.session_state.question_bank = load_bank(QUESTION_SETS[selected_set])

    st.session_state.order = list(range(len(st.session_state.question_bank)))
    st.session_state.current_pos = 0
    st.session_state.attempts = {}
    st.session_state.review_index = None
    st.session_state.current_answered = False
    st.session_state.jump_widget = 1
    st.rerun()

with nav_col2:
    total_qns = len(st.session_state.order)
    if total_qns > 0:
        st.selectbox(
            "Jump to",
            options=list(range(1, total_qns + 1)),
            format_func=lambda x: f"Question {x}",
            key="jump_widget",
            on_change=handle_jump,
        )

if not st.session_state.question_bank:
    st.error(f"Error: `{QUESTION_SETS[st.session_state.selected_set]}` not found. Please ensure the file exists in the directory.")
    st.stop()


# --- Score & Attempt Metrics ---
total_attempted = len(st.session_state.attempts)
total_correct = sum(
    1 for att in st.session_state.attempts.values() if att["is_correct"]
)
pct_score = (
    (total_correct / total_attempted * 100) if total_attempted > 0 else 0.0
)
score_label = f"{total_correct}/{total_attempted} ({pct_score:.0f}%)"

top_left, top_right = st.columns([1.5, 1], vertical_alignment="center")

with top_left:
    btn_col1, btn_col2 = st.columns([1, 1])
    with btn_col1:
        st.button("🔀 Randomize", use_container_width=True, on_click=cb_randomize)
    with btn_col2:
        if st.session_state.review_index is not None:
            st.button("⬅ Back to Quiz", use_container_width=True, on_click=cb_back_to_quiz)

with top_right:
    with st.popover(f"📊 Score: {score_label}", use_container_width=True):
        st.markdown("#### Attempt History")
        if not st.session_state.attempts:
            st.caption("No questions completed yet.")
        else:
            cols = st.columns(3)
            for i, order_idx in enumerate(st.session_state.order):
                if order_idx in st.session_state.attempts:
                    att = st.session_state.attempts[order_idx]
                    status_icon = "✅" if att["is_correct"] else "❌"
                    btn_label = f"{status_icon} Q{i+1}"
                    col = cols[i % 3]
                    col.button(btn_label, key=f"hist_btn_{order_idx}", on_click=cb_review, args=(order_idx,))

st.divider()


# --- View Mode 1: Review Mode ---
if st.session_state.review_index is not None:
    rev_idx = st.session_state.review_index
    q_data = st.session_state.question_bank[rev_idx]
    att = st.session_state.attempts[rev_idx]
    q_type = q_data.get("question_type", "multiple_choice_single_answer")
    correct_ans = q_data["correct_answer"]
    user_ans = att["user_choice"]

    st.warning("🔍 **Review Mode**")
    st.caption(
        f"{q_data.get('section', 'Assessment')} • ID: {q_data.get('question_number', rev_idx + 1)}"
    )
    st.markdown(f"### {q_data['question']}")

    # Render Options based on Question Type
    if q_type == "ordering":
        st.markdown("##### Correct Order:")
        for i, opt in enumerate(correct_ans):
            clean_opt = re.sub(r"^[A-Z][\.\-\)]\s*", "", opt).strip()
            st.markdown(f"<div class='review-item review-correct'>✅ <strong>{i+1}.</strong> {clean_opt}</div>", unsafe_allow_html=True)

        if not att["is_correct"]:
            st.markdown("##### Your Submission:")
            for i, opt in enumerate(user_ans):
                st.markdown(f"<div class='review-item review-incorrect'>❌ <strong>{i+1}.</strong> {opt}</div>", unsafe_allow_html=True)

    elif q_type == "multi_select":
        for opt in q_data["options"]:
            is_correct_opt = opt in correct_ans
            is_user_opt = opt in user_ans

            if is_correct_opt and is_user_opt:
                st.markdown(f"<div class='review-item review-correct'>✅ <strong>{opt}</strong> <em>(Correctly Selected)</em></div>", unsafe_allow_html=True)
            elif is_correct_opt and not is_user_opt:
                st.markdown(f"<div class='review-item review-incorrect'>⚠️ <strong>{opt}</strong> <em>(Missed Correct Option)</em></div>", unsafe_allow_html=True)
            elif not is_correct_opt and is_user_opt:
                st.markdown(f"<div class='review-item review-incorrect'>❌ <strong>{opt}</strong> <em>(Incorrectly Selected)</em></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='review-item review-neutral'>{opt}</div>", unsafe_allow_html=True)

    else:
        for opt in q_data["options"]:
            if opt == correct_ans:
                st.markdown(f"<div class='review-item review-correct'>✅ <strong>{opt}</strong> <em>(Correct Answer)</em></div>", unsafe_allow_html=True)
            elif opt == user_ans and not att["is_correct"]:
                st.markdown(f"<div class='review-item review-incorrect'>❌ <strong>{opt}</strong> <em>(Your Choice)</em></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='review-item review-neutral'>{opt}</div>", unsafe_allow_html=True)

    st.write("")
    if q_data.get("explanation"):
        st.info(f"**Explanation:** {q_data['explanation']}")

    st.markdown("#### 🤖 AI Revision Prompt")

    user_choice_str = "\n- ".join(user_ans) if isinstance(user_ans, list) else user_ans
    correct_ans_str = "\n- ".join(correct_ans) if isinstance(correct_ans, list) else correct_ans

    revision_prompt = f"""I am studying this topic and answered a practice question incorrectly. Help me understand where my reasoning failed and explain the core concept in depth.

### Context:
- Section: {q_data.get('section', 'General Assessment')}
- Question: {q_data['question']}
- My Selected (Incorrect) Answer(s):\n{user_choice_str}
- Correct Answer(s):\n{correct_ans_str}
- Official Explanation: {q_data.get('explanation', 'None provided')}

### What I need from you:
1. Break down why my chosen option/sequence is incorrect or misleading.
2. Explain why the correct answer is valid.
3. Provide a concise mental model or rule of thumb to avoid this mistake in the future.
4. Give me 2 new scenario-based follow-up questions to test my understanding."""

    render_copyable_prompt(revision_prompt)
    st.text_area("Prompt preview:", value=revision_prompt, height=220, disabled=True, label_visibility="collapsed")


# --- View Mode 2: Active Quiz Flow ---
else:
    pos = st.session_state.current_pos
    total_qns = len(st.session_state.order)

    if pos < total_qns:
        orig_idx = st.session_state.order[pos]
        q_data = st.session_state.question_bank[orig_idx]
        q_type = q_data.get("question_type", "multiple_choice_single_answer")

        st.caption(
            f"{q_data.get('section', 'Assessment')} • Question {pos + 1} of {total_qns}"
        )
        st.markdown(f"### {q_data['question']}")

        selected = None

        # Render Question Input Based on Type
        if q_type == "multiple_choice_single_answer":
            selected = st.radio(
                "Select an option:",
                q_data["options"],
                key=f"active_q_{orig_idx}_radio",
                label_visibility="collapsed",
                disabled=st.session_state.current_answered,
            )

        elif q_type == "multi_select":
            st.markdown("**(Select all that apply)**")
            selected = []
            for i, opt in enumerate(q_data["options"]):
                if st.checkbox(opt, key=f"active_q_{orig_idx}_check_{i}", disabled=st.session_state.current_answered):
                    selected.append(opt)

        elif q_type == "ordering":
            if st.session_state.current_answered:
                st.markdown("##### Your Submitted Sequence:")
                submitted_order = st.session_state.attempts[orig_idx]["user_choice"]

                static_html = "<div class='submitted-order-box'>"
                static_html += "<br>".join([f"<strong>{i+1}.</strong> {item}" for i, item in enumerate(submitted_order)])
                static_html += "</div>"
                st.markdown(static_html, unsafe_allow_html=True)
                selected = submitted_order
            else:
                if HAS_SORTABLES:
                    st.markdown("**(Drag and drop the options below to establish the correct vertical sequence)**")

                    one_item_per_row_style = """
                        .sortable-container-body {
                            display: flex;
                            flex-direction: column !important;
                        }
                        .sortable-item {
                            width: 100% !important;
                        }
                    """

                    sortable_data = [
                        {"header": "⬇️ Sort items here (1st at the Top, Last at the Bottom)", "items": q_data["options"]}
                    ]

                    res = sort_items(
                        sortable_data,
                        multi_containers=True,
                        custom_style=one_item_per_row_style,
                        key=f"active_q_{orig_idx}_order"
                    )

                    selected = res[0]["items"] if res else q_data["options"]

                    st.markdown("##### 📋 Your Current Sequence:")
                    sequence_html = "<div class='submitted-order-box'>"
                    sequence_html += "<br>".join([f"<strong>{i+1}.</strong> {item}" for i, item in enumerate(selected)])
                    sequence_html += "</div>"
                    st.markdown(sequence_html, unsafe_allow_html=True)

                else:
                    st.markdown("**(Select the options in the correct sequence)**")
                    st.caption("💡 Tip: Run `pip install streamlit-sortables` to enable drag-and-drop.")
                    selected = st.multiselect(
                        "Select options in order",
                        q_data["options"],
                        key=f"active_q_{orig_idx}_order",
                        label_visibility="collapsed"
                    )

        st.write("")
        submit_col, next_col = st.columns([1, 1])

        with submit_col:
            if not st.session_state.current_answered:
                if st.button("Submit Answer", use_container_width=True, type="primary"):
                    st.session_state.current_answered = True
                    correct_answer = q_data["correct_answer"]

                    # Grade Based on Question Type
                    if q_type == "multi_select":
                        is_correct = set(selected) == set(correct_answer)

                    elif q_type == "ordering":
                        clean_correct = [re.sub(r"^[A-Z][\.\-\)]\s*", "", c).strip() for c in correct_answer]
                        clean_selected = [s.strip() for s in selected]
                        is_correct = clean_selected == clean_correct

                    else:
                        is_correct = selected == correct_answer

                    st.session_state.attempts[orig_idx] = {
                        "user_choice": selected,
                        "is_correct": is_correct,
                    }
                    st.rerun()

        # Render Post-Submit Feedback
        if st.session_state.current_answered:
            att = st.session_state.attempts[orig_idx]
            correct_ans = q_data["correct_answer"]

            if att["is_correct"]:
                st.success("✅ **Correct!**")
            else:
                if q_type == "ordering":
                    clean_correct = [re.sub(r"^[A-Z][\.\-\)]\s*", "", c).strip() for c in correct_ans]
                    st.error("❌ **Incorrect.** The correct order was:\n\n" + "\n".join([f"**{i+1}.** {o}" for i, o in enumerate(clean_correct)]))
                elif q_type == "multi_select":
                    st.error("❌ **Incorrect.** The correct options were:\n\n- " + "\n- ".join(correct_ans))
                else:
                    st.error(f"❌ **Incorrect.** The correct answer was: **{correct_ans}**")

            if q_data.get("explanation"):
                st.info(f"**Explanation:** {q_data['explanation']}")

            with next_col:
                st.button("Next Question ➡", use_container_width=True, type="primary", on_click=cb_next_question)

    else:
        st.header("🎉 Quiz Finished!")
        st.markdown(
            f"### Final Score: **{total_correct} / {total_qns}** ({pct_score:.1f}%)"
        )
        st.button("Restart Quiz", type="primary", on_click=cb_restart)
