import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from modules.data.sheets import carregar_dados_sob_demanda

def formatar_valor(valor):
    """
    Formata um valor numérico como moeda brasileira.
    
    Args:
        valor: Valor a ser formatado
    
    Returns:
        str: Valor formatado como moeda brasileira
    """
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def aplicar_filtros(df, filtros, tipo="receitas"):
    """
    Aplica os filtros selecionados ao DataFrame.
    
    Args:
        df: DataFrame a ser filtrado
        filtros: Dicionário com os filtros a serem aplicados
        tipo: Tipo de dados ("receitas", "despesas" ou "projetos")
    
    Returns:
        pandas.DataFrame: DataFrame filtrado
    """
    df_filtrado = df.copy()
    
    # Converter colunas de data
    try:
        if tipo == "receitas":
            df_filtrado["DataRecebimento"] = pd.to_datetime(df_filtrado["DataRecebimento"], dayfirst=True, errors='coerce')
        elif tipo == "despesas":
            df_filtrado["DataPagamento"] = pd.to_datetime(df_filtrado["DataPagamento"], dayfirst=True, errors='coerce')
    except:
        pass
    
    # Filtrar por mês
    if filtros["mes"] is not None and len(filtros["mes"]) > 0 and "Todos" not in filtros["mes"]:
        try:
            if tipo == "receitas":
                df_filtrado = df_filtrado[df_filtrado["DataRecebimento"].dt.month.isin(filtros["mes"])]
            elif tipo == "despesas":
                df_filtrado = df_filtrado[df_filtrado["DataPagamento"].dt.month.isin(filtros["mes"])]
        except:
            pass
    
    # Filtrar por ano
    if filtros["ano"] is not None and len(filtros["ano"]) > 0 and "Todos" not in filtros["ano"]:
        try:
            if tipo == "receitas":
                df_filtrado = df_filtrado[df_filtrado["DataRecebimento"].dt.year.isin(filtros["ano"])]
            elif tipo == "despesas":
                df_filtrado = df_filtrado[df_filtrado["DataPagamento"].dt.year.isin(filtros["ano"])]
        except:
            pass
    
    # Filtrar por categoria
    if filtros["categoria"] is not None and len(filtros["categoria"]) > 0:
        try:
            df_filtrado = df_filtrado[df_filtrado["Categoria"].isin(filtros["categoria"])]
        except:
            pass
    
    # Filtrar por projeto
    if filtros["projeto"] is not None and len(filtros["projeto"]) > 0:
        try:
            df_filtrado = df_filtrado[df_filtrado["Projeto"].isin(filtros["projeto"])]
        except:
            pass
    
    # Filtrar por responsável (apenas para despesas e projetos)
    if filtros["responsavel"] is not None and len(filtros["responsavel"]) > 0:
        try:
            if tipo == "despesas" and "Responsável" in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado["Responsável"].isin(filtros["responsavel"])]
            elif tipo == "projetos":
                # Filtrar por qualquer um dos campos de responsável
                mask = (
                    df_filtrado["ResponsávelElétrico"].isin(filtros["responsavel"]) |
                    df_filtrado["ResponsávelHidráulico"].isin(filtros["responsavel"]) |
                    df_filtrado["ResponsávelModelagem"].isin(filtros["responsavel"]) |
                    df_filtrado["ResponsávelDetalhamento"].isin(filtros["responsavel"])
                )
                df_filtrado = df_filtrado[mask]
        except:
            pass
    
    # Filtrar por fornecedor (apenas para despesas)
    if tipo == "despesas" and filtros["fornecedor"] is not None and len(filtros["fornecedor"]) > 0:
        try:
            df_filtrado = df_filtrado[df_filtrado["Fornecedor"].isin(filtros["fornecedor"])]
        except:
            pass
    
    # Filtrar por status (apenas para projetos)
    if tipo == "projetos" and filtros["status"] is not None and len(filtros["status"]) > 0:
        try:
            df_filtrado = df_filtrado[df_filtrado["Status"].isin(filtros["status"])]
        except:
            pass
    
    # Filtrar por arquiteto (apenas para projetos)
    if tipo == "projetos" and filtros["arquiteto"] is not None and len(filtros["arquiteto"]) > 0:
        try:
            df_filtrado = df_filtrado[df_filtrado["Arquiteto"].isin(filtros["arquiteto"])]
        except:
            pass
    
    return df_filtrado

def calcular_metricas_financeiras(df_receitas, df_despesas, filtros=None):
    """
    Calcula as métricas financeiras com base nas receitas e despesas.
    
    Args:
        df_receitas: DataFrame com as receitas
        df_despesas: DataFrame com as despesas
        filtros: Dicionário com os filtros a serem aplicados
    
    Returns:
        tuple: Receita total, despesa total, saldo, receitas por categoria, despesas por categoria
    """
    # Aplicar filtros se especificados
    if filtros:
        df_receitas = aplicar_filtros(df_receitas, filtros, tipo="receitas")
        df_despesas = aplicar_filtros(df_despesas, filtros, tipo="despesas")
    
    # Calcular receita total
    try:
        receita_total = df_receitas["ValorTotal"].astype(float).sum()
    except:
        receita_total = 0
    
    # Calcular despesa total
    try:
        despesa_total = df_despesas["ValorTotal"].astype(float).sum()
    except:
        despesa_total = 0
    
    # Calcular saldo
    saldo = receita_total - despesa_total
    
    # Calcular receitas por categoria
    try:
        receitas_por_categoria = df_receitas.groupby("Categoria")["ValorTotal"].astype(float).sum().reset_index()
    except:
        receitas_por_categoria = pd.DataFrame(columns=["Categoria", "ValorTotal"])
    
    # Calcular despesas por categoria
    try:
        despesas_por_categoria = df_despesas.groupby("Categoria")["ValorTotal"].astype(float).sum().reset_index()
    except:
        despesas_por_categoria = pd.DataFrame(columns=["Categoria", "ValorTotal"])
    
    return receita_total, despesa_total, saldo, receitas_por_categoria, despesas_por_categoria

def dashboard():
    """
    Página principal do dashboard financeiro.
    """
    st.title("📊 Dashboard Financeiro")
    
    # Carregar dados
    df_receitas = carregar_dados_sob_demanda("Receitas")
    df_despesas = carregar_dados_sob_demanda("Despesas")
    df_projetos = carregar_dados_sob_demanda("Projetos")

    # Filtros na sidebar
    st.sidebar.title("Filtros")

    # Filtros de período
    col1, col2 = st.columns(2)
    with col1:
        opcoes_mes = ["Todos"] + list(range(1, 13))
        mes_selecionado = st.sidebar.multiselect("Mês", opcoes_mes)
        # Converter para inteiro se não for "Todos"
        mes = None if "Todos" in mes_selecionado else mes_selecionado
    with col2:
        opcoes_ano = ["Todos"] + list(range(2020, 2031))
        ano_selecionado = st.sidebar.multiselect("Ano", opcoes_ano)
        # Converter para inteiro se não for "Todos"
        ano = None if "Todos" in ano_selecionado else ano_selecionado

    # Filtro por categoria (afeta receitas e despesas)
    categorias_receitas = df_receitas["Categoria"].unique()
    categorias_despesas = df_despesas["Categoria"].unique()
    categorias = list(set(categorias_receitas) | set(categorias_despesas))  # União das categorias
    categoria_selecionada = st.sidebar.multiselect("Categoria", categorias)

    # Filtro por número do projeto (afeta receitas, despesas e projetos)
    projetos = df_projetos["Projeto"].unique()
    projeto_selecionado = st.sidebar.multiselect("Projeto", projetos)

    # Filtro por responsável (afeta despesas e projetos)
    responsaveis_despesas = df_despesas["Responsável"].unique()
    responsaveis_projetos = df_projetos["ResponsávelElétrico"].unique().tolist() + \
                            df_projetos["ResponsávelHidráulico"].unique().tolist() + \
                            df_projetos["ResponsávelModelagem"].unique().tolist() + \
                            df_projetos["ResponsávelDetalhamento"].unique().tolist()
    responsaveis = list(set(responsaveis_despesas) | set(responsaveis_projetos))  # União dos responsáveis
    responsavel_selecionado = st.sidebar.multiselect("Responsável", responsaveis)

    # Filtro por fornecedor (afeta despesas)
    fornecedores = df_despesas["Fornecedor"].unique()
    fornecedor_selecionado = st.sidebar.multiselect("Fornecedor", fornecedores)

    # Filtro por status (afeta projetos)
    status = df_projetos["Status"].unique()
    status_selecionado = st.sidebar.multiselect("Status", status)

    # Filtro por arquiteto (afeta projetos)
    arquitetos = df_projetos["Arquiteto"].unique()
    arquiteto_selecionado = st.sidebar.multiselect("Arquiteto", arquitetos)
    
    # Criar dicionário de filtros
    filtros = {
        "mes": mes_selecionado,
        "ano": ano_selecionado,
        "categoria": categoria_selecionada,
        "projeto": projeto_selecionado,
        "responsavel": responsavel_selecionado,
        "fornecedor": fornecedor_selecionado,
        "status": status_selecionado,
        "arquiteto": arquiteto_selecionado
    }

    # Verificar se os dados foram carregados corretamente
    if df_receitas.empty or df_despesas.empty:
        st.warning("Não foi possível carregar os dados financeiros. Verifique a conexão com o Google Sheets.")
        return
    
    # Aplicar filtros aos DataFrames
    df_receitas_filtrado = aplicar_filtros(df_receitas, filtros, tipo="receitas")
    df_despesas_filtrado = aplicar_filtros(df_despesas, filtros, tipo="despesas")
    df_projetos_filtrado = aplicar_filtros(df_projetos, filtros, tipo="projetos")
    
    # Calcular métricas financeiras
    receita_total, despesa_total, saldo, receitas_por_categoria, despesas_por_categoria = calcular_metricas_financeiras(
        df_receitas_filtrado, df_despesas_filtrado, filtros
    )
    
    # Exibir cards com métricas principais
    col1, col2, col3 = st.columns(3)
    with col1:
        cor_receitas = "#4caf50"
        st.markdown(f"""
        <div class="card">
            <h3>Receita Total</h3>
            <p style="color: {cor_receitas};">{formatar_valor(receita_total)}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        cor_despesas = "#f44336"
        st.markdown(f"""
        <div class="card">
            <h3>Despesa Total</h3>
            <p style="color: {cor_despesas};">{formatar_valor(despesa_total)}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        cor_saldo = "#4caf50" if saldo >= 0 else "#f44336"
        st.markdown(f"""
        <div class="card">
            <h3>Saldo</h3>
            <p style="color: {cor_saldo};">{formatar_valor(saldo)}</p>
        </div>
        """, unsafe_allow_html=True)

    st.write("")
    st.write("")

    # Organização dos gráficos em abas para melhor visualização
    tabs = st.tabs(["Financeiro", "Projetos", "Funcionários"])
    
    with tabs[0]:  # Aba Financeiro
        # Seção 1: Gráficos de Receitas e Despesas por Mês/Ano
        st.markdown("### Análise Mensal")
        col1, col2 = st.columns(2)
        
        # Gráfico 1: Quantidade de receitas por mês/ano
        with col1:
            if not df_receitas_filtrado.empty:
                df_receitas_filtrado["DataRecebimento"] = pd.to_datetime(df_receitas_filtrado["DataRecebimento"])
                df_receitas_filtrado["MesAno"] = df_receitas_filtrado["DataRecebimento"].dt.to_period("M").astype(str)
                receitas_por_mes_ano = df_receitas_filtrado.groupby("MesAno")["ValorTotal"].sum().reset_index()
                receitas_por_mes_ano["MesAno"] = pd.to_datetime(receitas_por_mes_ano["MesAno"])
                
                fig_receitas_mes_ano = px.bar(
                    receitas_por_mes_ano,
                    x="MesAno",
                    y="ValorTotal",
                    text="ValorTotal",
                    title="Receitas por Mês/Ano",
                    labels={"ValorTotal": "Total de Receitas", "MesAno": "Mês/Ano"},
                    color_discrete_sequence=[cor_receitas]
                )
                
                fig_receitas_mes_ano.update_traces(textposition="outside")
                fig_receitas_mes_ano.update_xaxes(
                    tickformat="%b/%Y",
                    dtick="M1",
                    showgrid=False
                )
                fig_receitas_mes_ano.update_yaxes(showgrid=False, showticklabels=False)
                
                st.plotly_chart(fig_receitas_mes_ano, use_container_width=True)

        # Gráfico 2: Quantidade de despesas por mês/ano
        with col2:
            if not df_despesas_filtrado.empty:
                df_despesas_filtrado["DataPagamento"] = pd.to_datetime(df_despesas_filtrado["DataPagamento"])
                df_despesas_filtrado["MesAno"] = df_despesas_filtrado["DataPagamento"].dt.to_period("M").astype(str)
                despesas_por_mes_ano = df_despesas_filtrado.groupby("MesAno")["ValorTotal"].sum().reset_index()
                despesas_por_mes_ano["MesAno"] = pd.to_datetime(despesas_por_mes_ano["MesAno"])
                
                fig_despesas_mes_ano = px.bar(
                    despesas_por_mes_ano,
                    x="MesAno",
                    y="ValorTotal",
                    text="ValorTotal",
                    title="Despesas por Mês/Ano",
                    labels={"ValorTotal": "Total de Despesas", "MesAno": "Mês/Ano"},
                    color_discrete_sequence=[cor_despesas]
                )
                
                fig_despesas_mes_ano.update_traces(textposition="outside")
                fig_despesas_mes_ano.update_xaxes(
                    tickformat="%b/%Y",
                    dtick="M1"
                )
                fig_despesas_mes_ano.update_yaxes(showgrid=False, showticklabels=False)
                
                st.plotly_chart(fig_despesas_mes_ano, use_container_width=True)
        
        # Seção 2: Gráficos de Receitas e Despesas por Categoria
        st.markdown("### Análise por Categoria")
        col1, col2 = st.columns(2)
        
        # Gráfico 3: Receitas por categoria
        with col1:
            if not df_receitas_filtrado.empty:
                receitas_por_categoria = df_receitas_filtrado.groupby("Categoria")["ValorTotal"].sum().reset_index()
                fig_receitas_categoria = px.bar(
                    receitas_por_categoria,
                    x="Categoria",
                    y="ValorTotal",
                    text="ValorTotal",
                    title="Receitas por Categoria",
                    color_discrete_sequence=[cor_receitas]
                )
                fig_receitas_categoria.update_traces(textposition="outside")
                fig_receitas_categoria.update_yaxes(showgrid=False, showticklabels=False)
                st.plotly_chart(fig_receitas_categoria, use_container_width=True)

        # Gráfico 4: Despesas por categoria
        with col2:
            if not df_despesas_filtrado.empty:
                despesas_por_categoria = df_despesas_filtrado.groupby("Categoria")["ValorTotal"].sum().reset_index()
                fig_despesas_categoria = px.bar(
                    despesas_por_categoria,
                    x="Categoria",
                    y="ValorTotal",
                    text="ValorTotal",
                    title="Despesas por Categoria",
                    color_discrete_sequence=[cor_despesas]
                )
                fig_despesas_categoria.update_traces(textposition="outside")
                fig_despesas_categoria.update_yaxes(showgrid=False, showticklabels=False)
                st.plotly_chart(fig_despesas_categoria, use_container_width=True)
        
        # Seção 3: Gráficos de Receitas e Despesas por Projeto e Método de Pagamento
        st.markdown("### Análise por Projeto e Método de Pagamento")
        col1, col2 = st.columns(2)
        
        # Gráfico 5: Receitas e despesas por projeto
        with col1:
            if not df_receitas_filtrado.empty or not df_despesas_filtrado.empty:
                receitas_por_projeto = df_receitas_filtrado.groupby("Projeto")["ValorTotal"].sum().reset_index()
                despesas_por_projeto = df_despesas_filtrado.groupby("Projeto")["ValorTotal"].sum().reset_index()
                fig_projetos = px.bar(
                    pd.concat([receitas_por_projeto.assign(Tipo="Receita"), despesas_por_projeto.assign(Tipo="Despesa")]),
                    x="Projeto",
                    y="ValorTotal",
                    text="ValorTotal",
                    color="Tipo",
                    title="Receitas e Despesas por Projeto",
                    barmode="group",
                    color_discrete_sequence=[cor_receitas, cor_despesas]
                )
                
                fig_projetos.update_traces(textposition="outside")
                fig_projetos.update_yaxes(showgrid=False, showticklabels=False)
                
                st.plotly_chart(fig_projetos, use_container_width=True)

        # Gráfico 6: Receitas e despesas por método de pagamento
        with col2:
            if not df_receitas_filtrado.empty or not df_despesas_filtrado.empty:
                receitas_por_metodo = df_receitas_filtrado.groupby("FormaPagamento")["ValorTotal"].sum().reset_index()
                despesas_por_metodo = df_despesas_filtrado.groupby("FormaPagamento")["ValorTotal"].sum().reset_index()
                fig_metodo_pagamento = px.bar(
                    pd.concat([receitas_por_metodo.assign(Tipo="Receita"), despesas_por_metodo.assign(Tipo="Despesa")]),
                    x="FormaPagamento",
                    y="ValorTotal",
                    text="ValorTotal",
                    color="Tipo",
                    title="Receitas e Despesas por Método de Pagamento",
                    barmode="group",
                    color_discrete_sequence=[cor_receitas, cor_despesas]
                )
                fig_metodo_pagamento.update_traces(textposition="outside")
                fig_metodo_pagamento.update_yaxes(showgrid=False, showticklabels=False)
                st.plotly_chart(fig_metodo_pagamento, use_container_width=True)
        
        # Seção 4: Gráficos de Despesas por Responsável e Fornecedor
        st.markdown("### Análise de Despesas")
        col1, col2 = st.columns(2)
        
        # Gráfico 7: Despesas por responsável
        with col1:
            if not df_despesas_filtrado.empty:
                despesas_por_responsavel = df_despesas_filtrado.groupby("Responsável")["ValorTotal"].sum().reset_index()
                fig_despesas_responsavel = px.bar(
                    despesas_por_responsavel,
                    x="Responsável",
                    y="ValorTotal",
                    text="ValorTotal",
                    title="Despesas por Responsável",
                    color_discrete_sequence=[cor_despesas]
                )
                fig_despesas_responsavel.update_traces(textposition="outside")
                fig_despesas_responsavel.update_yaxes(showgrid=False, showticklabels=False)
                st.plotly_chart(fig_despesas_responsavel, use_container_width=True)

        # Gráfico 8: Despesas por fornecedor
        with col2:
            if not df_despesas_filtrado.empty:
                despesas_por_fornecedor = df_despesas_filtrado.groupby("Fornecedor")["ValorTotal"].sum().reset_index()
                fig_despesas_fornecedor = px.bar(
                    despesas_por_fornecedor,
                    x="Fornecedor",
                    y="ValorTotal",
                    text="ValorTotal",
                    title="Despesas por Fornecedor",
                    color_discrete_sequence=[cor_despesas]
                )
                fig_despesas_fornecedor.update_traces(textposition="outside")
                fig_despesas_fornecedor.update_yaxes(showgrid=False, showticklabels=False)
                st.plotly_chart(fig_despesas_fornecedor, use_container_width=True)
    
    with tabs[1]:  # Aba Projetos        
        # Seção 1: Localização e Status
        st.markdown("### Localização e Status")
        col1, col2 = st.columns(2)
        
        # Gráfico 9: Quantidade de projetos por localização
        with col1:
            if not df_projetos_filtrado.empty:
                projetos_por_localizacao = df_projetos_filtrado["Localizacao"].value_counts().reset_index()
                projetos_por_localizacao.columns = ["Localizacao", "Quantidade"]
                fig_projetos_localizacao = px.bar(
                    projetos_por_localizacao,
                    x="Localizacao",
                    y="Quantidade",
                    text="Quantidade",
                    title="Quantidade de Projetos por Localização"
                )
                fig_projetos_localizacao.update_traces(textposition="outside")
                fig_projetos_localizacao.update_yaxes(showgrid=False, showticklabels=False)
                st.plotly_chart(fig_projetos_localizacao, use_container_width=True)
        
        # Gráfico 13: Quantidade de projetos pelo status
        with col2:
            if not df_projetos_filtrado.empty:
                projetos_status = df_projetos_filtrado["Status"].value_counts().reset_index()
                projetos_status.columns = ["Status", "Quantidade"]
                fig_projetos_status = px.bar(
                    projetos_status,
                    x="Status",
                    y="Quantidade",
                    text="Quantidade",
                    title="Quantidade de Projetos por Status"
                )
                fig_projetos_status.update_traces(textposition="outside")
                fig_projetos_status.update_yaxes(showgrid=False, showticklabels=False)
                st.plotly_chart(fig_projetos_status, use_container_width=True)
        
        # Seção 2: Características dos Projetos
        st.markdown("### Características dos Projetos")
        col1, col2, col3 = st.columns(3)
        
        # Gráfico 10: Quantidade de projetos com placa e sem placa
        with col1:
            if not df_projetos_filtrado.empty:
                projetos_placa = df_projetos_filtrado["Placa"].value_counts().reset_index()
                projetos_placa.columns = ["Placa", "Quantidade"]
                fig_projetos_placa = px.pie(
                    projetos_placa,
                    names="Placa",
                    values="Quantidade",
                    title="Projetos com/sem Placa"
                )
                st.plotly_chart(fig_projetos_placa, use_container_width=True)
        
        # Gráfico 11: Quantidade de projetos com post e sem post
        with col2:
            if not df_projetos_filtrado.empty:
                projetos_post = df_projetos_filtrado["Post"].value_counts().reset_index()
                projetos_post.columns = ["Post", "Quantidade"]
                fig_projetos_post = px.pie(
                    projetos_post,
                    names="Post",
                    values="Quantidade",
                    title="Projetos com/sem Post"
                )
                st.plotly_chart(fig_projetos_post, use_container_width=True)
        
        # Gráfico 12: Quantidade de projetos com contrato e sem contrato
        with col3:
            if not df_projetos_filtrado.empty:
                projetos_contrato = df_projetos_filtrado["Contrato"].value_counts().reset_index()
                projetos_contrato.columns = ["Contrato", "Quantidade"]
                fig_projetos_contrato = px.pie(
                    projetos_contrato,
                    names="Contrato",
                    values="Quantidade",
                    title="Projetos com/sem Contrato"
                )
                st.plotly_chart(fig_projetos_contrato, use_container_width=True)
        
        # Seção 3: Categorização de Projetos
        st.markdown("### Categorização de Projetos")
        col1, col2 = st.columns(2)
        
        # Gráfico 14: Quantidade de projetos pelo briefing
        with col1:
            if not df_projetos_filtrado.empty:
                projetos_briefing = df_projetos_filtrado["Briefing"].value_counts().reset_index()
                projetos_briefing.columns = ["Briefing", "Quantidade"]
                fig_projetos_briefing = px.pie(
                    projetos_briefing,
                    names="Briefing",
                    values="Quantidade",
                    title="Projetos por Briefing"
                )
                st.plotly_chart(fig_projetos_briefing, use_container_width=True)
        
        # Gráfico 16: Quantidade de projetos pelo tipo
        with col2:
            if not df_projetos_filtrado.empty:
                projetos_tipo = df_projetos_filtrado["Tipo"].value_counts().reset_index()
                projetos_tipo.columns = ["Tipo", "Quantidade"]
                fig_projetos_tipo = px.bar(
                    projetos_tipo,
                    x="Tipo",
                    y="Quantidade",
                    text="Quantidade",
                    title="Projetos por Tipo"
                )
                fig_projetos_tipo.update_traces(textposition="outside")
                fig_projetos_tipo.update_yaxes(showgrid=False, showticklabels=False)
                st.plotly_chart(fig_projetos_tipo, use_container_width=True)
        
        # Seção 4: Arquitetos e Pacotes
        st.markdown("### Arquitetos e Pacotes")
        col1, col2 = st.columns(2)
        
        # Gráfico 15: Quantidade de projetos por arquiteto
        with col1:
            if not df_projetos_filtrado.empty:
                projetos_arquiteto = df_projetos_filtrado["Arquiteto"].value_counts().reset_index()
                projetos_arquiteto.columns = ["Arquiteto", "Quantidade"]
                fig_projetos_arquiteto = px.bar(
                    projetos_arquiteto,
                    x="Arquiteto",
                    y="Quantidade",
                    text="Quantidade",
                    title="Projetos por Arquiteto"
                )
                fig_projetos_arquiteto.update_traces(textposition="outside")
                fig_projetos_arquiteto.update_yaxes(showgrid=False, showticklabels=False)
                st.plotly_chart(fig_projetos_arquiteto, use_container_width=True)
        
        # Gráfico 17: Quantidade de projetos pelo pacote
        with col2:
            if not df_projetos_filtrado.empty:
                projetos_pacote = df_projetos_filtrado["Pacote"].value_counts().reset_index()
                projetos_pacote.columns = ["Pacote", "Quantidade"]
                fig_projetos_pacote = px.bar(
                    projetos_pacote,
                    x="Pacote",
                    y="Quantidade",
                    text="Quantidade",
                    title="Projetos por Pacote"
                )
                fig_projetos_pacote.update_traces(textposition="outside")
                fig_projetos_pacote.update_yaxes(showgrid=False, showticklabels=False)
                st.plotly_chart(fig_projetos_pacote, use_container_width=True)
    
    with tabs[2]:  # Aba Responsáveis        
        # Seção 1: m² por Responsáveis
        st.markdown("### Metros Quadrados por Responsável")
        col1, col2 = st.columns(2)
        
        # Gráfico 18: m2 pelo responsável elétrico
        with col1:
            if not df_projetos_filtrado.empty:
                m2_responsavel_eletrico = df_projetos_filtrado.groupby("ResponsávelElétrico")["m2"].sum().reset_index()
                fig_m2_eletrico = px.bar(
                    m2_responsavel_eletrico,
                    x="ResponsávelElétrico",
                    y="m2",
                    text="m2",
                    title="m² por Responsável Elétrico"
                )
                fig_m2_eletrico.update_traces(textposition="outside")
                fig_m2_eletrico.update_yaxes(showgrid=False, showticklabels=False)
                st.plotly_chart(fig_m2_eletrico, use_container_width=True)
        
        # Gráfico 19: m2 pelo responsável hidráulico
        with col2:
            if not df_projetos_filtrado.empty:
                m2_responsavel_hidraulico = df_projetos_filtrado.groupby("ResponsávelHidráulico")["m2"].sum().reset_index()
                fig_m2_hidraulico = px.bar(
                    m2_responsavel_hidraulico,
                    x="ResponsávelHidráulico",
                    y="m2",
                    text="m2",
                    title="m² por Responsável Hidráulico"
                )
                fig_m2_hidraulico.update_traces(textposition="outside")
                fig_m2_hidraulico.update_yaxes(showgrid=False, showticklabels=False)
                st.plotly_chart(fig_m2_hidraulico, use_container_width=True)
        
        # Seção 2: Mais m² por Responsáveis
        col1, col2 = st.columns(2)
        
        # Gráfico 20: m2 pelo responsável de modelagem
        with col1:
            if not df_projetos_filtrado.empty:
                m2_responsavel_modelagem = df_projetos_filtrado.groupby("ResponsávelModelagem")["m2"].sum().reset_index()
                fig_m2_modelagem = px.bar(
                    m2_responsavel_modelagem,
                    x="ResponsávelModelagem",
                    y="m2",
                    text="m2",
                    title="m² por Responsável de Modelagem"
                )
                fig_m2_modelagem.update_traces(textposition="outside")
                fig_m2_modelagem.update_yaxes(showgrid=False, showticklabels=False)
                st.plotly_chart(fig_m2_modelagem, use_container_width=True)
        
        # Gráfico 21: m2 pelo responsável de detalhamento
        with col2:
            if not df_projetos_filtrado.empty:
                m2_responsavel_detalhamento = df_projetos_filtrado.groupby("ResponsávelDetalhamento")["m2"].sum().reset_index()
                fig_m2_detalhamento = px.bar(
                    m2_responsavel_detalhamento,
                    x="ResponsávelDetalhamento",
                    y="m2",
                    text="m2",
                    title="m² por Responsável de Detalhamento"
                )
                fig_m2_detalhamento.update_traces(textposition="outside")
                fig_m2_detalhamento.update_yaxes(showgrid=False, showticklabels=False)
                st.plotly_chart(fig_m2_detalhamento, use_container_width=True)