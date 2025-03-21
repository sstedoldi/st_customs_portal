################################
####### RAG CHATBOT ########
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
from modules.gral_config import back_url_config

# processing
import pandas as pd
import numpy as np
pd.options.display.float_format = '{:.2f}'.format
from modules.chat_llm import semantic_search, ask_question, \
                             index_documents, get_index_history, \
                             response_generator
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
rag_url = back_url_config["rag_url"]

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# Function to simulate streaming of assistant response
def response_generator(response_text):
    for word in response_text.split():
        yield word + " "
        time.sleep(0.05)

################################
# TABS
################################

chat_tab, search_tab, index_tab, history_tab = st.tabs([
    "Chatbot", "Semantic Search", "Index Documents", "Indexing History"
])

################################
# CHATBOT
with chat_tab:
    st.subheader("Chatbot")
    st.markdown("Ask about customs matters and get answers")

    # Display existing messages FIRST
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Then capture new user input
    if prompt := st.chat_input("Ask something..."):
        # Display user's message in the chat
        with st.chat_message("user"):
            st.markdown(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        # Use question answering for chatbot queries
        response_text = ask_question(prompt, rag_url=rag_url)

        # Display the assistant's response with a stream-like effect
        with st.chat_message("assistant"):
            if response_text:
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
# SEMANTIC SEARCH
with search_tab:
    st.subheader("Semantic Search")
    st.markdown("Enter a query to find documentation :gear:")
    
    search_query = st.text_input("Search Query", key="semantic_search_query")
    if st.button("Search", key="semantic_search_button"):
        if search_query:
            response_data = semantic_search(search_query, rag_url=rag_url)
            if response_data:
                rows = []
                # Iterate over each result returned from the backend
                for item in response_data:
                    node = item.get("node")
                    score = item.get("score")
                    # If the node is a dict, extract metadata; otherwise, fall back to string representation
                    if isinstance(node, dict):
                        metadata = node.get("metadata", {})
                        doc_title = metadata.get("doc_title", "N/A")
                        file_path = metadata.get("file_path", "N/A")
                        source_type = metadata.get("source_type", "N/A")
                        indexed_date = metadata.get("indexed_date", "N/A")
                        snippet = node.get("text", "")[:200]  # Show first 200 characters as a snippet
                    else:
                        # When node is not a dict, show its string representation
                        doc_title = "N/A"
                        file_path = "N/A"
                        source_type = "N/A"
                        indexed_date = "N/A"
                        snippet = str(node)[:200]
                    
                    rows.append({
                        "Document Title": doc_title,
                        "File Path": file_path,
                        "Source Type": source_type,
                        "Indexed Date": indexed_date,
                        "Score": score,
                        "Snippet": snippet
                    })
                
                # Display results as a DataFrame
                df = pd.DataFrame(rows)
                st.write("Retrieved Documents:")
                st.dataframe(df)
                
                # Additionally, display each document's full details in expandable sections
                st.write("Detailed Results:")
                for i, row in df.iterrows():
                    with st.expander(f"Document {i+1}: {row['Document Title']} (Score: {row['Score']})"):
                        st.write(row)
            else:
                st.info("No results found.")
        else:
            st.warning("Please enter a search query.")

################################
# INDEX DOCUMENTS
with index_tab:
    st.subheader("Index Documents")
    st.markdown("Feed the knowledge database :robot_face:")
    source_type = st.selectbox("Source Type", ["pdf", "webpage", "directory"])
    source_path = st.text_input("Enter the document path or URL")
    doc_title = st.text_input("Enter the document title")
    additional_info  = st.text_input("Enter additional information")
    comments = st.text_input("Enter the other comments")
    if st.button("Index"):
        if source_path:
            index_documents(source_type, 
                            source_path, 
                            doc_title, 
                            additional_info, 
                            comments,
                            rag_url=rag_url)
        else:
            st.warning("Please provide a valid document path or URL")

################################
# INDEXING HISTORY
with history_tab:
    st.subheader("Indexing History")
    st.markdown("Review the indexing history :floppy_disk:")
    if st.button("Refresh History"):
        history_data = get_index_history(rag_url=rag_url)
        if history_data:
            df = pd.DataFrame(history_data)
            if "indexed_date" in df.columns:
                df["indexed_date"] = pd.to_datetime(df["indexed_date"])
            st.dataframe(df)

