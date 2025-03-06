import streamlit as st
# local compenents
from modules.gral_config import page_config
from modules.gral_comp import title
# local styles
from styles.basics import hide, lg_color

### site configuration
st.set_page_config(**page_config)

### styles
st.markdown(lg_color(".st-emotion-cache-1dp5vir.ezrtsby1"), unsafe_allow_html=True) # line
st.markdown(hide(".st-emotion-cache-zq5wmm.ezrtsby0"), unsafe_allow_html=True) # options & deploy botton

### content

def main():
    title()
    st.header("Operations management")

if __name__ == "__main__":
    main()