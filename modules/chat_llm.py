import streamlit as st
import time
import requests

# Function to call Flask backend for semantic search
def semantic_search(query, rag_url):
    response = requests.post(f"{rag_url}/sem_search", json={"query": query})
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Error in semantic search: {response.json().get('error', 'Unknown error')}")
        return None

# Function to call Flask backend for question answering
def ask_question(query, rag_url):
    response = requests.post(f"{rag_url}/answer", json={"query": query})
    if response.status_code == 200:
        return response.json()['response']
    else:
        st.error(f"Error in question answering: {response.json().get('error', 'Unknown error')}")
        return None

# Function to call Flask backend for indexing documents
def index_documents(source_type, source_path, 
                    doc_title, additional_info, comments,
                    rag_url):
    
    response = requests.post(f"{rag_url}/index", json={
        "source_type": source_type,
        "source_path": source_path,
        "doc_title": doc_title,
        "additional_info": additional_info,
        "comments": comments,
    })
    if response.status_code == 200 and response.json().get('message') == "Indexing completed":
        st.success("Indexing completed successfully!")
    else:
        st.error(f"Error in indexing: {response.json().get('error', 'Unknown error')}")

# Function to get indexing history from Flask backend
def get_index_history(rag_url):
    response = requests.get(f"{rag_url}/index_history")
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