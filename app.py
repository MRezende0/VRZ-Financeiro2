import streamlit as st
import pandas as pd
import os

# Importar módulos de utilidades
from utils.ssl_patch import patch_ssl
from utils.styling import setup_page_config, local_css

# Importar módulos de autenticação
from modules.auth.login import login_screen

# Importar módulos de páginas
from modules.pages.dashboard import dashboard
from modules.pages.transacoes import registrar
from modules.pages.projetos import projetos
from modules.pages.funcionarios import funcionarios
from modules.pages.relatorios import relatorios
from modules.pages.admin import admin

# Importar módulos de dados
from modules.data.sheets import carregar_dados_iniciais, verificar_todas_planilhas

# Importar módulos de UI
from modules.ui.layout import create_sidebar

# Aplicar patch SSL para resolver problemas de certificado
patch_ssl()

# Configuração inicial da página
setup_page_config()

# Aplicar estilos personalizados
local_css()

# Criar pasta de backups se não existir
backup_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backups")
os.makedirs(backup_dir, exist_ok=True)

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

# Definir permissões de administrador (temporário, depois usar banco de dados)
if "admin" not in st.session_state:
    st.session_state.admin = True  # Temporariamente todos são admin

# Cache para a planilha
if 'spreadsheet' not in st.session_state:
    st.session_state.spreadsheet = None

# Cache para as worksheets
if 'worksheets_cache' not in st.session_state:
    st.session_state.worksheets_cache = {}

def main_app():
    """
    Função principal que gerencia a navegação entre as diferentes páginas da aplicação.
    """
    # Usar o layout padronizado para a sidebar
    menu_option = create_sidebar()

    # Navegar para a página selecionada
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
    elif menu_option == "Admin":
        admin()

if __name__ == "__main__":
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
    
    # Verificar se precisamos carregar dados após o login
    if st.session_state.get("carregar_dados_apos_login", False) and not st.session_state.get("dados_carregados", False):
        # Verificar a estrutura das planilhas antes de carregar os dados
        with st.spinner("Verificando estrutura das planilhas..."):
            verificar_todas_planilhas()
        
        # Iniciar carregamento em segundo plano sem bloquear a interface
        with st.spinner("Carregando dados..."):
            carregar_dados_iniciais()
        
        # Limpar a flag
        st.session_state.carregar_dados_apos_login = False

    if st.session_state["logged_in"]:
        main_app()
    else:
        login_screen()