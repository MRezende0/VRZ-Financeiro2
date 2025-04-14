import streamlit as st
import pandas as pd
from modules.data.sheets import carregar_dados_sob_demanda, salvar_dados_sheets, adicionar_linha_sheets
from modules.ui.tables import create_editable_table_with_delete_button

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
    
    # Usar a nova função de tabela editável com coluna de seleção
    create_editable_table_with_delete_button(df_fornecedores, "Fornecedor_Despesas", key_prefix="fornecedores")
    
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
