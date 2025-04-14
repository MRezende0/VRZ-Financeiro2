"""
Utilitários para backup de dados.
"""
import os
import json
import pandas as pd
from datetime import datetime
from modules.data.sheets import carregar_dados_sheets
from utils.config import COLUNAS_ESPERADAS

def criar_backup_local(diretorio_backup=None):
    """
    Cria um backup local de todas as planilhas do Google Sheets.
    
    Args:
        diretorio_backup: Diretório onde os backups serão salvos. Se None, usa o diretório 'backups' na pasta do projeto.
    
    Returns:
        str: Caminho do arquivo de backup criado ou None se ocorrer um erro
    """
    try:
        # Define o diretório de backup
        if diretorio_backup is None:
            diretorio_backup = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups")
        
        # Cria o diretório se não existir
        os.makedirs(diretorio_backup, exist_ok=True)
        
        # Nome do arquivo de backup com timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        arquivo_backup = os.path.join(diretorio_backup, f"backup_{timestamp}.json")
        
        # Dicionário para armazenar os dados de backup
        dados_backup = {}
        
        # Para cada planilha, carrega os dados e adiciona ao backup
        for sheet_name in COLUNAS_ESPERADAS.keys():
            try:
                df = carregar_dados_sheets(sheet_name)
                # Converte o DataFrame para um formato serializável
                dados_backup[sheet_name] = df.to_dict(orient="records")
            except Exception as e:
                print(f"Erro ao fazer backup da planilha '{sheet_name}': {e}")
        
        # Salva os dados em um arquivo JSON
        with open(arquivo_backup, "w", encoding="utf-8") as f:
            json.dump(dados_backup, f, ensure_ascii=False, indent=2)
        
        return arquivo_backup
    
    except Exception as e:
        print(f"Erro ao criar backup: {e}")
        return None

def restaurar_backup(arquivo_backup):
    """
    Restaura os dados de um arquivo de backup.
    
    Args:
        arquivo_backup: Caminho do arquivo de backup a ser restaurado
    
    Returns:
        dict: Dicionário com os DataFrames restaurados ou None se ocorrer um erro
    """
    try:
        # Verifica se o arquivo existe
        if not os.path.exists(arquivo_backup):
            print(f"Arquivo de backup '{arquivo_backup}' não encontrado.")
            return None
        
        # Carrega os dados do arquivo JSON
        with open(arquivo_backup, "r", encoding="utf-8") as f:
            dados_backup = json.load(f)
        
        # Dicionário para armazenar os DataFrames restaurados
        dfs_restaurados = {}
        
        # Para cada planilha, converte os dados para DataFrame
        for sheet_name, dados in dados_backup.items():
            try:
                dfs_restaurados[sheet_name] = pd.DataFrame(dados)
            except Exception as e:
                print(f"Erro ao restaurar planilha '{sheet_name}': {e}")
        
        return dfs_restaurados
    
    except Exception as e:
        print(f"Erro ao restaurar backup: {e}")
        return None

def listar_backups(diretorio_backup=None):
    """
    Lista todos os arquivos de backup disponíveis.
    
    Args:
        diretorio_backup: Diretório onde os backups estão salvos. Se None, usa o diretório 'backups' na pasta do projeto.
    
    Returns:
        list: Lista de caminhos dos arquivos de backup
    """
    try:
        # Define o diretório de backup
        if diretorio_backup is None:
            diretorio_backup = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "backups")
        
        # Verifica se o diretório existe
        if not os.path.exists(diretorio_backup):
            return []
        
        # Lista todos os arquivos de backup
        arquivos_backup = []
        for arquivo in os.listdir(diretorio_backup):
            if arquivo.startswith("backup_") and arquivo.endswith(".json"):
                arquivos_backup.append(os.path.join(diretorio_backup, arquivo))
        
        # Ordena os arquivos por data (mais recente primeiro)
        arquivos_backup.sort(reverse=True)
        
        return arquivos_backup
    
    except Exception as e:
        print(f"Erro ao listar backups: {e}")
        return []
