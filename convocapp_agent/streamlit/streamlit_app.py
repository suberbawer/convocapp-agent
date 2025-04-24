import os
import streamlit as st

from dotenv import load_dotenv

from convocapp_agent.clients.llm import call_model
from prompts.prompt_builder import render_prompt

st.set_page_config(page_title="⚽ Match Agent Chat", layout="centered")

st.title("🤖 Match Agent Chat")
load_dotenv()
base_url = os.getenv("BASE_URL")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display chat history
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# User input
user_input = st.chat_input("Type your message here...")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Build MCP payload
    payload = {
        "context": {
            "messages": [{"role": "user", "content": user_input}],
            "task": "classify_action_match",
            "metadata": {},
        }
    }

    # Call match-agent
    try:
        with st.spinner("Thinking..."):
            prompt = render_prompt("classify.txt.tmpl", user_input=user_input)
            result = call_model(prompt, "classify_action_match")

        st.session_state.chat_history.append({"role": "assistant", "content": result})

        with st.chat_message("assistant"):
            st.markdown(result)

    except Exception as e:
        st.error(f"❌ Error: {e}")
