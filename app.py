import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os
from dotenv import load_dotenv

# Configuração inicial da página
st.set_page_config(
    page_title="VRZ Gestão Financeira",
    page_icon="💸",
    layout="wide",
)

# Carrega as variáveis do .env
load_dotenv()

USER_CREDENTIALS = {
    os.getenv("USER_EMAIL"): os.getenv("USER_PASSWORD"),
    os.getenv("ADMIN_EMAIL"): os.getenv("ADMIN_PASSWORD"),
}

# Estilo personalizado
def add_custom_css():
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
                background-color: #ffffff;
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

# Inicialização de dados
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "transactions" not in st.session_state:
    st.session_state["transactions"] = pd.DataFrame(
        columns=["Data", "Descrição", "Categoria", "Valor", "Tipo"]
    )

# Tela de Login
def login_screen():
    st.title("🔐 Login - VRZ Gestão Financeira")
    st.markdown("Por favor, insira suas credenciais para acessar o sistema.")

    # Formulário de login
    with st.form("login_form"):
        email = st.text_input("E-mail")
        password = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")

    if submit:
        if email in USER_CREDENTIALS and USER_CREDENTIALS[email] == password:
            st.success("Login realizado com sucesso! Redirecionando...")
            st.session_state["logged_in"] = True
            
        else:
            st.error("Credenciais inválidas. Verifique seu e-mail e senha.")

# Função para buscar informações do CNPJ
def buscar_cnpj(cnpj):
    url = f"https://receitaws.com.br/v1/cnpj/{cnpj}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        else:
            st.error("Não foi possível buscar informações do CNPJ. Verifique o número e tente novamente.")
            return None
    except Exception as e:
        st.error(f"Erro ao buscar CNPJ: {e}")
        return None

# Tela de consulta ao CNPJ
def consultar_cnpj():
    st.title("🔍 Busca de Informações pelo CNPJ")

    cnpj_input = st.text_input("Digite o CNPJ:", placeholder="Ex.: 00000000000191")
    if st.button("Buscar"):
        if cnpj_input:
            cnpj_data = buscar_cnpj(cnpj_input)
            if cnpj_data:
                st.write(f"**Nome da Empresa:** {cnpj_data.get('nome')}")
                st.write(f"**Situação:** {cnpj_data.get('situacao')}")
                st.write(f"**UF:** {cnpj_data.get('uf')}")
                st.write(f"**Atividade Principal:** {cnpj_data.get('atividade_principal')[0]['text']}")
            else:
                st.warning("Nenhum dado encontrado para o CNPJ informado.")
        else:
            st.warning("Por favor, insira um CNPJ válido.")

# Função para calcular o saldo
def calcular_saldo(transactions):
    receitas = transactions[transactions["Tipo"] == "Receita"]["Valor"].sum()
    despesas = transactions[transactions["Tipo"] == "Despesa"]["Valor"].sum()
    saldo = receitas - despesas
    return receitas, despesas, saldo

# Dashboard
def dashboard():
    st.title("📊 Dashboard Financeiro")
    
    # Dados e cálculos
    transactions = st.session_state["transactions"]
    receitas, despesas, saldo = calcular_saldo(transactions)

    # Layout de Cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="card"><h3>Receitas</h3><p>R$ {:,.2f}</p></div>'.format(receitas), unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="card"><h3>Despesas</h3><p style="color: #e74c3c;">R$ {:,.2f}</p></div>'.format(despesas), unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="card"><h3>Saldo</h3><p>R$ {:,.2f}</p></div>'.format(saldo), unsafe_allow_html=True)

    # Gráfico
    if not transactions.empty:
        fig = px.bar(
            transactions,
            x="Categoria",
            y="Valor",
            color="Tipo",
            title="Receitas e Despesas por Categoria",
            barmode="group",
            text="Valor",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhuma transação registrada ainda.")

# Tela do sistema (após login)
def main_app():
    st.sidebar.image("imagens/VRZ-LOGO-44.png")
    st.sidebar.title("Menu")
    menu_option = st.sidebar.radio(
        "Selecione a funcionalidade:",
        ("Dashboard", "Registrar Transação", "Relatórios", "Consultar CNPJ", "Sair")
    )

    if menu_option == "Dashboard":
        dashboard()

    elif menu_option == "Registrar Transação":
        st.title("💾 Registrar Transação")

        with st.form("form_transaction"):
            data = st.date_input("Data")
            descricao = st.text_input("Descrição")
            categoria = st.selectbox(
                "Categoria",
                ["Alimentação", "Moradia", "Transporte", "Lazer", "Salário", "Outros"]
            )
            valor = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
            tipo = st.radio("Tipo", ["Receita", "Despesa"])
            submit = st.form_submit_button("Salvar Transação")

        if submit:
            nova_transacao = pd.DataFrame(
                [[data, descricao, categoria, valor, tipo]],
                columns=["Data", "Descrição", "Categoria", "Valor", "Tipo"]
            )
            st.session_state["transactions"] = pd.concat(
                [st.session_state["transactions"], nova_transacao],
                ignore_index=True
            )
            st.success("Transação registrada com sucesso!")

    elif menu_option == "Relatórios":
        st.title("📈 Relatórios Financeiros")

        transactions = st.session_state["transactions"]

        if not transactions.empty:
            # Tabela de transações
            st.dataframe(transactions)

            # Gráficos
            fig_pie = px.pie(
                transactions,
                values="Valor",
                names="Categoria",
                title="Distribuição por Categoria",
                hole=0.5,
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        else:
            st.info("Nenhuma transação registrada ainda.")

    elif menu_option == "Consultar CNPJ":
        consultar_cnpj()

    elif menu_option == "Sair":
        st.session_state["logged_in"] = False
        st.success("Você saiu do sistema. Por favor, faça login novamente.")

# Controle de acesso ao sistema
if __name__ == "__main__":
    add_custom_css()
    if st.session_state["logged_in"]:
        main_app()
    else:
        login_screen()
