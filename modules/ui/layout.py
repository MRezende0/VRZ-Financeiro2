import streamlit as st

def create_sidebar():
    """
    Cria a barra lateral padrão com menu e logo.
    
    Returns:
        str: Opção selecionada no menu
    """
    st.sidebar.image("imagens/logo-cocal.png")
    st.sidebar.title("Menu")
    
    # Lista de opções do menu
    menu_options = ["Dashboard", "Registrar", "Projetos", "Funcionários", "Relatórios"]
    
    # Adiciona a opção de administração se o usuário tiver permissão
    if st.session_state.get("admin", False):
        menu_options.append("Admin")
    
    menu_option = st.sidebar.radio(
        "Selecione a funcionalidade:",
        menu_options
    )
    
    # Botão "Sair" na parte inferior da sidebar
    st.sidebar.markdown("---")  # Linha separadora
    if st.sidebar.button("Sair", key="sair"):
        st.session_state["logged_in"] = False
        st.success("Você saiu do sistema.")
        st.rerun()  # Atualiza a página para voltar à tela de login
    
    return menu_option

def create_page_header(title, icon=None, description=None):
    """
    Cria um cabeçalho padronizado para a página.
    
    Args:
        title: Título da página
        icon: Ícone da página (emoji)
        description: Descrição da página
    """
    icon_text = f"{icon} " if icon else ""
    st.title(f"{icon_text}{title}")
    
    if description:
        st.markdown(f"<p class='page-description'>{description}</p>", unsafe_allow_html=True)
    
    st.markdown("---")

def create_tabbed_interface(tabs_content):
    """
    Cria uma interface com abas.
    
    Args:
        tabs_content: Lista de dicionários com o conteúdo das abas (title, content_func)
    """
    tab_titles = [tab["title"] for tab in tabs_content]
    tabs = st.tabs(tab_titles)
    
    for i, tab in enumerate(tabs):
        with tab:
            tabs_content[i]["content_func"]()

def create_two_column_layout(left_content_func, right_content_func, left_width=1, right_width=1):
    """
    Cria um layout de duas colunas.
    
    Args:
        left_content_func: Função para renderizar o conteúdo da coluna esquerda
        right_content_func: Função para renderizar o conteúdo da coluna direita
        left_width: Largura relativa da coluna esquerda
        right_width: Largura relativa da coluna direita
    """
    col1, col2 = st.columns([left_width, right_width])
    
    with col1:
        left_content_func()
    
    with col2:
        right_content_func()

def create_expandable_section(title, content_func, expanded=False):
    """
    Cria uma seção expansível.
    
    Args:
        title: Título da seção
        content_func: Função para renderizar o conteúdo da seção
        expanded: Se True, a seção começa expandida
    """
    with st.expander(title, expanded=expanded):
        content_func()

def create_success_message(message):
    """
    Exibe uma mensagem de sucesso.
    
    Args:
        message: Mensagem a ser exibida
    """
    st.success(message)

def create_error_message(message):
    """
    Exibe uma mensagem de erro.
    
    Args:
        message: Mensagem a ser exibida
    """
    st.error(message)

def create_info_message(message):
    """
    Exibe uma mensagem informativa.
    
    Args:
        message: Mensagem a ser exibida
    """
    st.info(message)

def create_warning_message(message):
    """
    Exibe uma mensagem de aviso.
    
    Args:
        message: Mensagem a ser exibida
    """
    st.warning(message)

def create_loading_spinner(loading_text="Carregando..."):
    """
    Cria um spinner de carregamento.
    
    Args:
        loading_text: Texto a ser exibido durante o carregamento
    
    Returns:
        objeto st.spinner: Spinner de carregamento
    """
    return st.spinner(loading_text)

def create_progress_bar(progress_text="Progresso:"):
    """
    Cria uma barra de progresso.
    
    Args:
        progress_text: Texto a ser exibido acima da barra de progresso
    
    Returns:
        objeto st.progress: Barra de progresso
    """
    st.text(progress_text)
    return st.progress(0)

def update_progress_bar(progress_bar, value):
    """
    Atualiza o valor de uma barra de progresso.
    
    Args:
        progress_bar: Objeto de barra de progresso
        value: Valor de progresso (0-100)
    """
    progress_bar.progress(min(100, max(0, value)) / 100)

def create_download_button(data, file_name, button_text="Download", mime_type=None):
    """
    Cria um botão de download.
    
    Args:
        data: Dados a serem baixados
        file_name: Nome do arquivo
        button_text: Texto do botão
        mime_type: Tipo MIME do arquivo
    """
    st.download_button(
        label=button_text,
        data=data,
        file_name=file_name,
        mime=mime_type
    )
