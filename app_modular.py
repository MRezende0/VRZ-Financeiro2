import streamlit as st
import pandas as pd
import os
import requests
import urllib3
import ssl
import functools

# Aplicar patch SSL para resolver problemas de certificado
def patch_ssl():
    # Criar um contexto SSL personalizado que ignora verificações de certificado
    old_merge_environment_settings = requests.Session.merge_environment_settings

    @functools.wraps(old_merge_environment_settings)
    def new_merge_environment_settings(self, url, proxies, stream, verify, cert):
        settings = old_merge_environment_settings(self, url, proxies, stream, verify, cert)
        settings['verify'] = False
        return settings

    requests.Session.merge_environment_settings = new_merge_environment_settings

    # Desabilitar avisos de SSL inseguro
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Configurar contexto SSL personalizado
    ssl._create_default_https_context = ssl._create_unverified_context
    
    # Configurar variável de ambiente para ignorar verificação SSL
    os.environ['PYTHONHTTPSVERIFY'] = '0'

# Aplicar patch SSL
patch_ssl()

# Configuração inicial da página
st.set_page_config(
    page_title="VRZ Gestão Financeira",
    page_icon="imagens/VRZ-LOGO-50.png",
    layout="wide",
)

# Estilo personalizado
def local_css():
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

local_css()

# Carrega credenciais dos Secrets
USER_CREDENTIALS = {
    "contato@vrzengenharia.com.br": "123",
    "20242025": "123",
}

# Inicialização dos dados locais
if 'local_data' not in st.session_state:
    st.session_state.local_data = {
        'receitas': pd.DataFrame(),
        'despesas': pd.DataFrame(),
        'projetos': pd.DataFrame(),
        'clientes': pd.DataFrame(),
        'categorias_receitas': pd.DataFrame(),
        'categorias_despesas': pd.DataFrame(),
        'fornecedor_despesas': pd.DataFrame(),
        'funcionarios': pd.DataFrame()
    }

# Cache para a planilha
if 'spreadsheet' not in st.session_state:
    st.session_state.spreadsheet = None

# Cache para as worksheets
if 'worksheets_cache' not in st.session_state:
    st.session_state.worksheets_cache = {}

# Importar módulos (todos os imports estão aqui para garantir que o Streamlit possa encontrá-los)
from utils.ssl_patch import patch_ssl
from utils.styling import local_css, setup_page_config
from utils.config import USER_CREDENTIALS, SHEET_ID, SHEET_GIDS, COLUNAS_ESPERADAS, FUNCIONARIOS

from modules.auth.login import login, login_screen
from modules.data.sheets import (
    conectar_sheets, carregar_dados_sheets, salvar_dados_sheets, 
    adicionar_linha_sheets, carregar_dados_sob_demanda, 
    carregar_dados_iniciais, carregar_dados_background
)

from modules.pages.dashboard import dashboard
from modules.pages.transacoes import registrar, registrar_receita, registrar_despesa, salvar_dados
from modules.pages.projetos import projetos, registrar_projeto, carregar_projetos, salvar_projetos
from modules.pages.clientes import clientes, registrar_cliente
from modules.pages.funcionarios import funcionarios, registrar_funcionario, calcular_produtividade
from modules.pages.categorias import registrar_categoria, salvar_categorias
from modules.pages.fornecedores import registrar_fornecedor
from modules.pages.relatorios import relatorios

def main_app():
    """
    Função principal que gerencia a navegação entre as diferentes páginas da aplicação.
    """
    st.sidebar.image("imagens/logo-cocal.png")
    st.sidebar.title("Menu")
    menu_option = st.sidebar.radio(
        "Selecione a funcionalidade:",
        ("Dashboard", "Registrar", "Projetos", "Funcionários", "Relatórios")
    )

    # Botão "Sair" na parte inferior da sidebar
    st.sidebar.markdown("---")  # Linha separadora
    if st.sidebar.button("Sair", key="sair"):
        st.session_state["logged_in"] = False
        st.success("Você saiu do sistema.")
        st.rerun()  # Atualiza a página para voltar à tela de login

    if menu_option == "Dashboard":
        dashboard()
    elif menu_option == "Registrar":
        registrar()
    elif menu_option == "Projetos":
        projetos()
    elif menu_option == "Funcionários":
        funcionarios()
    elif menu_option == "Relatórios":
        relatorios()

if __name__ == "__main__":
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    
    # Verificar se precisamos carregar dados após o login
    if st.session_state.get("carregar_dados_apos_login", False) and not st.session_state.get("dados_carregados", False):
        # Iniciar carregamento em segundo plano sem bloquear a interface
        carregar_dados_iniciais()
        # Limpar a flag
        st.session_state.carregar_dados_apos_login = False

    if st.session_state["logged_in"]:
        main_app()
    else:
        login_screen()
