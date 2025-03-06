import streamlit as st
import time as ts
from datetime import time

def change():
    return

def click():
    return

options = ("op1","op2","op3")


def main():

    st.title("st element testing")

    st.sidebar.write("Sidebar")

    st.header("simple options")

    checkbox =st.checkbox("Single option",
                        value=False,
                        on_change=change(),
                        key="checkbox")

    radio_btn = st.radio("Vertical listed options", 
                        options=options,
                        on_change=change(),
                        key="radio_btn")

    btn = st.button("Click button",
                    on_click=click())

    select = st.selectbox("Single options selection",
                        options=options)

    multiselect = st.multiselect("Multi-options selection",
                                options=options)
    
    st.header("interactive")

    slide = st.slider("Slider", min_value=10, max_value=150)
    # print(slide)

    text = st.text_input("Text input", max_chars=100) # short texts
    # print(text)

    text_desc = st.text_area("Text area") # comments a multine-texts
    # print(text_desc)

    date = st.date_input("Date input")
    # print(date)

    time_in = st.time_input("Time input", value=time(0,0,0))
    # print(time_in)

    st.header("Progress bar")

    bar = st.progress(0) # it can be proper for story telling, chaging plots
    # for i in range(10):
    #     bar.progress((i+1)*10)
    #     ts.sleep(1)

    st.header("Forms")

    # form = st.form("Form_simple")
    # form.text_input("Text 1")
    # form.form_submit_button("Submit")

    def empty_check(vars):
        check = True
        for var in vars:
            if var=="":
                check = False
        return check

    with st.form("Form_with", clear_on_submit=True):
        st.header("Form with")
        col1, col2 = st.columns(2)
        text1 = col1.text_input("Text 1")
        text2 = col2.text_input("Text 2")
        text3 = st.text_input("Text 3")
        binding_vars = [text1, text2]
        submit = st.form_submit_button("Submit")
        if submit:
            if empty_check(binding_vars):
                st.success("Information sent!")
            else:
                st.warning("Mandatory fields are missing!")


if __name__ == "__main__":
    main()


