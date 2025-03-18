################################
####### Chatbot ########
################################

# app
import streamlit as st
# general
import os
import datetime
import random
import time
import requests
# configurations
from modules.gral_config import page_config

# processing
import pandas as pd
import numpy as np
pd.options.display.float_format = '{:.2f}'.format
# local components
from modules.gral_comp import title
# local styles
from styles.basics import hide, lg_color, cont_padding

################################
### CONFIG
st.set_page_config(**page_config)

### STYLES
st.markdown(lg_color(".st-emotion-cache-1dp5vir.ezrtsby1"), unsafe_allow_html=True)  # line
st.markdown(hide(".st-emotion-cache-zq5wmm.ezrtsby0"), unsafe_allow_html=True)       # options & deploy button
st.markdown(cont_padding(".block-container.st-emotion-cache-z5fcl4.ea3mdgi5"), unsafe_allow_html=True)

################################
### HEADER
img = "images/DALLE-chatbot_cut.jpg"
st.image(img, use_container_width=True)
st.header("Assistant Bot")

################################
# Base URL for the Flask app
BASE_URL = 'http://localhost:8080'

# Function to call Flask backend for semantic search
def semantic_search(query):
    response = requests.post(f"{BASE_URL}/sem_search", json={"query": query})
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error in semantic search: {response.json().get('error', 'Unknown error')}")
        return None

# Function to call Flask backend for question answering
def ask_question(query):
    response = requests.post(f"{BASE_URL}/answer", json={"query": query})
    if response.status_code == 200:
        return response.json()['response']
    else:
        st.error(f"Error in question answering: {response.json().get('error', 'Unknown error')}")
        return None

# Function to call Flask backend for indexing documents
def index_documents(source_type, source_path, doc_title, additional_info, comments):
    response = requests.post(f"{BASE_URL}/index", json={
        "source_type": source_type,
        "source_path": source_path,
        "doc_title": doc_title,
        "additional_info": additional_info,
        "comments": comments,
    })
    if response.status_code == 200:
        st.success("Indexing completed successfully!")
    else:
        st.error(f"Error in indexing: {response.json().get('error', 'Unknown error')}")

# Function to get indexing history from Flask backend
def get_index_history():
    response = requests.get(f"{BASE_URL}/index_history")
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error retrieving indexing history: {response.json().get('error', 'Unknown error')}")
        return []

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Function to simulate streaming of assistant response
def response_generator(response_text):
    for word in response_text.split():
        yield word + " "
        time.sleep(0.05)

# Create tabs for Chatbot, Index Documents, and Indexing History
chat_tab, index_tab, history_tab = st.tabs(["Chatbot", "Search", "Index Documents", "Indexing History"])

################################
# Chatbot Tab
with chat_tab:
    st.subheader("Chatbot")
    st.markdown("Ask me about customs :female-police-officer:")

    ################################
    # 1. Display existing messages FIRST
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    ################################
    # 2. Then capture new user input
    # Accept user input for chat
    if prompt := st.chat_input("Ask something..."):
        # Display user's message in the chat
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Determine whether the query is for semantic search or QA
        if prompt.lower().startswith("search:"):
            query = prompt[7:]
            response_data = semantic_search(query)
            if response_data:
                response_text = "\n".join([
                    f"Node: {item['node']}, Score: {item['score']}" 
                    for item in response_data
                ])
            else:
                response_text = "No results found."
        else:
            response_text = ask_question(prompt)

        # Display the assistant's response with a stream-like effect
        with st.chat_message("assistant"):
            if response_text:
                # Simulate streaming
                response_stream = response_generator(response_text)
                streamed_text = ""
                text_placeholder = st.empty()  # Placeholder for incremental text
                for token in response_stream:
                    streamed_text += token
                    text_placeholder.markdown(streamed_text)
            else:
                st.error("No response from the assistant.")

        # Store assistant message in session
        st.session_state.messages.append({"role": "assistant", "content": response_text})


################################
# Indexer Tab
with index_tab:
    st.subheader("Indexer")
    st.markdown("Feed the knowledge database.")
    # Input fields for document indexing
    source_type = st.selectbox("Source Type", ["pdf", "webpage", "directory"])
    source_path = st.text_input("Enter the document path or URL")
    doc_title = st.text_input("Enter the document title")
    additional_info  = st.text_input("Enter additional information")
    comments = st.text_input("Enter the other comments")
    # Button to trigger indexing
    if st.button("Index"):
        if source_path:
            index_documents(source_type, source_path, doc_title, additional_info, comments)
        else:
            st.warning("Please provide a valid document path or URL")

################################
# History Tab
with history_tab:
    st.subheader("Indexer")
    st.markdown("Review the indexing history.")
    # Button to refresh the history
    if st.button("Refresh History"):
        history_data = get_index_history()
        if history_data:
            df = pd.DataFrame(history_data)
            # Format the indexed_date column as datetime if available
            if "indexed_date" in df.columns:
                df["indexed_date"] = pd.to_datetime(df["indexed_date"])
            st.dataframe(df)

