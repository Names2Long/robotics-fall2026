"""Launch Lab 8 with streamlit run app.py."""
from lab.application import main

if __name__ == '__main__':
    import streamlit as st
    st.navigation([st.Page(main,title='Lab 8')],position='hidden').run()
