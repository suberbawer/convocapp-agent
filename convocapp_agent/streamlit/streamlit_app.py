import os
import streamlit as st
import requests
import json

from dotenv import load_dotenv

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
            "task": "classification",
            "metadata": {},
        }
    }

    # Call match-agent
    try:
        with st.spinner("Thinking..."):
            response = requests.post(f"{base_url}/classify", json=payload)
            result = response.json()

        # Format agent response
        agent_reply = f"**Intent**: `{result['intent']}`\n\n"
        agent_reply += f"**Args**: ```json\n{json.dumps(result['args'], indent=2)}\n```\n"
        agent_reply += f"**Confidence**: `{result.get('confidence', 'N/A')}`"

        st.session_state.chat_history.append({"role": "assistant", "content": agent_reply})

        with st.chat_message("assistant"):
            st.markdown(agent_reply)

    except Exception as e:
        st.error(f"❌ Error: {e}")
