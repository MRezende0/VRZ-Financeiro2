import streamlit as st
import pandas as pd
from modules.data.sheets import carregar_dados_sob_demanda, salvar_dados_sheets, adicionar_linha_sheets

def registrar_cliente():
    """
    Formulário para registrar um novo cliente.
    """
    st.subheader("👤 Cliente")
    
    # Carregar dados existentes
    try:
        df_clientes = carregar_dados_sob_demanda("Clientes")
        
        # Verificar se o DataFrame está vazio ou não existe
        if df_clientes.empty:
            df_clientes = pd.DataFrame(columns=["Nome", "CPF", "Endereço", "Contato", "TipoNF"])
        
        # Converter todas as colunas para string para evitar problemas de tipo
        for col in df_clientes.columns:
            df_clientes[col] = df_clientes[col].astype(str)
        
        # Flag para controlar se um novo cliente foi adicionado
        novo_cliente_adicionado = False
        novo_cliente_dados = {}
        
        # Abas para registrar e visualizar clientes
        tabs = st.tabs(["Registrar Cliente", "Clientes Cadastrados"])
        with tabs[0]:
            st.markdown("### Novo Cliente")
            with st.form("novo_cliente"):
                col1, col2 = st.columns(2)
                with col1:
                    nome = st.text_input("Nome/Razão Social")
                    cpf = st.text_input("CPF/CNPJ")
                with col2:
                    contato = st.text_input("Contato")
                    tipo_nf = st.selectbox("Tipo de Nota Fiscal", ["Engenharia", "Desenho Técnico"])
                endereco = st.text_input("Endereço completo de cobrança")
                submit_cliente = st.form_submit_button("Registrar Cliente")
                if submit_cliente:
                    campos_invalidos = []
                    if not nome:
                        campos_invalidos.append("Nome/Razão Social")
                    if not contato:
                        campos_invalidos.append("Contato")
                    if campos_invalidos:
                        st.error(f"Os seguintes campos são obrigatórios: {', '.join(campos_invalidos)}")
                    else:
                        novo_cliente = {
                            "Nome": nome,
                            "CPF": str(cpf),
                            "Endereço": endereco,
                            "Contato": contato,
                            "TipoNF": tipo_nf
                        }
                        if adicionar_linha_sheets(novo_cliente, "Clientes"):
                            st.success("Cliente registrado com sucesso!")
                            novo_cliente_adicionado = True
                            st.session_state.local_data["clientes"] = pd.DataFrame()
                        else:
                            st.error("Erro ao registrar cliente.")
        with tabs[1]:
            st.markdown("### Clientes Cadastrados")
            if novo_cliente_adicionado:
                df_clientes = carregar_dados_sob_demanda("Clientes", force_reload=True)
            column_config = {
                "Nome": st.column_config.TextColumn("Nome/Razão Social"),
                "CPF": st.column_config.TextColumn("CPF/CNPJ"),
                "Endereço": st.column_config.TextColumn("Endereço completo de cobrança"),
                "Contato": st.column_config.TextColumn("Contato"),
                "TipoNF": st.column_config.SelectboxColumn("Tipo de Nota Fiscal", options=["Engenharia", "Desenho Técnico"])
            }
            column_order = ["Nome", "CPF", "Endereço", "Contato", "TipoNF"]
            with st.form("clientes_reg_form"): 
                edited_df = st.data_editor(
                    df_clientes,
                    use_container_width=True,
                    hide_index=True,
                    num_rows="dynamic",
                    key="clientes_reg_editor",
                    column_config=column_config,
                    column_order=column_order,
                    height=400
                )
                if st.form_submit_button("Salvar Alterações", use_container_width=True):
                    with st.spinner("Salvando dados..."):
                        try:
                            if salvar_dados_sheets(edited_df, "Clientes"):
                                st.success("Dados salvos com sucesso!")
                                st.session_state.local_data["clientes"] = pd.DataFrame()
                                st.rerun()
                            else:
                                st.error("Erro ao salvar dados no Google Sheets.")
                        except Exception as e:
                            st.error(f"Erro ao salvar dados: {str(e)}")
    
    except Exception as e:
        st.error(f"Erro ao carregar dados dos clientes: {e}")

def clientes():
    """
    Página principal para gerenciar clientes.
    """
    st.title("👥 Clientes")
    
    # Carregar dados dos clientes
    df_clientes = carregar_dados_sob_demanda("Clientes")
    
    # Exibir a tabela de clientes
    st.write("### Lista de Clientes")
    
    # Filtro de busca
    filtro = st.text_input("Buscar cliente por nome ou CPF/CNPJ")
    
    # Aplicar filtro
    if filtro:
        df_filtrado = df_clientes[
            df_clientes["Nome"].str.contains(filtro, case=False, na=False) | 
            df_clientes["CPF"].str.contains(filtro, case=False, na=False)
        ]
    else:
        df_filtrado = df_clientes
    
    # Configuração das colunas para a tabela de clientes
    column_config = {
        "Nome": st.column_config.TextColumn("Nome/Razão Social"),
        "CPF": st.column_config.TextColumn("CPF/CNPJ"),
        "Endereço": st.column_config.TextColumn("Endereço"),
        "Contato": st.column_config.TextColumn("Contato"),
        "TipoNF": st.column_config.SelectboxColumn("Tipo de Nota Fiscal", options=["Pessoa Física", "Pessoa Jurídica", "Não Aplicável"])
    }
    
    # Definir a ordem das colunas
    column_order = ["Nome", "CPF", "Endereço", "Contato", "TipoNF"]
    
    # Criar formulário para a tabela editável
    if not df_filtrado.empty:
        with st.form("clientes_page_form"):
            # Exibe a tabela editável com configuração personalizada
            edited_df = st.data_editor(
                df_filtrado,
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic",
                key="clientes_page_editor",
                column_config=column_config,
                column_order=column_order,
                height=400
            )
            
            # Botão para salvar alterações
            if st.form_submit_button("Salvar Alterações", use_container_width=True):
                with st.spinner("Salvando dados..."):
                    try:
                        # Recarregar os dados mais recentes do Google Sheets
                        df_completo = carregar_dados_sob_demanda("Clientes")
                        
                        # Remover os registros que foram editados para evitar duplicações
                        if filtro:
                            # Se há filtro, manter os registros que não foram filtrados
                            mask = ~(df_completo["Nome"].str.contains(filtro, case=False, na=False) | 
                                   df_completo["CPF"].str.contains(filtro, case=False, na=False))
                            df_completo = df_completo[mask]
                        else:
                            # Se não há filtro, substituir completamente os dados
                            df_completo = pd.DataFrame(columns=df_clientes.columns)
                        
                        # Combinar os dados originais com os editados
                        df_final = pd.concat([df_completo, edited_df], ignore_index=True)
                        
                        # Atualizar os dados no Google Sheets
                        if salvar_dados_sheets(df_final, "Clientes"):
                            st.success("Dados salvos com sucesso!")
                            # Limpar o cache para forçar recarregar os dados
                            st.session_state.local_data["clientes"] = pd.DataFrame()
                            st.rerun()
                        else:
                            st.error("Erro ao salvar dados no Google Sheets.")
                    except Exception as e:
                        st.error(f"Erro ao salvar dados: {str(e)}")
    else:
        st.info("Nenhum cliente encontrado.")
    
    # Botão para adicionar novo cliente
    if st.button("Adicionar Novo Cliente"):
        st.session_state.page = "registrar"
        st.session_state.tab = "Cliente"
        st.rerun()
