import streamlit as st
import pandas as pd
import plotly.express as px
import os

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

add_custom_css()

########################################## CREDENCIAIS ##########################################

# Carrega credenciais dos Secrets
USER_CREDENTIALS = {
    st.secrets["USER_EMAIL"]: st.secrets["USER_PASSWORD"],
    st.secrets["ADMIN_EMAIL"]: st.secrets["ADMIN_PASSWORD"],
}

########################################## DADOS ##########################################

# Caminho dos arquivos CSV
RECEITAS_PATH = "dados/receitas.csv"
DESPESAS_PATH = "dados/despesas.csv"
PROJETOS_PATH = "dados/projetos.csv"
CATEGORIAS_RECEITAS_PATH = "dados/categorias_receita.csv"
FORNECEDOR_DESPESAS_PATH = "dados/fornecedor_despesa.csv"

# Função para carregar dados
def carregar_dados(caminho, colunas):
    if os.path.exists(caminho):
        return pd.read_csv(caminho)
    else:
        return pd.DataFrame(columns=colunas)

# Carrega os dados iniciais
df_receitas = carregar_dados(RECEITAS_PATH, ["DataRecebimento", "Descrição", "Projeto", "Categoria", "ValorTotal", "FormaPagamento", "NF"])
df_despesas = carregar_dados(DESPESAS_PATH, ["DataPagamento", "Descrição", "Categoria", "ValorTotal", "Parcelas", "FormaPagamento", "Responsável", "Fornecedor", "Projeto", "NF"])
df_projetos = carregar_dados(PROJETOS_PATH, ["Projeto", "Cliente", "Localizacao", "Placa", "Post", "DataInicio", "DataFinal", "Contrato", "Status", "Briefing", "Arquiteto", "Tipo", "Pacote", "m2", "Parcelas", "ValorTotal", "ResponsávelElétrico", "ResponsávelHidráulico", "ResponsávelModelagem", "ResponsávelDetalhamento"]).sort_values("Projeto")

# Carrega as categorias de receitas e despesas
if os.path.exists(CATEGORIAS_RECEITAS_PATH):
    df_categorias_receitas = pd.read_csv(CATEGORIAS_RECEITAS_PATH)
else:
    df_categorias_receitas = pd.DataFrame({"Categoria": ["Pró-Labore", "Investimentos", "Freelance", "Outros"]})  # Categorias padrão
    df_categorias_receitas.to_csv(CATEGORIAS_RECEITAS_PATH, index=False)

if os.path.exists(FORNECEDOR_DESPESAS_PATH):
    df_fornecedor_despesas = pd.read_csv(FORNECEDOR_DESPESAS_PATH).sort_values("Fornecedor")
else:
    df_fornecedor_despesas = pd.DataFrame({"Fornecedor": ["Outros"]})  # Categorias padrão
    df_fornecedor_despesas.to_csv(FORNECEDOR_DESPESAS_PATH, index=False)

# Função para salvar categorias
def salvar_categorias(df, caminho):
    df.to_csv(caminho, index=False)

########################################## LOGIN ##########################################

# Função de login
def login(email, senha):
    if email in USER_CREDENTIALS and USER_CREDENTIALS[email] == senha:
        return True
    return False

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
        if login(email, password):
            st.success("Login feito com sucesso!")
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.error("Credenciais inválidas. Verifique seu e-mail e senha.")

########################################## TRANSAÇÕES ##########################################

# Função para salvar dados
def salvar_dados(df, caminho):
    df.to_csv(caminho, index=False)

# Tela de Registrar Receita
def registrar_receita():
    global df_receitas, df_categorias_receitas
    st.title("💸 Registrar Receita")

    with st.form("form_receita"):
        DataRecebimento = st.date_input("Data de Recebimento")
        Descrição = st.text_input("Descrição")

        projetos = ["-"] + list(df_projetos["Projeto"].unique()) if not df_projetos.empty else ["-"]
        Projeto = st.selectbox("Projeto", projetos)

        Categoria = st.selectbox("Categoria", df_categorias_receitas["Categoria"].unique())
        ValorTotal = st.number_input("Valor", min_value=0.0, step=1.0, format="%.2f")
        FormaPagamento = st.selectbox("Forma de Pagamento", ["Pix", "TED", "Dinheiro"])
        NF = st.selectbox("Nota Fiscal", ["Sim", "Não"])
        submit = st.form_submit_button("Salvar Receita")

    if submit:
        nova_receita = pd.DataFrame({
            "DataRecebimento": [DataRecebimento],
            "Descrição": [Descrição],
            "Projeto": [Projeto],
            "Categoria": [Categoria],
            "ValorTotal": [ValorTotal],
            "FormaPagamento": [FormaPagamento],
            "NF": [NF]
        })
        df_receitas = pd.concat([df_receitas, nova_receita], ignore_index=True)
        df_receitas.to_csv(RECEITAS_PATH, index=False)
        st.success("Receita registrada com sucesso!")

    # Campo para adicionar nova categoria de receita
    nova_categoria = st.text_input("Nova Categoria")
    if st.button("Adicionar"):
        if nova_categoria and nova_categoria not in df_categorias_receitas["Categoria"].values:
            nova_categoria_df = pd.DataFrame({"Categoria": [nova_categoria]})
            df_categorias_receitas = pd.concat([df_categorias_receitas, nova_categoria_df], ignore_index=True)
            salvar_categorias(df_categorias_receitas, CATEGORIAS_RECEITAS_PATH)
            st.success(f"Categoria '{nova_categoria}' adicionada com sucesso!")
        else:
            st.warning("Categoria já existe ou está vazia.")

# Tela de Registrar Despesa
def registrar_despesa():
    global df_despesas, df_fornecedor_despesas
    st.title("📤 Registrar Despesa")

    with st.form("form_despesa"):
        DataPagamento = st.date_input("Data de Pagamento")
        Descricao = st.text_input("Descrição")
        Categoria = st.selectbox("Categoria", ["Pró-Labore", "Aluguel", "Alimentação", "Outro"])
        ValorTotal = st.number_input("Valor", min_value=0.0, step=1.0, format="%.2f")
        Parcelas = st.number_input("Parcelas", min_value=1, step=1)
        FormaPagamento = st.selectbox("Forma de Pagamento", ["Cartão de Crédito", "Pix", "TED", "Dinheiro"])
        Responsável = st.selectbox("Responsável", ["Bruno", "Victor"])
        Fornecedor = st.selectbox("Fornecedor", df_fornecedor_despesas["Fornecedor"].unique())
        Projeto = st.selectbox("Projeto", df_projetos["Projeto"].unique())
        NF = st.selectbox("Nota Fiscal", ["Sim", "Não"])
        submit = st.form_submit_button("Salvar Despesa")

    if submit:
        nova_despesa = pd.DataFrame({
            "DataPagamento": [DataPagamento],
            "Descrição": [Descricao],
            "Categoria": [Categoria],
            "ValorTotal": [ValorTotal],
            "Parcelas": [Parcelas],
            "FormaPagamento": [FormaPagamento],
            "Responsável": [Responsável],
            "Fornecedor": [Fornecedor],
            "Projeto": [Projeto],
            "NF": [NF]
        })
        df_despesas = pd.concat([df_despesas, nova_despesa], ignore_index=True)
        df_despesas.to_csv(DESPESAS_PATH, index=False)
        st.success("Despesa registrada com sucesso!")

    # Campo para adicionar nova categoria de despesa
    novo_fornecedor = st.text_input("Novo Fornecedor")
    if st.button("Adicionar"):
        if novo_fornecedor and novo_fornecedor not in df_fornecedor_despesas["Fornecedor"].values:
            novo_fornecedor_df = pd.DataFrame({"Fornecedor": [novo_fornecedor]})
            df_fornecedor_despesas = pd.concat([df_fornecedor_despesas, novo_fornecedor_df], ignore_index=True)
            salvar_categorias(df_fornecedor_despesas, FORNECEDOR_DESPESAS_PATH)
            st.success(f"Fornecedor '{novo_fornecedor}' adicionado com sucesso!")
        else:
            st.warning("Fornecedor já existe ou está vazio.")

########################################## PROJETOS ##########################################

# Tela de Registrar Projeto
def registrar_projeto():
    global df_projetos  # Declara df_projetos como global
    st.title("🏗️ Registrar Projeto")

    with st.form("form_projeto"):
        Projeto = st.text_input("ID Projeto")
        Cliente = st.text_input("Nome do cliente")
        Localizacao = st.text_input("Localização")
        Placa = st.selectbox("Já possui placa na obra?", ["Sim", "Não"])
        Post = st.selectbox("Já foi feito o post do projeto?", ["Sim", "Não"])
        DataInicio = st.date_input("Data de Início")
        DataFinal = st.date_input("Data de Conclusão Prevista")
        Contrato = st.selectbox("Contrato", ["Sim", "Não"])
        Status = st.selectbox("Status", ["Concluído", "Em Andamento", "A fazer", "Impedido"])
        Briefing = st.selectbox("Briefing", ["Sim", "Não"])
        Arquiteto = st.text_input("Arquiteto")
        Tipo = st.selectbox("Tipo", ["Residencial", "Comercial"])
        Pacote = st.selectbox("Pacote", ["Completo", "Estrutural e Hidráulico", "Estrutural e Elétrico"])
        m2 = st.number_input("m²", min_value=0.0, step=1.0)
        Parcelas = st.number_input("Parcelas", min_value=0, step=1)
        ValorTotal = st.number_input("Valor Total", min_value=0.0, step=1.0, format="%.2f")
        ResponsávelElétrico = st.selectbox("ResponsávelElétrico", ["Flávio"])
        ResponsávelHidráulico = st.selectbox("ResponsávelHidráulico", ["Flávio"])
        ResponsávelModelagem = st.selectbox("ResponsávelModelagem", ["Bia"])
        ResponsávelDetalhamento = st.selectbox("ResponsávelDetalhamento", ["Bia"])
        submit = st.form_submit_button("Salvar Projeto")

    if submit:
        novo_projeto = pd.DataFrame({
            "Projeto": [Projeto],
            "Cliente": [Cliente],
            "Localizacao": [Localizacao],
            "Placa": [Placa],
            "Post": [Post],
            "DataInicio": [DataInicio],
            "DataFinal": [DataFinal],
            "Contrato": [Contrato],
            "Status": [Status],
            "Briefing": [Briefing],
            "Arquiteto": [Arquiteto],
            "Tipo": [Tipo],
            "Pacote": [Pacote],
            "m2": [m2],
            "Parcelas": [Parcelas],
            "ValorTotal": [ValorTotal],
            "ResponsávelElétrico": [ResponsávelElétrico],
            "ResponsávelHidráulico": [ResponsávelHidráulico],
            "ResponsávelModelagem": [ResponsávelModelagem],
            "ResponsávelDetalhamento": [ResponsávelDetalhamento]
        })
        df_projetos = pd.concat([df_projetos, novo_projeto], ignore_index=True)
        salvar_dados(df_projetos, PROJETOS_PATH)
        st.success("Projeto registrado com sucesso!")

########################################## DASHBOARD ##########################################

def formatar_br(valor):
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def dashboard():
    st.title("📊 Dashboard Financeiro")

    # Cálculos
    receitas = df_receitas["ValorTotal"].sum()
    despesas = df_despesas["ValorTotal"].sum()
    saldo = receitas - despesas

    # Define a cor do saldo com base no valor
    cor_saldo = "#e74c3c" if saldo < 0 else "#4caf50"  # Vermelho para negativo, verde para positivo

    # Formata os valores no formato brasileiro (2.000,00)
    receitas_formatada = formatar_br(receitas)
    despesas_formatada = formatar_br(despesas)
    saldo_formatado = formatar_br(saldo)

    # Cards
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="card"><h3>Receitas</h3><p>R$ {}</p></div>'.format(receitas_formatada), unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="card"><h3>Despesas</h3><p style="color: #e74c3c;">R$ {}</p></div>'.format(despesas_formatada), unsafe_allow_html=True)
    with col3:
        st.markdown(
            '<div class="card"><h3>Saldo</h3><p style="color: {};">R$ {}</p></div>'.format(cor_saldo, saldo_formatado),
            unsafe_allow_html=True
        )
        
    # Gráfico
    if not df_receitas.empty or not df_despesas.empty:
        df_transacoes = pd.concat([df_receitas.assign(Tipo="Receita"), df_despesas.assign(Tipo="Despesa")])
        fig = px.bar(
            df_transacoes,
            x="Categoria",
            y="ValorTotal",
            color="Tipo",
            title="Receitas e Despesas por Categoria",
            barmode="group"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhuma transação registrada ainda.")

########################################## RELATÓRIOS ##########################################

def relatorios():
    st.title("📈 Relatórios Financeiros")

    if not df_receitas.empty or not df_despesas.empty:
        st.dataframe(df_receitas)
        st.dataframe(df_despesas)
    else:
        st.info("Nenhuma transação registrada ainda.")

########################################## PÁGINA PRINCIPAL ##########################################

def main_app():
    st.sidebar.image("imagens/VRZ-LOGO-44.png")
    st.sidebar.title("Menu")
    menu_option = st.sidebar.radio(
        "Selecione a funcionalidade:",
        ("Dashboard", "Registrar Receita", "Registrar Despesa", "Registrar Projeto", "Relatórios")
    )

    # Botão "Sair" na parte inferior da sidebar
    st.sidebar.markdown("---")  # Linha separadora
    if st.sidebar.button("Sair", key="sair"):
        st.session_state["logged_in"] = False
        st.success("Você saiu do sistema.")
        st.rerun()  # Atualiza a página para voltar à tela de login

    if menu_option == "Dashboard":
        dashboard()
    elif menu_option == "Registrar Receita":
        registrar_receita()
    elif menu_option == "Registrar Despesa":
        registrar_despesa()
    elif menu_option == "Registrar Projeto":
        registrar_projeto()
    elif menu_option == "Relatórios":
        relatorios()

########################################## EXECUÇÃO ##########################################

if __name__ == "__main__":
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if st.session_state["logged_in"]:
        main_app()
    else:
        login_screen()