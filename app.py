import streamlit as st
#from langchain_core.chat_history import InMemoryChatMessageHistory
#from chatbot import chat_bot
from Translation import translation
from tocket_bot3 import get_session_history, booking_chain, bot_Start, bot_End

# Title of the Streamlit app
st.title('Museum Ticket Chatbot')

lang_opt = st.sidebar.radio("Languages: ", ["English", "Hindi", "Tamil", "Malayalam", "Kanada", "Telugu", "Punjabi", "Urdu"])

lang_codes = {"English": "en", "Hindi": "hi", "Tamil": "ta", "Malayalam": "ml", "Kanada": "ka","Punjabi": "pa", "Telugu": "te", "Urdu": "ur"}

ln_code = lang_codes[lang_opt]

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hi, my name is Atwas. I am a museum ticket booking bot. Please tell me your queries."}]
if "history" not in st.session_state:
    st.session_state.history = {}

if "id" not in st.session_state:
    st.session_state.id = "1"


# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
default_text = translation("Enter Query", ln_code, 1)
u_prompt = st.chat_input(default_text)

if u_prompt:
    # Display user message in chat message container
    #prompt = translation(u_prompt, ln_code, 0)

    chat_history = get_session_history(st.session_state.id, st.session_state.history)

    if "inputs" not in st.session_state:
        st.session_state.inputs = {}
    

    reply, st.session_state.inputs, proceed = booking_chain(chat_history, u_prompt, st.session_state.inputs)
    st.write(st.session_state.inputs)

    with st.chat_message("user"):
        st.markdown(u_prompt)

    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": u_prompt})
    chat_history.add_user_message(u_prompt)
    
    sql_query = bot_Start(reply)
    st.write(sql_query)
    response = bot_End(reply, sql_query)

    

    #response = chat_bot(prompt)
    u_response = translation(response, ln_code, 0)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        st.markdown(f"{u_response}")
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": u_response})
else:
    with st.chat_message("assistant"):
        st.markdown("Start Convo")

if st.button("Restart"):
    st.session_state.messages = [{"role": "assistant", "content": "Hi I am a museum ticket booking bot. Please tell me your queries."}]
    # Display chat messages from history on app rerun
    st.session_state.inputs = {}
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
          
    st.rerun()

#test_query
#Book me 1 ticket for 3rd November 2024 at 3 pm to 5pm.Name is Ram and ticket type is Indian adult
