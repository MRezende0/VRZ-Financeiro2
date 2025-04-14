import streamlit as st
import pandas as pd
from modules.data.sheets import carregar_dados_sob_demanda, salvar_dados_sheets

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
        # Colunas a serem exibidas
        colunas_exibir = ["Projeto", "Cliente", "Status", "Tipo", "m2", "ValorTotal", "DataInicio", "DataFinal"]
        
        # Exibe a tabela editável
        edited_df = st.data_editor(
            df_filtrado[colunas_exibir],
            use_container_width=True,
            hide_index=True,
            num_rows="fixed"
        )
        
        # Verifica se houve alterações
        if not edited_df.equals(df_filtrado[colunas_exibir]):
            # Atualiza o DataFrame original com as alterações
            for index, row in edited_df.iterrows():
                for col in colunas_exibir:
                    df_projetos.loc[index, col] = row[col]
            
            # Salva as alterações
            if salvar_projetos(df_projetos):
                st.success("Alterações salvas com sucesso!")
            else:
                st.error("Erro ao salvar alterações.")
    else:
        st.info("Nenhum projeto encontrado com os filtros selecionados.")
    
    # Botão para adicionar novo projeto
    if st.button("Adicionar Novo Projeto"):
        st.session_state.page = "registrar"
        st.session_state.tab = "Projeto"
        st.rerun()
