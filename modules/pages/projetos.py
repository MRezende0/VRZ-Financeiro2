import streamlit as st
import pandas as pd
from modules.data.sheets import carregar_dados_sob_demanda, salvar_dados_sheets


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
            # Tenta converter para datetime
            df_formatted[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)
            # Formata para DD/MM/YYYY
            df_formatted[col] = df_formatted[col].dt.strftime('%d/%m/%Y')
        except:
            # Se falhar, garante que a coluna seja do tipo string
            if col in df_formatted.columns:
                df_formatted[col] = df_formatted[col].astype(str)
    
    return df_formatted

def carregar_projetos():
    """
    Carrega os dados dos projetos.
    
    Returns:
        pandas.DataFrame: DataFrame com os dados dos projetos
    """
    # Carrega os dados dos projetos
    df_projetos = carregar_dados_sob_demanda("Projetos")
    
    # Verifica se o DataFrame está vazio
    if df_projetos.empty:
        # Cria um DataFrame vazio com as colunas esperadas
        df_projetos = pd.DataFrame(columns=[
            "Projeto", "Cliente", "Localizacao", "Placa", "Post", "DataInicio", "DataFinal", 
            "Contrato", "Status", "Briefing", "Arquiteto", "Tipo", "Pacote", "m2", 
            "Parcelas", "ValorTotal", "ResponsávelElétrico", "ResponsávelHidráulico", 
            "ResponsávelModelagem", "ResponsávelDetalhamento"
        ])
    
    return df_projetos

def salvar_projetos(df):
    """
    Salva os dados dos projetos.
    
    Args:
        df: DataFrame com os dados dos projetos
    
    Returns:
        bool: True se os dados foram salvos com sucesso, False caso contrário
    """
    # Salva os dados no Google Sheets
    if salvar_dados_sheets(df, "Projetos"):
        # Limpa o cache para forçar recarregar os dados
        st.session_state.local_data["projetos"] = pd.DataFrame()
        return True
    return False

def registrar_projeto():
    """
    Formulário para registrar um novo projeto.
    """
    # Carregar dados necessários
    df_projetos = carregar_dados_sob_demanda("Projetos")
    
    # Formatar colunas de data e garantir que sejam strings
    df_projetos = format_date_columns(df_projetos)
    
    # Garantir que todas as colunas de data sejam strings
    for col in df_projetos.columns:
        if "Data" in col:
            df_projetos[col] = df_projetos[col].astype(str)
    
    st.subheader("🏗️ Projeto")

    with st.form("form_projeto"):
        col1, col2 = st.columns(2)
        
        with col1:
            Projeto = st.text_input("ID Projeto")
            Arquiteto = st.text_input("Arquiteto")
            Localizacao = st.text_input("Localização")
            Status = st.selectbox("Status", ["Concluído", "Em Andamento", "A fazer", "Impedido"])
            ValorTotal = st.number_input("Valor Total", min_value=0.0, step=1.0, format="%.2f")
            DataInicio = st.date_input("Data de Início")
            Contrato = st.selectbox("Contrato", ["Feito", "A fazer"])
            Placa = st.selectbox("Já possui placa na obra?", ["Sim", "Não"])
            ResponsávelModelagem = st.text_input("Responsável pela Modelagem")
            ResponsávelDetalhamento = st.text_input("Responsável pelo Detalhamento")
        
        with col2:
            Cliente = st.text_input("Nome do cliente")
            Tipo = st.selectbox("Tipo", ["Residencial", "Comercial"])
            m2 = st.number_input("m²", min_value=0.0, step=1.0)
            Pacote = st.selectbox("Pacote", ["Completo", "Estrutural e Hidráulico", "Estrutural e Elétrico"])
            Parcelas = st.number_input("Parcelas", min_value=0, step=1)
            DataFinal = st.date_input("Data de Conclusão Prevista")
            Briefing = st.selectbox("Briefing", ["Feito", "A fazer"])
            Post = st.selectbox("Já foi feito o post do projeto?", ["Sim", "Não"])
            ResponsávelElétrico = st.text_input("Responsável pelo Elétrico")
            ResponsávelHidráulico = st.text_input("Responsável pelo Hidráulico")
        
        submit = st.form_submit_button("Registrar Projeto")

    if submit:
        # Converter datas para string no formato DD/MM/YYYY
        data_inicio_str = DataInicio.strftime("%d/%m/%Y") if DataInicio else ""
        data_final_str = DataFinal.strftime("%d/%m/%Y") if DataFinal else ""
        
        # Converter valores numéricos para string para evitar problemas de serialização
        valor_total_str = str(ValorTotal) if ValorTotal is not None else "0"
        m2_str = str(m2) if m2 is not None else "0"
        parcelas_str = str(Parcelas) if Parcelas is not None else "0"
        
        novo_projeto = pd.DataFrame({
            "Projeto": [Projeto],
            "Cliente": [Cliente],
            "Localizacao": [Localizacao],
            "Placa": [Placa],
            "Post": [Post],
            "DataInicio": [data_inicio_str],
            "DataFinal": [data_final_str],
            "Contrato": [Contrato],
            "Status": [Status],
            "Briefing": [Briefing],
            "Arquiteto": [Arquiteto],
            "Tipo": [Tipo],
            "Pacote": [Pacote],
            "m2": [m2_str],
            "Parcelas": [parcelas_str],
            "ValorTotal": [valor_total_str],
            "ResponsávelElétrico": [ResponsávelElétrico],
            "ResponsávelHidráulico": [ResponsávelHidráulico],
            "ResponsávelModelagem": [ResponsávelModelagem],
            "ResponsávelDetalhamento": [ResponsávelDetalhamento]
        })
        df_projetos = pd.concat([df_projetos, novo_projeto], ignore_index=True)
        salvar_projetos(df_projetos)
        st.success("Projeto registrado com sucesso!")
        # Recarregar os dados para exibir o novo projeto na tabela
        df_projetos = carregar_dados_sob_demanda("Projetos", force_reload=True)
        # Formatar colunas de data e garantir que sejam strings
        df_projetos = format_date_columns(df_projetos)
        
        # Garantir que todas as colunas de data sejam strings
        for col in df_projetos.columns:
            if "Data" in col:
                df_projetos[col] = df_projetos[col].astype(str)
    
    # Exibir lista de projetos
    st.write("### Lista de Projetos")
    
    # Formatar colunas de data
    for col in df_projetos.columns:
        if "Data" in col:
            try:
                # Tenta converter para datetime
                df_projetos[col] = pd.to_datetime(df_projetos[col], errors='coerce', dayfirst=True)
                # Formata para DD/MM/YYYY
                df_projetos[col] = df_projetos[col].dt.strftime('%d/%m/%Y')
            except:
                # Se falhar, garante que a coluna seja do tipo string
                df_projetos[col] = df_projetos[col].astype(str)
    
    # Configuração das colunas para a tabela de registro
    column_config = {
        "Projeto": st.column_config.TextColumn("Projeto"),
        "Cliente": st.column_config.TextColumn("Cliente"),
        "Status": st.column_config.SelectboxColumn("Status", options=["Concluído", "Em Andamento", "A fazer", "Impedido"]),
        "Tipo": st.column_config.SelectboxColumn("Tipo", options=["Residencial", "Comercial"]),
        "Localizacao": st.column_config.TextColumn("Localização"),
        "Placa": st.column_config.SelectboxColumn("Placa", options=["Sim", "Não"]),
        "Post": st.column_config.SelectboxColumn("Post", options=["Sim", "Não"]),
        "DataInicio": st.column_config.TextColumn("Data de Início"),
        "DataFinal": st.column_config.TextColumn("Data de Conclusão"),
        "Contrato": st.column_config.SelectboxColumn("Contrato", options=["Feito", "A fazer"]),
        "Briefing": st.column_config.SelectboxColumn("Briefing", options=["Feito", "A fazer"]),
        "Arquiteto": st.column_config.TextColumn("Arquiteto"),
        "Pacote": st.column_config.SelectboxColumn("Pacote", options=["Completo", "Estrutural e Hidráulico", "Estrutural e Elétrico"]),
        "m2": st.column_config.NumberColumn("m²", min_value=0.0, step=1.0, format="%.2f"),
        "Parcelas": st.column_config.NumberColumn("Parcelas", min_value=0, step=1, format="%.0f"),
        "ValorTotal": st.column_config.NumberColumn("Valor Total", min_value=0.0, step=1.0, format="%.2f"),
        "ResponsávelElétrico": st.column_config.TextColumn("Responsável Elétrico"),
        "ResponsávelHidráulico": st.column_config.TextColumn("Responsável Hidráulico"),
        "ResponsávelModelagem": st.column_config.TextColumn("Responsável Modelagem"),
        "ResponsávelDetalhamento": st.column_config.TextColumn("Responsável Detalhamento")
    }
    
    # Definir a ordem das colunas
    column_order = ["Projeto", "Cliente", "Status", "Tipo", "Localizacao", "DataInicio", "DataFinal", 
                   "Contrato", "Briefing", "Arquiteto", "Pacote", "m2", "ValorTotal", "Parcelas",
                   "ResponsávelElétrico", "ResponsávelHidráulico", "ResponsávelModelagem", "ResponsávelDetalhamento",
                   "Placa", "Post"]
    
    # Criar formulário para a tabela editável
    with st.form("projetos_reg_form"):
        # Exibe a tabela editável com configuração personalizada
        edited_df = st.data_editor(
            df_projetos,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            key="projetos_reg_editor",
            column_config=column_config,
            column_order=column_order,
            height=400
        )
        
        # Botão para salvar alterações
        if st.form_submit_button("Salvar Alterações", use_container_width=True):
            with st.spinner("Salvando dados..."):
                try:
                    # Atualizar os dados no Google Sheets
                    if salvar_projetos(edited_df):
                        st.success("Dados salvos com sucesso!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar dados: {str(e)}")

def projetos():
    """
    Página principal para gerenciar projetos.
    """
    st.title("🏗️ Projetos")
    
    # Carrega os dados dos projetos
    df_projetos = carregar_projetos()
    
    # Exibe os projetos em uma tabela editável
    st.write("### Lista de Projetos")
    
    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        filtro_status = st.selectbox("Filtrar por Status", ["Todos"] + df_projetos["Status"].unique().tolist() if not df_projetos.empty else ["Todos"])
    with col2:
        filtro_tipo = st.selectbox("Filtrar por Tipo", ["Todos"] + df_projetos["Tipo"].unique().tolist() if not df_projetos.empty else ["Todos"])
    with col3:
        filtro_texto = st.text_input("Buscar por Projeto ou Cliente")
    
    # Aplica os filtros
    df_filtrado = df_projetos.copy()
    if filtro_status != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Status"] == filtro_status]
    if filtro_tipo != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Tipo"] == filtro_tipo]
    if filtro_texto:
        mask = (df_filtrado["Projeto"].str.contains(filtro_texto, case=False, na=False)) | \
               (df_filtrado["Cliente"].str.contains(filtro_texto, case=False, na=False))
        df_filtrado = df_filtrado[mask]
    
    # Exibe os projetos filtrados
    if not df_filtrado.empty:
        # Formatar colunas de data
        for col in df_filtrado.columns:
            if "Data" in col:
                try:
                    # Tenta converter para datetime
                    df_filtrado[col] = pd.to_datetime(df_filtrado[col], errors='coerce', dayfirst=True)
                    # Formata para DD/MM/YYYY
                    df_filtrado[col] = df_filtrado[col].dt.strftime('%d/%m/%Y')
                except:
                    # Se falhar, garante que a coluna seja do tipo string
                    df_filtrado[col] = df_filtrado[col].astype(str)
        
        # Colunas a serem exibidas e sua ordem
        colunas_exibir = ["Projeto", "Cliente", "Status", "Tipo", "m2", "ValorTotal", "DataInicio", "DataFinal"]
        
        # Configuração das colunas
        column_config = {
            "Projeto": st.column_config.TextColumn("Projeto"),
            "Cliente": st.column_config.TextColumn("Cliente"),
            "Status": st.column_config.SelectboxColumn("Status", options=["Concluído", "Em Andamento", "A fazer", "Impedido"]),
            "Tipo": st.column_config.SelectboxColumn("Tipo", options=["Residencial", "Comercial"]),
            "m2": st.column_config.NumberColumn("m²", min_value=0.0, step=1.0, format="%.2f"),
            "ValorTotal": st.column_config.NumberColumn("Valor Total", min_value=0.0, step=1.0, format="%.2f"),
            "DataInicio": st.column_config.TextColumn("Data de Início"),
            "DataFinal": st.column_config.TextColumn("Data de Conclusão")
        }
        
        # Criar formulário para a tabela editável
        with st.form("projetos_form"):
            # Exibe a tabela editável com configuração personalizada
            edited_df = st.data_editor(
                df_filtrado[colunas_exibir],
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic",
                key="projetos_editor",
                column_config=column_config,
                column_order=colunas_exibir,
                height=400
            )
            
            # Botão para salvar alterações
            if st.form_submit_button("Salvar Alterações", use_container_width=True):
                with st.spinner("Salvando dados..."):
                    try:
                        # Recarregar os dados mais recentes do Google Sheets
                        df_completo = carregar_projetos()
                        
                        # Remover os registros que foram editados para evitar duplicações
                        if filtro_status != "Todos" or filtro_tipo != "Todos" or filtro_texto:
                            # Se há filtros, manter os registros que não foram filtrados
                            if filtro_status != "Todos":
                                df_completo = df_completo[df_completo["Status"] != filtro_status]
                            if filtro_tipo != "Todos":
                                df_completo = df_completo[df_completo["Tipo"] != filtro_tipo]
                            if filtro_texto:
                                mask = ~((df_completo["Projeto"].str.contains(filtro_texto, case=False, na=False)) | 
                                        (df_completo["Cliente"].str.contains(filtro_texto, case=False, na=False)))
                                df_completo = df_completo[mask]
                        else:
                            # Se não há filtros, substituir completamente os dados
                            df_completo = pd.DataFrame(columns=df_projetos.columns)
                        
                        # Para as colunas que não estão no DataFrame editado, preencher com os valores originais
                        for col in df_projetos.columns:
                            if col not in edited_df.columns:
                                edited_df[col] = df_filtrado[col]
                        
                        # Combinar os dados originais com os editados
                        df_final = pd.concat([df_completo, edited_df], ignore_index=True)
                        
                        # Atualizar os dados no Google Sheets
                        if salvar_projetos(df_final):
                            st.success("Dados salvos com sucesso!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar dados: {str(e)}")
    else:
        st.info("Nenhum projeto encontrado com os filtros selecionados.")