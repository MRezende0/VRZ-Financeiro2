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
import urllib3
import requests
import certifi
import functools
import threading

# Monkey patch SSL para resolver problemas de certificado
# Esta é uma solução mais robusta para o problema de SSL
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

# Aplicar o patch SSL
patch_ssl()

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
    "Categorias_Receitas": "689806911",
    "Categorias_Despesas": "1610275753",
    "Fornecedor_Despesas": "1183581777",
    "Clientes": "1538370660",
    "Funcionarios": "1993815508"
}

COLUNAS_ESPERADAS = {
    "Receitas": ["DataRecebimento", "Descrição", "Projeto", "Categoria", "ValorTotal", "FormaPagamento", "NF"],
    "Despesas": ["DataPagamento", "Descrição", "Categoria", "ValorTotal", "Parcelas", "FormaPagamento", "Responsável", "Fornecedor", "Projeto", "NF"],
    "Projetos": ["Projeto", "Cliente", "Localizacao", "Placa", "Post", "DataInicio", "DataFinal", "Contrato", "Status", "Briefing", "Arquiteto", "Tipo", "Pacote", "m2", "Parcelas", "ValorTotal", "ResponsávelElétrico", "ResponsávelHidráulico", "ResponsávelModelagem", "ResponsávelDetalhamento"],
    "Funcionarios": ["Nome", "Cargo", "Admissão", "Salário", "Contato", "Endereço"],    
    "Clientes": ["Nome", "CPF", "Endereço", "Contato", "TipoNF"],
    "Categorias_Receitas": ["Categoria"],
    "Categorias_Despesas": ["Categoria"],
    "Fornecedor_Despesas": ["Fornecedor"]
}

########################################## DADOS ##########################################

# Inicialização dos dados locais
if 'local_data' not in st.session_state:
    st.session_state.local_data = {
        'receitas': pd.DataFrame(),
        'despesas': pd.DataFrame(),
        'projetos': pd.DataFrame(),
        'categorias_receitas': pd.DataFrame(),
        'categorias_despesas': pd.DataFrame(),
        'fornecedor_despesas': pd.DataFrame(),
        'clientes': pd.DataFrame(),
        'funcionarios': pd.DataFrame()
    }

# Flag para controlar se os dados já foram carregados
if 'dados_carregados' not in st.session_state:
    st.session_state.dados_carregados = False

# Cache para o cliente do Google Sheets
if 'sheets_client' not in st.session_state:
    st.session_state.sheets_client = None

# Cache para a planilha
if 'spreadsheet' not in st.session_state:
    st.session_state.spreadsheet = None

# Cache para as worksheets
if 'worksheets_cache' not in st.session_state:
    st.session_state.worksheets_cache = {}

def conectar_sheets(force_reconnect=False):
    # Se já temos um cliente conectado e não estamos forçando reconexão, retornar o cliente existente
    if not force_reconnect and st.session_state.sheets_client is not None and st.session_state.spreadsheet is not None:
        return st.session_state.spreadsheet
    
    try:
        # Escopo para acesso ao Google Sheets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Carregar credenciais do arquivo secrets.toml
        try:
            # Tentar carregar de secrets primeiro
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
            except:
                # Se não conseguir carregar de secrets, usar valores padrão para desenvolvimento
                return None
            
            # Criar uma sessão personalizada com SSL desativado
            session = requests.Session()
            session.verify = False
            
            # Desativar avisos de SSL
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            
            # Criar credenciais
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            
            # Adicionar a sessão personalizada às credenciais
            creds.session = session
        except Exception as e:
            return None
        
        # Conectar ao Google Sheets com retry
        max_retries = 2  # Reduzido para 2 tentativas para acelerar
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                client = gspread.authorize(creds)
                st.session_state.sheets_client = client
                break
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    return None
                time.sleep(0.5)  # Reduzido para 0.5 segundo
        
        # Abrir a planilha pelo ID com retry
        retry_count = 0
        while retry_count < max_retries:
            try:
                spreadsheet = client.open_by_key(SHEET_ID)
                st.session_state.spreadsheet = spreadsheet
                return spreadsheet
            except Exception as e:
                retry_count += 1
                if retry_count >= max_retries:
                    return None
                time.sleep(0.5)  # Reduzido para 0.5 segundo
    except Exception as e:
        return None

# Função para carregar dados do Google Sheets
def carregar_dados_sheets(sheet_name, force_reload=False):
    try:
        # Verificar se já temos os dados em cache na sessão e não estamos forçando recarga
        if not force_reload and sheet_name.lower() in st.session_state.local_data and not st.session_state.local_data[sheet_name.lower()].empty:
            return st.session_state.local_data[sheet_name.lower()]
        
        # Dados padrão para retornar em caso de falha
        default_data = {
            "Categorias_Receitas": pd.DataFrame({"Categoria": ["Pró-Labore", "Investimentos", "Freelance", "Outros"]}),
            "Categorias_Despesas": pd.DataFrame({"Categoria": ["Fixo", "Variável", "Investimento", "Outros"]}),
            "Fornecedor_Despesas": pd.DataFrame({"Fornecedor": ["Outros"]}),
            "Clientes": pd.DataFrame({"Nome": [""], "CPF": [""]}),
            "Funcionarios": pd.DataFrame({"Nome": [""]})
        }
        
        # Conectar ao Google Sheets
        spreadsheet = conectar_sheets()
        if spreadsheet is None:
            # Se não conseguir conectar, retornar dados padrão se disponíveis
            if sheet_name in default_data:
                df = default_data[sheet_name]
                st.session_state.local_data[sheet_name.lower()] = df
                return df
            return pd.DataFrame()
        
        # Verificar se a worksheet está em cache
        if sheet_name in st.session_state.worksheets_cache:
            worksheet = st.session_state.worksheets_cache[sheet_name]
        else:
            # Abrir a aba específica
            try:
                # Tentar acessar a planilha pelo GID primeiro (mais confiável)
                if sheet_name in SHEET_GIDS:
                    gid = SHEET_GIDS[sheet_name]
                    
                    # Se já temos as worksheets em cache, não precisamos buscar todas novamente
                    if 'all_worksheets' not in st.session_state:
                        st.session_state.all_worksheets = spreadsheet.worksheets()
                    
                    # Encontrar a worksheet com o GID correspondente
                    worksheet = None
                    for ws in st.session_state.all_worksheets:
                        if ws.id == gid:
                            worksheet = ws
                            break
                    
                    # Se não encontrou pelo GID, tenta pelo nome
                    if worksheet is None:
                        worksheet = spreadsheet.worksheet(sheet_name)
                else:
                    # Se não tiver GID definido, tenta pelo nome
                    worksheet = spreadsheet.worksheet(sheet_name)
                
                # Adicionar ao cache
                st.session_state.worksheets_cache[sheet_name] = worksheet
                
            except Exception as e:
                # Tentar criar a planilha se ela não existir
                try:
                    if sheet_name == "Categorias_Receitas":
                        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=20)
                        # Adicionar cabeçalho
                        worksheet.append_row(["Categoria"])
                        # Adicionar categorias padrão
                        for categoria in ["Pró-Labore", "Investimentos", "Freelance", "Outros"]:
                            worksheet.append_row([categoria])
                        df = default_data["Categorias_Receitas"]
                        # Armazenar no cache da sessão
                        st.session_state.local_data[sheet_name.lower()] = df
                        # Adicionar ao cache de worksheets
                        st.session_state.worksheets_cache[sheet_name] = worksheet
                        return df
                    elif sheet_name == "Categorias_Despesas":
                        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=20)
                        # Adicionar cabeçalho
                        worksheet.append_row(["Categoria"])
                        # Adicionar categorias padrão
                        for categoria in ["Fixo", "Variável", "Investimento", "Outros"]:
                            worksheet.append_row([categoria])
                        df = default_data["Categorias_Despesas"]
                        # Armazenar no cache da sessão
                        st.session_state.local_data[sheet_name.lower()] = df
                        # Adicionar ao cache de worksheets
                        st.session_state.worksheets_cache[sheet_name] = worksheet
                        return df
                    elif sheet_name == "Fornecedor_Despesas":
                        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=20)
                        # Adicionar cabeçalho
                        worksheet.append_row(["Fornecedor"])
                        # Adicionar fornecedor padrão
                        worksheet.append_row(["Outros"])
                        df = default_data["Fornecedor_Despesas"]
                        # Armazenar no cache da sessão
                        st.session_state.local_data[sheet_name.lower()] = df
                        # Adicionar ao cache de worksheets
                        st.session_state.worksheets_cache[sheet_name] = worksheet
                        return df
                    elif sheet_name == "Clientes":
                        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=20)
                        # Adicionar cabeçalho
                        worksheet.append_row(["Nome", "CPF", "Endereço", "Contato", "TipoNF"])
                        df = default_data["Clientes"]
                        # Armazenar no cache da sessão
                        st.session_state.local_data[sheet_name.lower()] = df
                        # Adicionar ao cache de worksheets
                        st.session_state.worksheets_cache[sheet_name] = worksheet
                        return df
                    elif sheet_name == "Funcionarios":
                        worksheet = spreadsheet.add_worksheet(title=sheet_name, rows=100, cols=20)
                        # Adicionar cabeçalho
                        worksheet.append_row(["Nome", "Cargo", "Admissão", "Salário", "Contato", "Endereço"])
                        df = default_data["Funcionarios"]
                        # Armazenar no cache da sessão
                        st.session_state.local_data[sheet_name.lower()] = df
                        # Adicionar ao cache de worksheets
                        st.session_state.worksheets_cache[sheet_name] = worksheet
                        return df
                    else:
                        return pd.DataFrame()
                except Exception as e:
                    # Se não conseguir criar, retorna dados padrão se disponíveis
                    if sheet_name in default_data:
                        df = default_data[sheet_name]
                        st.session_state.local_data[sheet_name.lower()] = df
                        return df
                    return pd.DataFrame()
        
        # Obter todos os dados
        data = worksheet.get_all_records()
        
        # Converter para DataFrame
        df = pd.DataFrame(data)
        
        # Armazenar no cache da sessão
        st.session_state.local_data[sheet_name.lower()] = df
        
        return df
    except Exception as e:
        # Em caso de erro, retornar dados padrão se disponíveis
        if sheet_name in default_data:
            df = default_data[sheet_name]
            st.session_state.local_data[sheet_name.lower()] = df
            return df
        return pd.DataFrame()

# Função para salvar dados no Google Sheets
def salvar_dados_sheets(df, sheet_name):
    """
    Salva um DataFrame no Google Sheets.
    
    Args:
        df: DataFrame do pandas com os dados a serem salvos
        sheet_name: Nome da planilha onde os dados serão salvos
    
    Returns:
        bool: True se os dados foram salvos com sucesso, False caso contrário
    """
    try:
        # Conectar ao Google Sheets
        spreadsheet = conectar_sheets()
        if spreadsheet is None:
            st.error(f"Não foi possível conectar ao Google Sheets para salvar os dados em {sheet_name}.")
            return False
        
        # Verificar se a worksheet está em cache
        if sheet_name in st.session_state.worksheets_cache:
            worksheet = st.session_state.worksheets_cache[sheet_name]
        else:
            # Abrir a aba específica
            try:
                # Tentar acessar a planilha pelo GID primeiro (mais confiável)
                if sheet_name in SHEET_GIDS:
                    gid = SHEET_GIDS[sheet_name]
                    
                    # Se já temos as worksheets em cache, não precisamos buscar todas novamente
                    if 'all_worksheets' not in st.session_state:
                        st.session_state.all_worksheets = spreadsheet.worksheets()
                    
                    # Encontrar a worksheet com o GID correspondente
                    worksheet = None
                    for ws in st.session_state.all_worksheets:
                        if ws.id == gid:
                            worksheet = ws
                            break
                    
                    # Se não encontrou pelo GID, tenta pelo nome
                    if worksheet is None:
                        worksheet = spreadsheet.worksheet(sheet_name)
                else:
                    # Se não tiver GID definido, tenta pelo nome
                    worksheet = spreadsheet.worksheet(sheet_name)
                
                # Adicionar ao cache
                st.session_state.worksheets_cache[sheet_name] = worksheet
                
            except Exception as e:
                st.error(f"Erro ao acessar a planilha {sheet_name}: {str(e)}")
                return False
        
        # Limpar a planilha, mas manter o cabeçalho
        try:
            # Obter o número de linhas na planilha
            all_values = worksheet.get_all_values()
            if len(all_values) > 1:  # Se tiver mais que o cabeçalho
                # Limpar todas as linhas exceto o cabeçalho
                worksheet.delete_rows(2, len(all_values))
        except Exception as e:
            st.error(f"Erro ao limpar a planilha {sheet_name}: {str(e)}")
            # Continuar mesmo com erro, pois pode ser que a planilha esteja vazia
        
        # Verificar se o DataFrame está vazio
        if df.empty:
            # Atualizar o cache local
            st.session_state.local_data[sheet_name.lower()] = df
            return True
        
        # Preparar os dados para salvar
        # Primeiro, converter o DataFrame para uma lista de listas
        # A primeira lista contém os nomes das colunas
        header = df.columns.tolist()
        
        # Verificar se o cabeçalho atual da planilha corresponde ao do DataFrame
        try:
            current_header = worksheet.row_values(1)
            if current_header != header:
                # Se o cabeçalho for diferente, atualizar o cabeçalho
                worksheet.update('A1', [header])
        except Exception as e:
            # Se não conseguir obter o cabeçalho atual, apenas atualiza
            worksheet.update('A1', [header])
        
        # Converter os valores do DataFrame para lista de listas
        values = df.values.tolist()
        
        # Adicionar os dados à planilha
        if values:  # Verificar se há valores para adicionar
            try:
                # Adicionar linha por linha para evitar problemas com tipos de dados
                for i, row in enumerate(values, start=2):  # Começar da linha 2 (após o cabeçalho)
                    # Converter valores para string para evitar problemas de tipo
                    row_str = [str(val) if val is not None else "" for val in row]
                    worksheet.update(f'A{i}', [row_str])
            except Exception as e:
                st.error(f"Erro ao adicionar dados à planilha {sheet_name}: {str(e)}")
                return False
        
        # Atualizar o cache local
        st.session_state.local_data[sheet_name.lower()] = df
        
        return True
    except Exception as e:
        st.error(f"Erro ao salvar dados na planilha {sheet_name}: {str(e)}")
        return False

# Função para adicionar uma linha ao Google Sheets
def adicionar_linha_sheets(nova_linha, sheet_name):
    """
    Adiciona uma nova linha de dados ao Google Sheets.
    
    Args:
        nova_linha: Dicionário com os dados a serem adicionados
        sheet_name: Nome da planilha onde os dados serão adicionados
    
    Returns:
        bool: True se os dados foram adicionados com sucesso, False caso contrário
    """
    try:
        # Conectar ao Google Sheets
        spreadsheet = conectar_sheets()
        if spreadsheet is None:
            st.error(f"Não foi possível conectar ao Google Sheets para adicionar dados em {sheet_name}.")
            return False
        
        # Verificar se a worksheet está em cache
        if sheet_name in st.session_state.worksheets_cache:
            worksheet = st.session_state.worksheets_cache[sheet_name]
        else:
            # Abrir a aba específica
            try:
                # Tentar acessar a planilha pelo GID primeiro (mais confiável)
                if sheet_name in SHEET_GIDS:
                    gid = SHEET_GIDS[sheet_name]
                    
                    # Se já temos as worksheets em cache, não precisamos buscar todas novamente
                    if 'all_worksheets' not in st.session_state:
                        st.session_state.all_worksheets = spreadsheet.worksheets()
                    
                    # Encontrar a worksheet com o GID correspondente
                    worksheet = None
                    for ws in st.session_state.all_worksheets:
                        if ws.id == gid:
                            worksheet = ws
                            break
                    
                    # Se não encontrou pelo GID, tenta pelo nome
                    if worksheet is None:
                        worksheet = spreadsheet.worksheet(sheet_name)
                else:
                    # Se não tiver GID definido, tenta pelo nome
                    worksheet = spreadsheet.worksheet(sheet_name)
                
                # Adicionar ao cache
                st.session_state.worksheets_cache[sheet_name] = worksheet
                
            except Exception as e:
                st.error(f"Erro ao acessar a planilha {sheet_name}: {str(e)}")
                return False
        
        # Obter os dados atuais para verificar o cabeçalho
        try:
            # Obter o cabeçalho atual
            header = worksheet.row_values(1)
            
            # Se o cabeçalho estiver vazio, usar as chaves do dicionário como cabeçalho
            if not header:
                header = list(nova_linha.keys())
                worksheet.update('A1', [header])
        except Exception as e:
            # Se não conseguir obter o cabeçalho, usar as chaves do dicionário
            header = list(nova_linha.keys())
            worksheet.update('A1', [header])
        
        # Preparar a nova linha de acordo com o cabeçalho
        nova_linha_valores = []
        for coluna in header:
            if coluna in nova_linha:
                nova_linha_valores.append(str(nova_linha[coluna]) if nova_linha[coluna] is not None else "")
            else:
                nova_linha_valores.append("")  # Valor vazio para colunas que não estão no dicionário
        
        # Adicionar a nova linha à planilha
        try:
            # Obter o número atual de linhas
            all_values = worksheet.get_all_values()
            next_row = len(all_values) + 1
            
            # Adicionar a nova linha
            worksheet.update(f'A{next_row}', [nova_linha_valores])
            
            # Atualizar o cache local
            if sheet_name.lower() in st.session_state.local_data:
                df = st.session_state.local_data[sheet_name.lower()]
                # Criar um DataFrame com a nova linha
                nova_linha_df = pd.DataFrame([nova_linha])
                # Concatenar com o DataFrame existente
                df = pd.concat([df, nova_linha_df], ignore_index=True)
                # Atualizar o cache
                st.session_state.local_data[sheet_name.lower()] = df
            
            return True
        except Exception as e:
            st.error(f"Erro ao adicionar linha à planilha {sheet_name}: {str(e)}")
            return False
    
    except Exception as e:
        st.error(f"Erro ao adicionar linha à planilha {sheet_name}: {str(e)}")
        return False

# Função para carregar dados sob demanda
def carregar_dados_sob_demanda(sheet_name):
    """
    Carrega dados de uma planilha específica apenas quando necessário
    """
    # Inicializar o dicionário de dados locais se não existir
    if "local_data" not in st.session_state:
        st.session_state.local_data = {}
    
    # Normalizar o nome da planilha para evitar problemas de case
    sheet_name_lower = sheet_name.lower()
    
    # Se os dados já estiverem em cache e não estiverem vazios, retorna do cache
    if sheet_name_lower in st.session_state.local_data and not st.session_state.local_data[sheet_name_lower].empty:
        return st.session_state.local_data[sheet_name_lower]
    
    try:
        # Tenta carregar os dados do Google Sheets
        df = carregar_dados_sheets(sheet_name)
        
        # Processar dados específicos conforme necessário
        if sheet_name == "Receitas" and not df.empty and "DataRecebimento" in df.columns:
            df["DataRecebimento"] = pd.to_datetime(df["DataRecebimento"], dayfirst=True, errors="coerce")
        elif sheet_name == "Despesas" and not df.empty and "DataPagamento" in df.columns:
            df["DataPagamento"] = pd.to_datetime(df["DataPagamento"], dayfirst=True, errors="coerce")
        elif sheet_name == "Projetos" and not df.empty:
            if "DataInicio" in df.columns:
                df["DataInicio"] = pd.to_datetime(df["DataInicio"], dayfirst=True, errors="coerce")
            if "DataFinal" in df.columns:
                df["DataFinal"] = pd.to_datetime(df["DataFinal"], dayfirst=True, errors="coerce")
            if "Projeto" in df.columns:
                df = df.sort_values("Projeto")
        
        # Armazenar no cache
        st.session_state.local_data[sheet_name_lower] = df
        return df
    except Exception as e:
        # Em caso de erro, retornar um DataFrame padrão ou vazio
        if sheet_name == "Categorias_Receitas":
            df = pd.DataFrame({"Categoria": ["Pró-Labore", "Investimentos", "Freelance", "Outros"]})
        elif sheet_name == "Categorias_Despesas":
            df = pd.DataFrame({"Categoria": ["Fixo", "Variável", "Investimento", "Outros"]})
        elif sheet_name == "Fornecedor_Despesas":
            df = pd.DataFrame({"Fornecedor": ["Outros"]})
        elif sheet_name == "Receitas" or sheet_name == "Despesas":
            df = pd.DataFrame({"DataRecebimento" if sheet_name == "Receitas" else "DataPagamento": [], 
                              "Descrição": [], "Categoria": [], "ValorTotal": []})
        elif sheet_name == "Projetos":
            df = pd.DataFrame({"Projeto": [], "Cliente": [], "Status": []})
        elif sheet_name == "Clientes":
            df = pd.DataFrame({"Nome": [], "CPF": [], "Endereço": [], "Contato": [], "TipoNF": []})
        elif sheet_name == "Funcionarios":
            df = pd.DataFrame({"Nome": [], "Cargo": [], "Admissão": [], "Salário": [], "Contato": [], "Endereço": []})
        else:
            df = pd.DataFrame()
        
        # Armazenar o DataFrame padrão no cache
        st.session_state.local_data[sheet_name_lower] = df
        return df

# Função para carregar dados iniciais (chamada após login bem-sucedido)
def carregar_dados_iniciais():
    # Evitar carregar os dados novamente se já foram carregados
    if st.session_state.dados_carregados:
        return
    
    # Marcar os dados como carregados para evitar carregamentos repetidos
    st.session_state.dados_carregados = True
    
    # Carregar apenas os dados essenciais para o funcionamento inicial
    # Outros dados serão carregados sob demanda quando necessário
    try:
        # Carregar categorias de receitas em segundo plano
        if 'categorias_receitas' in st.session_state.local_data and st.session_state.local_data['categorias_receitas'].empty:
            st.session_state.local_data['categorias_receitas'] = pd.DataFrame({"Categoria": ["Pró-Labore", "Investimentos", "Freelance", "Outros"]})
        
        # Carregar fornecedores de despesas em segundo plano
        if 'fornecedor_despesas' in st.session_state.local_data and st.session_state.local_data['fornecedor_despesas'].empty:
            st.session_state.local_data['fornecedor_despesas'] = pd.DataFrame({"Fornecedor": ["Outros"]})
        
        # Iniciar thread para carregar dados em segundo plano
        threading.Thread(target=carregar_dados_background, daemon=True).start()
    except Exception as e:
        pass

# Função para carregar dados em segundo plano
def carregar_dados_background():
    try:
        # Conectar ao Google Sheets se ainda não estiver conectado
        if st.session_state.spreadsheet is None:
            conectar_sheets()
        
        # Carregar categorias de receitas
        carregar_dados_sheets("Categorias_Receitas")
        
        # Carregar fornecedores de despesas
        carregar_dados_sheets("Fornecedor_Despesas")
    except Exception as e:
        pass

# Função de login
def login(email, senha):
    if email in USER_CREDENTIALS and USER_CREDENTIALS[email] == senha:
        return True
    return False

# Tela de Login
def login_screen():
    # st.title("🔐 Login - VRZ Gestão Financeira")
    st.markdown("Por favor, insira suas credenciais para acessar o sistema.")
    
    # Formulário de login
    with st.form("login_form"):
        email = st.text_input("E-mail")
        password = st.text_input("Senha", type="password")
        submit = st.form_submit_button("Entrar")
    
    if submit:
        if login(email, password):
            # Definir o estado de login antes de qualquer outra operação
            st.session_state["logged_in"] = True
            
            # Iniciar conexão com Google Sheets em segundo plano
            conectar_sheets()
            
            # Marcar que os dados serão carregados após o redirecionamento
            st.session_state.carregar_dados_apos_login = True
            
            # Mensagem de sucesso
            st.success("Login feito com sucesso!")
            
            # Redirecionar para a página principal sem esperar pelo carregamento dos dados
            st.rerun()
        else:
            st.error("Credenciais inválidas. Verifique seu e-mail e senha.")

########################################## TRANSAÇÕES ##########################################

# Função para salvar dados
def salvar_dados(df, sheet_name):
    return salvar_dados_sheets(df, sheet_name)

# Tela de Registrar Receita
def registrar_receita():
    st.subheader("📈 Receita")
    
    # Carregar dados necessários
    df_categorias_receitas = carregar_dados_sob_demanda("Categorias_Receitas")
    df_projetos = carregar_dados_sob_demanda("Projetos")
    
    # Verificar se os dados foram carregados corretamente
    if df_categorias_receitas.empty or "Categoria" not in df_categorias_receitas.columns:
        df_categorias_receitas = pd.DataFrame({"Categoria": ["Pró-Labore", "Investimentos", "Freelance", "Outros"]})
    
    with st.form("nova_receita"):
        col1, col2 = st.columns(2)
        
        with col1:
            data_recebimento = st.date_input("Data de Recebimento", datetime.now())
            descricao = st.text_input("Descrição")
            categoria = st.selectbox("Categoria", df_categorias_receitas["Categoria"].tolist())
            
        with col2:
            valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
            forma_pagamento = st.selectbox("Forma de Pagamento", ["Pix", "Transferência", "Dinheiro", "Cheque", "Cartão de Crédito", "Outros"])
            projeto = st.selectbox("Projeto", [""] + list(df_projetos["Projeto"]) if not df_projetos.empty and "Projeto" in df_projetos.columns else [""])
        
        # Botão para adicionar nova categoria
        nova_categoria = st.text_input("Adicionar Nova Categoria")
        
        # Botões de ação
        col1, col2 = st.columns(2)
        with col1:
            add_categoria = st.form_submit_button("Adicionar Categoria")
        with col2:
            submit_receita = st.form_submit_button("Salvar Receita")
            
        if add_categoria:
            if nova_categoria and nova_categoria not in df_categorias_receitas["Categoria"].values:
                nova_categoria_df = pd.DataFrame({"Categoria": [nova_categoria]})
                df_categorias_receitas = pd.concat([df_categorias_receitas, nova_categoria_df], ignore_index=True)
                salvar_categorias(df_categorias_receitas, "Categorias_Receitas")
                st.success(f"Categoria '{nova_categoria}' adicionada com sucesso!")
            else:
                st.warning("Categoria já existe ou está vazia.")
            
        if submit_receita:
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
    # Carregar dados necessários
    df_categorias_despesas = carregar_dados_sob_demanda("Categorias_Despesas")
    df_fornecedor_despesas = carregar_dados_sob_demanda("Fornecedor_Despesas")
    df_projetos = carregar_dados_sob_demanda("Projetos")
    
    st.subheader("📤 Despesa")
    
    # Formulário para adicionar nova despesa
    with st.form("nova_despesa"):
        col1, col2 = st.columns(2)
        
        with col1:
            data_pagamento = st.date_input("Data de Pagamento", datetime.now())
            descricao = st.text_input("Descrição")
            categoria = st.selectbox("Categoria", df_categorias_despesas["Categoria"].tolist() if not df_categorias_despesas.empty else ["Alimentação", "Transporte", "Moradia", "Saúde", "Educação", "Lazer", "Outros"])
            fornecedor = st.selectbox("Fornecedor", df_fornecedor_despesas["Fornecedor"].tolist() if not df_fornecedor_despesas.empty else ["Outros"])
            
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
            return True
        else:
            st.error("Erro ao salvar os projetos.")
            return False
    except Exception as e:
        st.error(f"Erro ao salvar projetos: {e}")
        return False

# Tela de Registrar Projeto
def registrar_projeto():
    # Carregar dados necessários
    df_projetos = carregar_dados_sob_demanda("Projetos")
    
    st.subheader("🏗️ Projeto")

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

# Função para registrar cliente
def registrar_cliente():
    st.subheader("👤 Cliente")
    
    # Carregar dados existentes
    try:
        df_clientes = carregar_dados_sob_demanda("Clientes")
        
        # Verificar se o DataFrame está vazio ou não existe
        if df_clientes.empty:
            df_clientes = pd.DataFrame(columns=["Nome", "CPF", "Endereço", "Contato", "TipoNF"])
        
        # Converter todas as colunas para string para evitar problemas de tipo
        for col in df_clientes.columns:
            df_clientes[col] = df_clientes[col].astype(str)
        
        # Flag para controlar se um novo cliente foi adicionado
        novo_cliente_adicionado = False
        novo_cliente_dados = {}
        
        # Formulário para adicionar novo cliente
        with st.form("novo_cliente"):
            col1, col2 = st.columns(2)
            
            with col1:
                nome = st.text_input("Nome")
                cpf = st.text_input("CPF")
                endereco = st.text_input("Endereço")
            
            with col2:
                contato = st.text_input("Contato")
                tipo_nf = st.selectbox("Tipo de Nota Fiscal", ["Pessoa Física", "Pessoa Jurídica", "Não Aplicável"])
            
            submit_cliente = st.form_submit_button("Salvar Cliente")
            
            if submit_cliente:
                # Validar dados
                if not nome:
                    st.error("O nome do cliente é obrigatório.")
                else:
                    # Criar dicionário com os dados do novo cliente
                    novo_cliente = {
                        "Nome": nome,
                        "CPF": str(cpf),  # Garantir que CPF seja string
                        "Endereço": endereco,
                        "Contato": contato,
                        "TipoNF": tipo_nf
                    }
                    
                    # Adicionar ao Google Sheets
                    try:
                        if adicionar_linha_sheets(novo_cliente, "Clientes"):
                            st.success("Cliente registrado com sucesso!")
                            # Adicionar o novo cliente ao DataFrame local para exibição imediata
                            novo_cliente_df = pd.DataFrame([novo_cliente])
                            df_clientes = pd.concat([df_clientes, novo_cliente_df], ignore_index=True)
                            # Atualizar o cache
                            st.session_state.local_data["clientes"] = df_clientes
                            novo_cliente_adicionado = True
                            novo_cliente_dados = novo_cliente
                        else:
                            st.error("Erro ao registrar cliente.")
                    except Exception as e:
                        st.error(f"Erro ao registrar cliente: {str(e)}")
        
        st.divider()

        # Exibir clientes existentes em uma tabela editável
        st.subheader("Clientes Cadastrados")
        
        if not df_clientes.empty:
            # Garantir que todas as colunas necessárias existam
            for col in ["Nome", "CPF", "Endereço", "Contato", "TipoNF"]:
                if col not in df_clientes.columns:
                    df_clientes[col] = ""
            
            # Criar uma cópia editável do DataFrame
            try:
                edited_df = st.data_editor(
                    df_clientes,
                    use_container_width=True,
                    num_rows="dynamic",
                    column_config={
                        "Nome": st.column_config.TextColumn("Nome", width="medium"),
                        "CPF": st.column_config.TextColumn("CPF", width="small"),
                        "Endereço": st.column_config.TextColumn("Endereço", width="large"),
                        "Contato": st.column_config.TextColumn("Contato", width="medium"),
                        "TipoNF": st.column_config.SelectboxColumn(
                            "Tipo NF", 
                            options=["Pessoa Física", "Pessoa Jurídica", "Não Aplicável"],
                            width="medium"
                        )
                    },
                    hide_index=True
                )
                
                # Verificar se houve alterações no DataFrame
                if not edited_df.equals(df_clientes):
                    if st.button("Salvar Alterações"):
                        try:
                            if salvar_dados_sheets(edited_df, "Clientes"):
                                st.success("Alterações salvas com sucesso!")
                                # Atualizar o cache
                                st.session_state.local_data["clientes"] = edited_df
                            else:
                                st.error("Erro ao salvar alterações.")
                        except Exception as e:
                            st.error(f"Erro ao salvar alterações: {str(e)}")
            except Exception as e:
                st.error(f"Erro ao exibir tabela de clientes: {str(e)}")
                st.info("Tente recarregar a página ou verificar a estrutura dos dados.")
        else:
            st.info("Nenhum cliente cadastrado.")
    except Exception as e:
        st.error(f"Erro ao acessar a planilha Clientes: {str(e)}. Verifique as credenciais de acesso ao Google Sheets.")

# Função para registrar funcionário
def registrar_funcionario():
    st.subheader("👷 Funcionário")
    
    # Carregar dados existentes
    try:
        df_funcionarios = carregar_dados_sob_demanda("Funcionarios")
        
        # Verificar se o DataFrame está vazio ou não existe
        if df_funcionarios.empty:
            df_funcionarios = pd.DataFrame(columns=["Nome", "Cargo", "Admissão", "Salário", "Contato", "Endereço"])
        
        # Formulário para adicionar novo funcionário
        with st.form("novo_funcionario"):
            col1, col2 = st.columns(2)
            
            with col1:
                nome = st.text_input("Nome")
                cargo = st.text_input("Cargo")
                data_admissao = st.date_input("Data de Admissão", datetime.now())
            
            with col2:
                salario = st.number_input("Salário (R$)", min_value=0.0, format="%.2f")
                contato = st.text_input("Contato")
                endereco = st.text_input("Endereço")
            
            submit_funcionario = st.form_submit_button("Salvar Funcionário")
            
            if submit_funcionario:
                # Validar dados
                if not nome:
                    st.error("O nome do funcionário é obrigatório.")
                else:
                    # Criar dicionário com os dados do novo funcionário
                    novo_funcionario = {
                        "Nome": nome,
                        "Cargo": cargo,
                        "Admissão": data_admissao.strftime("%d/%m/%Y"),
                        "Salário": str(salario),  # Converter para string
                        "Contato": contato,
                        "Endereço": endereco
                    }
                    
                    # Adicionar diretamente à planilha usando gspread
                    try:
                        # Obter a planilha
                        spreadsheet = conectar_sheets()
                        if spreadsheet:
                            # Obter a worksheet
                            try:
                                worksheet = spreadsheet.worksheet("Funcionarios")
                            except:
                                # Se a worksheet não existir, criar uma nova
                                worksheet = spreadsheet.add_worksheet(title="Funcionarios", rows=100, cols=20)
                                # Adicionar cabeçalho
                                worksheet.append_row(["Nome", "Cargo", "Admissão", "Salário", "Contato", "Endereço"])
                            
                            # Adicionar a nova linha
                            worksheet.append_row([
                                novo_funcionario["Nome"],
                                novo_funcionario["Cargo"],
                                novo_funcionario["Admissão"],
                                novo_funcionario["Salário"],
                                novo_funcionario["Contato"],
                                novo_funcionario["Endereço"]
                            ])
                            
                            st.success("Funcionário registrado com sucesso!")
                            # Adicionar o novo funcionário ao DataFrame local para exibição imediata
                            novo_funcionario_df = pd.DataFrame([novo_funcionario])
                            df_funcionarios = pd.concat([df_funcionarios, novo_funcionario_df], ignore_index=True)
                            # Atualizar o cache
                            st.session_state.local_data["funcionarios"] = df_funcionarios
                        else:
                            st.error("Erro ao conectar ao Google Sheets. Verifique as credenciais.")
                    except Exception as e:
                        st.error(f"Erro ao registrar funcionário: {str(e)}")
        
        st.divider()
        
        # Exibir funcionários existentes em uma tabela editável
        st.subheader("Funcionários Cadastrados")
        
        if not df_funcionarios.empty:
            # Garantir que todas as colunas necessárias existam
            for col in ["Nome", "Cargo", "Admissão", "Salário", "Contato", "Endereço"]:
                if col not in df_funcionarios.columns:
                    df_funcionarios[col] = ""
            
            # Converter todas as colunas para string para evitar problemas de tipo
            for col in df_funcionarios.columns:
                df_funcionarios[col] = df_funcionarios[col].astype(str)
            
            # Criar uma cópia editável do DataFrame
            try:
                edited_df = st.data_editor(
                    df_funcionarios,
                    use_container_width=True,
                    num_rows="dynamic",
                    column_config={
                        "Nome": st.column_config.TextColumn("Nome", width="medium"),
                        "Cargo": st.column_config.TextColumn("Cargo", width="medium"),
                        "Admissão": st.column_config.TextColumn("Admissão", width="small"),
                        "Salário": st.column_config.TextColumn("Salário", width="small"),
                        "Contato": st.column_config.TextColumn("Contato", width="medium"),
                        "Endereço": st.column_config.TextColumn("Endereço", width="large")
                    },
                    hide_index=True
                )
                
                # Verificar se houve alterações no DataFrame
                if not edited_df.equals(df_funcionarios):
                    if st.button("Salvar Alterações"):
                        try:
                            if salvar_dados_sheets(edited_df, "Funcionarios"):
                                st.success("Alterações salvas com sucesso!")
                                # Atualizar o cache
                                st.session_state.local_data["funcionarios"] = edited_df
                            else:
                                st.error("Erro ao salvar alterações. Verifique as credenciais de acesso ao Google Sheets.")
                        except Exception as e:
                            st.error(f"Erro ao salvar alterações: {str(e)}")
            except Exception as e:
                st.error(f"Erro ao exibir tabela de funcionários: {str(e)}")
                st.info("Tente recarregar a página ou verificar a estrutura dos dados.")
        else:
            st.info("Nenhum funcionário cadastrado.")
    except Exception as e:
        st.error(f"Erro ao acessar a planilha Funcionarios: {str(e)}. Verifique as credenciais de acesso ao Google Sheets.")

# Função para registrar categoria
def registrar_categoria():
    st.subheader("🏷️ Categorias")
    
    # Tabs para separar categorias de receitas e despesas
    tab_receitas, tab_despesas = st.tabs(["Categorias de Receitas", "Categorias de Despesas"])
    
    with tab_receitas:
        # Carregar categorias de receitas
        df_categorias_receitas = carregar_dados_sob_demanda("Categorias_Receitas")
        
        # Verificar se o DataFrame está vazio ou não existe
        if df_categorias_receitas.empty:
            df_categorias_receitas = pd.DataFrame({"Categoria": ["Pró-Labore", "Investimentos", "Freelance", "Outros"]})
        
        # Formulário para adicionar nova categoria
        with st.form("nova_categoria_receita"):
            nova_categoria = st.text_input("Nova Categoria de Receita")
            submit_categoria = st.form_submit_button("Adicionar Categoria")
            
            if submit_categoria:
                if nova_categoria and nova_categoria not in df_categorias_receitas["Categoria"].values:
                    nova_categoria_df = pd.DataFrame({"Categoria": [nova_categoria]})
                    df_categorias_receitas = pd.concat([df_categorias_receitas, nova_categoria_df], ignore_index=True)
                    
                    if salvar_dados_sheets(df_categorias_receitas, "Categorias_Receitas"):
                        st.success(f"Categoria '{nova_categoria}' adicionada com sucesso!")
                        # Atualizar o cache
                        st.session_state.local_data["categorias_receitas"] = df_categorias_receitas
                    else:
                        st.error("Erro ao adicionar categoria.")
                else:
                    st.warning("Categoria já existe ou está vazia.")
        
        # Exibir categorias existentes em uma tabela editável
        st.subheader("Categorias de Receitas")
        
        edited_df_receitas = st.data_editor(
            df_categorias_receitas,
            use_container_width=True,
            num_rows="dynamic",
            hide_index=True
        )
        
        # Verificar se houve alterações no DataFrame
        if not edited_df_receitas.equals(df_categorias_receitas):
            if st.button("Salvar Alterações (Receitas)"):
                if salvar_dados_sheets(edited_df_receitas, "Categorias_Receitas"):
                    st.success("Alterações salvas com sucesso!")
                    # Atualizar o cache
                    st.session_state.local_data["categorias_receitas"] = edited_df_receitas
                else:
                    st.error("Erro ao salvar alterações.")
    
    with tab_despesas:
        # Carregar categorias de despesas
        df_categorias_despesas = carregar_dados_sob_demanda("Categorias_Despesas")
        
        # Verificar se o DataFrame está vazio ou não existe
        if df_categorias_despesas.empty:
            df_categorias_despesas = pd.DataFrame({"Categoria": ["Aluguel", "Água", "Luz", "Internet", "Materiais", "Salários", "Impostos", "Outros"]})
        
        # Formulário para adicionar nova categoria
        with st.form("nova_categoria_despesa"):
            nova_categoria = st.text_input("Nova Categoria de Despesa")
            submit_categoria = st.form_submit_button("Adicionar Categoria")
            
            if submit_categoria:
                if nova_categoria and nova_categoria not in df_categorias_despesas["Categoria"].values:
                    nova_categoria_df = pd.DataFrame({"Categoria": [nova_categoria]})
                    df_categorias_despesas = pd.concat([df_categorias_despesas, nova_categoria_df], ignore_index=True)
                    
                    if salvar_dados_sheets(df_categorias_despesas, "Categorias_Despesas"):
                        st.success(f"Categoria '{nova_categoria}' adicionada com sucesso!")
                        # Atualizar o cache
                        st.session_state.local_data["categorias_despesas"] = df_categorias_despesas
                    else:
                        st.error("Erro ao adicionar categoria.")
                else:
                    st.warning("Categoria já existe ou está vazia.")
        
        # Exibir categorias existentes em uma tabela editável
        st.subheader("Categorias de Despesas")
        
        edited_df_despesas = st.data_editor(
            df_categorias_despesas,
            use_container_width=True,
            num_rows="dynamic",
            hide_index=True
        )
        
        # Verificar se houve alterações no DataFrame
        if not edited_df_despesas.equals(df_categorias_despesas):
            if st.button("Salvar Alterações (Despesas)"):
                if salvar_dados_sheets(edited_df_despesas, "Categorias_Despesas"):
                    st.success("Alterações salvas com sucesso!")
                    # Atualizar o cache
                    st.session_state.local_data["categorias_despesas"] = edited_df_despesas
                else:
                    st.error("Erro ao salvar alterações.")

# Função para registrar fornecedor
def registrar_fornecedor():
    st.subheader("🏢 Fornecedores")
    
    # Carregar fornecedores existentes
    df_fornecedores = carregar_dados_sob_demanda("Fornecedor_Despesas")
    
    # Verificar se o DataFrame está vazio ou não existe
    if df_fornecedores.empty:
        df_fornecedores = pd.DataFrame({"Fornecedor": ["Outros"]})
    
    # Formulário para adicionar novo fornecedor
    with st.form("novo_fornecedor"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome_fornecedor = st.text_input("Nome do Fornecedor")
        
        with col2:
            categoria_fornecedor = st.selectbox("Categoria", ["Material", "Serviço", "Utilidades", "Outros"])
        
        submit_fornecedor = st.form_submit_button("Adicionar Fornecedor")
        
        if submit_fornecedor:
            if nome_fornecedor and nome_fornecedor not in df_fornecedores["Fornecedor"].values:
                # Verificar se precisamos adicionar a coluna Categoria
                if "Categoria" not in df_fornecedores.columns:
                    df_fornecedores["Categoria"] = "Outros"
                
                novo_fornecedor_df = pd.DataFrame({"Fornecedor": [nome_fornecedor], "Categoria": [categoria_fornecedor]})
                df_fornecedores = pd.concat([df_fornecedores, novo_fornecedor_df], ignore_index=True)
                
                if salvar_dados_sheets(df_fornecedores, "Fornecedor_Despesas"):
                    st.success(f"Fornecedor '{nome_fornecedor}' adicionado com sucesso!")
                    # Atualizar o cache
                    st.session_state.local_data["fornecedor_despesas"] = df_fornecedores
                else:
                    st.error("Erro ao adicionar fornecedor.")
            else:
                st.warning("Fornecedor já existe ou está vazio.")
    
    # Exibir fornecedores existentes em uma tabela editável
    st.subheader("Fornecedores Cadastrados")
    
    # Adicionar coluna de categoria se não existir
    if "Categoria" not in df_fornecedores.columns:
        df_fornecedores["Categoria"] = "Outros"
    
    edited_df = st.data_editor(
        df_fornecedores,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Fornecedor": st.column_config.TextColumn("Fornecedor", width="large"),
            "Categoria": st.column_config.SelectboxColumn(
                "Categoria", 
                options=["Material", "Serviço", "Utilidades", "Outros"],
                width="medium"
            )
        },
        hide_index=True
    )
    
    # Verificar se houve alterações no DataFrame
    if not edited_df.equals(df_fornecedores):
        if st.button("Salvar Alterações"):
            if salvar_dados_sheets(edited_df, "Fornecedor_Despesas"):
                st.success("Alterações salvas com sucesso!")
                # Atualizar o cache
                st.session_state.local_data["fornecedor_despesas"] = edited_df
            else:
                st.error("Erro ao salvar alterações.")

def registrar():
    st.title("📝 Registrar")
    
    # Criar abas para os diferentes tipos de registro
    tabs = st.tabs(["Receita", "Despesa", "Projeto", "Cliente", "Funcionário", "Categoria", "Fornecedor"])
    
    # Conteúdo da aba Receita
    with tabs[0]:
        registrar_receita()
    
    # Conteúdo da aba Despesa
    with tabs[1]:
        registrar_despesa()
    
    # Conteúdo da aba Projeto
    with tabs[2]:
        registrar_projeto()
    
    # Conteúdo da aba Cliente
    with tabs[3]:
        registrar_cliente()
    
    # Conteúdo da aba Funcionário
    with tabs[4]:
        registrar_funcionario()
    
    # Conteúdo da aba Categoria
    with tabs[5]:
        registrar_categoria()
    
    # Conteúdo da aba Fornecedor
    with tabs[6]:
        registrar_fornecedor()

########################################## DASHBOARD ##########################################

def formatar_br(valor):
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def dashboard():
    # Carregar dados necessários para o dashboard
    df_receitas = carregar_dados_sob_demanda("Receitas")
    df_despesas = carregar_dados_sob_demanda("Despesas")
    df_projetos = carregar_dados_sob_demanda("Projetos")

    st.title("📊 Dashboard Financeiro")

    # Cálculos
    receitas = df_receitas["ValorTotal"].sum() if not df_receitas.empty and "ValorTotal" in df_receitas.columns else 0
    despesas = df_despesas["ValorTotal"].sum() if not df_despesas.empty and "ValorTotal" in df_despesas.columns else 0
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

    st.write("")
    st.write("")

    # Organização dos gráficos em abas para melhor visualização
    tabs = st.tabs(["Financeiro", "Projetos", "Funcionários"])
    
    with tabs[0]:  # Aba Financeiro
        # Seção 1: Gráficos de Receitas e Despesas por Mês/Ano
        st.markdown("### Análise Mensal")
        col1, col2 = st.columns(2)
        
        # Gráfico 1: Quantidade de receitas por mês/ano
        with col1:
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
                    color_discrete_sequence=[cor_receitas]
                )
                
                fig_receitas_mes_ano.update_traces(textposition="outside")
                fig_receitas_mes_ano.update_xaxes(
                    tickformat="%b/%Y",
                    dtick="M1",
                    showgrid=False
                )
                fig_receitas_mes_ano.update_yaxes(showgrid=False, showticklabels=False)
                
                st.plotly_chart(fig_receitas_mes_ano, use_container_width=True)

        # Gráfico 2: Quantidade de despesas por mês/ano
        with col2:
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
                    color_discrete_sequence=[cor_despesas]
                )
                
                fig_despesas_mes_ano.update_traces(textposition="outside")
                fig_despesas_mes_ano.update_xaxes(
                    tickformat="%b/%Y",
                    dtick="M1"
                )
                fig_despesas_mes_ano.update_yaxes(showgrid=False, showticklabels=False)
                
                st.plotly_chart(fig_despesas_mes_ano, use_container_width=True)
        
        # Seção 2: Gráficos de Receitas e Despesas por Categoria
        st.markdown("### Análise por Categoria")
        col1, col2 = st.columns(2)
        
        # Gráfico 3: Receitas por categoria
        with col1:
            if not df_receitas.empty:
                receitas_por_categoria = df_receitas.groupby("Categoria")["ValorTotal"].sum().reset_index()
                fig_receitas_categoria = px.bar(
                    receitas_por_categoria,
                    x="Categoria",
                    y="ValorTotal",
                    text="ValorTotal",
                    title="Receitas por Categoria",
                    color_discrete_sequence=[cor_receitas]
                )
                fig_receitas_categoria.update_traces(textposition="outside")
                fig_receitas_categoria.update_yaxes(showgrid=False, showticklabels=False)
                st.plotly_chart(fig_receitas_categoria, use_container_width=True)

        # Gráfico 4: Despesas por categoria
        with col2:
            if not df_despesas.empty:
                despesas_por_categoria = df_despesas.groupby("Categoria")["ValorTotal"].sum().reset_index()
                fig_despesas_categoria = px.bar(
                    despesas_por_categoria,
                    x="Categoria",
                    y="ValorTotal",
                    text="ValorTotal",
                    title="Despesas por Categoria",
                    color_discrete_sequence=[cor_despesas]
                )
                fig_despesas_categoria.update_traces(textposition="outside")
                fig_despesas_categoria.update_yaxes(showgrid=False, showticklabels=False)
                st.plotly_chart(fig_despesas_categoria, use_container_width=True)
        
        # Seção 3: Gráficos de Receitas e Despesas por Projeto e Método de Pagamento
        st.markdown("### Análise por Projeto e Método de Pagamento")
        col1, col2 = st.columns(2)
        
        # Gráfico 5: Receitas e despesas por projeto
        with col1:
            if not df_receitas.empty or not df_despesas.empty:
                receitas_por_projeto = df_receitas.groupby("Projeto")["ValorTotal"].sum().reset_index()
                despesas_por_projeto = df_despesas.groupby("Projeto")["ValorTotal"].sum().reset_index()
                fig_projetos = px.bar(
                    pd.concat([receitas_por_projeto.assign(Tipo="Receita"), despesas_por_projeto.assign(Tipo="Despesa")]),
                    x="Projeto",
                    y="ValorTotal",
                    text="ValorTotal",
                    color="Tipo",
                    title="Receitas e Despesas por Projeto",
                    barmode="group",
                    color_discrete_sequence=[cor_receitas, cor_despesas]
                )
                
                fig_projetos.update_traces(textposition="outside")
                fig_projetos.update_yaxes(showgrid=False, showticklabels=False)
                
                st.plotly_chart(fig_projetos, use_container_width=True)

        # Gráfico 6: Receitas e despesas por método de pagamento
        with col2:
            if not df_receitas.empty or not df_despesas.empty:
                receitas_por_metodo = df_receitas.groupby("FormaPagamento")["ValorTotal"].sum().reset_index()
                despesas_por_metodo = df_despesas.groupby("FormaPagamento")["ValorTotal"].sum().reset_index()
                fig_metodo_pagamento = px.bar(
                    pd.concat([receitas_por_metodo.assign(Tipo="Receita"), despesas_por_metodo.assign(Tipo="Despesa")]),
                    x="FormaPagamento",
                    y="ValorTotal",
                    text="ValorTotal",
                    color="Tipo",
                    title="Receitas e Despesas por Método de Pagamento",
                    barmode="group",
                    color_discrete_sequence=[cor_receitas, cor_despesas]
                )
                fig_metodo_pagamento.update_traces(textposition="outside")
                fig_metodo_pagamento.update_yaxes(showgrid=False, showticklabels=False)
                st.plotly_chart(fig_metodo_pagamento, use_container_width=True)
        
        # Seção 4: Gráficos de Despesas por Responsável e Fornecedor
        st.markdown("### Análise de Despesas")
        col1, col2 = st.columns(2)
        
        # Gráfico 7: Despesas por responsável
        with col1:
            if not df_despesas.empty:
                despesas_por_responsavel = df_despesas.groupby("Responsável")["ValorTotal"].sum().reset_index()
                fig_despesas_responsavel = px.bar(
                    despesas_por_responsavel,
                    x="Responsável",
                    y="ValorTotal",
                    text="ValorTotal",
                    title="Despesas por Responsável",
                    color_discrete_sequence=[cor_despesas]
                )
                fig_despesas_responsavel.update_traces(textposition="outside")
                fig_despesas_responsavel.update_yaxes(showgrid=False, showticklabels=False)
                st.plotly_chart(fig_despesas_responsavel, use_container_width=True)

        # Gráfico 8: Despesas por fornecedor
        with col2:
            if not df_despesas.empty:
                despesas_por_fornecedor = df_despesas.groupby("Fornecedor")["ValorTotal"].sum().reset_index()
                fig_despesas_fornecedor = px.bar(
                    despesas_por_fornecedor,
                    x="Fornecedor",
                    y="ValorTotal",
                    text="ValorTotal",
                    title="Despesas por Fornecedor",
                    color_discrete_sequence=[cor_despesas]
                )
                fig_despesas_fornecedor.update_traces(textposition="outside")
                fig_despesas_fornecedor.update_yaxes(showgrid=False, showticklabels=False)
                st.plotly_chart(fig_despesas_fornecedor, use_container_width=True)
    
    with tabs[1]:  # Aba Projetos        
        # Seção 1: Localização e Status
        st.markdown("### Localização e Status")
        col1, col2 = st.columns(2)
        
        # Gráfico 9: Quantidade de projetos por localização
        with col1:
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
                fig_projetos_localizacao.update_traces(textposition="outside")
                fig_projetos_localizacao.update_yaxes(showgrid=False, showticklabels=False)
                st.plotly_chart(fig_projetos_localizacao, use_container_width=True)
        
        # Gráfico 13: Quantidade de projetos pelo status
        with col2:
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
                fig_projetos_status.update_traces(textposition="outside")
                fig_projetos_status.update_yaxes(showgrid=False, showticklabels=False)
                st.plotly_chart(fig_projetos_status, use_container_width=True)
        
        # Seção 2: Características dos Projetos
        st.markdown("### Características dos Projetos")
        col1, col2, col3 = st.columns(3)
        
        # Gráfico 10: Quantidade de projetos com placa e sem placa
        with col1:
            if not df_projetos.empty:
                projetos_placa = df_projetos["Placa"].value_counts().reset_index()
                projetos_placa.columns = ["Placa", "Quantidade"]
                fig_projetos_placa = px.pie(
                    projetos_placa,
                    names="Placa",
                    values="Quantidade",
                    title="Projetos com/sem Placa"
                )
                st.plotly_chart(fig_projetos_placa, use_container_width=True)
        
        # Gráfico 11: Quantidade de projetos com post e sem post
        with col2:
            if not df_projetos.empty:
                projetos_post = df_projetos["Post"].value_counts().reset_index()
                projetos_post.columns = ["Post", "Quantidade"]
                fig_projetos_post = px.pie(
                    projetos_post,
                    names="Post",
                    values="Quantidade",
                    title="Projetos com/sem Post"
                )
                st.plotly_chart(fig_projetos_post, use_container_width=True)
        
        # Gráfico 12: Quantidade de projetos com contrato e sem contrato
        with col3:
            if not df_projetos.empty:
                projetos_contrato = df_projetos["Contrato"].value_counts().reset_index()
                projetos_contrato.columns = ["Contrato", "Quantidade"]
                fig_projetos_contrato = px.pie(
                    projetos_contrato,
                    names="Contrato",
                    values="Quantidade",
                    title="Projetos com/sem Contrato"
                )
                st.plotly_chart(fig_projetos_contrato, use_container_width=True)
        
        # Seção 3: Categorização de Projetos
        st.markdown("### Categorização de Projetos")
        col1, col2 = st.columns(2)
        
        # Gráfico 14: Quantidade de projetos pelo briefing
        with col1:
            if not df_projetos.empty:
                projetos_briefing = df_projetos["Briefing"].value_counts().reset_index()
                projetos_briefing.columns = ["Briefing", "Quantidade"]
                fig_projetos_briefing = px.pie(
                    projetos_briefing,
                    names="Briefing",
                    values="Quantidade",
                    title="Projetos por Briefing"
                )
                st.plotly_chart(fig_projetos_briefing, use_container_width=True)
        
        # Gráfico 16: Quantidade de projetos pelo tipo
        with col2:
            if not df_projetos.empty:
                projetos_tipo = df_projetos["Tipo"].value_counts().reset_index()
                projetos_tipo.columns = ["Tipo", "Quantidade"]
                fig_projetos_tipo = px.bar(
                    projetos_tipo,
                    x="Tipo",
                    y="Quantidade",
                    text="Quantidade",
                    title="Projetos por Tipo"
                )
                fig_projetos_tipo.update_traces(textposition="outside")
                fig_projetos_tipo.update_yaxes(showgrid=False, showticklabels=False)
                st.plotly_chart(fig_projetos_tipo, use_container_width=True)
        
        # Seção 4: Arquitetos e Pacotes
        st.markdown("### Arquitetos e Pacotes")
        col1, col2 = st.columns(2)
        
        # Gráfico 15: Quantidade de projetos por arquiteto
        with col1:
            if not df_projetos.empty:
                projetos_arquiteto = df_projetos["Arquiteto"].value_counts().reset_index()
                projetos_arquiteto.columns = ["Arquiteto", "Quantidade"]
                fig_projetos_arquiteto = px.bar(
                    projetos_arquiteto,
                    x="Arquiteto",
                    y="Quantidade",
                    text="Quantidade",
                    title="Projetos por Arquiteto"
                )
                fig_projetos_arquiteto.update_traces(textposition="outside")
                fig_projetos_arquiteto.update_yaxes(showgrid=False, showticklabels=False)
                st.plotly_chart(fig_projetos_arquiteto, use_container_width=True)
        
        # Gráfico 17: Quantidade de projetos pelo pacote
        with col2:
            if not df_projetos.empty:
                projetos_pacote = df_projetos["Pacote"].value_counts().reset_index()
                projetos_pacote.columns = ["Pacote", "Quantidade"]
                fig_projetos_pacote = px.bar(
                    projetos_pacote,
                    x="Pacote",
                    y="Quantidade",
                    text="Quantidade",
                    title="Projetos por Pacote"
                )
                fig_projetos_pacote.update_traces(textposition="outside")
                fig_projetos_pacote.update_yaxes(showgrid=False, showticklabels=False)
                st.plotly_chart(fig_projetos_pacote, use_container_width=True)
    
    with tabs[2]:  # Aba Responsáveis        
        # Seção 1: m² por Responsáveis
        st.markdown("### Metros Quadrados por Responsável")
        col1, col2 = st.columns(2)
        
        # Gráfico 18: m2 pelo responsável elétrico
        with col1:
            if not df_projetos.empty:
                m2_responsavel_eletrico = df_projetos.groupby("ResponsávelElétrico")["m2"].sum().reset_index()
                fig_m2_eletrico = px.bar(
                    m2_responsavel_eletrico,
                    x="ResponsávelElétrico",
                    y="m2",
                    text="m2",
                    title="m² por Responsável Elétrico"
                )
                fig_m2_eletrico.update_traces(textposition="outside")
                fig_m2_eletrico.update_yaxes(showgrid=False, showticklabels=False)
                st.plotly_chart(fig_m2_eletrico, use_container_width=True)
        
        # Gráfico 19: m2 pelo responsável hidráulico
        with col2:
            if not df_projetos.empty:
                m2_responsavel_hidraulico = df_projetos.groupby("ResponsávelHidráulico")["m2"].sum().reset_index()
                fig_m2_hidraulico = px.bar(
                    m2_responsavel_hidraulico,
                    x="ResponsávelHidráulico",
                    y="m2",
                    text="m2",
                    title="m² por Responsável Hidráulico"
                )
                fig_m2_hidraulico.update_traces(textposition="outside")
                fig_m2_hidraulico.update_yaxes(showgrid=False, showticklabels=False)
                st.plotly_chart(fig_m2_hidraulico, use_container_width=True)
        
        # Seção 2: Mais m² por Responsáveis
        col1, col2 = st.columns(2)
        
        # Gráfico 20: m2 pelo responsável de modelagem
        with col1:
            if not df_projetos.empty:
                m2_responsavel_modelagem = df_projetos.groupby("ResponsávelModelagem")["m2"].sum().reset_index()
                fig_m2_modelagem = px.bar(
                    m2_responsavel_modelagem,
                    x="ResponsávelModelagem",
                    y="m2",
                    text="m2",
                    title="m² por Responsável de Modelagem"
                )
                fig_m2_modelagem.update_traces(textposition="outside")
                fig_m2_modelagem.update_yaxes(showgrid=False, showticklabels=False)
                st.plotly_chart(fig_m2_modelagem, use_container_width=True)
        
        # Gráfico 21: m2 pelo responsável de detalhamento
        with col2:
            if not df_projetos.empty:
                m2_responsavel_detalhamento = df_projetos.groupby("ResponsávelDetalhamento")["m2"].sum().reset_index()
                fig_m2_detalhamento = px.bar(
                    m2_responsavel_detalhamento,
                    x="ResponsávelDetalhamento",
                    y="m2",
                    text="m2",
                    title="m² por Responsável de Detalhamento"
                )
                fig_m2_detalhamento.update_traces(textposition="outside")
                fig_m2_detalhamento.update_yaxes(showgrid=False, showticklabels=False)
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
    
    # Converter datas para formato consistente
    if not df_projetos.empty:
        # Garantir que as colunas de data existam
        if "DataInicio" in df_projetos.columns and "DataFinal" in df_projetos.columns:
            # Converter para datetime e depois para string no formato padrão
            try:
                # Tentar converter datas que estão em diferentes formatos
                for idx, row in df_projetos.iterrows():
                    for date_col in ["DataInicio", "DataFinal"]:
                        try:
                            # Tentar formato ISO
                            date_val = pd.to_datetime(row[date_col])
                            df_projetos.at[idx, date_col] = date_val.strftime("%Y-%m-%d")
                        except:
                            # Se falhar, manter o valor original
                            pass
            except Exception as e:
                st.warning(f"Aviso: Alguns formatos de data podem estar inconsistentes. {str(e)}")
    
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
                
                # Corrigir o tratamento de datas para lidar com diferentes formatos
                try:
                    # Tenta converter a data no formato "%Y-%m-%d"
                    DataInicio = st.date_input("Data de Início", value=datetime.strptime(projeto["DataInicio"], "%Y-%m-%d"))
                except ValueError:
                    try:
                        # Tenta converter a data no formato "%d/%m/%Y"
                        DataInicio = st.date_input("Data de Início", value=datetime.strptime(projeto["DataInicio"], "%d/%m/%Y"))
                    except:
                        # Se falhar, usa a data atual
                        DataInicio = st.date_input("Data de Início", value=datetime.now())
                
                try:
                    # Tenta converter a data no formato "%Y-%m-%d"
                    DataFinal = st.date_input("Data de Conclusão Prevista", value=datetime.strptime(projeto["DataFinal"], "%Y-%m-%d"))
                except ValueError:
                    try:
                        # Tenta converter a data no formato "%d/%m/%Y"
                        DataFinal = st.date_input("Data de Conclusão Prevista", value=datetime.strptime(projeto["DataFinal"], "%d/%m/%Y"))
                    except:
                        # Se falhar, usa a data atual + 30 dias
                        DataFinal = st.date_input("Data de Conclusão Prevista", value=datetime.now() + timedelta(days=30))
                
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
                submit = st.form_submit_button("Salvar Alterações")

                if submit:
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

########################################## EXECUÇÃO ##########################################

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