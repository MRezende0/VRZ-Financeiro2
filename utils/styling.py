import streamlit as st

def local_css():
    """
    Define o estilo personalizado para a aplicação Streamlit.
    """
    st.markdown("""
        <style>
            [data-testid="stSidebar"] {
                background-color: #f8f9fa;
                padding: 20px;
            }
            h1, h2, h3 {
                color: #ff6411;
                font-weight: bold;
            }
            .card {
                background-color: #f8f9fa;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
                margin: 10px;
                text-align: center;
            }
            .card h3 {
                margin-bottom: 10px;
                color: #333333;
            }
            .card p {
                font-size: 1.5rem;
                font-weight: bold;
                color: #4caf50;
            }
            .stApp {
                background-color: #fff;
            }
        </style>
    """, unsafe_allow_html=True)

def setup_page_config():
    """
    Configura as definições iniciais da página Streamlit.
    """
    st.set_page_config(
        page_title="VRZ Gestão Financeira",
        page_icon="imagens/VRZ-LOGO-50.png",
        layout="wide",
    )
