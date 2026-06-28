import streamlit as st
from chat_bot_ui.core.config import config
import requests

#--------------------------------------------------------------
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
#--------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi How can I help you today?"}]
#--------------------------------------------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
#--------------------------------------------------------------
if prompt := st.chat_input("Enter a message:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        response = api_call("post", "http://api-app:8000/rag", json={"query": prompt})
        answer = response[1]["answer"]
        st.write(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
#--------------------------------------------------------------