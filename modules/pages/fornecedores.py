import streamlit as st
import pandas as pd
from modules.data.sheets import carregar_dados_sob_demanda, salvar_dados_sheets, adicionar_linha_sheets

def registrar_fornecedor():
    """
    Formulário para registrar um novo fornecedor.
    """
    st.subheader("🏢 Fornecedor")
    
    # Carregar dados existentes
    df_fornecedores = carregar_dados_sob_demanda("Fornecedor_Despesas")
    
    # Verificar se o DataFrame está vazio
    if df_fornecedores.empty:
        df_fornecedores = pd.DataFrame({"Fornecedor": ["Outros"]})
    
    # Exibir lista de fornecedores existentes
    st.write("### Fornecedores Existentes")
    
    # Configuração das colunas para a tabela de fornecedores
    column_config = {
        "Fornecedor": st.column_config.TextColumn("Fornecedor")
    }
    
    # Definir a ordem das colunas
    column_order = ["Fornecedor"]
    
    # Criar formulário para a tabela editável
    with st.form("fornecedores_form"):
        # Exibe a tabela editável com configuração personalizada
        edited_df = st.data_editor(
            df_fornecedores,
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
            key="fornecedores_editor",
            column_config=column_config,
            column_order=column_order,
            height=400
        )
        
        # Botão para salvar alterações
        if st.form_submit_button("Salvar Alterações", use_container_width=True):
            with st.spinner("Salvando dados..."):
                try:
                    # Atualizar os dados no Google Sheets
                    if salvar_dados_sheets(edited_df, "Fornecedor_Despesas"):
                        # Limpar o cache para forçar recarregar os dados
                        st.session_state.local_data["fornecedor_despesas"] = pd.DataFrame()
                        st.success("Dados salvos com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro ao salvar dados no Google Sheets.")
                except Exception as e:
                    st.error(f"Erro ao salvar dados: {str(e)}")
    
    # Formulário para adicionar novo fornecedor
    with st.form("novo_fornecedor"):
        # Simplificado para apenas o nome do fornecedor
        nome_fornecedor = st.text_input("Nome do Fornecedor")
        
        submit_fornecedor = st.form_submit_button("Registrar Fornecedor")
        
        if submit_fornecedor:
            if nome_fornecedor and nome_fornecedor not in df_fornecedores["Fornecedor"].values:
                # Adicionar novo fornecedor
                novo_fornecedor = {"Fornecedor": nome_fornecedor}
                
                # Adicionar diretamente à planilha
                if adicionar_linha_sheets(novo_fornecedor, "Fornecedor_Despesas"):
                    st.success(f"Fornecedor '{nome_fornecedor}' adicionado com sucesso!")
                    # Limpar o cache para forçar recarregar os dados
                    st.session_state.local_data["fornecedor_despesas"] = pd.DataFrame()
                    # Recarregar os dados para exibir o novo fornecedor na tabela
                    df_fornecedores = carregar_dados_sob_demanda("Fornecedor_Despesas", force_reload=True)
                else:
                    st.error("Erro ao adicionar fornecedor.")
            else:
                st.warning("Fornecedor já existe ou está vazio.")
