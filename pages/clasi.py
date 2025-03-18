################################
####### Chatbot ########
################################

# app
import streamlit as st
# general
# import os
# import datetime
# import random
import time
import requests
# configutations
from modules.gral_config import page_config
# recourses

# processing
import pandas as pd
# import numpy as np
pd.options.display.float_format = '{:.2f}'.format
# # ploting
# import plotly.express as px
# import plotly.graph_objects as go
# local compenents
from modules.gral_comp import title
# local styles
from styles.basics import hide, lg_color, cont_padding

################################
################################
################################

### CONFIG
st.set_page_config(**page_config)

################################
################################
################################

### STYLES
st.markdown(lg_color(".st-emotion-cache-1dp5vir.ezrtsby1"), unsafe_allow_html=True) # line
st.markdown(hide(".st-emotion-cache-zq5wmm.ezrtsby0"), unsafe_allow_html=True) # options & deploy botton
st.markdown(cont_padding(".block-container.st-emotion-cache-z5fcl4.ea3mdgi5"), unsafe_allow_html=True)

################################
################################
################################

### HEADER
img = "images/DALLE-hs-classi_cut.jpg"
st.image(img, use_container_width=True)
st.header("HS Classification")

################################
################################
################################

### CONTENT

# FastAPI endpoint URL
API_URL = "http://localhost:8000/predict_info"

st.write("Enter a product description to get predicted HS Codes with additional information")

# User input for the product description
description = st.text_input("Product Description", value="apple iphone")

# Optional input for number of top predictions
topn = st.number_input("Number of top predictions", min_value=1, value=3, step=1)

if st.button("Predict HS Code"):
    if description:
        # Create payload for the POST request
        payload = {
            "description": description,
            "topn": topn
        }
        try:
            # Send a POST request to the FastAPI endpoint
            response = requests.post(API_URL, json=payload)
            if response.status_code == 200:
                data = response.json()
                predictions = data.get("predictions", [])
                if predictions:
                    for pred in predictions:
                        st.subheader(f"HS Code: {pred.get('predict')}")
                        st.write(f"**Score:** {pred.get('score')}")
                        hs_info = pred.get("hs_info", [])
                        if hs_info:
                            st.write("**HS Code Information:**")
                            for info in hs_info:
                                st.write(f"- {info}")
                        st.markdown("---")
                else:
                    st.info("No predictions were returned.")
            else:
                st.error(f"Error {response.status_code}: {response.text}")
        except Exception as e:
            st.error(f"An error occurred: {e}")
    else:
        st.warning("Please enter a product description.")