import streamlit as st
import pandas as pd
from modules.data.sheets import carregar_dados_sob_demanda, salvar_dados_sheets

def salvar_categorias(df, sheet_name):
    """
    Salva as categorias no Google Sheets.
    
    Args:
        df: DataFrame com as categorias
        sheet_name: Nome da planilha
    
    Returns:
        bool: True se os dados foram salvos com sucesso, False caso contrário
    """
    # Salva os dados no Google Sheets
    if salvar_dados_sheets(df, sheet_name):
        # Limpa o cache para forçar recarregar os dados
        st.session_state.local_data[sheet_name.lower()] = pd.DataFrame()
        return True
    return False

def registrar_categoria():
    """
    Formulário para registrar novas categorias de receitas e despesas.
    """
    # Aba principal
    abas_principais = st.tabs(["Categorias de Receitas", "Categorias de Despesas"])

    # Abas de Receitas
    with abas_principais[0]:
        abas_receitas = st.tabs(["Registrar Categoria de Receita", "Categorias de Receita Cadastradas"])
        # Carregar dados existentes
        df_categorias_receitas = carregar_dados_sob_demanda("Categorias_Receitas")
        if df_categorias_receitas.empty:
            df_categorias_receitas = pd.DataFrame({"Categoria": ["Pró-Labore", "Investimentos", "Freelance", "Outros"]})
        with abas_receitas[0]:
            st.markdown("### Nova Categoria de Receita")
            with st.form("nova_categoria_receita"):
                nova_categoria = st.text_input("Nova Categoria de Receita")
                submit_categoria = st.form_submit_button("Registrar Categoria")
                if submit_categoria:
                    if nova_categoria and nova_categoria not in df_categorias_receitas["Categoria"].values:
                        nova_df = pd.DataFrame({"Categoria": [nova_categoria]})
                        df_categorias_receitas = pd.concat([df_categorias_receitas, nova_df], ignore_index=True)
                        if salvar_categorias(df_categorias_receitas, "Categorias_Receitas"):
                            st.success(f"Categoria '{nova_categoria}' adicionada com sucesso!")
                        else:
                            st.error("Erro ao adicionar categoria.")
                    else:
                        st.warning("Categoria já existe ou está vazia.")
        with abas_receitas[1]:
            st.markdown("### Categorias de Receita Cadastradas")
            column_config = {
                "Categoria": st.column_config.TextColumn("Categoria")
            }
            column_order = ["Categoria"]
            with st.form("cat_receitas_form"):
                edited_df = st.data_editor(
                    df_categorias_receitas,
                    use_container_width=True,
                    hide_index=True,
                    num_rows="dynamic",
                    key="cat_receitas_editor",
                    column_config=column_config,
                    column_order=column_order,
                    height=300
                )
                if st.form_submit_button("Salvar Alterações", use_container_width=True):
                    with st.spinner("Salvando dados..."):
                        try:
                            if salvar_categorias(edited_df, "Categorias_Receitas"):
                                st.success("Dados salvos com sucesso!")
                                st.rerun()
                            else:
                                st.error("Erro ao salvar dados no Google Sheets.")
                        except Exception as e:
                            st.error(f"Erro ao salvar dados: {str(e)}")
    # Abas de Despesas
    with abas_principais[1]:
        abas_despesas = st.tabs(["Registrar Categoria de Despesa", "Categorias de Despesa Cadastradas"])
        df_categorias_despesas = carregar_dados_sob_demanda("Categorias_Despesas")
        if df_categorias_despesas.empty:
            df_categorias_despesas = pd.DataFrame({"Categoria": ["Alimentação", "Transporte", "Moradia", "Saúde", "Educação", "Lazer", "Outros"]})
        with abas_despesas[0]:
            st.markdown("### Nova Categoria de Despesa")
            with st.form("nova_categoria_despesa"):
                nova_categoria = st.text_input("Nova Categoria de Despesa")
                submit_categoria = st.form_submit_button("Registrar Categoria")
                if submit_categoria:
                    if nova_categoria and nova_categoria not in df_categorias_despesas["Categoria"].values:
                        nova_df = pd.DataFrame({"Categoria": [nova_categoria]})
                        df_categorias_despesas = pd.concat([df_categorias_despesas, nova_df], ignore_index=True)
                        if salvar_categorias(df_categorias_despesas, "Categorias_Despesas"):
                            st.success(f"Categoria '{nova_categoria}' adicionada com sucesso!")
                        else:
                            st.error("Erro ao adicionar categoria.")
                    else:
                        st.warning("Categoria já existe ou está vazia.")
        with abas_despesas[1]:
            st.markdown("### Categorias de Despesa Cadastradas")
            column_config = {
                "Categoria": st.column_config.TextColumn("Categoria")
            }
            column_order = ["Categoria"]
            with st.form("cat_despesas_form"):
                edited_df = st.data_editor(
                    df_categorias_despesas,
                    use_container_width=True,
                    hide_index=True,
                    num_rows="dynamic",
                    key="cat_despesas_editor",
                    column_config=column_config,
                    column_order=column_order,
                    height=300
                )
                if st.form_submit_button("Salvar Alterações", use_container_width=True):
                    with st.spinner("Salvando dados..."):
                        try:
                            if salvar_categorias(edited_df, "Categorias_Despesas"):
                                st.success("Dados salvos com sucesso!")
                                st.rerun()
                            else:
                                st.error("Erro ao salvar dados no Google Sheets.")
                        except Exception as e:
                            st.error(f"Erro ao salvar dados: {str(e)}")
