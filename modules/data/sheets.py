import time
import streamlit as st
import pandas as pd
import gspread
from google.oauth2 import service_account
from random import uniform
from utils.config import SHEET_ID, SHEET_GIDS, COLUNAS_ESPERADAS
from utils.data_utils import preparar_dados_para_sheets, converter_para_string_segura

def conectar_sheets(force_reconnect=False):
    """
    Estabelece conexão com o Google Sheets.
    
    Args:
        force_reconnect: Se True, força uma nova conexão mesmo que já exista uma
    
    Returns:
        objeto gspread.Spreadsheet: Planilha conectada
    """
    # Se já temos uma conexão e não estamos forçando reconexão, retorna a conexão existente
    if not force_reconnect and st.session_state.spreadsheet is not None:
        return st.session_state.spreadsheet
    
    try:
        # Tenta carregar as credenciais do arquivo de secrets
        credentials = service_account.Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ],
        )
        
        # Conecta ao serviço do Google Sheets
        gc = gspread.authorize(credentials)
        
        # Abre a planilha pelo ID
        sheet_id = st.secrets.get("sheet_id", SHEET_ID)
        spreadsheet = gc.open_by_key(sheet_id)
        
        # Armazena a planilha no estado da sessão
        st.session_state.spreadsheet = spreadsheet
        
        return spreadsheet
    
    except Exception as e:
        st.error(f"Erro ao conectar com o Google Sheets: {e}")
        # Tenta usar o ID da planilha padrão se falhar com o do secrets
        try:
            if "sheet_id" in st.secrets and st.secrets["sheet_id"] != SHEET_ID:
                # Tenta com o ID padrão
                gc = gspread.authorize(credentials)
                spreadsheet = gc.open_by_key(SHEET_ID)
                st.session_state.spreadsheet = spreadsheet
                return spreadsheet
        except:
            pass
        
        return None

def carregar_dados_sheets(sheet_name, force_reload=False):
    """
    Carrega dados de uma planilha específica do Google Sheets.
    
    Args:
        sheet_name: Nome da planilha a ser carregada
        force_reload: Se True, força o recarregamento mesmo que os dados já estejam em cache
    
    Returns:
        pandas.DataFrame: DataFrame com os dados carregados
    """
    # Verifica se já temos os dados em cache e não estamos forçando recarregamento
    if not force_reload and sheet_name in st.session_state.local_data and not st.session_state.local_data[sheet_name].empty:
        return st.session_state.local_data[sheet_name]
    
    # Tenta carregar os dados do Google Sheets
    try:
        # Conecta ao Google Sheets
        spreadsheet = conectar_sheets()
        if spreadsheet is None:
            st.error("Não foi possível conectar ao Google Sheets.")
            return pd.DataFrame()
        
        # Verifica se a planilha está em cache
        if sheet_name in st.session_state.worksheets_cache:
            worksheet = st.session_state.worksheets_cache[sheet_name]
        else:
            # Tenta abrir a planilha pelo nome
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
            except:
                # Se falhar, tenta abrir pelo ID (gid)
                if sheet_name in SHEET_GIDS:
                    worksheet = spreadsheet.get_worksheet_by_id(int(SHEET_GIDS[sheet_name]))
                else:
                    st.error(f"Planilha '{sheet_name}' não encontrada.")
                    return pd.DataFrame()
            
            # Armazena a planilha em cache
            st.session_state.worksheets_cache[sheet_name] = worksheet
        
        # Obtém todos os valores da planilha
        data = worksheet.get_all_values()
        
        # Verifica se há dados
        if not data:
            return pd.DataFrame(columns=COLUNAS_ESPERADAS.get(sheet_name, []))
        
        # Cria um DataFrame com os dados
        headers = data[0]
        df = pd.DataFrame(data[1:], columns=headers)
        
        # Verifica se as colunas esperadas estão presentes
        if sheet_name in COLUNAS_ESPERADAS:
            missing_cols = [col for col in COLUNAS_ESPERADAS[sheet_name] if col not in df.columns]
            for col in missing_cols:
                df[col] = ""
        
        # Armazena os dados em cache
        st.session_state.local_data[sheet_name] = df
        
        return df
    
    except Exception as e:
        st.error(f"Erro ao carregar dados da planilha '{sheet_name}': {e}")
        return pd.DataFrame()

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
        # Prepara os dados para serialização segura
        df_preparado = preparar_dados_para_sheets(df, is_dataframe=True)
        
        # Conecta ao Google Sheets
        spreadsheet = conectar_sheets()
        if spreadsheet is None:
            st.error("Não foi possível conectar ao Google Sheets.")
            return False
        
        # Verifica se a planilha está em cache
        if sheet_name in st.session_state.worksheets_cache:
            worksheet = st.session_state.worksheets_cache[sheet_name]
        else:
            # Tenta abrir a planilha pelo nome
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
            except:
                # Se falhar, tenta abrir pelo ID (gid)
                if sheet_name in SHEET_GIDS:
                    worksheet = spreadsheet.get_worksheet_by_id(int(SHEET_GIDS[sheet_name]))
                else:
                    st.error(f"Planilha '{sheet_name}' não encontrada.")
                    return False
            
            # Armazena a planilha em cache
            st.session_state.worksheets_cache[sheet_name] = worksheet
        
        # Prepara os dados para salvar
        headers = df_preparado.columns.tolist()
        
        # Converte todos os valores para string para evitar problemas de serialização
        values = []
        for _, row in df_preparado.iterrows():
            row_values = []
            for val in row:
                # Usa a função de conversão segura
                row_values.append(converter_para_string_segura(val))
            values.append(row_values)
        
        all_values = [headers] + values
        
        # Verifica se a planilha está vazia
        current_data = worksheet.get_all_values()
        if not current_data or len(current_data) <= 1:  # Vazia ou só tem cabeçalho
            # Se estiver vazia, apenas atualiza com os novos dados
            worksheet.update(all_values)
        else:
            # Se não estiver vazia, verifica se os cabeçalhos são iguais
            current_headers = current_data[0]
            if current_headers == headers:
                # Cria um backup dos dados atuais antes de qualquer modificação
                backup_data = current_data.copy()
                
                # Adiciona um pequeno atraso para evitar problemas de rate limit
                time.sleep(uniform(0.5, 1.0))
                
                # Atualiza apenas as células necessárias em vez de limpar tudo
                # Primeiro, atualiza o intervalo existente
                if len(all_values) > 1:  # Se temos dados para atualizar
                    try:
                        # Atualiza o intervalo existente (preserva formatação e fórmulas)
                        worksheet.update(all_values)
                    except Exception as e:
                        st.error(f"Erro ao atualizar dados: {e}. Tentando restaurar backup.")
                        # Tenta restaurar o backup em caso de falha
                        try:
                            worksheet.clear()
                            worksheet.update(backup_data)
                            st.warning("Dados restaurados do backup após falha na atualização.")
                        except:
                            st.error("Não foi possível restaurar o backup. Contate o administrador.")
                        return False
            else:
                # Se os cabeçalhos forem diferentes, tenta preservar os dados
                st.warning(f"Os cabeçalhos da planilha '{sheet_name}' foram alterados. Tentando preservar os dados.")
                
                # Cria um backup dos dados atuais
                backup_file = f"backups/{sheet_name}_{int(time.time())}.csv"
                try:
                    # Converte os dados atuais para DataFrame
                    backup_df = pd.DataFrame(current_data[1:], columns=current_headers)
                    # Salva o backup localmente
                    backup_df.to_csv(backup_file, index=False)
                    st.info(f"Backup dos dados criado em {backup_file}")
                except Exception as e:
                    st.warning(f"Não foi possível criar backup local: {e}")
                
                # Atualiza a planilha com os novos dados
                try:
                    worksheet.clear()
                    worksheet.update(all_values)
                except Exception as e:
                    st.error(f"Erro ao atualizar dados com novos cabeçalhos: {e}")
        
        # Atualiza o cache local
        st.session_state.local_data[sheet_name] = df
        
        return True
    
    except Exception as e:
        st.error(f"Erro ao salvar dados na planilha '{sheet_name}': {e}")
        return False

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
        # Prepara os dados para serialização segura
        nova_linha = preparar_dados_para_sheets(nova_linha, is_dataframe=False)
        
        # Conecta ao Google Sheets
        spreadsheet = conectar_sheets()
        if spreadsheet is None:
            st.error("Não foi possível conectar ao Google Sheets.")
            return False
        
        # Verifica se a planilha está em cache
        if sheet_name in st.session_state.worksheets_cache:
            worksheet = st.session_state.worksheets_cache[sheet_name]
        else:
            # Tenta abrir a planilha pelo nome
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
            except:
                # Se falhar, tenta abrir pelo ID (gid)
                if sheet_name in SHEET_GIDS:
                    worksheet = spreadsheet.get_worksheet_by_id(int(SHEET_GIDS[sheet_name]))
                else:
                    st.error(f"Planilha '{sheet_name}' não encontrada.")
                    return False
            
            # Armazena a planilha em cache
            st.session_state.worksheets_cache[sheet_name] = worksheet
        
        # Verifica se a planilha está vazia
        current_data = worksheet.get_all_values()
        if not current_data:
            # Se estiver vazia, cria com as colunas esperadas
            if sheet_name in COLUNAS_ESPERADAS:
                headers = COLUNAS_ESPERADAS[sheet_name]
            else:
                headers = list(nova_linha.keys())
            
            # Prepara os valores da nova linha
            row_values = []
            for col in headers:
                val = nova_linha.get(col, "")
                row_values.append(converter_para_string_segura(val))
            
            # Atualiza a planilha com o cabeçalho e a nova linha
            worksheet.update([headers, row_values])
        else:
            # Se não estiver vazia, adiciona a nova linha
            headers = current_data[0]
            
            # Prepara os valores da nova linha na ordem correta dos cabeçalhos
            row_values = []
            for col in headers:
                val = nova_linha.get(col, "")
                row_values.append(converter_para_string_segura(val))
            
            # Adiciona a nova linha ao final da planilha
            worksheet.append_row(row_values)
        
        # Atualiza o cache local
        df = carregar_dados_sheets(sheet_name, force_reload=True)
        st.session_state.local_data[sheet_name] = df
        
        return True
    
    except Exception as e:
        st.error(f"Erro ao adicionar linha na planilha '{sheet_name}': {e}")
        return False

def carregar_dados_sob_demanda(sheet_name, force_reload=False):
    """
    Carrega dados de uma planilha específica apenas quando necessário.
    
    Args:
        sheet_name: Nome da planilha a ser carregada
        force_reload: Se True, força o recarregamento mesmo que os dados já estejam em cache
    
    Returns:
        pandas.DataFrame: DataFrame com os dados carregados
    """
    # Verifica se já temos os dados em cache e não estamos forçando recarregamento
    if not force_reload and sheet_name in st.session_state.local_data and not st.session_state.local_data[sheet_name].empty:
        return st.session_state.local_data[sheet_name]
    
    # Se não temos os dados em cache ou estamos forçando recarregamento, carrega do Google Sheets
    df = carregar_dados_sheets(sheet_name, force_reload=force_reload)
    
    # Armazena os dados em cache
    st.session_state.local_data[sheet_name] = df
    
    return df

def carregar_dados_iniciais():
    """
    Carrega dados iniciais (chamada após login bem-sucedido).
    """
    # Lista de planilhas a serem carregadas inicialmente
    planilhas_iniciais = ["Receitas", "Despesas", "Projetos"]
    
    # Carrega cada planilha
    for sheet_name in planilhas_iniciais:
        df = carregar_dados_sheets(sheet_name)
        st.session_state.local_data[sheet_name] = df
    
    # Marca que os dados foram carregados
    st.session_state.dados_carregados = True

def carregar_dados_background():
    """
    Carrega dados em segundo plano.
    """
    # Lista de planilhas a serem carregadas em segundo plano
    planilhas_background = ["Categorias_Receitas", "Categorias_Despesas", "Fornecedor_Despesas", "Clientes"]
    
    # Carrega cada planilha
    for sheet_name in planilhas_background:
        df = carregar_dados_sheets(sheet_name)
        st.session_state.local_data[sheet_name] = df

def verificar_estrutura_planilha(sheet_name):
    """
    Verifica se a estrutura da planilha está correta e restaura se necessário.
    
    Args:
        sheet_name: Nome da planilha a ser verificada
    
    Returns:
        bool: True se a estrutura está correta ou foi restaurada, False caso contrário
    """
    try:
        # Carrega os dados da planilha
        df = carregar_dados_sheets(sheet_name, force_reload=True)
        
        # Verifica se a planilha está vazia ou não tem as colunas esperadas
        if df.empty or not all(col in df.columns for col in COLUNAS_ESPERADAS.get(sheet_name, [])):
            # Cria um DataFrame vazio com as colunas esperadas
            df_novo = pd.DataFrame(columns=COLUNAS_ESPERADAS.get(sheet_name, []))
            
            # Se a planilha não está vazia, tenta preservar os dados existentes
            if not df.empty:
                # Para cada coluna esperada, verifica se existe na planilha atual
                for col in COLUNAS_ESPERADAS.get(sheet_name, []):
                    if col in df.columns:
                        df_novo[col] = df[col]
            
            # Salva o DataFrame com a estrutura correta
            if salvar_dados_sheets(df_novo, sheet_name):
                st.success(f"A estrutura da planilha '{sheet_name}' foi restaurada com sucesso.")
                return True
            else:
                st.error(f"Não foi possível restaurar a estrutura da planilha '{sheet_name}'.")
                return False
        
        return True
    
    except Exception as e:
        st.error(f"Erro ao verificar estrutura da planilha '{sheet_name}': {e}")
        return False

def verificar_todas_planilhas():
    """
    Verifica a estrutura de todas as planilhas e restaura se necessário.
    
    Returns:
        bool: True se todas as planilhas estão corretas ou foram restauradas, False caso contrário
    """
    # Lista de todas as planilhas
    todas_planilhas = list(COLUNAS_ESPERADAS.keys())
    
    # Verifica cada planilha
    resultados = []
    for sheet_name in todas_planilhas:
        resultados.append(verificar_estrutura_planilha(sheet_name))
    
    # Retorna True se todas as planilhas estão corretas
    return all(resultados)
