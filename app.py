import os
import ssl
import time
from datetime import datetime, timedelta
from random import uniform

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from google.oauth2 import service_account
import streamlit.components.v1 as components
import json
import locale
import base64
import io
import uuid
from dateutil.relativedelta import relativedelta

########################################## CONFIGURAÇÃO ##########################################

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

########################################## CREDENCIAIS ##########################################

# Carrega credenciais dos Secrets
USER_CREDENTIALS = {
    "contato@vrzengenharia.com.br": "123",
    "20242025": "123",
}

SHEET_ID = "1E72Z_HBydw_IxM143IAFlrfhqrxhnOfBMxZGjfjJj5o"
SHEET_GIDS = {
    "Receitas": "0",
    "Despesas": "2095402559",
    "Projetos": "1967040877",
    "Categorias_Receitas": "70356418",
    "Fornecedor_Despesas": "62015063"
}

COLUNAS_ESPERADAS = {
    "Receitas": ["DataRecebimento", "Descrição", "Projeto", "Categoria", "ValorTotal", "FormaPagamento", "NF"],
    "Despesas": ["DataPagamento", "Descrição", "Categoria", "ValorTotal", "Parcelas", "FormaPagamento", "Responsável", "Fornecedor", "Projeto", "NF"],
    "Projetos": ["Projeto", "Cliente", "Localizacao", "Placa", "Post", "DataInicio", "DataFinal", "Contrato", "Status", "Briefing", "Arquiteto", "Tipo", "Pacote", "m2", "Parcelas", "ValorTotal", "ResponsávelElétrico", "ResponsávelHidráulico", "ResponsávelModelagem", "ResponsávelDetalhamento"],
    "Categorias_Receitas": ["Data", "Solicitante", "Biologico", "Quimico", "Observacoes", "Status"],
    "Fornecedor_Despesas": ["Data", "Biologico", "Quimico", "Tempo", "Placa1", "Placa2", "Placa3", "MédiaPlacas", "Diluicao", "ConcObtida", "Dose", "ConcAtivo", "VolumeCalda", "ConcEsperada", "Razao", "Resultado"]
}

########################################## DADOS ##########################################

# Função para conectar ao Google Sheets
def conectar_sheets():
    try:
        # Desabilitar verificação SSL temporariamente para contornar problemas de certificado
        ssl._create_default_https_context = ssl._create_unverified_context
        
        # Escopo para acesso ao Google Sheets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Carregar credenciais do arquivo secrets.toml
        try:
            creds_info = st.secrets["gcp_service_account"]
            creds_dict = {
                "type": creds_info["type"],
                "project_id": creds_info["project_id"],
                "private_key_id": creds_info["private_key_id"],
                "private_key": creds_info["private_key"].replace("\\n", "\n"),
                "client_email": creds_info["client_email"],
                "client_id": creds_info["client_id"],
                "auth_uri": creds_info["auth_uri"],
                "token_uri": creds_info["token_uri"],
                "auth_provider_x509_cert_url": creds_info["auth_provider_x509_cert_url"],
                "client_x509_cert_url": creds_info["client_x509_cert_url"]
            }
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        except Exception as e:
            st.error(f"Erro ao carregar credenciais: {e}")
            return None
        
        # Conectar ao Google Sheets
        client = gspread.authorize(creds)
        
        # Abrir a planilha pelo ID
        try:
            spreadsheet = client.open_by_key(st.secrets["sheet_id"])
            return spreadsheet
        except Exception as e:
            st.error(f"Erro ao abrir planilha: {e}")
            return None
    except Exception as e:
        st.error(f"Erro ao conectar ao Google Sheets: {e}")
        return None

# Função para carregar dados do Google Sheets
def carregar_dados_sheets(sheet_name):
    try:
        # Verificar se já temos os dados em cache na sessão
        if sheet_name.lower() in st.session_state.local_data and not st.session_state.local_data[sheet_name.lower()].empty:
            return st.session_state.local_data[sheet_name.lower()]
        
        # Conectar ao Google Sheets
        spreadsheet = conectar_sheets()
        if spreadsheet is None:
            return pd.DataFrame()
        
        # Abrir a aba específica
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except Exception as e:
            st.error(f"Erro ao abrir aba {sheet_name}: {e}")
            return pd.DataFrame()
        
        # Obter todos os dados
        data = worksheet.get_all_records()
        
        # Converter para DataFrame
        df = pd.DataFrame(data)
        
        # Armazenar no cache da sessão
        st.session_state.local_data[sheet_name.lower()] = df
        
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados de {sheet_name}: {e}")
        return pd.DataFrame()

# Função para salvar dados no Google Sheets
def salvar_dados_sheets(df, sheet_name):
    try:
        # Conectar ao Google Sheets
        spreadsheet = conectar_sheets()
        if spreadsheet is None:
            return False
        
        # Abrir a aba específica
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except Exception as e:
            st.error(f"Erro ao abrir aba {sheet_name}: {e}")
            return False
        
        # Limpar a planilha
        worksheet.clear()
        
        # Adicionar cabeçalhos
        headers = df.columns.tolist()
        worksheet.append_row(headers)
        
        # Adicionar dados
        for _, row in df.iterrows():
            worksheet.append_row(row.tolist())
        
        # Atualizar o cache da sessão
        st.session_state.local_data[sheet_name.lower()] = df
        
        return True
    except Exception as e:
        st.error(f"Erro ao salvar dados em {sheet_name}: {e}")
        return False

# Função para adicionar uma linha ao Google Sheets
def adicionar_linha_sheets(dados, sheet_name):
    try:
        # Conectar ao Google Sheets
        spreadsheet = conectar_sheets()
        if spreadsheet is None:
            return False
        
        # Abrir a aba específica
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
        except Exception as e:
            st.error(f"Erro ao abrir aba {sheet_name}: {e}")
            return False
        
        # Verificar se a planilha está vazia
        try:
            headers = worksheet.row_values(1)
            if not headers:
                # Se estiver vazia, adicionar cabeçalhos
                headers = list(dados.keys())
                worksheet.append_row(headers)
        except:
            # Se ocorrer erro, provavelmente a planilha está vazia
            headers = list(dados.keys())
            worksheet.append_row(headers)
        
        # Preparar os dados na ordem correta
        row_data = [dados.get(header, "") for header in headers]
        
        # Adicionar a linha
        worksheet.append_row(row_data)
        
        # Limpar o cache da sessão para forçar recarga
        if sheet_name.lower() in st.session_state.local_data:
            st.session_state.local_data[sheet_name.lower()] = pd.DataFrame()
        
        return True
    except Exception as e:
        st.error(f"Erro ao adicionar linha em {sheet_name}: {e}")
        return False

# Função para salvar categorias
def salvar_categorias(df, sheet_name):
    return salvar_dados_sheets(df, sheet_name)

# Inicialização dos dados locais
if 'local_data' not in st.session_state:
    st.session_state.local_data = {
        'receitas': pd.DataFrame(),
        'despesas': pd.DataFrame(),
        'projetos': pd.DataFrame(),
        'categorias_receitas': pd.DataFrame(),
        'fornecedor_despesas': pd.DataFrame()
    }

# Carrega os dados iniciais
if 'receitas' in st.session_state.local_data and not st.session_state.local_data['receitas'].empty:
    df_receitas = st.session_state.local_data['receitas']
else:
    df_receitas = carregar_dados_sheets("Receitas")
    st.session_state.local_data['receitas'] = df_receitas

if 'despesas' in st.session_state.local_data and not st.session_state.local_data['despesas'].empty:
    df_despesas = st.session_state.local_data['despesas']
else:
    df_despesas = carregar_dados_sheets("Despesas")
    st.session_state.local_data['despesas'] = df_despesas

if 'projetos' in st.session_state.local_data and not st.session_state.local_data['projetos'].empty:
    df_projetos = st.session_state.local_data['projetos']
else:
    df_projetos = carregar_dados_sheets("Projetos")
    st.session_state.local_data['projetos'] = df_projetos

# Ordenar projetos por nome
if not df_projetos.empty and "Projeto" in df_projetos.columns:
    df_projetos = df_projetos.sort_values("Projeto")

# Converter colunas de data explicitamente
if not df_receitas.empty and "DataRecebimento" in df_receitas.columns:
    df_receitas["DataRecebimento"] = pd.to_datetime(df_receitas["DataRecebimento"], dayfirst=True, errors="coerce")
if not df_despesas.empty and "DataPagamento" in df_despesas.columns:
    df_despesas["DataPagamento"] = pd.to_datetime(df_despesas["DataPagamento"], dayfirst=True, errors="coerce")
if not df_projetos.empty:
    if "DataInicio" in df_projetos.columns:
        df_projetos["DataInicio"] = pd.to_datetime(df_projetos["DataInicio"], dayfirst=True, errors="coerce")
    if "DataFinal" in df_projetos.columns:
        df_projetos["DataFinal"] = pd.to_datetime(df_projetos["DataFinal"], dayfirst=True, errors="coerce")

# Carrega as categorias de receitas e despesas
if 'categorias_receitas' in st.session_state.local_data and not st.session_state.local_data['categorias_receitas'].empty:
    df_categorias_receitas = st.session_state.local_data['categorias_receitas']
else:
    df_categorias_receitas = carregar_dados_sheets("Categorias_Receitas")
    if df_categorias_receitas.empty:
        df_categorias_receitas = pd.DataFrame({"Categoria": ["Pró-Labore", "Investimentos", "Freelance", "Outros"]})
        salvar_dados_sheets(df_categorias_receitas, "Categorias_Receitas")
    st.session_state.local_data['categorias_receitas'] = df_categorias_receitas

if 'fornecedor_despesas' in st.session_state.local_data and not st.session_state.local_data['fornecedor_despesas'].empty:
    df_fornecedor_despesas = st.session_state.local_data['fornecedor_despesas']
else:
    df_fornecedor_despesas = carregar_dados_sheets("Fornecedor_Despesas")
    if df_fornecedor_despesas.empty:
        df_fornecedor_despesas = pd.DataFrame({"Fornecedor": ["Outros"]})
        salvar_dados_sheets(df_fornecedor_despesas, "Fornecedor_Despesas")
    st.session_state.local_data['fornecedor_despesas'] = df_fornecedor_despesas

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
def salvar_dados(df, sheet_name):
    return salvar_dados_sheets(df, sheet_name)

# Tela de Registrar Receita
def registrar_receita():
    global df_receitas  # Declara df_receitas como global
    
    st.subheader("📥 Registrar Receita")
    
    # Formulário para adicionar nova receita
    with st.form("nova_receita"):
        col1, col2 = st.columns(2)
        
        with col1:
            data_recebimento = st.date_input("Data de Recebimento", datetime.now())
            descricao = st.text_input("Descrição")
            categoria = st.selectbox("Categoria", df_categorias_receitas["Categoria"])
            
        with col2:
            valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            forma_pagamento = st.selectbox("Forma de Pagamento", ["Pix", "Transferência", "Dinheiro", "Cheque", "Cartão de Crédito", "Outros"])
            projeto = st.selectbox("Projeto", [""] + list(df_projetos["Projeto"]) if not df_projetos.empty else [""])
            
        # Botão para adicionar nova categoria
        nova_categoria = st.text_input("Adicionar Nova Categoria")
        if st.form_submit_button("Adicionar Categoria"):
            if nova_categoria and nova_categoria not in df_categorias_receitas["Categoria"].values:
                nova_categoria_df = pd.DataFrame({"Categoria": [nova_categoria]})
                df_categorias_receitas = pd.concat([df_categorias_receitas, nova_categoria_df], ignore_index=True)
                salvar_categorias(df_categorias_receitas, "Categorias_Receitas")
                st.success(f"Categoria '{nova_categoria}' adicionada com sucesso!")
            else:
                st.warning("Categoria já existe ou está vazia.")
            
        # Botão para submeter o formulário
        submitted = st.form_submit_button("Registrar Receita")
        
        if submitted:
            # Cria um dicionário com os dados da nova receita
            nova_receita = {
                "DataRecebimento": data_recebimento.strftime("%d/%m/%Y"),
                "Descrição": descricao,
                "Categoria": categoria,
                "ValorTotal": valor,
                "FormaPagamento": forma_pagamento,
                "Projeto": projeto
            }
            
            # Adiciona a nova receita ao Google Sheets
            if adicionar_linha_sheets(nova_receita, "Receitas"):
                st.success("Receita registrada com sucesso!")
                # Limpar o cache para forçar recarregar os dados
                st.session_state.local_data["receitas"] = pd.DataFrame()
            else:
                st.error("Erro ao registrar receita.")

# Tela de Registrar Despesa
def registrar_despesa():
    global df_despesas  # Declara df_despesas como global
    
    st.subheader("📤 Registrar Despesa")
    
    # Formulário para adicionar nova despesa
    with st.form("nova_despesa"):
        col1, col2 = st.columns(2)
        
        with col1:
            data_pagamento = st.date_input("Data de Pagamento", datetime.now())
            descricao = st.text_input("Descrição")
            categoria = st.selectbox("Categoria", ["Alimentação", "Transporte", "Moradia", "Saúde", "Educação", "Lazer", "Outros"])
            fornecedor = st.selectbox("Fornecedor", df_fornecedor_despesas["Fornecedor"])
            
        with col2:
            valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            parcelas = st.number_input("Parcelas", min_value=1, step=1)
            forma_pagamento = st.selectbox("Forma de Pagamento", ["Pix", "Transferência", "Dinheiro", "Cheque", "Cartão de Crédito", "Outros"])
            projeto = st.selectbox("Projeto", [""] + list(df_projetos["Projeto"]) if not df_projetos.empty else [""])
            responsavel = st.selectbox("Responsável", ["Bruno", "Victor"])
            nf = st.checkbox("Nota Fiscal")
            
        # Botão para adicionar novo fornecedor
        novo_fornecedor = st.text_input("Adicionar Novo Fornecedor")
        if st.form_submit_button("Adicionar Fornecedor"):
            if novo_fornecedor and novo_fornecedor not in df_fornecedor_despesas["Fornecedor"].values:
                novo_fornecedor_df = pd.DataFrame({"Fornecedor": [novo_fornecedor]})
                df_fornecedor_despesas = pd.concat([df_fornecedor_despesas, novo_fornecedor_df], ignore_index=True)
                salvar_categorias(df_fornecedor_despesas, "Fornecedor_Despesas")
                st.success(f"Fornecedor '{novo_fornecedor}' adicionado com sucesso!")
            else:
                st.warning("Fornecedor já existe ou está vazio.")
            
        # Botão para submeter o formulário
        submitted = st.form_submit_button("Registrar Despesa")
        
        if submitted:
            # Calcula o valor de cada parcela
            valor_parcela = round(valor / parcelas, 2)
            
            # Lista para armazenar as parcelas
            lista_parcelas = []
            
            # Gera as parcelas
            for i in range(parcelas):
                data_parcela = data_pagamento + relativedelta(months=+i)  # Incrementa a data em 'i' meses
                parcela_info = {
                    "DataPagamento": data_parcela.strftime("%d/%m/%Y"),
                    "Descrição": descricao,
                    "Categoria": categoria,
                    "ValorTotal": valor_parcela,
                    "Parcelas": f"{i + 1}/{parcelas}",  # Identifica a parcela atual
                    "FormaPagamento": forma_pagamento,
                    "Responsável": responsavel,
                    "Fornecedor": fornecedor,
                    "Projeto": projeto,
                    "NF": "Sim" if nf else "Não"
                }
                lista_parcelas.append(parcela_info)
            
            # Adiciona as parcelas ao Google Sheets
            sucesso = True
            for parcela in lista_parcelas:
                if not adicionar_linha_sheets(parcela, "Despesas"):
                    sucesso = False
                    break
            
            if sucesso:
                st.success(f"Despesa registrada com sucesso! {parcelas} parcela(s) criada(s).")
                # Limpar o cache para forçar recarregar os dados
                st.session_state.local_data["despesas"] = pd.DataFrame()
            else:
                st.error("Erro ao registrar despesa.")

########################################## PROJETOS ##########################################

# Função para carregar os projetos
def carregar_projetos():
    try:
        # Verificar se já temos os dados em cache na sessão
        if 'projetos' in st.session_state.local_data and not st.session_state.local_data['projetos'].empty:
            return st.session_state.local_data['projetos']
        else:
            df_projetos = carregar_dados_sheets("Projetos")
            if not df_projetos.empty:
                st.session_state.local_data['projetos'] = df_projetos
            return df_projetos
    except Exception as e:
        st.error(f"Erro ao carregar projetos: {e}")
        return pd.DataFrame()

# Função para salvar os projetos
def salvar_projetos(df):
    try:
        resultado = salvar_dados_sheets(df, "Projetos")
        if resultado:
            st.session_state.local_data['projetos'] = df
            st.success("Alterações salvas com sucesso!")
            return True
        else:
            st.error("Erro ao salvar os projetos.")
            return False
    except Exception as e:
        st.error(f"Erro ao salvar projetos: {e}")
        return False

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
        Contrato = st.selectbox("Contrato", ["Feito", "A fazer"])
        Status = st.selectbox("Status", ["Concluído", "Em Andamento", "A fazer", "Impedido"])
        Briefing = st.selectbox("Briefing", ["Feito", "A fazer"])
        Arquiteto = st.text_input("Arquiteto")
        Tipo = st.selectbox("Tipo", ["Residencial", "Comercial"])
        Pacote = st.selectbox("Pacote", ["Completo", "Estrutural e Hidráulico", "Estrutural e Elétrico"])
        m2 = st.number_input("m²", min_value=0.0, step=1.0)
        Parcelas = st.number_input("Parcelas", min_value=0, step=1)
        ValorTotal = st.number_input("Valor Total", min_value=0.0, step=1.0, format="%.2f")
        ResponsávelElétrico = st.text_input("Responsável pelo Elétrico")
        ResponsávelHidráulico = st.text_input("Responsável pelo Hidráulico")
        ResponsávelModelagem = st.text_input("Responsável pela Modelagem")
        ResponsávelDetalhamento = st.text_input("Responsável pelo Detalhamento")
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
        salvar_projetos(df_projetos)
        st.success("Projeto registrado com sucesso!")

def registrar():
    # st.title("📝 Registrar")

    # Seletor para escolher o tipo de registro
    tipo_registro = st.radio(
        "O que você deseja registrar?",
        ("Receita", "Despesa", "Projeto")
    )

    if tipo_registro == "Receita":
        registrar_receita()
    elif tipo_registro == "Despesa":
        registrar_despesa()
    elif tipo_registro == "Projeto":
        registrar_projeto()

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

    # Cores fixas para receitas e despesas
    cor_receitas = "#4caf50"  # Verde
    cor_despesas = "#e74c3c"  # Vermelho

    # Converter colunas de data para datetime com o formato correto
    # df_receitas["DataRecebimento"] = pd.to_datetime(df_receitas["DataRecebimento"], format="%d/%m/%Y", dayfirst=True)
    # df_despesas["DataPagamento"] = pd.to_datetime(df_despesas["DataPagamento"], format="%d/%m/%Y", dayfirst=True)
    # df_projetos["DataInicio"] = pd.to_datetime(df_projetos["DataInicio"], format="%d/%m/%Y", dayfirst=True)
    # df_projetos["DataFinal"] = pd.to_datetime(df_projetos["DataFinal"], format="%d/%m/%Y", dayfirst=True)

    # Filtros na sidebar
    st.sidebar.title("Filtros Globais")

    # Filtro por período (afeta receitas, despesas e projetos)
    # st.sidebar.markdown("### Filtro por Período")
    # data_inicio = st.sidebar.date_input("Data de Início", value=pd.to_datetime("2023-01-01"))
    # data_fim = st.sidebar.date_input("Data de Fim", value=pd.to_datetime("2023-12-31"))

    # Filtro por categoria (afeta receitas e despesas)
    st.sidebar.markdown("### Filtro por Categoria")
    categorias_receitas = df_receitas["Categoria"].unique()
    categorias_despesas = df_despesas["Categoria"].unique()
    categorias = list(set(categorias_receitas) | set(categorias_despesas))  # União das categorias
    categoria_selecionada = st.sidebar.multiselect("Categoria", categorias)

    # Filtro por número do projeto (afeta receitas, despesas e projetos)
    st.sidebar.markdown("### Filtro por Projeto")
    projetos = df_projetos["Projeto"].unique()
    projeto_selecionado = st.sidebar.multiselect("Projeto", projetos)

    # Filtro por responsável (afeta despesas e projetos)
    st.sidebar.markdown("### Filtro por Responsável")
    responsaveis_despesas = df_despesas["Responsável"].unique()
    responsaveis_projetos = df_projetos["ResponsávelElétrico"].unique().tolist() + \
                            df_projetos["ResponsávelHidráulico"].unique().tolist() + \
                            df_projetos["ResponsávelModelagem"].unique().tolist() + \
                            df_projetos["ResponsávelDetalhamento"].unique().tolist()
    responsaveis = list(set(responsaveis_despesas) | set(responsaveis_projetos))  # União dos responsáveis
    responsavel_selecionado = st.sidebar.multiselect("Responsável", responsaveis)

    # Filtro por fornecedor (afeta despesas)
    st.sidebar.markdown("### Filtro por Fornecedor")
    fornecedores = df_despesas["Fornecedor"].unique()
    fornecedor_selecionado = st.sidebar.multiselect("Fornecedor", fornecedores)

    # Filtro por status (afeta projetos)
    st.sidebar.markdown("### Filtro por Status")
    status = df_projetos["Status"].unique()
    status_selecionado = st.sidebar.multiselect("Status", status)

    # Filtro por arquiteto (afeta projetos)
    st.sidebar.markdown("### Filtro por Arquiteto")
    arquitetos = df_projetos["Arquiteto"].unique()
    arquiteto_selecionado = st.sidebar.multiselect("Arquiteto", arquitetos)

    st.divider()

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
            text="ValorTotal",
            title="Receitas por Mês/Ano",
            labels={"ValorTotal": "Total de Receitas", "MesAno": "Mês/Ano"},
            color_discrete_sequence=[cor_receitas]  # Verde para receitas
        )
        
        fig_receitas_mes_ano.update_traces(textposition="outside")  # Posiciona rótulos fora das barras
        fig_receitas_mes_ano.update_xaxes(
            tickformat="%b/%Y",
            dtick="M1",
            showgrid=False  # Remove linhas de grade verticais
        )
        fig_receitas_mes_ano.update_yaxes(showgrid=False, showticklabels=False)  # Remove linhas de grade horizontais
        
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
            text="ValorTotal",
            title="Despesas por Mês/Ano",
            labels={"ValorTotal": "Total de Despesas", "MesAno": "Mês/Ano"},
            color_discrete_sequence=[cor_despesas]  # Vermelho para despesas
        )
        
        fig_despesas_mes_ano.update_traces(textposition="outside")  # Posiciona rótulos fora das barras
        fig_despesas_mes_ano.update_xaxes(
            tickformat="%b/%Y",
            dtick="M1"
        )

        fig_despesas_mes_ano.update_yaxes(showgrid=False, showticklabels=False)  # Remove linhas de grade horizontais

        
        st.plotly_chart(fig_despesas_mes_ano, use_container_width=True)

    # Gráfico 3: Receitas por categoria
    if not df_receitas.empty:
        receitas_por_categoria = df_receitas.groupby("Categoria")["ValorTotal"].sum().reset_index()
        fig_receitas_categoria = px.bar(
            receitas_por_categoria,
            x="Categoria",
            y="ValorTotal",
            text="ValorTotal",
            title="Receitas por Categoria",
            color_discrete_sequence=[cor_receitas]  # Verde para receitas
        )

        fig_receitas_categoria.update_traces(textposition="outside")  # Posiciona rótulos fora das barras
        fig_receitas_categoria.update_yaxes(showgrid=False, showticklabels=False)  # Remove linhas de grade horizontais

        st.plotly_chart(fig_receitas_categoria, use_container_width=True)

    # Gráfico 4: Despesas por categoria
    if not df_despesas.empty:
        despesas_por_categoria = df_despesas.groupby("Categoria")["ValorTotal"].sum().reset_index()
        fig_despesas_categoria = px.bar(
            despesas_por_categoria,
            x="Categoria",
            y="ValorTotal",
            text="ValorTotal",
            title="Despesas por Categoria",
            color_discrete_sequence=[cor_despesas]  # Vermelho para despesas
        )

        fig_despesas_categoria.update_traces(textposition="outside")  # Posiciona rótulos fora das barras
        fig_despesas_categoria.update_yaxes(showgrid=False, showticklabels=False)  # Remove linhas de grade horizontais

        st.plotly_chart(fig_despesas_categoria, use_container_width=True)

    # Gráfico 5: Receitas e despesas por projeto
    if not df_receitas.empty or not df_despesas.empty:
        receitas_por_projeto = df_receitas.groupby("Projeto")["ValorTotal"].sum().reset_index()
        despesas_por_projeto = df_despesas.groupby("Projeto")["ValorTotal"].sum().reset_index()
        fig_projetos = px.bar(
            pd.concat([receitas_por_projeto.assign(Tipo="Receita"), despesas_por_projeto.assign(Tipo="Despesa")]),
            x="Projeto",
            y="ValorTotal",
            text="ValorTotal",
            color="Tipo",  # Usa cores diferentes para receitas e despesas
            title="Receitas e Despesas por Projeto",
            barmode="group",
            color_discrete_sequence=[cor_receitas, cor_despesas]  # Verde para receitas, vermelho para despesas
        )

        fig_projetos.update_traces(textposition="outside")  # Posiciona rótulos fora das barras
        fig_projetos.update_yaxes(showgrid=False, showticklabels=False)  # Remove linhas de grade horizontais

        st.plotly_chart(fig_projetos, use_container_width=True)

    # Gráfico 6: Receitas e despesas por método de pagamento
    if not df_receitas.empty or not df_despesas.empty:
        receitas_por_metodo = df_receitas.groupby("FormaPagamento")["ValorTotal"].sum().reset_index()
        despesas_por_metodo = df_despesas.groupby("FormaPagamento")["ValorTotal"].sum().reset_index()
        fig_metodo_pagamento = px.bar(
            pd.concat([receitas_por_metodo.assign(Tipo="Receita"), despesas_por_metodo.assign(Tipo="Despesa")]),
            x="FormaPagamento",
            y="ValorTotal",
            text="ValorTotal",
            color="Tipo",  # Usa cores diferentes para receitas e despesas
            title="Receitas e Despesas por Método de Pagamento",
            barmode="group",
            color_discrete_sequence=[cor_receitas, cor_despesas]  # Verde para receitas, vermelho para despesas
        )

        fig_metodo_pagamento.update_traces(textposition="outside")  # Posiciona rótulos fora das barras
        fig_metodo_pagamento.update_yaxes(showgrid=False, showticklabels=False)  # Remove linhas de grade horizontais

        st.plotly_chart(fig_metodo_pagamento, use_container_width=True)

    # Gráfico 7: Despesas por responsável
    if not df_despesas.empty:
        despesas_por_responsavel = df_despesas.groupby("Responsável")["ValorTotal"].sum().reset_index()
        fig_despesas_responsavel = px.bar(
            despesas_por_responsavel,
            x="Responsável",
            y="ValorTotal",
            text="ValorTotal",
            title="Despesas por Responsável",
            color_discrete_sequence=[cor_despesas]  # Vermelho para despesas
        )

        fig_despesas_responsavel.update_traces(textposition="outside")  # Posiciona rótulos fora das barras
        fig_despesas_responsavel.update_yaxes(showgrid=False, showticklabels=False)  # Remove linhas de grade horizontais

        st.plotly_chart(fig_despesas_responsavel, use_container_width=True)

    # Gráfico 8: Despesas por fornecedor
    if not df_despesas.empty:
        despesas_por_fornecedor = df_despesas.groupby("Fornecedor")["ValorTotal"].sum().reset_index()
        fig_despesas_fornecedor = px.bar(
            despesas_por_fornecedor,
            x="Fornecedor",
            y="ValorTotal",
            text="ValorTotal",
            title="Despesas por Fornecedor",
            color_discrete_sequence=[cor_despesas]  # Vermelho para despesas
        )

        fig_despesas_fornecedor.update_traces(textposition="outside")  # Posiciona rótulos fora das barras
        fig_despesas_fornecedor.update_yaxes(showgrid=False, showticklabels=False)  # Remove linhas de grade horizontais

        st.plotly_chart(fig_despesas_fornecedor, use_container_width=True)

    # 9. Quantidade de projetos por localização
    if not df_projetos.empty:
        projetos_por_localizacao = df_projetos["Localizacao"].value_counts().reset_index()
        projetos_por_localizacao.columns = ["Localizacao", "Quantidade"]
        fig_projetos_localizacao = px.bar(
            projetos_por_localizacao,
            x="Localizacao",
            y="Quantidade",
            text="Quantidade",
            title="Quantidade de Projetos por Localização"
        )

        fig_projetos_localizacao.update_traces(textposition="outside")  # Posiciona rótulos fora das barras
        fig_projetos_localizacao.update_yaxes(showgrid=False, showticklabels=False)  # Remove linhas de grade horizontais

        st.plotly_chart(fig_projetos_localizacao, use_container_width=True)

    # 10. Quantidade de projetos com placa e sem placa
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

    # 11. Quantidade de projetos com post e sem post
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

    # 12. Quantidade de projetos com contrato e sem contrato
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

    # 13. Quantidade de projetos pelo status
    if not df_projetos.empty:
        projetos_status = df_projetos["Status"].value_counts().reset_index()
        projetos_status.columns = ["Status", "Quantidade"]
        fig_projetos_status = px.bar(
            projetos_status,
            x="Status",
            y="Quantidade",
            text="Quantidade",
            title="Quantidade de Projetos por Status"
        )

        fig_projetos_status.update_traces(textposition="outside")  # Posiciona rótulos fora das barras
        fig_projetos_status.update_yaxes(showgrid=False, showticklabels=False)  # Remove linhas de grade horizontais

        st.plotly_chart(fig_projetos_status, use_container_width=True)

    # 14. Quantidade de projetos pelo briefing
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

    # 15. Quantidade de projetos por arquiteto
    if not df_projetos.empty:
        projetos_arquiteto = df_projetos["Arquiteto"].value_counts().reset_index()
        projetos_arquiteto.columns = ["Arquiteto", "Quantidade"]
        fig_projetos_arquiteto = px.bar(
            projetos_arquiteto,
            x="Arquiteto",
            y="Quantidade",
            text="Quantidade",
            title="Quantidade de Projetos por Arquiteto"
        )

        fig_projetos_arquiteto.update_traces(textposition="outside")  # Posiciona rótulos fora das barras
        fig_projetos_arquiteto.update_yaxes(showgrid=False, showticklabels=False)  # Remove linhas de grade horizontais

        st.plotly_chart(fig_projetos_arquiteto, use_container_width=True)

    # 16. Quantidade de projetos pelo tipo
    if not df_projetos.empty:
        projetos_tipo = df_projetos["Tipo"].value_counts().reset_index()
        projetos_tipo.columns = ["Tipo", "Quantidade"]
        fig_projetos_tipo = px.bar(
            projetos_tipo,
            x="Tipo",
            y="Quantidade",
            text="Quantidade",
            title="Quantidade de Projetos por Tipo"
        )

        fig_projetos_tipo.update_traces(textposition="outside")  # Posiciona rótulos fora das barras
        fig_projetos_tipo.update_yaxes(showgrid=False, showticklabels=False)  # Remove linhas de grade horizontais

        st.plotly_chart(fig_projetos_tipo, use_container_width=True)

    # 17. Quantidade de projetos pelo pacote
    if not df_projetos.empty:
        projetos_pacote = df_projetos["Pacote"].value_counts().reset_index()
        projetos_pacote.columns = ["Pacote", "Quantidade"]
        fig_projetos_pacote = px.bar(
            projetos_pacote,
            x="Pacote",
            y="Quantidade",
            text="Quantidade",
            title="Quantidade de Projetos por Pacote"
        )

        fig_projetos_pacote.update_traces(textposition="outside")  # Posiciona rótulos fora das barras
        fig_projetos_pacote.update_yaxes(showgrid=False, showticklabels=False)  # Remove linhas de grade horizontais

        st.plotly_chart(fig_projetos_pacote, use_container_width=True)

    # 18. m2 pelo responsável elétrico
    if not df_projetos.empty:
        m2_responsavel_eletrico = df_projetos.groupby("ResponsávelElétrico")["m2"].sum().reset_index()
        fig_m2_eletrico = px.bar(
            m2_responsavel_eletrico,
            x="ResponsávelElétrico",
            y="m2",
            text="m2",
            title="m² por Responsável Elétrico"
        )

        fig_m2_eletrico.update_traces(textposition="outside")  # Posiciona rótulos fora das barras
        fig_m2_eletrico.update_yaxes(showgrid=False, showticklabels=False)  # Remove linhas de grade horizontais

        st.plotly_chart(fig_m2_eletrico, use_container_width=True)

    # 19. m2 pelo responsável hidráulico
    if not df_projetos.empty:
        m2_responsavel_hidraulico = df_projetos.groupby("ResponsávelHidráulico")["m2"].sum().reset_index()
        fig_m2_hidraulico = px.bar(
            m2_responsavel_hidraulico,
            x="ResponsávelHidráulico",
            y="m2",
            text="m2",
            title="m² por Responsável Hidráulico"
        )

        fig_m2_hidraulico.update_traces(textposition="outside")  # Posiciona rótulos fora das barras
        fig_m2_hidraulico.update_yaxes(showgrid=False, showticklabels=False)  # Remove linhas de grade horizontais

        st.plotly_chart(fig_m2_hidraulico, use_container_width=True)

    # 20. m2 pelo responsável de modelagem
    if not df_projetos.empty:
        m2_responsavel_modelagem = df_projetos.groupby("ResponsávelModelagem")["m2"].sum().reset_index()
        fig_m2_modelagem = px.bar(
            m2_responsavel_modelagem,
            x="ResponsávelModelagem",
            y="m2",
            text="m2",
            title="m² por Responsável de Modelagem"
        )

        fig_m2_modelagem.update_traces(textposition="outside")  # Posiciona rótulos fora das barras
        fig_m2_modelagem.update_yaxes(showgrid=False, showticklabels=False)  # Remove linhas de grade horizontais

        st.plotly_chart(fig_m2_modelagem, use_container_width=True)

    # 21. m2 pelo responsável de detalhamento
    if not df_projetos.empty:
        m2_responsavel_detalhamento = df_projetos.groupby("ResponsávelDetalhamento")["m2"].sum().reset_index()
        fig_m2_detalhamento = px.bar(
            m2_responsavel_detalhamento,
            x="ResponsávelDetalhamento",
            y="m2",
            text="m2",
            title="m² por Responsável de Detalhamento"
        )

        fig_m2_detalhamento.update_traces(textposition="outside")  # Posiciona rótulos fora das barras
        fig_m2_detalhamento.update_yaxes(showgrid=False, showticklabels=False)  # Remove linhas de grade horizontais

        st.plotly_chart(fig_m2_detalhamento, use_container_width=True)

########################################## RELATÓRIOS ##########################################

# Função para carregar os dados de receitas e despesas
def carregar_dados():
    try:
        # Verificar se já temos os dados em cache na sessão
        if 'receitas' in st.session_state.local_data and not st.session_state.local_data['receitas'].empty:
            df_receitas = st.session_state.local_data['receitas']
        else:
            df_receitas = carregar_dados_sheets("Receitas")
            st.session_state.local_data['receitas'] = df_receitas
        
        if 'despesas' in st.session_state.local_data and not st.session_state.local_data['despesas'].empty:
            df_despesas = st.session_state.local_data['despesas']
        else:
            df_despesas = carregar_dados_sheets("Despesas")
            st.session_state.local_data['despesas'] = df_despesas
        
        return df_receitas, df_despesas
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame(), pd.DataFrame()

# Função para filtrar os dados por período
def filtrar_por_periodo(df, mes, ano):
    if "Data" in df.columns:
        df["Data"] = pd.to_datetime(df["Data"])
        return df[(df["Data"].dt.month == mes) & (df["Data"].dt.year == ano)]
    return df

# Função para exibir a página de relatórios
def relatorios():
    st.title("📈 Relatórios Financeiros")

    # Carregar os dados
    df_receitas, df_despesas = carregar_dados()

    # Selecionar mês e ano para análise
    mes = st.selectbox("Selecione o mês", range(1, 13), index=0)
    ano = st.selectbox("Selecione o ano", range(2020, 2031), index=3)

    # Filtrar os dados pelo período selecionado
    df_receitas_filtrado = filtrar_por_periodo(df_receitas, mes, ano)
    df_despesas_filtrado = filtrar_por_periodo(df_despesas, mes, ano)

    # Exibir os dados filtrados
    if not df_receitas_filtrado.empty or not df_despesas_filtrado.empty:
        st.write("### Receitas")
        st.dataframe(df_receitas_filtrado)

        st.write("### Despesas")
        st.dataframe(df_despesas_filtrado)

        # Cálculos financeiros
        total_receitas = df_receitas_filtrado["ValorTotal"].sum()
        total_despesas = df_despesas_filtrado["ValorTotal"].sum()
        saldo_final = total_receitas - total_despesas

        st.write("### Resumo Financeiro")
        st.write(f"**Total de Receitas:** R$ {total_receitas:.2f}")
        st.write(f"**Total de Despesas:** R$ {total_despesas:.2f}")
        st.write(f"**Saldo Final:** R$ {saldo_final:.2f}")

        # Botões para exportar os dados
        st.write("### Exportar Dados")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Exportar Receitas (CSV)"):
                csv = df_receitas_filtrado.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="receitas_filtrado.csv">Baixar arquivo CSV</a>'
                st.markdown(href, unsafe_allow_html=True)
                st.success("Arquivo de receitas pronto para download!")
        with col2:
            if st.button("Exportar Despesas (CSV)"):
                csv = df_despesas_filtrado.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="despesas_filtrado.csv">Baixar arquivo CSV</a>'
                st.markdown(href, unsafe_allow_html=True)
                st.success("Arquivo de despesas pronto para download!")
    else:
        st.info("Nenhuma transação registrada para o período selecionado.")

########################################## PROJETOS ##########################################

# Função para exibir os projetos como cards clicáveis
def projetos():
    st.title("📂 Projetos")

    # Carrega os projetos do Google Sheets
    df_projetos = carregar_projetos()
    
    filtro_dropdown = st.selectbox(
        "🔍 Selecione um projeto",
        options=[""] + list(df_projetos["Projeto"].unique()),  # Dropdown inclui opção vazia
        index=0
    )

    # Filtrar os projetos
    if filtro_dropdown:
        df_projetos = df_projetos[df_projetos["Projeto"] == filtro_dropdown]
    else:
        df_projetos = df_projetos

    # Divide a tela em 3 colunas
    col1, col2, col3 = st.columns(3)

    for i, row in df_projetos.iterrows():
        # Criando um card HTML clicável com efeito hover
        card = f"""
        <div onclick="selectProject({i})" style="
            background-color: #ffffff;
            padding: 15px;
            border-radius: 10px;
            border: 1px solid #ddd;
            text-align: center;
            width: 220px;
            height: 160px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        "
        onmouseover="this.style.transform='scale(1.05)'; this.style.boxShadow='4px 4px 15px rgba(0,0,0,0.2)';"
        onmouseout="this.style.transform='scale(1)'; this.style.boxShadow='2px 2px 10px rgba(0,0,0,0.1)';">
            <strong>{row['Projeto']}</strong><br>
            📌 Cliente: {row['Cliente']}<br>
            📍 Localização: {row['Localizacao']}<br>
            📏 Área: {row['m2']} m²
        </div>
        """

        # Distribuir os cards nas colunas
        if i % 3 == 0:
            with col1:
                if st.button(f"{row['Projeto']}", key=f"proj_{i}") :
                    st.session_state["projeto_selecionado"] = row.to_dict()
                st.markdown(card, unsafe_allow_html=True)
        elif i % 3 == 1:
            with col2:
                if st.button(f"{row['Projeto']}", key=f"proj_{i}") :
                    st.session_state["projeto_selecionado"] = row.to_dict()
                st.markdown(card, unsafe_allow_html=True)
        else:
            with col3:
                if st.button(f"{row['Projeto']}", key=f"proj_{i}") :
                    st.session_state["projeto_selecionado"] = row.to_dict()
                st.markdown(card, unsafe_allow_html=True)

    # Verificar se um projeto foi selecionado
    if "projeto_selecionado" in st.session_state:
        projeto = st.session_state["projeto_selecionado"]

        # Criar as abas para exibir detalhes ou editar
        tabs = st.radio("Escolha uma opção", ("Detalhes", "Editar"))

        if tabs == "Detalhes":
            # Exibir detalhes do projeto selecionado
            st.markdown(
                f"""
                <div style="
                    background-color: #f8f9fa;
                    padding: 20px;
                    border-radius: 10px;
                    border: 1px solid #ddd;
                    box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
                    text-align: left;
                    margin-top: 20px;">
                    <h3 style="text-align: center;">📄 Detalhes do Projeto</h3>
                    <strong>Projeto:</strong> {projeto['Projeto']}<br>
                    <strong>Cliente:</strong> {projeto['Cliente']}<br>
                    <strong>Localização:</strong> {projeto['Localizacao']}<br>
                    <strong>Placa:</strong> {projeto['Placa']}<br>
                    <strong>Post:</strong> {projeto['Post']}<br>
                    <strong>Data Inicial:</strong> {projeto['DataInicio']}<br>
                    <strong>Data Final:</strong> {projeto['DataFinal']}<br>
                    <strong>Contrato:</strong> {projeto['Contrato']}<br>
                    <strong>Status:</strong> {projeto['Status']}<br>
                    <strong>Briefing:</strong> {projeto['Briefing']}<br>
                    <strong>Arquiteto:</strong> {projeto['Arquiteto']}<br>
                    <strong>Tipo:</strong> {projeto['Tipo']}<br>
                    <strong>Pacote:</strong> {projeto['Pacote']}<br>
                    <strong>Área:</strong> {projeto['m2']} m²<br>
                    <strong>Parcelas:</strong> {projeto['Parcelas']}<br>
                    <strong>Valor Total:</strong> {projeto['ValorTotal']}<br>
                    <strong>Responsável Elétrico:</strong> {projeto['ResponsávelElétrico']}<br>
                    <strong>Responsável Hidráulico:</strong> {projeto['ResponsávelHidráulico']}<br>
                    <strong>Responsável Modelagem:</strong> {projeto['ResponsávelModelagem']}<br>
                    <strong>Responsável Detalhamento:</strong> {projeto['ResponsávelDetalhamento']}
                </div>
                """, 
                unsafe_allow_html=True
            )

        elif tabs == "Editar":
            # Formulário de edição do projeto
            st.subheader("Editar Projeto")

            with st.form(key="edit_form"):
                # Campos de edição (como no seu código anterior)
                Projeto = st.text_input("ID Projeto", value=projeto["Projeto"])
                Cliente = st.text_input("Nome do cliente", value=projeto["Cliente"])
                Localizacao = st.text_input("Localização", value=projeto["Localizacao"])
                Placa = st.selectbox("Já possui placa na obra?", ["Sim", "Não"], index=["Sim", "Não"].index(projeto["Placa"]))
                Post = st.selectbox("Já foi feito o post do projeto?", ["Sim", "Não"], index=["Sim", "Não"].index(projeto["Post"]))
                DataInicio = st.date_input("Data de Início", value=datetime.strptime(projeto["DataInicio"], "%Y-%m-%d"))
                DataFinal = st.date_input("Data de Conclusão Prevista", value=datetime.strptime(projeto["DataFinal"], "%Y-%m-%d"))
                Contrato = st.selectbox("Contrato", ["Feito", "A fazer"], index=["Feito", "A fazer"].index(projeto["Contrato"]))
                Status = st.selectbox("Status", ["Concluído", "Em Andamento", "A fazer", "Impedido"], index=["Concluído", "Em Andamento", "A fazer", "Impedido"].index(projeto["Status"]))
                Briefing = st.selectbox("Briefing", ["Feito", "A fazer"], index=["Feito", "A fazer"].index(projeto["Briefing"]))
                Arquiteto = st.text_input("Arquiteto", value=projeto["Arquiteto"])
                Tipo = st.selectbox("Tipo", ["Residencial", "Comercial"], index=["Residencial", "Comercial"].index(projeto["Tipo"]))
                Pacote = st.selectbox("Pacote", ["Completo", "Estrutural e Hidráulico", "Estrutural e Elétrico"], index=["Completo", "Estrutural e Hidráulico", "Estrutural e Elétrico"].index(projeto["Pacote"]))
                m2 = st.number_input("m²", value=float(projeto["m2"]), min_value=0.0, step=100.0)
                Parcelas = st.number_input("Parcelas", value=int(projeto["Parcelas"]), min_value=0, step=1)
                ValorTotal = st.number_input("Valor Total", value=float(projeto["ValorTotal"]), min_value=0.0, step=1000.0, format="%.2f")
                ResponsávelElétrico = st.text_input("Responsável Elétrico", value=projeto["ResponsávelElétrico"])
                ResponsávelHidráulico = st.text_input("Responsável Hidráulico", value=projeto["ResponsávelHidráulico"])
                ResponsávelModelagem = st.text_input("Responsável Modelagem", value=projeto["ResponsávelModelagem"])
                ResponsávelDetalhamento = st.text_input("Responsável Detalhamento", value=projeto["ResponsávelDetalhamento"])

                # Botões de salvar e cancelar
                col1, col2 = st.columns(2)

                with col1:
                    if st.form_submit_button("Salvar Alterações"):
                        # Atualiza o projeto no DataFrame
                        index = df_projetos[df_projetos["Projeto"] == projeto["Projeto"]].index[0]
                        df_projetos.loc[index] = {
                            "Projeto": Projeto,
                            "Cliente": Cliente,
                            "Localizacao": Localizacao,
                            "Placa": Placa,
                            "Post": Post,
                            "DataInicio": DataInicio.strftime("%Y-%m-%d"),
                            "DataFinal": DataFinal.strftime("%Y-%m-%d"),
                            "Contrato": Contrato,
                            "Status": Status,
                            "Briefing": Briefing,
                            "Arquiteto": Arquiteto,
                            "Tipo": Tipo,
                            "Pacote": Pacote,
                            "m2": m2,
                            "Parcelas": Parcelas,
                            "ValorTotal": ValorTotal,
                            "ResponsávelElétrico": ResponsávelElétrico,
                            "ResponsávelHidráulico": ResponsávelHidráulico,
                            "ResponsávelModelagem": ResponsávelModelagem,
                            "ResponsávelDetalhamento": ResponsávelDetalhamento,
                        }

                        salvar_projetos(df_projetos)  # Salva no Google Sheets
                        st.session_state["projeto_selecionado"] = df_projetos.loc[index].to_dict()
                        st.session_state["editando"] = False
                        st.rerun()

                with col2:
                    if st.form_submit_button("Cancelar"):
                        st.session_state["editando"] = False
                        st.rerun()

########################################## FUNCIONÁRIOS ##########################################

# Dados dos funcionários (valor por m² projetado)
FUNCIONARIOS = {
    "Bia": 1.0,  # R$ 1,00 por m²
    "Flávio": 1.0,  # R$ 0,80 por m²
}

# Função para calcular a produtividade dos funcionários
def calcular_produtividade(df_projetos, mes, ano):
    # Filtra os projetos pelo mês e ano
    df_projetos["DataInicio"] = pd.to_datetime(df_projetos["DataInicio"], dayfirst=True, errors='coerce')
    df_projetos_filtrados = df_projetos[
        (df_projetos["DataInicio"].dt.month == mes) & (df_projetos["DataInicio"].dt.year == ano)
    ]

    # Calcula a produtividade de cada funcionário
    produtividade = {funcionario: 0 for funcionario in FUNCIONARIOS}
    for _, row in df_projetos_filtrados.iterrows():
        if row["ResponsávelModelagem"] in FUNCIONARIOS:
            produtividade[row["ResponsávelModelagem"]] += row["m2"]
        if row["ResponsávelDetalhamento"] in FUNCIONARIOS:
            produtividade[row["ResponsávelDetalhamento"]] += row["m2"]

    return produtividade

# Função para exibir a seção de Funcionários
def funcionarios():
    st.title("👥 Funcionários")

    # Carrega os projetos
    df_projetos = carregar_projetos()

    # Selecionar mês e ano para análise
    mes = st.selectbox("Selecione o mês", range(1, 13), index=0)
    ano = st.selectbox("Selecione o ano", range(2020, 2031), index=3)

    # Calcula a produtividade
    produtividade = calcular_produtividade(df_projetos, mes, ano)

    # Cria um DataFrame para exibição
    df_produtividade = pd.DataFrame({
        "Funcionário": list(produtividade.keys()),
        "m² Projetado": list(produtividade.values()),
        "Valor a Receber (R$)": [produtividade[func] * FUNCIONARIOS[func] for func in produtividade]
    })

    # Exibe o DataFrame
    st.write("### Produtividade dos Funcionários")
    st.dataframe(df_produtividade)

    # Gráfico de m² projetado por funcionário
    st.write("### m² Projetado por Funcionário")
    fig_m2 = px.bar(
        df_produtividade,
        x="Funcionário",
        y="m² Projetado",
        title="m² Projetado por Funcionário",
        labels={"Funcionário": "Funcionário", "m² Projetado": "m² Projetado"},
    )
    st.plotly_chart(fig_m2)

    # Gráfico de valor a receber por funcionário
    st.write("### Valor a Receber por Funcionário")
    fig_valor = px.bar(
        df_produtividade,
        x="Funcionário",
        y="Valor a Receber (R$)",
        title="Valor a Receber por Funcionário",
        labels={"Funcionário": "Funcionário", "Valor a Receber (R$)": "Valor a Receber (R$)"},
    )
    st.plotly_chart(fig_valor)

########################################## PÁGINA PRINCIPAL ##########################################

def main_app():
    # st.sidebar.image("imagens/VRZ-LOGO-44.png")
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

########################################## EXECUÇÃO ##########################################

if __name__ == "__main__":
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if st.session_state["logged_in"]:
        main_app()
    else:
        login_screen()