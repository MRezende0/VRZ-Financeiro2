"""
Módulo para criação de tabelas editáveis com funcionalidades avançadas.
"""
import streamlit as st
import pandas as pd
import numpy as np
from modules.data.sheets import salvar_dados_sheets, carregar_dados_sob_demanda

def create_editable_table_with_delete_button(df, sheet_name, key_prefix="table", columns=None, hide_index=True):
    """
    Cria uma tabela editável com coluna de seleção e botão de exclusão.
    
    Args:
        df: DataFrame com os dados
        sheet_name: Nome da planilha para salvar alterações
        key_prefix: Prefixo para as chaves dos componentes
        columns: Lista de colunas a serem exibidas (None para todas)
        hide_index: Se True, esconde o índice da tabela
    
    Returns:
        bool: True se houve alterações salvas, False caso contrário
    """
    if df.empty:
        st.info(f"Nenhum dado encontrado para {sheet_name}.")
        return False
    
    # Cria uma cópia do DataFrame para exibição
    df_display = df.copy()
    
    # Filtra as colunas se especificado
    if columns:
        df_display = df_display[columns].copy()
    
    # Adiciona coluna de seleção
    df_display.insert(0, "Selecionar", False)
    
    # Configura opções de edição para cada coluna
    column_config = {
        "Selecionar": st.column_config.CheckboxColumn(
            "Selecionar",
            help="Selecione para excluir",
            width="small",
            default=False
        )
    }
    
    # Configuração especial para colunas de data
    for col in df_display.columns:
        if "Data" in col:
            # Para colunas de data, usamos TextColumn com formato personalizado
            # em vez de DateColumn para evitar incompatibilidade de tipos
            column_config[col] = st.column_config.TextColumn(
                col,
                help=f"Data no formato DD/MM/YYYY",
                width="medium"
            )
    
    # Adiciona função de ordenação para colunas de data
    for col in df_display.columns:
        if "Data" in col and col != "Selecionar":
            # Garante que a coluna seja do tipo string
            df_display[col] = df_display[col].astype(str)
    
    # Exibe a tabela editável com configuração personalizada
    edited_df = st.data_editor(
        df_display,
        use_container_width=True,
        hide_index=hide_index,
        num_rows="fixed",
        key=f"{key_prefix}_{sheet_name}",
        column_config=column_config
    )
    
    # Verifica se houve alterações na tabela
    if not edited_df.equals(df_display):
        # Verifica se há linhas selecionadas para exclusão
        rows_to_delete = edited_df[edited_df["Selecionar"] == True].index.tolist()
        
        if rows_to_delete:
            # Remove as linhas selecionadas do DataFrame original
            df_updated = df.drop(rows_to_delete).reset_index(drop=True)
            
            # Salva o DataFrame atualizado
            if salvar_dados_sheets(df_updated, sheet_name):
                st.success(f"{len(rows_to_delete)} registro(s) excluído(s) com sucesso!")
                # Limpa o cache para forçar recarregar os dados
                st.session_state.local_data[sheet_name.lower()] = df_updated
                # Força o recarregamento da página para mostrar as alterações
                st.rerun()
                return True
            else:
                st.error("Erro ao excluir registros.")
                return False
        else:
            # Atualiza o DataFrame original com as alterações (exceto a coluna de seleção)
            for index, row in edited_df.iterrows():
                for col in edited_df.columns:
                    if col in df.columns and col != "Selecionar":
                        df.loc[index, col] = row[col]
            
            # Salva as alterações
            if salvar_dados_sheets(df, sheet_name):
                st.success("Alterações salvas com sucesso!")
                # Limpa o cache para forçar recarregar os dados
                st.session_state.local_data[sheet_name.lower()] = pd.DataFrame()
                return True
            else:
                st.error("Erro ao salvar alterações.")
                return False
    
    # Botão para atualizar a tabela
    if st.button(f"Atualizar {sheet_name}", key=f"refresh_{key_prefix}_{sheet_name}"):
        st.session_state.local_data[sheet_name.lower()] = pd.DataFrame()
        st.rerun()
    
    return False


def format_date_columns(df):
    """
    Formata todas as colunas de data para o formato DD/MM/YYYY.
    
    Args:
        df: DataFrame com os dados
    
    Returns:
        pandas.DataFrame: DataFrame com as colunas de data formatadas
    """
    if df.empty:
        return df
    
    df_formatted = df.copy()
    
    # Identifica colunas que podem conter datas
    date_columns = [col for col in df.columns if "Data" in col]
    
    for col in date_columns:
        try:
            # Tenta converter para datetime com formato específico
            df_formatted[col] = pd.to_datetime(df[col], errors='coerce', format="%d/%m/%Y")
            # Formata para DD/MM/YYYY
            df_formatted[col] = df_formatted[col].dt.strftime('%d/%m/%Y')
        except:
            # Se falhar, garante que a coluna seja do tipo string
            if col in df_formatted.columns:
                df_formatted[col] = df_formatted[col].astype(str)
    
    return df_formatted


def convert_date_for_sorting(date_str):
    """
    Converte uma string de data no formato DD/MM/YYYY para um objeto datetime para ordenação.
    
    Args:
        date_str: String de data no formato DD/MM/YYYY
    
    Returns:
        datetime: Objeto datetime ou None se a conversão falhar
    """
    if not date_str or pd.isna(date_str) or date_str == "":
        return None
    
    try:
        # Tenta converter para datetime assumindo formato DD/MM/YYYY
        return pd.to_datetime(date_str, format="%d/%m/%Y", errors='coerce')
    except:
        try:
            # Tenta outros formatos comuns
            return pd.to_datetime(date_str, errors='coerce', dayfirst=True)
        except:
            return None


def create_clean_editable_table(df, sheet_name, key_prefix="clean_table", column_config=None, column_order=None, height=400):
    """
    Cria uma tabela editável sem a coluna de seleção padrão do Streamlit.
    
    Args:
        df: DataFrame com os dados
        sheet_name: Nome da planilha para salvar alterações
        key_prefix: Prefixo para as chaves dos componentes
        column_config: Configuração personalizada para as colunas
        column_order: Ordem das colunas na tabela
        height: Altura da tabela em pixels
    
    Returns:
        bool: True se houve alterações salvas, False caso contrário
    """
    if df.empty:
        st.info(f"Nenhum dado encontrado para {sheet_name}.")
        return False
    
    # Cria uma cópia do DataFrame para exibição
    df_display = df.copy()
    
    # Cria um formulário para a tabela e o botão de salvar
    with st.form(f"{key_prefix}_{sheet_name}_form"):
        # Exibe a tabela editável com configuração personalizada
        edited_df = st.data_editor(
            df_display,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            key=f"{key_prefix}_{sheet_name}",
            column_config=column_config,
            column_order=column_order,
            height=height
        )
        
        # Botão para salvar alterações
        submitted = st.form_submit_button("Salvar Alterações", use_container_width=True)
        
        if submitted:
            with st.spinner("Salvando dados..."):
                try:
                    # Verifica se há colunas esperadas que precisam ser adicionadas
                    if hasattr(st.session_state, 'COLUNAS_ESPERADAS') and sheet_name in st.session_state.COLUNAS_ESPERADAS:
                        for col in st.session_state.COLUNAS_ESPERADAS[sheet_name]:
                            if col not in edited_df.columns:
                                edited_df[col] = ""
                        
                        # Garantir que o DataFrame editado tenha as colunas na ordem correta
                        edited_df = edited_df[st.session_state.COLUNAS_ESPERADAS[sheet_name]]
                    
                    # Recarregar os dados mais recentes do Google Sheets
                    if hasattr(st.session_state, 'local_data') and sheet_name.lower() in st.session_state.local_data:
                        # Atualiza os dados locais e no Google Sheets
                        if salvar_dados_sheets(edited_df, sheet_name):
                            st.session_state.local_data[sheet_name.lower()] = edited_df
                            st.success("Dados salvos com sucesso!")
                            return True
                        else:
                            st.error("Erro ao salvar dados no Google Sheets.")
                            return False
                    else:
                        # Se não há dados locais, apenas salva diretamente
                        if salvar_dados_sheets(edited_df, sheet_name):
                            st.success("Dados salvos com sucesso!")
                            return True
                        else:
                            st.error("Erro ao salvar dados no Google Sheets.")
                            return False
                except Exception as e:
                    st.error(f"Erro ao salvar dados: {str(e)}")
                    return False
    
    return False
