import streamlit as st
from langgraph_tool_backend import chatbot
from langchain_core.messages import HumanMessage, AIMessage
import uuid

# **************************************** utility functions *************************

def generate_thread_id():
    # UUID ko string me convert kar lete hain taaki sidebar me clean dikhe aur compare karne me asani ho
    return str(uuid.uuid4())

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id
    add_thread(thread_id)
    st.session_state['message_history'] = []

def add_thread(thread_id):
    if thread_id not in st.session_state['chat_threads']:
        st.session_state['chat_threads'].append(thread_id)

def load_conversation(thread_id):
    state = chatbot.get_state(config={'configurable': {'thread_id': thread_id}})
    # Check if messages key exists in state values, return empty list if not
    if state and state.values:
        return state.values.get('messages', [])
    return []


# **************************************** Session Setup ******************************
if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in st.session_state:
    st.session_state['chat_threads'] = []

add_thread(st.session_state['thread_id'])


# **************************************** Sidebar UI *********************************

st.sidebar.title('LangGraph Chatbot')

if st.sidebar.button('New Chat'):
    reset_chat()
    st.rerun()

st.sidebar.header('My Conversations')

# Threads ko display karne ke liye loop (latest upar ya neeche ke mutabiq)
for thread_id in st.session_state['chat_threads'][::-1]:
    # Thread ID ka chota/readable version button par dikhayein
    short_id = thread_id[:8] + "..."
    if st.sidebar.button(short_id, key=thread_id):
        st.session_state['thread_id'] = thread_id
        messages = load_conversation(thread_id)

        temp_messages = []
        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = 'user'
            else:
                role = 'assistant'
            temp_messages.append({'role': role, 'content': msg.content})

        st.session_state['message_history'] = temp_messages
        # Thread switch hone par app ko rerun karein taaki chat history turant dikhe
        st.rerun()


# **************************************** Main UI ************************************

# Loading the conversation history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])  # st.text ki jagah st.markdown

user_input = st.chat_input('Type here')

if user_input:
    # First add the message to message_history
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.markdown(user_input)

    CONFIG = {'configurable': {'thread_id': st.session_state['thread_id']}}

    # Assistant response stream
    with st.chat_message("assistant"):
        def ai_only_stream():
            for message_chunk, metadata in chatbot.stream(
                {"messages": [HumanMessage(content=user_input)]},
                config=CONFIG,
                stream_mode="messages"
            ):
                if isinstance(message_chunk, AIMessage) and message_chunk.content:
                    content = message_chunk.content
                    # Gemini/LangChain content handling (string ya list check)
                    if isinstance(content, str):
                        yield content
                    elif isinstance(content, list):
                        for item in content:
                            if isinstance(item, dict) and 'text' in item:
                                yield item['text']

        ai_message = st.write_stream(ai_only_stream())
        
        # Ensure ai_message is a clean string
        if not isinstance(ai_message, str):
            ai_message = str(ai_message)

    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})