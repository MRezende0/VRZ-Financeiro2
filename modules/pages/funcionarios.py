import streamlit as st
import pandas as pd
import plotly.express as px
from modules.data.sheets import carregar_dados_sob_demanda, salvar_dados_sheets, adicionar_linha_sheets
from utils.config import FUNCIONARIOS
from modules.ui.tables import create_editable_table_with_delete_button, format_date_columns

def registrar_funcionario():
    """
    Formulário para registrar um novo funcionário.
    """
    st.subheader("👤 Funcionário")
    
    # Carregar dados existentes
    try:
        df_funcionarios = carregar_dados_sob_demanda("Funcionarios")
        
        # Verificar se o DataFrame está vazio ou não existe
        if df_funcionarios.empty:
            df_funcionarios = pd.DataFrame(columns=["Nome", "CPF", "Cargo", "Contato", "Endereço"])
        
        # Converter todas as colunas para string para evitar problemas de tipo
        for col in df_funcionarios.columns:
            df_funcionarios[col] = df_funcionarios[col].astype(str)
        
        # Formulário para adicionar novo funcionário
        with st.form("novo_funcionario"):
            col1, col2 = st.columns(2)
            
            with col1:
                nome = st.text_input("Nome")
                cpf = st.text_input("CPF")
                cargo = st.selectbox("Cargo", ["Engenheiro", "Arquiteto", "Projetista", "Administrativo", "Outros"])
            
            with col2:
                contato = st.text_input("Contato")
                endereco = st.text_input("Endereço")
            
            submit_funcionario = st.form_submit_button("Registrar Funcionário")
            
            if submit_funcionario:
                # Validar dados
                if not nome:
                    st.error("O nome do funcionário é obrigatório.")
                else:
                    # Criar dicionário com os dados do novo funcionário
                    novo_funcionario = {
                        "Nome": nome,
                        "CPF": str(cpf),  # Garantir que CPF seja string
                        "Cargo": cargo,
                        "Contato": contato,
                        "Endereço": endereco
                    }
                    
                    # Adicionar o novo funcionário diretamente à planilha
                    if adicionar_linha_sheets(novo_funcionario, "Funcionarios"):
                        st.success("Funcionário registrado com sucesso!")
                        # Limpar o cache para forçar recarregar os dados
                        st.session_state.local_data["funcionarios"] = pd.DataFrame()
                        
                        # Recarregar os dados para exibir o novo funcionário na tabela
                        df_funcionarios = carregar_dados_sob_demanda("Funcionarios", force_reload=True)
                    else:
                        st.error("Erro ao registrar funcionário.")
        
        # Exibir lista de funcionários
        st.write("### Lista de Funcionários")
        
        # Usar a nova função de tabela editável com coluna de seleção
        create_editable_table_with_delete_button(df_funcionarios, "Funcionarios", key_prefix="funcionarios")
    
    except Exception as e:
        st.error(f"Erro ao carregar dados dos funcionários: {e}")

def calcular_produtividade(df_projetos, mes, ano):
    """
    Calcula a produtividade de cada funcionário com base nos projetos.
    
    Args:
        df_projetos: DataFrame com os dados dos projetos
        mes: Mês para filtrar os projetos
        ano: Ano para filtrar os projetos
    
    Returns:
        dict: Dicionário com a produtividade de cada funcionário
    """
    # Filtra os projetos pelo mês e ano
    df_projetos["DataInicio"] = pd.to_datetime(df_projetos["DataInicio"], dayfirst=True, errors='coerce')
    df_projetos_filtrados = df_projetos[
        (df_projetos["DataInicio"].dt.month == mes) & (df_projetos["DataInicio"].dt.year == ano)
    ]

    # Calcula a produtividade de cada funcionário
    produtividade = {funcionario: 0 for funcionario in FUNCIONARIOS}
    for _, row in df_projetos_filtrados.iterrows():
        if row["ResponsávelModelagem"] in FUNCIONARIOS:
            produtividade[row["ResponsávelModelagem"]] += row["m2"]
        if row["ResponsávelDetalhamento"] in FUNCIONARIOS:
            produtividade[row["ResponsávelDetalhamento"]] += row["m2"]

    return produtividade

def funcionarios():
    """
    Página principal para gerenciar funcionários e visualizar produtividade.
    """
    st.title("👥 Funcionários")

    # Carrega os projetos
    df_projetos = carregar_dados_sob_demanda("Projetos")

    # Selecionar mês e ano para análise
    mes = st.selectbox("Selecione o mês", range(1, 13), index=0)
    ano = st.selectbox("Selecione o ano", range(2020, 2031), index=3)

    # Calcula a produtividade
    produtividade = calcular_produtividade(df_projetos, mes, ano)

    # Cria um DataFrame para exibição
    df_produtividade = pd.DataFrame({
        "Funcionário": list(produtividade.keys()),
        "m² Projetado": list(produtividade.values()),
        "Valor a Receber (R$)": [produtividade[func] * FUNCIONARIOS[func] for func in produtividade]
    })

    # Exibe o DataFrame
    st.write("### Produtividade dos Funcionários")
    st.dataframe(df_produtividade)

    # Gráfico de m² projetado por funcionário
    st.write("### m² Projetado por Funcionário")
    fig_m2 = px.bar(
        df_produtividade,
        x="Funcionário",
        y="m² Projetado",
        title="m² Projetado por Funcionário",
        labels={"Funcionário": "Funcionário", "m² Projetado": "m² Projetado"},
    )
    st.plotly_chart(fig_m2)

    # Gráfico de valor a receber por funcionário
    st.write("### Valor a Receber por Funcionário")
    fig_valor = px.bar(
        df_produtividade,
        x="Funcionário",
        y="Valor a Receber (R$)",
        title="Valor a Receber por Funcionário",
        labels={"Funcionário": "Funcionário", "Valor a Receber (R$)": "Valor a Receber (R$)"},
    )
    st.plotly_chart(fig_valor)
