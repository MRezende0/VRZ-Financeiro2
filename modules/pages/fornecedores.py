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
    if df_fornecedores.empty:
        df_fornecedores = pd.DataFrame({"Fornecedor": ["Outros"]})
    tabs = st.tabs(["Registrar Fornecedor", "Fornecedores Cadastrados"])
    with tabs[0]:
        st.markdown("### Novo Fornecedor")
        with st.form("novo_fornecedor"):
            nome_fornecedor = st.text_input("Nome do Fornecedor")
            submit_fornecedor = st.form_submit_button("Registrar Fornecedor")
            # Flag para saber se houve novo fornecedor
            novo_fornecedor_adicionado = False
            if submit_fornecedor:
                if nome_fornecedor and nome_fornecedor not in df_fornecedores["Fornecedor"].values:
                    novo_fornecedor = {"Fornecedor": nome_fornecedor}
                    if adicionar_linha_sheets(novo_fornecedor, "Fornecedor_Despesas"):
                        st.success(f"Fornecedor '{nome_fornecedor}' adicionado com sucesso!")
                        st.session_state.local_data["fornecedor_despesas"] = pd.DataFrame()
                        novo_fornecedor_adicionado = True
                    else:
                        st.error("Erro ao adicionar fornecedor.")
                else:
                    st.warning("Fornecedor já existe ou está vazio.")
    with tabs[1]:
        st.markdown("### Fornecedores Cadastrados")
        # Se acabou de adicionar, recarrega para refletir
        if 'novo_fornecedor_adicionado' in locals() and novo_fornecedor_adicionado:
            df_fornecedores = carregar_dados_sob_demanda("Fornecedor_Despesas", force_reload=True)
    with tabs[1]:
        st.markdown("### Fornecedores Cadastrados")
        column_config = {
            "Fornecedor": st.column_config.TextColumn("Fornecedor")
        }
        column_order = ["Fornecedor"]
        with st.form("fornecedores_form"):
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
            if st.form_submit_button("Salvar Alterações", use_container_width=True):
                with st.spinner("Salvando dados..."):
                    try:
                        if salvar_dados_sheets(edited_df, "Fornecedor_Despesas"):
                            st.session_state.local_data["fornecedor_despesas"] = pd.DataFrame()
                            st.success("Dados salvos com sucesso!")
                            st.rerun()
                        else:
                            st.error("Erro ao salvar dados no Google Sheets.")
                    except Exception as e:
                        st.error(f"Erro ao salvar dados: {str(e)}")
