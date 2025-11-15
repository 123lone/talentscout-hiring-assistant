# logic.py
import os
import openai
import json
import time
import re
from prompts import (
    SYSTEM_PROMPT_BASE,
    PROMPT_COLLECT_INFO,
    PROMPT_GENERATE_QS,
    PROMPT_FOLLOWUP,
    PROMPT_FALLBACK,
)
from utils import validate_email, validate_phone, save_to_json

# Exit keywords
EXIT_KEYWORDS = {"exit", "quit", "bye", "stop", "done", "thank you", "thanks"}

# Required fields for a submission
REQUIRED_FIELDS = ["full_name", "email", "phone", "years_experience", "desired_positions", "current_location", "tech_stack"]

def initialize_session():
    import streamlit as st
    if "history" not in st.session_state:
        st.session_state["history"] = []
    if "collected" not in st.session_state:
        st.session_state["collected"] = {}
    if "live_mode" not in st.session_state:
        # try enabling live mode if OPENAI_API_KEY set
        st.session_state["live_mode"] = bool(os.environ.get("OPENAI_API_KEY"))
    if "conversation_stage" not in st.session_state:
        st.session_state["conversation_stage"] = "greeting"  # or "collecting", "tech_questions", "finished"
    if "awaiting_field" not in st.session_state:
        st.session_state["awaiting_field"] = None
    if "input_text" not in st.session_state:
        st.session_state["input_text"] = ""
    if "last_generated_questions" not in st.session_state:
        st.session_state["last_generated_questions"] = {}
    if "storage_file" not in st.session_state:
        st.session_state["storage_file"] = os.environ.get("STORAGE_FILE", "data/submissions.json")

def add_history(role, content):
    import streamlit as st
    st.session_state['history'].append({"role": role, "content": content})

def call_llm(messages, stream=False):
    """
    Call OpenAI ChatCompletion API. If OPENAI_API_KEY not set, run mock response.
    """
    import streamlit as st
    if not st.session_state["live_mode"]:
        # Mock behavior: simple rule-based responses
        return mock_response(messages)

    openai.api_key = os.environ.get("OPENAI_API_KEY")
    model = os.environ.get("OPENAI_MODEL", "gpt-4")
    try:
        resp = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=0.2,
            max_tokens=800
        )
        return resp['choices'][0]['message']['content'].strip()
    except Exception as e:
        # fallback to a readable error message
        return f"⚠️ [LLM error] {str(e)}"

def mock_response(messages):
    """
    When API key not set. Very simple mock logic:
    - If system/greeting present -> provide greeting & ask first info
    - If asked to generate Qs -> produce simple questions
    - Otherwise: fallback
    """
    # Infer intent from latest user message
    last_user = None
    for m in reversed(messages):
        if m['role'] == 'user':
            last_user = m['content'].lower()
            break
    if last_user is None:
        return "Hello! I am TalentScout's hiring assistant."

    if "/start" in last_user or "hello" in last_user or "hi" in last_user:
        return "Hello! I will collect your basic details (name, email, phone, experience, desired positions, location, tech stack). Let's start: What is your full name?"
    if "python" in last_user or "django" in last_user:
        # simple generate: 3 questions per tech
        techs = re.split(r'[,\n]+', last_user)
        techs = [t.strip().title() for t in techs if t.strip()]
        out = ""
        for t in techs:
            out += f"**{t} Questions**\n"
            out += "1. Explain the core concept of " + t + ".\n"
            out += "2. Give a common interview question about " + t + ".\n"
            out += "3. Describe a performance consideration for " + t + ".\n\n"
        return out
    # default fallback
    return "I didn't fully understand that. Could you please rephrase or provide the requested info?"

def parse_tech_stack(text):
    # split on commas, semicolons, newlines
    parts = re.split(r'[,;\n]+', text)
    parts = [p.strip() for p in parts if p.strip()]
    return parts

def request_next_field():
    """Return the next field name to request based on what's missing"""
    import streamlit as st
    for field in REQUIRED_FIELDS:
        if field not in st.session_state['collected']:
            return field
    return None

def format_field_prompt(field):
    prompts = {
        "full_name": "Please share your full name.",
        "email": "Please provide your email address.",
        "phone": "Please provide your phone number (include country code if outside India).",
        "years_experience": "How many years of professional experience do you have? (e.g., 2, 5.5)",
        "desired_positions": "Which position(s) are you applying for or interested in?",
        "current_location": "What is your current location (city, country)?",
        "tech_stack": "Please list your tech stack (comma-separated): programming languages, frameworks, databases, tools."
    }
    return prompts.get(field, "Please provide the information.")

def handle_user_message(user_text):
    """
    Main orchestrator: receives user text, updates session, returns assistant reply.
    Returns (assistant_reply, finished_bool)
    """
    import streamlit as st
    text = user_text.strip()
    # check exit keywords
    if text.lower() in EXIT_KEYWORDS:
        final_msg = "Thanks for your time! Our recruiters will review your submission and contact you soon. Goodbye."
        add_history("user", user_text)
        add_history("assistant", final_msg)
        st.session_state["conversation_stage"] = "finished"
        return final_msg, True

    # add the user's message
    add_history("user", user_text)

    # starting flow
    if st.session_state["conversation_stage"] == "greeting":
        # greet and ask first field
        system = SYSTEM_PROMPT_BASE
        greet_msg = "Hello! I'm TalentScout's Hiring Assistant. I will collect a few details and ask technical questions based on your tech stack. Let's begin."
        add_history("assistant", greet_msg)
        # ask first required info
        next_field = request_next_field()
        field_prompt = format_field_prompt(next_field)
        add_history("assistant", field_prompt)
        st.session_state["conversation_stage"] = "collecting"
        st.session_state["awaiting_field"] = next_field
        return greet_msg + " " + field_prompt, False

    # collecting info stage
    if st.session_state["conversation_stage"] == "collecting":
        # if awaiting a specific field, try to validate & store
        field = st.session_state.get("awaiting_field")
        stored_msg = ""
        if field:
            val = text
            # basic validation for email/phone
            if field == "email":
                if not validate_email(val):
                    reply = "That doesn't look like a valid email. Please provide a correct email address."
                    add_history("assistant", reply)
                    return reply, False
            if field == "phone":
                if not validate_phone(val):
                    reply = "That doesn't look like a valid phone number. Please provide digits with country code or try another format."
                    add_history("assistant", reply)
                    return reply, False
            if field == "years_experience":
                # accept float/integer
                try:
                    y = float(val)
                    if y < 0:
                        raise ValueError()
                    val = str(y)
                except:
                    reply = "Please provide years of experience as a number (e.g., 2 or 3.5)."
                    add_history("assistant", reply)
                    return reply, False
            if field == "tech_stack":
                # normalize list
                val_list = parse_tech_stack(val)
                if not val_list:
                    reply = "Please provide at least one technology in your tech stack."
                    add_history("assistant", reply)
                    return reply, False
                val = ", ".join(val_list)
            # store
            st.session_state['collected'][field] = val
            stored_msg = f"Saved {field.replace('_',' ')}."
            add_history("assistant", stored_msg)

        # Ask next field or move to tech questions
        next_field = request_next_field()
        if next_field:
            field_prompt = format_field_prompt(next_field)
            add_history("assistant", field_prompt)
            st.session_state["awaiting_field"] = next_field
            return stored_msg + " " + field_prompt, False
        else:
            # all fields collected -> generate tech questions
            st.session_state["conversation_stage"] = "tech_questions"
            techs = st.session_state['collected'].get("tech_stack", "")
            add_history("assistant", "Thanks — generating technical questions based on your tech stack...")
            # prepare prompt
            tech_list = parse_tech_stack(techs)
            # Build generation prompt
            messages = [
                {"role":"system", "content": SYSTEM_PROMPT_BASE},
                {"role":"user", "content": PROMPT_GENERATE_QS.format(techs=", ".join(tech_list))}
            ]
            llm_output = call_llm(messages)
            add_history("assistant", llm_output)
            st.session_state["last_generated_questions"] = {"by_tech": tech_list, "raw": llm_output}
            # after generating, offer to ask follow-ups or conclude
            follow_msg = "I generated questions above. Do you want to answer them now, request a different difficulty, or finish the session?"
            add_history("assistant", follow_msg)
            st.session_state["awaiting_field"] = None
            return llm_output + "\n\n" + follow_msg, False

    # tech_questions stage: allow follow-up commands
    if st.session_state["conversation_stage"] == "tech_questions":
        # handle user requests: difficulty change, regenerate, answer question, or finish
        lower = text.lower()
        if "regenerate" in lower or "different" in lower or "new" in lower:
            techs = st.session_state['collected'].get("tech_stack", "")
            tech_list = parse_tech_stack(techs)
            messages = [
                {"role":"system", "content": SYSTEM_PROMPT_BASE},
                {"role":"user", "content": PROMPT_GENERATE_QS.format(techs=", ".join(tech_list) + " (please provide different/difficulty-adjusted questions)")}
            ]
            llm_output = call_llm(messages)
            add_history("assistant", llm_output)
            st.session_state["last_generated_questions"] = {"by_tech": tech_list, "raw": llm_output}
            return llm_output, False
        elif "answer" in lower or "i will answer" in lower or "i want to answer" in lower:
            reply = "Great — please paste your answers and I will append them to your submission (simulated)."
            add_history("assistant", reply)
            st.session_state["awaiting_field"] = "candidate_answers"
            return reply, False
        else:
            # generic follow-up: use LLM for short guidance or fallback
            messages = [
                {"role":"system", "content": SYSTEM_PROMPT_BASE},
                {"role":"user", "content": PROMPT_FOLLOWUP.format(user_input=text)}
            ]
            llm_output = call_llm(messages)
            add_history("assistant", llm_output)
            return llm_output, False

    # fallback default
    fallback = PROMPT_FALLBACK
    add_history("assistant", fallback)
    return fallback, False

def save_submission_if_complete():
    """
    Saves collected info + generated questions + candidate answers if present to JSON file.
    Returns True if saved.
    """
    import streamlit as st
    collected = st.session_state.get("collected", {})
    # simple check
    for f in REQUIRED_FIELDS:
        if f not in collected:
            return False
    submission = {
        "timestamp": int(time.time()),
        "collected": collected,
        "generated_questions": st.session_state.get("last_generated_questions", {}),
        "answers": collected.get("candidate_answers", None)
    }
    saved = save_to_json(submission, st.session_state["storage_file"])
    return saved
