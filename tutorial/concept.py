import streamlit as st

### callbacks

def callback(input):
    print(input)

input = st.text_input("Enter text")
submit = st.button("Submit")
if submit:
    option = st.checkbox("input display?", 
                         on_change=callback,
                         args=(input,)) #tupple format

# actions available: on_change, on_click
    
### session states
    
text = ":dog:"

if "click" not in st.session_state:
    st.session_state.click = False
else:
    if st.session_state.click == False:
        text= ":cat:"
        st.session_state.click = True
    else:
        text = ":dog:"
        st.session_state.click = False

btn = st.button(text)

### cache st

# first time execution

import time

@st.cache_data(suppress_st_warning=True) # vs. cache_resource (??)
def printer():
    st.write("Running...")
    time.sleep(3)
    return "Message"

st.write(printer())

# cache_data -> for data loading, queries, api calls, pre-processing, transformations and model execution

# cache_resource -> for caching database connections and ML models

from transformers import pipeline

@st.cache_resource  # 👈 Add the caching decorator
def load_model():
    return pipeline("sentiment-analysis")

model = load_model()

query = st.text_input("Your query", value="I love Streamlit! 🎈")
if query:
    result = model(query)[0]  # 👈 Classify the query text
    st.write(result)