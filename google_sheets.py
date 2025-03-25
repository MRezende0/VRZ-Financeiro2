import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import streamlit as st

class GoogleSheetsManager:
    def __init__(self):
        # Escopo de uso da API
        self.scope = [
            'https://spreadsheets.google.com/feeds',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Inicializa a conexão apenas quando necessário
        self._client = None
        
    @property
    def client(self):
        # Lazy loading do cliente para minimizar requisições
        if self._client is None:
            try:
                # Carrega as credenciais do arquivo
                credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', self.scope)
                
                # Autoriza o cliente
                self._client = gspread.authorize(credentials)
                
            except Exception as e:
                st.error(f"Erro ao conectar com o Google Sheets: {e}")
                return None
                
        return self._client
    
    def get_worksheet(self, spreadsheet_key, worksheet_index=0):
        """
        Obtém uma planilha específica pelo ID da planilha e índice da aba
        
        Args:
            spreadsheet_key (str): ID da planilha do Google Sheets
            worksheet_index (int): Índice da aba (0 para a primeira aba)
            
        Returns:
            worksheet: Objeto da planilha ou None em caso de erro
        """
        try:
            # Verifica se o cliente está disponível
            if not self.client:
                return None
                
            # Abre a planilha pelo ID
            spreadsheet = self.client.open_by_key(spreadsheet_key)
            
            # Obtém a aba pelo índice
            worksheet = spreadsheet.get_worksheet(worksheet_index)
            
            return worksheet
            
        except Exception as e:
            st.error(f"Erro ao acessar a planilha: {e}")
            return None
    
    def get_worksheet_by_name(self, spreadsheet_key, worksheet_name):
        """
        Obtém uma planilha específica pelo ID da planilha e nome da aba
        
        Args:
            spreadsheet_key (str): ID da planilha do Google Sheets
            worksheet_name (str): Nome da aba
            
        Returns:
            worksheet: Objeto da planilha ou None em caso de erro
        """
        try:
            # Verifica se o cliente está disponível
            if not self.client:
                return None
                
            # Abre a planilha pelo ID
            spreadsheet = self.client.open_by_key(spreadsheet_key)
            
            # Obtém a aba pelo nome
            worksheet = spreadsheet.worksheet(worksheet_name)
            
            return worksheet
            
        except Exception as e:
            st.error(f"Erro ao acessar a planilha: {e}")
            return None
    
    def get_all_data(self, worksheet):
        """
        Obtém todos os dados de uma planilha como DataFrame
        
        Args:
            worksheet: Objeto da planilha
            
        Returns:
            DataFrame: Dados da planilha ou None em caso de erro
        """
        try:
            # Obtém todos os registros como dicionários
            data = worksheet.get_all_records()
            
            # Converte para DataFrame
            df = pd.DataFrame(data)
            
            return df
            
        except Exception as e:
            st.error(f"Erro ao obter dados da planilha: {e}")
            return None
    
    def update_worksheet(self, worksheet, df):
        """
        Atualiza uma planilha com os dados de um DataFrame
        
        Args:
            worksheet: Objeto da planilha
            df (DataFrame): DataFrame com os dados a serem atualizados
            
        Returns:
            bool: True se a atualização foi bem-sucedida, False caso contrário
        """
        try:
            # Limpa a planilha atual
            worksheet.clear()
            
            # Adiciona os cabeçalhos
            headers = df.columns.tolist()
            worksheet.append_row(headers)
            
            # Adiciona os dados
            for _, row in df.iterrows():
                worksheet.append_row(row.tolist())
                
            return True
            
        except Exception as e:
            st.error(f"Erro ao atualizar a planilha: {e}")
            return False
    
    def append_row(self, worksheet, row_data):
        """
        Adiciona uma nova linha à planilha
        
        Args:
            worksheet: Objeto da planilha
            row_data (list): Lista com os dados da nova linha
            
        Returns:
            bool: True se a adição foi bem-sucedida, False caso contrário
        """
        try:
            worksheet.append_row(row_data)
            return True
            
        except Exception as e:
            st.error(f"Erro ao adicionar linha à planilha: {e}")
            return False
