import streamlit as st
from utils.config import USER_CREDENTIALS

def login(email, senha):
    """
    Verifica as credenciais de login do usuário.
    
    Args:
        email: Email ou nome de usuário
        senha: Senha do usuário
    
    Returns:
        bool: True se as credenciais são válidas, False caso contrário
    """
    return email in USER_CREDENTIALS and USER_CREDENTIALS[email] == senha

def login_screen():
    """
    Exibe a tela de login e gerencia o processo de autenticação.
    """
    # st.title("VRZ Gestão Financeira")
    
    # Centraliza o formulário de login
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.image("imagens/logo-cocal.png", width=200)
        
        # Formulário de login
        with st.form("login_form"):
            email = st.text_input("Email ou Usuário")
            senha = st.text_input("Senha", type="password")
            submit_button = st.form_submit_button("Entrar")
            
            if submit_button:
                if login(email, senha):
                    st.session_state["logged_in"] = True
                    st.session_state["user_email"] = email
                    st.session_state.carregar_dados_apos_login = True
                    st.success("Login realizado com sucesso!")
                    st.rerun()  # Recarrega a página para mostrar o dashboard
                else:
                    st.error("Credenciais inválidas. Tente novamente.")
