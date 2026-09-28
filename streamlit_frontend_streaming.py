import streamlit as st
from langgraph_backend import chatbot
from langchain_core.messages import HumanMessage

# st.session_state -> dict -> 
CONFIG = {'configurable': {'thread_id': 'thread-1'}}

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

# loading the conversation history
for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

user_input = st.chat_input('Type here')

if user_input:
    # first add the message to message_history
    st.session_state['message_history'].append({'role': 'user', 'content': user_input})
    with st.chat_message('user'):
        st.markdown(user_input)

    # Helper generator function to extract only the text content safely
    def generate_ai_response():
        for message_chunk, metadata in chatbot.stream(
            {'messages': [HumanMessage(content=user_input)]},
            config=CONFIG,
            stream_mode='messages'
        ):
            
            if hasattr(message_chunk, 'content') and message_chunk.content:
                content = message_chunk.content
                
                if isinstance(content, str):
                    yield content
                
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and 'text' in item:
                            yield item['text']

    with st.chat_message('assistant'):
        
        ai_message = st.write_stream(generate_ai_response())
        if not isinstance(ai_message, str):
            ai_message = str(ai_message)

    
    st.session_state['message_history'].append({'role': 'assistant', 'content': ai_message})