import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import base64
import io
from modules.data.sheets import carregar_dados_sob_demanda

def gerar_relatorio_excel(df_receitas, df_despesas, periodo=None):
    """
    Gera um relatório em Excel com os dados financeiros.
    
    Args:
        df_receitas: DataFrame com as receitas
        df_despesas: DataFrame com as despesas
        periodo: Período para filtrar os dados (mês/ano)
    
    Returns:
        bytes: Arquivo Excel em formato de bytes
    """
    # Criar um buffer para o arquivo Excel
    output = io.BytesIO()
    
    # Criar um escritor Excel
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    
    # Filtrar dados por período se especificado
    if periodo:
        mes, ano = periodo
        try:
            df_receitas["DataRecebimento"] = pd.to_datetime(df_receitas["DataRecebimento"], dayfirst=True, errors='coerce')
            df_receitas = df_receitas[
                (df_receitas["DataRecebimento"].dt.month == mes) & 
                (df_receitas["DataRecebimento"].dt.year == ano)
            ]
            
            df_despesas["DataPagamento"] = pd.to_datetime(df_despesas["DataPagamento"], dayfirst=True, errors='coerce')
            df_despesas = df_despesas[
                (df_despesas["DataPagamento"].dt.month == mes) & 
                (df_despesas["DataPagamento"].dt.year == ano)
            ]
        except:
            pass
    
    # Escrever DataFrames em planilhas separadas
    df_receitas.to_excel(writer, sheet_name='Receitas', index=False)
    df_despesas.to_excel(writer, sheet_name='Despesas', index=False)
    
    # Criar uma planilha de resumo
    resumo = pd.DataFrame({
        'Métrica': ['Receita Total', 'Despesa Total', 'Saldo'],
        'Valor': [
            df_receitas['ValorTotal'].astype(float).sum(),
            df_despesas['ValorTotal'].astype(float).sum(),
            df_receitas['ValorTotal'].astype(float).sum() - df_despesas['ValorTotal'].astype(float).sum()
        ]
    })
    resumo.to_excel(writer, sheet_name='Resumo', index=False)
    
    # Salvar o arquivo Excel
    writer.close()
    
    # Retornar o buffer como bytes
    output.seek(0)
    return output.getvalue()

def relatorios():
    """
    Página principal para geração de relatórios.
    """
    st.title("📊 Relatórios")
    
    # Carregar dados
    df_receitas = carregar_dados_sob_demanda("Receitas")
    df_despesas = carregar_dados_sob_demanda("Despesas")
    df_projetos = carregar_dados_sob_demanda("Projetos")
    
    # Verificar se os dados foram carregados corretamente
    if df_receitas.empty or df_despesas.empty:
        st.warning("Não foi possível carregar os dados financeiros. Verifique a conexão com o Google Sheets.")
        return
    
    # Criar abas para os diferentes tipos de relatórios
    tabs = st.tabs(["Relatório Financeiro", "Relatório de Projetos", "Relatório Personalizado"])
    
    # Conteúdo da aba Relatório Financeiro
    with tabs[0]:
        st.subheader("📈 Relatório Financeiro")
        
        # Filtros de período
        col1, col2 = st.columns(2)
        with col1:
            mes = st.selectbox("Mês", range(1, 13), index=datetime.now().month - 1, key="mes_financeiro")
        with col2:
            ano = st.selectbox("Ano", range(2020, 2031), index=datetime.now().year - 2020, key="ano_financeiro")
        
        # Converter colunas de data
        try:
            df_receitas["DataRecebimento"] = pd.to_datetime(df_receitas["DataRecebimento"], dayfirst=True, errors='coerce')
            df_despesas["DataPagamento"] = pd.to_datetime(df_despesas["DataPagamento"], dayfirst=True, errors='coerce')
        except:
            pass
        
        # Filtrar dados por período
        try:
            df_receitas_filtrado = df_receitas[
                (df_receitas["DataRecebimento"].dt.month == mes) & 
                (df_receitas["DataRecebimento"].dt.year == ano)
            ]
            
            df_despesas_filtrado = df_despesas[
                (df_despesas["DataPagamento"].dt.month == mes) & 
                (df_despesas["DataPagamento"].dt.year == ano)
            ]
        except:
            df_receitas_filtrado = df_receitas
            df_despesas_filtrado = df_despesas
        
        # Calcular métricas financeiras
        receita_total = df_receitas_filtrado["ValorTotal"].astype(float).sum()
        despesa_total = df_despesas_filtrado["ValorTotal"].astype(float).sum()
        saldo = receita_total - despesa_total
        
        # Exibir métricas financeiras
        col1, col2, col3 = st.columns(3)
        col1.metric("Receita Total", f"R$ {receita_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col2.metric("Despesa Total", f"R$ {despesa_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col3.metric("Saldo", f"R$ {saldo:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        # Gráfico de receitas vs despesas
        st.write("### Receitas vs Despesas")
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            x=["Receitas", "Despesas", "Saldo"],
            y=[receita_total, despesa_total, saldo],
            marker_color=["#4caf50", "#f44336", "#2196f3"]
        ))
        
        fig.update_layout(
            title=f"Resumo Financeiro - {mes}/{ano}",
            xaxis_title="Categoria",
            yaxis_title="Valor (R$)"
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabelas de receitas e despesas
        st.write("### Receitas")
        st.dataframe(df_receitas_filtrado, use_container_width=True)
        
        st.write("### Despesas")
        st.dataframe(df_despesas_filtrado, use_container_width=True)
        
        # Botão para download do relatório em Excel
        if st.button("Baixar Relatório Financeiro (Excel)"):
            excel_data = gerar_relatorio_excel(df_receitas, df_despesas, periodo=(mes, ano))
            b64 = base64.b64encode(excel_data).decode()
            href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="relatorio_financeiro_{mes}_{ano}.xlsx">Clique aqui para baixar o relatório</a>'
            st.markdown(href, unsafe_allow_html=True)
    
    # Conteúdo da aba Relatório de Projetos
    with tabs[1]:
        st.subheader("🏗️ Relatório de Projetos")
        
        # Filtros
        status = st.multiselect(
            "Status do Projeto",
            ["Concluído", "Em Andamento", "A fazer", "Impedido"],
            default=["Em Andamento"]
        )
        
        # Filtrar projetos por status
        if status:
            df_projetos_filtrado = df_projetos[df_projetos["Status"].isin(status)]
        else:
            df_projetos_filtrado = df_projetos
        
        # Exibir métricas de projetos
        num_projetos = len(df_projetos_filtrado)
        
        try:
            valor_total = df_projetos_filtrado["ValorTotal"].astype(float).sum()
            m2_total = df_projetos_filtrado["m2"].astype(float).sum()
        except:
            valor_total = 0
            m2_total = 0
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Número de Projetos", num_projetos)
        col2.metric("Valor Total", f"R$ {valor_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col3.metric("m² Total", f"{m2_total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        
        # Gráfico de projetos por status
        st.write("### Projetos por Status")
        status_counts = df_projetos["Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Quantidade"]
        
        fig = px.pie(
            status_counts,
            values="Quantidade",
            names="Status",
            title="Distribuição de Projetos por Status",
            hole=0.4,
            color_discrete_map={
                "Concluído": "#4caf50",
                "Em Andamento": "#2196f3",
                "A fazer": "#ff9800",
                "Impedido": "#f44336"
            }
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Tabela de projetos
        st.write("### Lista de Projetos")
        st.dataframe(df_projetos_filtrado, use_container_width=True)
        
        # Botão para download do relatório em Excel
        if st.button("Baixar Relatório de Projetos (Excel)"):
            output = io.BytesIO()
            writer = pd.ExcelWriter(output, engine='xlsxwriter')
            df_projetos_filtrado.to_excel(writer, sheet_name='Projetos', index=False)
            writer.close()
            output.seek(0)
            
            b64 = base64.b64encode(output.getvalue()).decode()
            href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="relatorio_projetos.xlsx">Clique aqui para baixar o relatório</a>'
            st.markdown(href, unsafe_allow_html=True)
    
    # Conteúdo da aba Relatório Personalizado
    with tabs[2]:
        st.subheader("🔍 Relatório Personalizado")
        
        # Selecionar tipo de dados
        tipo_dados = st.selectbox(
            "Selecione o tipo de dados",
            ["Receitas", "Despesas", "Projetos"]
        )
        
        # Carregar dados selecionados
        if tipo_dados == "Receitas":
            df = df_receitas
            data_col = "DataRecebimento"
        elif tipo_dados == "Despesas":
            df = df_despesas
            data_col = "DataPagamento"
        else:
            df = df_projetos
            data_col = "DataInicio"
        
        # Converter coluna de data
        try:
            df[data_col] = pd.to_datetime(df[data_col], dayfirst=True, errors='coerce')
        except:
            pass
        
        # Filtros de período
        col1, col2 = st.columns(2)
        with col1:
            data_inicio = st.date_input("Data Inicial", datetime.now().replace(day=1))
        with col2:
            data_fim = st.date_input("Data Final", datetime.now().replace(day=28))
        
        # Filtrar dados por período
        try:
            df_filtrado = df[(df[data_col].dt.date >= data_inicio) & (df[data_col].dt.date <= data_fim)]
        except:
            df_filtrado = df
        
        # Selecionar colunas para exibir
        if not df.empty:
            colunas = st.multiselect(
                "Selecione as colunas para exibir",
                df.columns.tolist(),
                default=df.columns.tolist()[:5]
            )
            
            if colunas:
                # Exibir dados filtrados
                st.write(f"### Dados de {tipo_dados}")
                st.dataframe(df_filtrado[colunas], use_container_width=True)
                
                # Botão para download do relatório em Excel
                if st.button("Baixar Relatório Personalizado (Excel)"):
                    output = io.BytesIO()
                    writer = pd.ExcelWriter(output, engine='xlsxwriter')
                    df_filtrado[colunas].to_excel(writer, sheet_name=tipo_dados, index=False)
                    writer.close()
                    output.seek(0)
                    
                    b64 = base64.b64encode(output.getvalue()).decode()
                    href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="relatorio_personalizado.xlsx">Clique aqui para baixar o relatório</a>'
                    st.markdown(href, unsafe_allow_html=True)
            else:
                st.warning("Selecione pelo menos uma coluna para exibir.")
        else:
            st.warning(f"Não há dados de {tipo_dados} disponíveis.")
