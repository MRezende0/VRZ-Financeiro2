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

    # # Filtros acima dos gráficos de receitas e despesas
    # st.markdown("### Filtros para Receitas e Despesas")
    # col1, col2 = st.columns(2)
    # with col1:
    #     categorias_receitas = df_receitas["Categoria"].unique()
    #     categoria_receita_selecionada = st.multiselect("Categoria de Receitas", categorias_receitas)
    # with col2:
    #     categorias_despesas = df_despesas["Categoria"].unique()
    #     categoria_despesa_selecionada = st.multiselect("Categoria de Despesas", categorias_despesas)

    # # Aplicar filtros aos dados
    # if categoria_receita_selecionada:
    #     df_receitas_filtrado = df_receitas[df_receitas["Categoria"].isin(categoria_receita_selecionada)]
    # else:
    #     df_receitas_filtrado = df_receitas

    # if categoria_despesa_selecionada:
    #     df_despesas_filtrado = df_despesas[df_despesas["Categoria"].isin(categoria_despesa_selecionada)]
    # else:
    #     df_despesas_filtrado = df_despesas

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

    # Cores fixas para receitas e despesas
    cor_receitas = "#4caf50"  # Verde
    cor_despesas = "#e74c3c"  # Vermelho

    # Gráfico 1: Quantidade de receitas por mês/ano
    if not df_receitas.empty:
        df_receitas["DataRecebimento"] = pd.to_datetime(df_receitas["DataRecebimento"])
        df_receitas["MesAno"] = df_receitas["DataRecebimento"].dt.to_period("M").astype(str)
        receitas_por_mes_ano = df_receitas.groupby("MesAno")["ValorTotal"].sum().reset_index()
        receitas_por_mes_ano["MesAno"] = pd.to_datetime(receitas_por_mes_ano["MesAno"])
        
        fig_receitas_mes_ano = px.bar(
            receitas_por_mes_ano,
            x="MesAno",
            y="ValorTotal",
            title="Receitas por Mês/Ano",
            labels={"ValorTotal": "Total de Receitas", "MesAno": "Mês/Ano"},
            color_discrete_sequence=[cor_receitas]  # Verde para receitas
        )
        
        fig_receitas_mes_ano.update_xaxes(
            tickformat="%b/%Y",
            dtick="M1"
        )
        
        st.plotly_chart(fig_receitas_mes_ano, use_container_width=True)

    # Gráfico 2: Quantidade de despesas por mês/ano
    if not df_despesas.empty:
        df_despesas["DataPagamento"] = pd.to_datetime(df_despesas["DataPagamento"])
        df_despesas["MesAno"] = df_despesas["DataPagamento"].dt.to_period("M").astype(str)
        despesas_por_mes_ano = df_despesas.groupby("MesAno")["ValorTotal"].sum().reset_index()
        despesas_por_mes_ano["MesAno"] = pd.to_datetime(despesas_por_mes_ano["MesAno"])
        
        fig_despesas_mes_ano = px.bar(
            despesas_por_mes_ano,
            x="MesAno",
            y="ValorTotal",
            title="Despesas por Mês/Ano",
            labels={"ValorTotal": "Total de Despesas", "MesAno": "Mês/Ano"},
            color_discrete_sequence=[cor_despesas]  # Vermelho para despesas
        )
        
        fig_despesas_mes_ano.update_xaxes(
            tickformat="%b/%Y",
            dtick="M1"
        )
        
        st.plotly_chart(fig_despesas_mes_ano, use_container_width=True)

    # Gráfico 3: Receitas por categoria
    if not df_receitas.empty:
        receitas_por_categoria = df_receitas.groupby("Categoria")["ValorTotal"].sum().reset_index()
        fig_receitas_categoria = px.bar(
            receitas_por_categoria,
            x="Categoria",
            y="ValorTotal",
            title="Receitas por Categoria",
            color_discrete_sequence=[cor_receitas]  # Verde para receitas
        )
        st.plotly_chart(fig_receitas_categoria, use_container_width=True)

    # Gráfico 4: Despesas por categoria
    if not df_despesas.empty:
        despesas_por_categoria = df_despesas.groupby("Categoria")["ValorTotal"].sum().reset_index()
        fig_despesas_categoria = px.bar(
            despesas_por_categoria,
            x="Categoria",
            y="ValorTotal",
            title="Despesas por Categoria",
            color_discrete_sequence=[cor_despesas]  # Vermelho para despesas
        )
        st.plotly_chart(fig_despesas_categoria, use_container_width=True)

    # Gráfico 5: Receitas e despesas por projeto
    if not df_receitas.empty or not df_despesas.empty:
        receitas_por_projeto = df_receitas.groupby("Projeto")["ValorTotal"].sum().reset_index()
        despesas_por_projeto = df_despesas.groupby("Projeto")["ValorTotal"].sum().reset_index()
        fig_projetos = px.bar(
            pd.concat([receitas_por_projeto.assign(Tipo="Receita"), despesas_por_projeto.assign(Tipo="Despesa")]),
            x="Projeto",
            y="ValorTotal",
            color="Tipo",  # Usa cores diferentes para receitas e despesas
            title="Receitas e Despesas por Projeto",
            barmode="group",
            color_discrete_sequence=[cor_receitas, cor_despesas]  # Verde para receitas, vermelho para despesas
        )
        st.plotly_chart(fig_projetos, use_container_width=True)

    # Gráfico 6: Receitas e despesas por método de pagamento
    if not df_receitas.empty or not df_despesas.empty:
        receitas_por_metodo = df_receitas.groupby("FormaPagamento")["ValorTotal"].sum().reset_index()
        despesas_por_metodo = df_despesas.groupby("FormaPagamento")["ValorTotal"].sum().reset_index()
        fig_metodo_pagamento = px.bar(
            pd.concat([receitas_por_metodo.assign(Tipo="Receita"), despesas_por_metodo.assign(Tipo="Despesa")]),
            x="FormaPagamento",
            y="ValorTotal",
            color="Tipo",  # Usa cores diferentes para receitas e despesas
            title="Receitas e Despesas por Método de Pagamento",
            barmode="group",
            color_discrete_sequence=[cor_receitas, cor_despesas]  # Verde para receitas, vermelho para despesas
        )
        st.plotly_chart(fig_metodo_pagamento, use_container_width=True)

    # Gráfico 7: Despesas por responsável
    if not df_despesas.empty:
        despesas_por_responsavel = df_despesas.groupby("Responsável")["ValorTotal"].sum().reset_index()
        fig_despesas_responsavel = px.bar(
            despesas_por_responsavel,
            x="Responsável",
            y="ValorTotal",
            title="Despesas por Responsável",
            color_discrete_sequence=[cor_despesas]  # Vermelho para despesas
        )
        st.plotly_chart(fig_despesas_responsavel, use_container_width=True)

    # Gráfico 8: Despesas por fornecedor
    if not df_despesas.empty:
        despesas_por_fornecedor = df_despesas.groupby("Fornecedor")["ValorTotal"].sum().reset_index()
        fig_despesas_fornecedor = px.bar(
            despesas_por_fornecedor,
            x="Fornecedor",
            y="ValorTotal",
            title="Despesas por Fornecedor",
            color_discrete_sequence=[cor_despesas]  # Vermelho para despesas
        )
        st.plotly_chart(fig_despesas_fornecedor, use_container_width=True)

    # 1. Quantidade de projetos por localização
    if not df_projetos.empty:
        projetos_por_localizacao = df_projetos["Localizacao"].value_counts().reset_index()
        projetos_por_localizacao.columns = ["Localizacao", "Quantidade"]
        fig_projetos_localizacao = px.bar(
            projetos_por_localizacao,
            x="Localizacao",
            y="Quantidade",
            title="Quantidade de Projetos por Localização"
        )
        st.plotly_chart(fig_projetos_localizacao, use_container_width=True)

    # 2. Quantidade de projetos com placa e sem placa
    if not df_projetos.empty:
        projetos_placa = df_projetos["Placa"].value_counts().reset_index()
        projetos_placa.columns = ["Placa", "Quantidade"]
        fig_projetos_placa = px.pie(
            projetos_placa,
            names="Placa",
            values="Quantidade",
            title="Quantidade de Projetos com Placa e sem Placa"
        )
        st.plotly_chart(fig_projetos_placa, use_container_width=True)

    # 3. Quantidade de projetos com post e sem post
    if not df_projetos.empty:
        projetos_post = df_projetos["Post"].value_counts().reset_index()
        projetos_post.columns = ["Post", "Quantidade"]
        fig_projetos_post = px.pie(
            projetos_post,
            names="Post",
            values="Quantidade",
            title="Quantidade de Projetos com Post e sem Post"
        )
        st.plotly_chart(fig_projetos_post, use_container_width=True)

    # 4. Quantidade de projetos com contrato e sem contrato
    if not df_projetos.empty:
        projetos_contrato = df_projetos["Contrato"].value_counts().reset_index()
        projetos_contrato.columns = ["Contrato", "Quantidade"]
        fig_projetos_contrato = px.pie(
            projetos_contrato,
            names="Contrato",
            values="Quantidade",
            title="Quantidade de Projetos com Contrato e sem Contrato"
        )
        st.plotly_chart(fig_projetos_contrato, use_container_width=True)

    # 5. Quantidade de projetos pelo status
    if not df_projetos.empty:
        projetos_status = df_projetos["Status"].value_counts().reset_index()
        projetos_status.columns = ["Status", "Quantidade"]
        fig_projetos_status = px.bar(
            projetos_status,
            x="Status",
            y="Quantidade",
            title="Quantidade de Projetos por Status"
        )
        st.plotly_chart(fig_projetos_status, use_container_width=True)

    # 6. Quantidade de projetos pelo briefing
    if not df_projetos.empty:
        projetos_briefing = df_projetos["Briefing"].value_counts().reset_index()
        projetos_briefing.columns = ["Briefing", "Quantidade"]
        fig_projetos_briefing = px.pie(
            projetos_briefing,
            names="Briefing",
            values="Quantidade",
            title="Quantidade de Projetos por Briefing"
        )
        st.plotly_chart(fig_projetos_briefing, use_container_width=True)

    # 7. Quantidade de projetos por arquiteto
    if not df_projetos.empty:
        projetos_arquiteto = df_projetos["Arquiteto"].value_counts().reset_index()
        projetos_arquiteto.columns = ["Arquiteto", "Quantidade"]
        fig_projetos_arquiteto = px.bar(
            projetos_arquiteto,
            x="Arquiteto",
            y="Quantidade",
            title="Quantidade de Projetos por Arquiteto"
        )
        st.plotly_chart(fig_projetos_arquiteto, use_container_width=True)

    # 8. Quantidade de projetos pelo tipo
    if not df_projetos.empty:
        projetos_tipo = df_projetos["Tipo"].value_counts().reset_index()
        projetos_tipo.columns = ["Tipo", "Quantidade"]
        fig_projetos_tipo = px.bar(
            projetos_tipo,
            x="Tipo",
            y="Quantidade",
            title="Quantidade de Projetos por Tipo"
        )
        st.plotly_chart(fig_projetos_tipo, use_container_width=True)

    # 9. Quantidade de projetos pelo pacote
    if not df_projetos.empty:
        projetos_pacote = df_projetos["Pacote"].value_counts().reset_index()
        projetos_pacote.columns = ["Pacote", "Quantidade"]
        fig_projetos_pacote = px.bar(
            projetos_pacote,
            x="Pacote",
            y="Quantidade",
            title="Quantidade de Projetos por Pacote"
        )
        st.plotly_chart(fig_projetos_pacote, use_container_width=True)

    # 10. m2 pelo responsável elétrico
    if not df_projetos.empty:
        m2_responsavel_eletrico = df_projetos.groupby("ResponsávelElétrico")["m2"].sum().reset_index()
        fig_m2_eletrico = px.bar(
            m2_responsavel_eletrico,
            x="ResponsávelElétrico",
            y="m2",
            title="m² por Responsável Elétrico"
        )
        st.plotly_chart(fig_m2_eletrico, use_container_width=True)

    # 11. m2 pelo responsável hidráulico
    if not df_projetos.empty:
        m2_responsavel_hidraulico = df_projetos.groupby("ResponsávelHidráulico")["m2"].sum().reset_index()
        fig_m2_hidraulico = px.bar(
            m2_responsavel_hidraulico,
            x="ResponsávelHidráulico",
            y="m2",
            title="m² por Responsável Hidráulico"
        )
        st.plotly_chart(fig_m2_hidraulico, use_container_width=True)

    # 12. m2 pelo responsável de modelagem
    if not df_projetos.empty:
        m2_responsavel_modelagem = df_projetos.groupby("ResponsávelModelagem")["m2"].sum().reset_index()
        fig_m2_modelagem = px.bar(
            m2_responsavel_modelagem,
            x="ResponsávelModelagem",
            y="m2",
            title="m² por Responsável de Modelagem"
        )
        st.plotly_chart(fig_m2_modelagem, use_container_width=True)

    # 13. m2 pelo responsável de detalhamento
    if not df_projetos.empty:
        m2_responsavel_detalhamento = df_projetos.groupby("ResponsávelDetalhamento")["m2"].sum().reset_index()
        fig_m2_detalhamento = px.bar(
            m2_responsavel_detalhamento,
            x="ResponsávelDetalhamento",
            y="m2",
            title="m² por Responsável de Detalhamento"
        )
        st.plotly_chart(fig_m2_detalhamento, use_container_width=True)

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