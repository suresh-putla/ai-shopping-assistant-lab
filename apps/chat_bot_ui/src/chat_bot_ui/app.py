import streamlit as st
from chat_bot_ui.core.config import config
import requests


def api_call(method, url, **kwargs):

    def _show_error_popup(message):
        st.session_state["error_popup"] = {
            "visible": True,
            "message": message
        }

    try:
        response = getattr(requests, method)(url, **kwargs)
        try:
        
            response_data = response.json()
        except requests.exceptions.JSONDecodeError:
            response_data = {"message": "Invalid response format from server"}

        if response.ok:
            return True, response_data
        return False, response_data
    except requests.exceptions.ConnectionError:
        _show_error_popup("Connection error. Check your network connection.")
        return False,  {"message": "Connection error"}
    except requests.exceptions.Timeout:
        _show_error_popup("Request Timeout")
        return False,  {"message": "Request Timeout"}
    except Exception as e:
        _show_error_popup(f"Unexpected error occured: {str(e)}")
        return False,  {"message": str(e)}



with st.sidebar:
    provider = st.selectbox("Select a provider", ["openai", "google"])
    if provider == "openai":
        model_name = st.selectbox("Select a model", ["gpt-5-nano", "gpt-4o-mini"])
    elif provider == "google":
        model_name = st.selectbox("Select a model", ["gemini-2.5-flash", "gemini-2.5-pro"])

    st.session_state.provider = provider
    st.session_state.model_name = model_name

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "how can I help you today?"}
    ]

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Enter a message:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = api_call("post", "http://api-app:8000/chat", json={"provider": st.session_state.provider,
                                                                "model_name": st.session_state.model_name,
                                                                "messages": st.session_state.messages})
       
        st.write(response[1]["message"])
    st.session_state.messages.append({"role": "assistant", "content": response[1]["message"]})
