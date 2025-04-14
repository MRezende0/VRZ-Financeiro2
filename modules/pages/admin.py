"""
Página de administração do sistema.
"""
import os
import streamlit as st
import pandas as pd
from datetime import datetime
from modules.data.sheets import verificar_estrutura_planilha, verificar_todas_planilhas, salvar_dados_sheets
from utils.backup import criar_backup_local, restaurar_backup, listar_backups
from utils.config import COLUNAS_ESPERADAS
from modules.ui.components import card_metric

def admin():
    """
    Página de administração do sistema.
    """
    st.title("⚙️ Administração do Sistema")
    
    # Verificar se o usuário tem permissão de administrador
    if not st.session_state.get("admin", False):
        st.warning("Você não tem permissão para acessar esta página.")
        return
    
    # Tabs para diferentes funcionalidades
    tab1, tab2, tab3 = st.tabs(["Backup e Restauração", "Verificação de Planilhas", "Informações do Sistema"])
    
    with tab1:
        backup_e_restauracao()
    
    with tab2:
        verificacao_planilhas()
    
    with tab3:
        informacoes_sistema()

def backup_e_restauracao():
    """
    Funcionalidade de backup e restauração de dados.
    """
    st.header("💾 Backup e Restauração")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Criar Backup")
        st.write("Crie um backup local de todos os dados do sistema.")
        
        if st.button("Criar Backup Agora", key="btn_criar_backup"):
            with st.spinner("Criando backup..."):
                arquivo_backup = criar_backup_local()
                if arquivo_backup:
                    st.success(f"Backup criado com sucesso: {os.path.basename(arquivo_backup)}")
                else:
                    st.error("Erro ao criar backup.")
    
    with col2:
        st.subheader("Backups Disponíveis")
        backups = listar_backups()
        
        if backups:
            # Formata os nomes dos arquivos para exibição
            opcoes_backup = {}
            for backup in backups:
                nome_arquivo = os.path.basename(backup)
                # Extrai a data e hora do nome do arquivo (formato: backup_YYYYMMDD_HHMMSS.json)
                try:
                    data_hora = nome_arquivo.replace("backup_", "").replace(".json", "")
                    data_hora_formatada = f"{data_hora[6:8]}/{data_hora[4:6]}/{data_hora[0:4]} {data_hora[9:11]}:{data_hora[11:13]}:{data_hora[13:15]}"
                    opcoes_backup[f"{data_hora_formatada}"] = backup
                except:
                    opcoes_backup[nome_arquivo] = backup
            
            backup_selecionado = st.selectbox(
                "Selecione um backup para restaurar:",
                options=list(opcoes_backup.keys()),
                key="select_backup"
            )
            
            if st.button("Restaurar Backup", key="btn_restaurar_backup"):
                with st.spinner("Restaurando backup..."):
                    caminho_backup = opcoes_backup[backup_selecionado]
                    dfs_restaurados = restaurar_backup(caminho_backup)
                    
                    if dfs_restaurados:
                        # Exibe as planilhas que serão restauradas
                        st.write("Planilhas que serão restauradas:")
                        for sheet_name, df in dfs_restaurados.items():
                            st.write(f"- {sheet_name}: {len(df)} registros")
                        
                        # Confirmação final
                        if st.button("Confirmar Restauração", key="btn_confirmar_restauracao"):
                            # Salva cada DataFrame restaurado
                            sucessos = []
                            falhas = []
                            for sheet_name, df in dfs_restaurados.items():
                                if salvar_dados_sheets(df, sheet_name):
                                    sucessos.append(sheet_name)
                                else:
                                    falhas.append(sheet_name)
                            
                            if falhas:
                                st.error(f"Erro ao restaurar as seguintes planilhas: {', '.join(falhas)}")
                            
                            if sucessos:
                                st.success(f"Backup restaurado com sucesso para: {', '.join(sucessos)}")
                                # Limpa o cache para forçar recarregar os dados
                                for sheet_name in sucessos:
                                    if sheet_name in st.session_state.local_data:
                                        st.session_state.local_data[sheet_name] = pd.DataFrame()
                    else:
                        st.error("Erro ao restaurar backup.")
        else:
            st.info("Nenhum backup disponível.")
    
    # Programação de backups automáticos
    st.subheader("Backups Automáticos")
    st.write("Configure backups automáticos para garantir a segurança dos seus dados.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        ativar_backup_auto = st.checkbox("Ativar backups automáticos", value=st.session_state.get("backup_auto_ativo", False))
        if ativar_backup_auto != st.session_state.get("backup_auto_ativo", False):
            st.session_state.backup_auto_ativo = ativar_backup_auto
    
    with col2:
        frequencia_backup = st.selectbox(
            "Frequência de backup:",
            options=["Diário", "Semanal", "Mensal"],
            index=0 if st.session_state.get("frequencia_backup", "Diário") == "Diário" else 
                  1 if st.session_state.get("frequencia_backup", "Diário") == "Semanal" else 2
        )
        if frequencia_backup != st.session_state.get("frequencia_backup", "Diário"):
            st.session_state.frequencia_backup = frequencia_backup
    
    # Informações sobre os backups
    st.info(
        "Os backups são armazenados localmente na pasta 'backups' do projeto. "
        "Recomendamos fazer backups regulares e manter cópias em um local seguro."
    )

def verificacao_planilhas():
    """
    Funcionalidade de verificação e reparo de planilhas.
    """
    st.header("🔍 Verificação de Planilhas")
    
    st.write("Verifique a estrutura das planilhas e corrija problemas automaticamente.")
    
    # Botão para verificar todas as planilhas
    if st.button("Verificar Todas as Planilhas", key="btn_verificar_todas"):
        with st.spinner("Verificando planilhas..."):
            if verificar_todas_planilhas():
                st.success("Todas as planilhas estão corretas ou foram corrigidas com sucesso.")
            else:
                st.error("Algumas planilhas não puderam ser corrigidas. Verifique os erros abaixo.")
    
    # Verificação individual de planilhas
    st.subheader("Verificação Individual")
    
    # Lista de planilhas
    planilhas = list(COLUNAS_ESPERADAS.keys())
    planilha_selecionada = st.selectbox("Selecione uma planilha:", options=planilhas)
    
    if st.button("Verificar Planilha", key="btn_verificar_individual"):
        with st.spinner(f"Verificando planilha '{planilha_selecionada}'..."):
            if verificar_estrutura_planilha(planilha_selecionada):
                st.success(f"A planilha '{planilha_selecionada}' está correta ou foi corrigida com sucesso.")
            else:
                st.error(f"Não foi possível corrigir a planilha '{planilha_selecionada}'.")
    
    # Exibir estrutura esperada
    if planilha_selecionada:
        st.subheader(f"Estrutura Esperada: {planilha_selecionada}")
        st.write("Colunas esperadas:")
        st.code(", ".join(COLUNAS_ESPERADAS.get(planilha_selecionada, [])))

def informacoes_sistema():
    """
    Exibe informações sobre o sistema.
    """
    st.header("ℹ️ Informações do Sistema")
    
    # Informações gerais
    st.subheader("Informações Gerais")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        card_metric("Versão do Sistema", "1.0.0")
    
    with col2:
        card_metric("Usuário", st.session_state.get("username", "Não logado"))
    
    with col3:
        card_metric("Último Login", datetime.now().strftime("%d/%m/%Y %H:%M"))
    
    # Informações sobre as planilhas
    st.subheader("Informações das Planilhas")
    
    # Carrega informações básicas sobre cada planilha
    info_planilhas = []
    for sheet_name in COLUNAS_ESPERADAS.keys():
        try:
            df = st.session_state.local_data.get(sheet_name, pd.DataFrame())
            info_planilhas.append({
                "Planilha": sheet_name,
                "Registros": len(df),
                "Colunas": len(df.columns) if not df.empty else 0,
                "Status": "Carregada" if not df.empty else "Não carregada"
            })
        except:
            info_planilhas.append({
                "Planilha": sheet_name,
                "Registros": 0,
                "Colunas": 0,
                "Status": "Erro"
            })
    
    # Exibe a tabela de informações
    st.dataframe(pd.DataFrame(info_planilhas), hide_index=True)
    
    # Informações sobre o ambiente
    st.subheader("Ambiente")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Python**")
        import sys
        st.code(f"Versão: {sys.version}")
    
    with col2:
        st.write("**Streamlit**")
        import streamlit as st
        st.code(f"Versão: {st.__version__}")
    
    # Bibliotecas utilizadas
    st.subheader("Bibliotecas")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Pandas**")
        import pandas as pd
        st.code(f"Versão: {pd.__version__}")
    
    with col2:
        st.write("**Plotly**")
        import plotly
        st.code(f"Versão: {plotly.__version__}")
    
    with col3:
        st.write("**gspread**")
        import gspread
        st.code(f"Versão: {gspread.__version__}")
