import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os
from dotenv import load_dotenv

########################################## CONFIGURAÇÃO ##########################################

# Configuração inicial da página
st.set_page_config(
    page_title="VRZ Gestão Financeira",
    page_icon="💸",
    layout="wide",
)

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

########################################## CREDENCIAIS ##########################################

# Carrega credenciais dos Secrets
USER_CREDENTIALS = {
    st.secrets["USER_EMAIL"]: st.secrets["USER_PASSWORD"],
    st.secrets["ADMIN_EMAIL"]: st.secrets["ADMIN_PASSWORD"],
}

########################################## DADOS ##########################################

# Caminho do arquivo CSV para armazenar as transações
df_receitas = pd.read_csv("dados/receitas.csv")
df_despesas = pd.read_csv("dados/despesas.csv")
df_projetos = pd.read_csv("dados/projetos.csv")
df_clientes = pd.read_csv("dados/clientes.csv")
df_fornecedores = pd.read_csv("dados/fornecedores.csv")

########################################## LOGIN ##########################################

# Função de login
def login(email, senha):
    if email in USER_CREDENTIALS and USER_CREDENTIALS[email] == senha:
        return True
    return False

########################################## INICIALIZAÇÃO ##########################################

# Inicialização de dados
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if "transactions" not in st.session_state:
    st.session_state["transactions"] = pd.DataFrame(
        columns=["Data", "Descrição", "Categoria", "Valor", "Tipo"]
    )

########################################## TELA LOGIN ##########################################

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
            st.session_state["logged_in"] = True
            st.rerun()  # Atualiza a página para mostrar o conteúdo após o login
        else:
            st.error("Credenciais inválidas. Verifique seu e-mail e senha.")

########################################## TRANSAÇÃO ##########################################

# Função para carregar transações de receitas e despesas
def carregar_transacoes():
    if os.path.exists(df_receitas) and os.path.exists(df_despesas):
        # df_receitas = pd.read_csv(df_receitas)
        # df_despesas = pd.read_csv(df_despesas)
        # Garantir que as colunas estão alinhadas ou padronizadas
        return pd.concat([df_receitas, df_despesas], ignore_index=True)
    else:
        # Caso não exista, retorna DataFrame vazio com as colunas necessárias
        return pd.DataFrame(columns=["Data", "Descrição", "Categoria", "Valor", "Tipo"])

# Função para salvar transações de receitas e despesas
def salvar_transacoes(receitas, despesas):
    if not receitas.empty:
        receitas.to_csv(df_receitas, index=False)
    if not despesas.empty:
        despesas.to_csv(df_despesas, index=False)

# Inicialização de dados
if "transactions" not in st.session_state:
    st.session_state["transactions"] = carregar_transacoes()

# Separação de receitas e despesas (assumindo que a coluna 'Tipo' define se é Receita ou Despesa)
df_receitas = st.session_state["transactions"][st.session_state["transactions"]['Tipo'] == 'Receita']
df_despesas = st.session_state["transactions"][st.session_state["transactions"]['Tipo'] == 'Despesa']

# Função para adicionar uma nova transação
def adicionar_transacao(data, descricao, categoria, valor, tipo):
    nova_transacao = pd.DataFrame({
        "Data": [data],
        "Descrição": [descricao],
        "Categoria": [categoria],
        "Valor": [valor],
        "Tipo": [tipo]
    })
    
    if tipo == "Receita":
        df_receitas = pd.concat([df_receitas, nova_transacao], ignore_index=True)
    elif tipo == "Despesa":
        df_despesas = pd.concat([df_despesas, nova_transacao], ignore_index=True)

    # Salvar novamente as transações
    salvar_transacoes(df_receitas, df_despesas)

########################################## REGISTRAR TRANSAÇÃO ##########################################

# Função para registrar transação
def registrar_transacao(data, descricao, categoria, valor, tipo, detalhes_adicionais):
    nova_transacao = pd.DataFrame([[data, descricao, categoria, valor, tipo, detalhes_adicionais]], 
                                  columns=["Data", "Descrição", "Categoria", "Valor", "Tipo", "Detalhes"])
    
    # Adiciona a nova transação ao estado e salva no CSV
    st.session_state["transactions"] = pd.concat(
        [st.session_state["transactions"], nova_transacao], ignore_index=True
    )
    salvar_transacoes(st.session_state["transactions"])

# Função para salvar as transações (ajustada)
def salvar_transacoes(transacoes):
    # Implemente a lógica de salvar as transações no arquivo CSV
    pass

########################################## TELA - REGISTRAR TRANSAÇÃO ##########################################

def registrar_transacao_tela():
    st.title("💾 Registrar Transação")
    
    # Seleção do tipo de transação
    tipo = st.radio("Tipo de Transação", ["Receita", "Despesa"], key="tipo_transacao")
    
    # Atualiza as opções de categoria de acordo com o tipo selecionado
    if tipo == "Receita":
        dataContrato = st.date_input("Data")
        projeto = st.selectbox(df_projetos["Clientes"])
        descricao = st.text_input("Descrição")
        categoria = st.selectbox("Categoria", ["Salário", "Investimentos", "Freelance", "Outros"])
        detalhes_adicionais = st.text_input("Fonte da Receita", "Ex: Nome da empresa, cliente, etc.")
        valor = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
    else:
        data = st.date_input("Data")
        descricao = st.text_input("Descrição")
        categoria = st.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Lazer", "Outros"])
        detalhes_adicionais = st.text_input("Método de Pagamento", "Ex: Cartão, Dinheiro, Transferência")
        valor = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")

    if st.button("Salvar Transação"):
        registrar_transacao(data, descricao, categoria, valor, tipo, detalhes_adicionais)
        st.success("Transação registrada com sucesso!")

# Inicializando o estado da sessão, se necessário
if "transactions" not in st.session_state:
    st.session_state["transactions"] = pd.DataFrame(columns=["Data", "Descrição", "Categoria", "Valor", "Tipo", "Detalhes"])

########################################## CNPJ ##########################################

# # Função para buscar informações do CNPJ
# def buscar_cnpj(cnpj):
#     url = f"https://receitaws.com.br/v1/cnpj/{cnpj}"
#     try:
#         response = requests.get(url)
#         if response.status_code == 200:
#             return response.json()
#         else:
#             st.error("Não foi possível buscar informações do CNPJ. Verifique o número e tente novamente.")
#             return None
#     except Exception as e:
#         st.error(f"Erro ao buscar CNPJ: {e}")
#         return None

# # Tela de consulta ao CNPJ
# def consultar_cnpj():
#     st.title("🔍 Busca de Informações pelo CNPJ")

#     cnpj_input = st.text_input("Digite o CNPJ:", placeholder="Ex.: 00000000000191")
#     if st.button("Buscar"):
#         if cnpj_input:
#             cnpj_data = buscar_cnpj(cnpj_input)
#             if cnpj_data:
#                 st.write(f"**Nome da Empresa:** {cnpj_data.get('nome')}")
#                 st.write(f"**Situação:** {cnpj_data.get('situacao')}")
#                 st.write(f"**UF:** {cnpj_data.get('uf')}")
#                 st.write(f"**Atividade Principal:** {cnpj_data.get('atividade_principal')[0]['text']}")
#             else:
#                 st.warning("Nenhum dado encontrado para o CNPJ informado.")
#         else:
#             st.warning("Por favor, insira um CNPJ válido.")

########################################## SALDO ##########################################

# Função para calcular o saldo
def calcular_saldo(transactions):
    receitas = transactions[transactions["Tipo"] == "Receita"]["Valor"].sum()
    despesas = transactions[transactions["Tipo"] == "Despesa"]["Valor"].sum()
    saldo = receitas - despesas
    return receitas, despesas, saldo

########################################## DASHBOARD ##########################################

def dashboard():
    st.title("📊 Dashboard Financeiro")
    
    # Dados e cálculos
    transactions = st.session_state["transactions"]

    if transactions.empty:
        st.info("Nenhuma transação registrada ainda.")
        return
    
    receitas = transactions[transactions["Tipo"] == "Receita"]["Valor"].sum()
    despesas = transactions[transactions["Tipo"] == "Despesa"]["Valor"].sum()
    saldo = receitas - despesas

###################### CARDS ######################

    # Layout de Cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="card"><h3>Receitas</h3><p>R$ {:,.2f}</p></div>'.format(receitas), unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="card"><h3>Despesas</h3><p style="color: #e74c3c;">R$ {:,.2f}</p></div>'.format(despesas), unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="card"><h3>Saldo</h3><p>R$ {:,.2f}</p></div>'.format(saldo), unsafe_allow_html=True)

###################### GRÁFICO ######################

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

########################################## RELATÓRIO ##########################################

def relatorio():
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

########################################## PÁGINA PRINCIPAL ##########################################

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
        registrar_transacao_tela()

    elif menu_option == "Relatórios":
        relatorio()

    elif menu_option == "Consultar CNPJ":
        print("")

    elif menu_option == "Sair":
        st.session_state["logged_in"] = False
        st.success("Você saiu do sistema.")

########################################## ACESSO AO SISTEMA ##########################################

# Controle de acesso ao sistema
if __name__ == "__main__":
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if st.session_state["logged_in"]:
        main_app()
    else:
        login_screen()
