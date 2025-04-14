import streamlit as st
import pandas as pd
from modules.data.sheets import carregar_dados_sob_demanda, salvar_dados_sheets

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
    
    # Exibir a tabela de fornecedores
    if not df_fornecedores.empty:
        edited_df = st.data_editor(
            df_fornecedores,
            use_container_width=True,
            hide_index=True,
            num_rows="fixed"
        )
        
        # Verificar se houve alterações
        if not edited_df.equals(df_fornecedores):
            # Salvar alterações
            if salvar_dados_sheets(edited_df, "Fornecedor_Despesas"):
                st.success("Alterações salvas com sucesso!")
                # Limpar o cache para forçar recarregar os dados
                st.session_state.local_data["fornecedor_despesas"] = pd.DataFrame()
            else:
                st.error("Erro ao salvar alterações.")
    
    # Formulário para adicionar novo fornecedor
    with st.form("novo_fornecedor"):
        col1, col2 = st.columns(2)
        
        with col1:
            nome_fornecedor = st.text_input("Nome do Fornecedor")
        
        with col2:
            categoria_fornecedor = st.selectbox("Categoria", ["Material", "Serviço", "Utilidades", "Outros"])
        
        submit_fornecedor = st.form_submit_button("Registrar Fornecedor")
        
        if submit_fornecedor:
            if nome_fornecedor and nome_fornecedor not in df_fornecedores["Fornecedor"].values:
                # Adicionar novo fornecedor
                nova_df = pd.DataFrame({"Fornecedor": [nome_fornecedor]})
                df_fornecedores = pd.concat([df_fornecedores, nova_df], ignore_index=True)
                
                # Salvar alterações
                if salvar_dados_sheets(df_fornecedores, "Fornecedor_Despesas"):
                    st.success(f"Fornecedor '{nome_fornecedor}' adicionado com sucesso!")
                    # Limpar o cache para forçar recarregar os dados
                    st.session_state.local_data["fornecedor_despesas"] = pd.DataFrame()
                else:
                    st.error("Erro ao adicionar fornecedor.")
            else:
                st.warning("Fornecedor já existe ou está vazio.")
