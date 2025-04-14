"""
Utilitários para manipulação de dados.
"""
import pandas as pd
from datetime import datetime

def converter_para_string_segura(valor):
    """
    Converte um valor para uma representação de string segura para serialização.
    
    Args:
        valor: Valor a ser convertido
    
    Returns:
        str: Valor convertido para string
    """
    if pd.isna(valor) or valor is None:
        return ""
    elif hasattr(valor, 'strftime'):  # Para objetos datetime
        return valor.strftime("%d/%m/%Y")
    elif isinstance(valor, (int, float)):
        return str(valor)
    else:
        return str(valor)

def preparar_dados_para_sheets(dados, is_dataframe=False):
    """
    Prepara dados para serem salvos no Google Sheets, convertendo valores problemáticos.
    
    Args:
        dados: DataFrame ou dicionário com os dados a serem preparados
        is_dataframe: Se True, dados é um DataFrame, caso contrário é um dicionário
    
    Returns:
        DataFrame ou dicionário com os dados preparados
    """
    if is_dataframe:
        # Cria uma cópia para não modificar o original
        df = dados.copy()
        
        # Converte colunas de data
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime("%d/%m/%Y")
        
        # Converte valores numéricos para string
        for col in df.select_dtypes(include=['int64', 'float64']).columns:
            df[col] = df[col].astype(str)
        
        # Substitui valores NaN por string vazia
        df = df.fillna("")
        
        return df
    else:
        # Para dicionários
        resultado = {}
        for chave, valor in dados.items():
            resultado[chave] = converter_para_string_segura(valor)
        
        return resultado

def formatar_valor_moeda(valor):
    """
    Formata um valor numérico como moeda brasileira (R$).
    
    Args:
        valor: Valor a ser formatado
    
    Returns:
        str: Valor formatado como moeda brasileira
    """
    try:
        return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

def converter_string_para_data(data_str):
    """
    Converte uma string de data no formato DD/MM/YYYY para um objeto datetime.
    
    Args:
        data_str: String de data no formato DD/MM/YYYY
    
    Returns:
        datetime: Objeto datetime ou None se a conversão falhar
    """
    if not data_str or pd.isna(data_str):
        return None
    
    try:
        return datetime.strptime(data_str, "%d/%m/%Y")
    except:
        try:
            # Tenta outros formatos comuns
            formatos = ["%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%Y/%m/%d"]
            for formato in formatos:
                try:
                    return datetime.strptime(data_str, formato)
                except:
                    continue
        except:
            return None

def converter_string_para_numero(valor_str):
    """
    Converte uma string para um número (int ou float).
    
    Args:
        valor_str: String a ser convertida
    
    Returns:
        int ou float: Valor numérico ou 0 se a conversão falhar
    """
    if not valor_str or pd.isna(valor_str):
        return 0
    
    try:
        # Remove caracteres não numéricos (exceto ponto e vírgula)
        valor_str = str(valor_str).replace("R$", "").strip()
        valor_str = valor_str.replace(".", "").replace(",", ".")
        
        # Tenta converter para float
        valor = float(valor_str)
        
        # Se for um número inteiro, converte para int
        if valor.is_integer():
            return int(valor)
        else:
            return valor
    except:
        return 0
