import streamlit as st
from chat_bot_ui.core.config import config
import requests
#--------------------------------------------------------------
st.set_page_config(
    page_title="amazon shopping assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)
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
if "used_context" not in st.session_state:
    st.session_state.used_context = []
#--------------------------------------------------------------
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
#--------------------------------------------------------------
with st.sidebar:
    suggestions_tab, =  st.tabs(["Suggestions"])
    with suggestions_tab:
        if st.session_state.used_context:
            for idx, item in enumerate(st.session_state.used_context):
                st.caption(item.get('description','No description'))
                if 'image_url' in item:
                    st.image(item["image_url"], width=250)
                st.caption(f"Price: {item['price']} USD")
                st.divider()
        else:
            st.info("No suggestions yet")
#--------------------------------------------------------------
if prompt := st.chat_input("Enter a message:"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        state, output = api_call("post", "http://api-app:8000/rag", json={"query": prompt})
        answer = output["answer"]
        used_context= output["used_context"]
        st.session_state.used_context= used_context
        st.write(answer)
    st.session_state.messages.append({"role": "assistant", "content": answer})
    st.rerun()
#--------------------------------------------------------------