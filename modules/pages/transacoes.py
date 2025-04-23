import streamlit as st
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from modules.data.sheets import carregar_dados_sob_demanda, adicionar_linha_sheets, salvar_dados_sheets

def salvar_dados(df, sheet_name):
    """
    Função auxiliar para salvar dados.
    
    Args:
        df: DataFrame a ser salvo
        sheet_name: Nome da planilha
    """
    # Limpa o cache para forçar recarregar os dados
    st.session_state.local_data[sheet_name] = pd.DataFrame()

def registrar_receita():
    """
    Formulário para registrar uma nova receita.
    """
    st.subheader("📈 Receita")
    
    # Carregar dados necessários
    df_categorias_receitas = carregar_dados_sob_demanda("Categorias_Receitas")
    df_projetos = carregar_dados_sob_demanda("Projetos")
    df_receitas = carregar_dados_sob_demanda("Receitas")
    
    # Formatar colunas de data
    for col in df_receitas.columns:
        if "Data" in col:
            try:
                # Tenta converter para datetime com formato específico
                df_receitas[col] = pd.to_datetime(df_receitas[col], errors='coerce', format="%d/%m/%Y")
                # Formata para DD/MM/YYYY
                df_receitas[col] = df_receitas[col].dt.strftime('%d/%m/%Y')
            except:
                # Se falhar, garante que a coluna seja do tipo string
                df_receitas[col] = df_receitas[col].astype(str)
    
    # Verificar se os dados foram carregados corretamente
    if df_categorias_receitas.empty or "Categoria" not in df_categorias_receitas.columns:
        df_categorias_receitas = pd.DataFrame({"Categoria": ["Pró-Labore", "Investimentos", "Freelance", "Outros"]})
    
    # Abas para registrar e visualizar receitas
    tabs = st.tabs(["Registrar Receita", "Receitas Cadastradas"])
    with tabs[0]:
        st.markdown("### Nova Receita")
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
            cols = st.columns(2)
            with cols[0]:
                submit_receita = st.form_submit_button("Registrar Receita")
            if submit_receita:
                campos_invalidos = []
                if valor <= 0:
                    campos_invalidos.append("Valor (deve ser maior que zero)")
                if not projeto:
                    campos_invalidos.append("Projeto")
                if campos_invalidos:
                    st.error(f"Os seguintes campos são obrigatórios: {', '.join(campos_invalidos)}")
                else:
                    nova_receita = {
                        "DataRecebimento": data_recebimento.strftime("%d/%m/%Y"),
                        "Descrição": descricao,
                        "Categoria": categoria,
                        "ValorTotal": str(valor),
                        "FormaPagamento": forma_pagamento,
                        "Projeto": projeto,
                        "NF": "Não"
                    }
                    if adicionar_linha_sheets(nova_receita, "Receitas"):
                        st.success("Receita registrada com sucesso!")
                        st.session_state.local_data["receitas"] = pd.DataFrame()
                    else:
                        st.error("Erro ao registrar receita.")
    with tabs[1]:
        st.markdown("### Receitas Cadastradas")
        column_config = {
            "DataRecebimento": st.column_config.TextColumn("Data de Recebimento"),
            "Descrição": st.column_config.TextColumn("Descrição"),
            "Categoria": st.column_config.SelectboxColumn("Categoria", options=df_categorias_receitas["Categoria"].tolist() if not df_categorias_receitas.empty else []),
            "ValorTotal": st.column_config.NumberColumn("Valor Total", min_value=0.0, step=0.01, format="%.2f"),
            "FormaPagamento": st.column_config.SelectboxColumn("Forma de Pagamento", options=["Pix", "Transferência", "Dinheiro", "Cheque", "Cartão de Crédito", "Outros"]),
            "Projeto": st.column_config.SelectboxColumn("Projeto", options=[""] + list(df_projetos["Projeto"]) if not df_projetos.empty and "Projeto" in df_projetos.columns else [""]),
            "NF": st.column_config.SelectboxColumn("Nota Fiscal", options=["Sim", "Não"])
        }
        column_order = ["DataRecebimento", "Descrição", "Categoria", "ValorTotal", "FormaPagamento", "Projeto", "NF"]
        with st.form("receitas_form"):
            edited_df = st.data_editor(
                df_receitas,
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic",
                key="receitas_editor",
                column_config=column_config,
                column_order=column_order,
                height=400
            )
            if st.form_submit_button("Salvar Alterações", use_container_width=True):
                with st.spinner("Salvando dados..."):
                    try:
                        if salvar_dados_sheets(edited_df, "Receitas"):
                            salvar_dados(edited_df, "receitas")
                            st.success("Dados salvos com sucesso!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar dados: {str(e)}")

def registrar_despesa():
    """
    Formulário para registrar uma nova despesa.
    """
    # Carregar dados necessários
    df_categorias_despesas = carregar_dados_sob_demanda("Categorias_Despesas")
    df_fornecedor_despesas = carregar_dados_sob_demanda("Fornecedor_Despesas")
    df_projetos = carregar_dados_sob_demanda("Projetos")
    df_despesas = carregar_dados_sob_demanda("Despesas")
    
    # Formatar colunas de data
    for col in df_despesas.columns:
        if "Data" in col:
            try:
                df_despesas[col] = pd.to_datetime(df_despesas[col], errors='coerce', format="%d/%m/%Y")
                df_despesas[col] = df_despesas[col].dt.strftime('%d/%m/%Y')
            except:
                df_despesas[col] = df_despesas[col].astype(str)
    st.subheader("📤 Despesa")
    abas_despesas = st.tabs(["Registrar Despesa", "Despesas Cadastradas"])
    with abas_despesas[0]:
        with st.form("nova_despesa"):
            col1, col2 = st.columns(2)
            with col1:
                data_pagamento = st.date_input("Data de Pagamento", datetime.now())
                descricao = st.text_input("Descrição")
                categoria = st.selectbox("Categoria", df_categorias_despesas["Categoria"].tolist() if not df_categorias_despesas.empty else ["Alimentação", "Transporte", "Moradia", "Saúde", "Educação", "Lazer", "Outros"])
                fornecedor = st.selectbox("Fornecedor", df_fornecedor_despesas["Fornecedor"].tolist() if not df_fornecedor_despesas.empty else ["Outros"])
                responsavel = st.selectbox("Responsável", ["Bruno", "Victor"])
            with col2:
                valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
                parcelas = st.number_input("Parcelas", min_value=1, step=1)
                forma_pagamento = st.selectbox("Forma de Pagamento", ["Pix", "Transferência", "Dinheiro", "Cheque", "Cartão de Crédito", "Outros"])
                projeto = st.selectbox("Projeto", [""] + list(df_projetos["Projeto"]) if not df_projetos.empty else [""])
                nf = st.selectbox("Nota Fiscal", ["Sim", "Não"])
            submitted = st.form_submit_button("Registrar Despesa")
            if submitted:
                campos_invalidos = []
                if valor <= 0:
                    campos_invalidos.append("Valor (deve ser maior que zero)")
                if not projeto:
                    campos_invalidos.append("Projeto")
                if campos_invalidos:
                    st.error(f"Os seguintes campos são obrigatórios: {', '.join(campos_invalidos)}")
                else:
                    valor_parcela = round(valor / parcelas, 2)
                    lista_parcelas = []
                    for i in range(parcelas):
                        data_parcela = data_pagamento + relativedelta(months=+i)
                        parcela_info = {
                            "DataPagamento": data_parcela.strftime("%d/%m/%Y"),
                            "Descrição": descricao,
                            "Categoria": categoria,
                            "ValorTotal": str(valor_parcela),
                            "Parcelas": f"{i + 1}/{parcelas}",
                            "FormaPagamento": forma_pagamento,
                            "Responsável": responsavel,
                            "Fornecedor": fornecedor,
                            "Projeto": projeto,
                            "NF": nf
                        }
                        lista_parcelas.append(parcela_info)
                    sucesso = True
                    for parcela in lista_parcelas:
                        if not adicionar_linha_sheets(parcela, "Despesas"):
                            sucesso = False
                            break
                    if sucesso:
                        st.success(f"Despesa registrada com sucesso! {parcelas} parcela(s) criada(s).")
                        st.session_state.local_data["despesas"] = pd.DataFrame()
                        df_despesas = carregar_dados_sob_demanda("Despesas", force_reload=True)
                    else:
                        st.error("Erro ao registrar despesa.")
    with abas_despesas[1]:
        st.markdown("### Despesas Cadastradas")
        column_config = {
            "DataPagamento": st.column_config.TextColumn("Data de Pagamento"),
            "Descrição": st.column_config.TextColumn("Descrição"),
            "Categoria": st.column_config.SelectboxColumn("Categoria", options=df_categorias_despesas["Categoria"].tolist() if not df_categorias_despesas.empty else []),
            "ValorTotal": st.column_config.NumberColumn("Valor Total", min_value=0.0, step=0.01, format="%.2f"),
            "Parcelas": st.column_config.TextColumn("Parcelas"),
            "FormaPagamento": st.column_config.SelectboxColumn("Forma de Pagamento", options=["Pix", "Transferência", "Dinheiro", "Cheque", "Cartão de Crédito", "Outros"]),
            "Responsável": st.column_config.SelectboxColumn("Responsável", options=["Bruno", "Victor"]),
            "Fornecedor": st.column_config.SelectboxColumn("Fornecedor", options=df_fornecedor_despesas["Fornecedor"].tolist() if not df_fornecedor_despesas.empty else []),
            "Projeto": st.column_config.SelectboxColumn("Projeto", options=[""] + list(df_projetos["Projeto"]) if not df_projetos.empty else [""]),
            "NF": st.column_config.SelectboxColumn("Nota Fiscal", options=["Sim", "Não"])
        }
        column_order = ["DataPagamento", "Descrição", "Categoria", "ValorTotal", "Parcelas", "FormaPagamento", 
                       "Responsável", "Fornecedor", "Projeto", "NF"]
        with st.form("despesas_form"):
            edited_df = st.data_editor(
                df_despesas,
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic",
                key="despesas_editor",
                column_config=column_config,
                column_order=column_order,
                height=400
            )
            if st.form_submit_button("Salvar Alterações", use_container_width=True):
                with st.spinner("Salvando dados..."):
                    try:
                        if salvar_dados_sheets(edited_df, "Despesas"):
                            salvar_dados(edited_df, "despesas")
                            st.success("Dados salvos com sucesso!")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar dados: {str(e)}")

def registrar():
    """
    Página principal para registrar transações.
    """
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
        from modules.pages.projetos import registrar_projeto
        registrar_projeto()
    
    # Conteúdo da aba Cliente
    with tabs[3]:
        from modules.pages.clientes import registrar_cliente
        registrar_cliente()
    
    # Conteúdo da aba Funcionário
    with tabs[4]:
        from modules.pages.funcionarios import registrar_funcionario
        registrar_funcionario()
    
    # Conteúdo da aba Categoria
    with tabs[5]:
        from modules.pages.categorias import registrar_categoria
        registrar_categoria()
    
    # Conteúdo da aba Fornecedor
    with tabs[6]:
        from modules.pages.fornecedores import registrar_fornecedor
        registrar_fornecedor()
