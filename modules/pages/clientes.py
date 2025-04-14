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
        
        # Formulário para adicionar novo cliente
        with st.form("novo_cliente"):
            col1, col2 = st.columns(2)
            
            with col1:
                nome = st.text_input("Nome?Razão Social")
                cpf = st.text_input("CPF/CNPJ")
            
            with col2:
                contato = st.text_input("Contato")
                tipo_nf = st.selectbox("Tipo de Nota Fiscal", ["Pessoa Física", "Pessoa Jurídica", "Não Aplicável"])

            endereco = st.text_input("Endereço")
            
            submit_cliente = st.form_submit_button("Registrar Cliente")
            
            if submit_cliente:
                # Validar dados
                if not nome:
                    st.error("O nome do cliente é obrigatório.")
                else:
                    # Criar dicionário com os dados do novo cliente
                    novo_cliente = {
                        "Nome": nome,
                        "CPF": str(cpf),  # Garantir que CPF seja string
                        "Endereço": endereco,
                        "Contato": contato,
                        "TipoNF": tipo_nf
                    }
                    
                    # Adicionar o novo cliente ao DataFrame
                    if adicionar_linha_sheets(novo_cliente, "Clientes"):
                        st.success("Cliente registrado com sucesso!")
                        novo_cliente_adicionado = True
                        novo_cliente_dados = novo_cliente
                        # Limpar o cache para forçar recarregar os dados
                        st.session_state.local_data["clientes"] = pd.DataFrame()
                    else:
                        st.error("Erro ao registrar cliente.")
        
        # Exibir lista de clientes
        st.write("### Lista de Clientes")
        
        # Recarregar dados se um novo cliente foi adicionado
        if novo_cliente_adicionado:
            df_clientes = carregar_dados_sob_demanda("Clientes", force_reload=True)
        
        # Exibir a tabela de clientes
        if not df_clientes.empty:
            edited_df = st.data_editor(
                df_clientes,
                use_container_width=True,
                hide_index=True,
                num_rows="fixed"
            )
            
            # Verificar se houve alterações
            if not edited_df.equals(df_clientes):
                # Salvar alterações
                if salvar_dados_sheets(edited_df, "Clientes"):
                    st.success("Alterações salvas com sucesso!")
                    # Limpar o cache para forçar recarregar os dados
                    st.session_state.local_data["clientes"] = pd.DataFrame()
                else:
                    st.error("Erro ao salvar alterações.")
        else:
            st.info("Nenhum cliente cadastrado.")
    
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
    
    # Exibir a tabela de clientes
    if not df_filtrado.empty:
        edited_df = st.data_editor(
            df_filtrado,
            use_container_width=True,
            hide_index=True,
            num_rows="fixed"
        )
        
        # Verificar se houve alterações
        if not edited_df.equals(df_filtrado):
            # Atualizar o DataFrame original
            for index, row in edited_df.iterrows():
                for col in df_clientes.columns:
                    df_clientes.loc[index, col] = row[col]
            
            # Salvar alterações
            if salvar_dados_sheets(df_clientes, "Clientes"):
                st.success("Alterações salvas com sucesso!")
                # Limpar o cache para forçar recarregar os dados
                st.session_state.local_data["clientes"] = pd.DataFrame()
            else:
                st.error("Erro ao salvar alterações.")
    else:
        st.info("Nenhum cliente encontrado.")
    
    # Botão para adicionar novo cliente
    if st.button("Adicionar Novo Cliente"):
        st.session_state.page = "registrar"
        st.session_state.tab = "Cliente"
        st.rerun()
