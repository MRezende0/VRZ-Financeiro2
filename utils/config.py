"""
Arquivo de configuração com constantes e credenciais para a aplicação.
"""

# Credenciais de usuário
USER_CREDENTIALS = {
    "contato@vrzengenharia.com.br": "123",
    "20242025": "123",
}

# Configurações do Google Sheets
SHEET_ID = "1E72Z_HBydw_IxM143IAFlrfhqrxhnOfBMxZGjfjJj5o"
SHEET_GIDS = {
    "Receitas": "0",
    "Despesas": "2095402559",
    "Projetos": "1967040877",
    "Categorias_Receitas": "689806911",
    "Categorias_Despesas": "1610275753",
    "Fornecedor_Despesas": "1183581777",
    "Clientes": "1538370660",
    "Funcionarios": "1993815508"
}

# Estrutura de colunas esperadas para cada planilha
COLUNAS_ESPERADAS = {
    "Receitas": ["DataRecebimento", "Descrição", "Projeto", "Categoria", "ValorTotal", "FormaPagamento", "NF"],
    "Despesas": ["DataPagamento", "Descrição", "Categoria", "ValorTotal", "Parcelas", "FormaPagamento", "Responsável", "Fornecedor", "Projeto", "NF"],
    "Projetos": ["Projeto", "Cliente", "Localizacao", "Placa", "Post", "DataInicio", "DataFinal", "Contrato", "Status", "Briefing", "Arquiteto", "Tipo", "Pacote", "m2", "Parcelas", "ValorTotal", "ResponsávelElétrico", "ResponsávelHidráulico", "ResponsávelModelagem", "ResponsávelDetalhamento"],
    "Clientes": ["Nome", "CPF", "Endereço", "Contato", "TipoNF"],
    "Categorias_Receitas": ["Categoria"],
    "Categorias_Despesas": ["Categoria"],
    "Fornecedor_Despesas": ["Fornecedor"]
}

# Configurações para funcionários
FUNCIONARIOS = {
    "Bruno": 0.50,  # R$ por m²
    "Victor": 0.50,  # R$ por m²
    "Matheus": 0.50  # R$ por m²
}
