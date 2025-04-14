import streamlit as st
import pandas as pd
import plotly.graph_objects as go

def create_card(title, value, color="#4caf50", icon=None):
    """
    Cria um card estilizado para exibir métricas.
    
    Args:
        title: Título do card
        value: Valor a ser exibido
        color: Cor do card (código hexadecimal)
        icon: Ícone do card (emoji)
    """
    icon_html = f"{icon} " if icon else ""
    st.markdown(f"""
    <div class="metric-card" style="border-left: 5px solid {color};">
        <h3>{icon_html}{title}</h3>
        <p style="color: {color}; font-size: 24px; font-weight: bold;">{value}</p>
    </div>
    """, unsafe_allow_html=True)

def create_metric_row(metrics):
    """
    Cria uma linha de métricas usando cards.
    
    Args:
        metrics: Lista de dicionários com as métricas (title, value, color, icon)
    """
    cols = st.columns(len(metrics))
    for i, metric in enumerate(metrics):
        with cols[i]:
            create_card(
                title=metric.get("title", ""),
                value=metric.get("value", ""),
                color=metric.get("color", "#4caf50"),
                icon=metric.get("icon", None)
            )

def create_donut_chart(data, names, values, title, colors=None):
    """
    Cria um gráfico de rosca (donut chart).
    
    Args:
        data: DataFrame com os dados
        names: Nome da coluna com as categorias
        values: Nome da coluna com os valores
        title: Título do gráfico
        colors: Lista de cores para o gráfico
    
    Returns:
        objeto plotly.graph_objects.Figure: Gráfico de rosca
    """
    fig = go.Figure(data=[go.Pie(
        labels=data[names],
        values=data[values],
        hole=0.4,
        marker_colors=colors
    )])
    
    fig.update_layout(
        title=title,
        showlegend=True
    )
    
    return fig

def create_bar_chart(x, y, name, title, color="#4caf50"):
    """
    Cria um gráfico de barras.
    
    Args:
        x: Valores do eixo X
        y: Valores do eixo Y
        name: Nome da série
        title: Título do gráfico
        color: Cor das barras
    
    Returns:
        objeto plotly.graph_objects.Figure: Gráfico de barras
    """
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=x,
        y=y,
        name=name,
        marker_color=color
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Categoria",
        yaxis_title="Valor (R$)"
    )
    
    return fig

def create_comparison_chart(x, y1, y2, name1, name2, title, color1="#4caf50", color2="#f44336"):
    """
    Cria um gráfico de barras para comparação.
    
    Args:
        x: Valores do eixo X
        y1: Valores da primeira série
        y2: Valores da segunda série
        name1: Nome da primeira série
        name2: Nome da segunda série
        title: Título do gráfico
        color1: Cor das barras da primeira série
        color2: Cor das barras da segunda série
    
    Returns:
        objeto plotly.graph_objects.Figure: Gráfico de barras para comparação
    """
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=x,
        y=y1,
        name=name1,
        marker_color=color1
    ))
    
    fig.add_trace(go.Bar(
        x=x,
        y=y2,
        name=name2,
        marker_color=color2
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Categoria",
        yaxis_title="Valor (R$)",
        barmode="group"
    )
    
    return fig

def create_editable_table(df, key, columns=None, hide_index=True, on_change=None):
    """
    Cria uma tabela editável.
    
    Args:
        df: DataFrame com os dados
        key: Chave única para o componente
        columns: Lista de colunas a serem exibidas (None para todas)
        hide_index: Se True, esconde o índice da tabela
        on_change: Função a ser chamada quando os dados são alterados
    
    Returns:
        pandas.DataFrame: DataFrame com os dados editados
    """
    if columns:
        df_display = df[columns].copy()
    else:
        df_display = df.copy()
    
    edited_df = st.data_editor(
        df_display,
        use_container_width=True,
        hide_index=hide_index,
        key=key
    )
    
    # Verifica se houve alterações
    if not edited_df.equals(df_display) and on_change:
        on_change(edited_df)
    
    return edited_df

def create_filter_section(filters, key_prefix="filter"):
    """
    Cria uma seção de filtros.
    
    Args:
        filters: Lista de dicionários com os filtros (type, label, options, default, key)
        key_prefix: Prefixo para as chaves dos componentes
    
    Returns:
        dict: Dicionário com os valores dos filtros
    """
    num_cols = min(3, len(filters))
    cols = st.columns(num_cols)
    
    results = {}
    
    for i, filter_config in enumerate(filters):
        col_idx = i % num_cols
        with cols[col_idx]:
            filter_type = filter_config.get("type", "selectbox")
            label = filter_config.get("label", "")
            options = filter_config.get("options", [])
            default = filter_config.get("default", None)
            key = f"{key_prefix}_{filter_config.get('key', i)}"
            
            if filter_type == "selectbox":
                value = st.selectbox(label, options, index=options.index(default) if default in options else 0, key=key)
            elif filter_type == "multiselect":
                value = st.multiselect(label, options, default=default if default else [], key=key)
            elif filter_type == "text_input":
                value = st.text_input(label, value=default if default else "", key=key)
            elif filter_type == "date_input":
                value = st.date_input(label, value=default if default else None, key=key)
            elif filter_type == "number_input":
                min_val = filter_config.get("min_value", 0)
                max_val = filter_config.get("max_value", None)
                step = filter_config.get("step", 1)
                value = st.number_input(label, min_value=min_val, max_value=max_val, value=default if default else min_val, step=step, key=key)
            else:
                value = None
            
            results[filter_config.get("key", i)] = value
    
    return results

def create_form_section(fields, key_prefix="form", submit_label="Enviar"):
    """
    Cria um formulário com campos configuráveis.
    
    Args:
        fields: Lista de dicionários com os campos (type, label, options, default, key, required)
        key_prefix: Prefixo para as chaves dos componentes
        submit_label: Texto do botão de envio
    
    Returns:
        tuple: (submitted, values) - se o formulário foi enviado e os valores dos campos
    """
    with st.form(f"{key_prefix}_form"):
        num_cols = min(2, len(fields))
        if num_cols > 1:
            cols = st.columns(num_cols)
        
        values = {}
        
        for i, field_config in enumerate(fields):
            field_type = field_config.get("type", "text_input")
            label = field_config.get("label", "")
            options = field_config.get("options", [])
            default = field_config.get("default", None)
            key = f"{key_prefix}_{field_config.get('key', i)}"
            required = field_config.get("required", False)
            
            # Adiciona um asterisco para campos obrigatórios
            display_label = f"{label} *" if required else label
            
            # Decide em qual coluna colocar o campo
            if num_cols > 1:
                col_idx = i % num_cols
                container = cols[col_idx]
            else:
                container = st
            
            with container:
                if field_type == "text_input":
                    value = st.text_input(display_label, value=default if default else "", key=key)
                elif field_type == "number_input":
                    min_val = field_config.get("min_value", 0)
                    max_val = field_config.get("max_value", None)
                    step = field_config.get("step", 1)
                    format_str = field_config.get("format", None)
                    value = st.number_input(
                        display_label, 
                        min_value=min_val, 
                        max_value=max_val, 
                        value=default if default is not None else min_val, 
                        step=step,
                        format=format_str,
                        key=key
                    )
                elif field_type == "selectbox":
                    value = st.selectbox(
                        display_label, 
                        options, 
                        index=options.index(default) if default in options else 0, 
                        key=key
                    )
                elif field_type == "multiselect":
                    value = st.multiselect(
                        display_label, 
                        options, 
                        default=default if default else [], 
                        key=key
                    )
                elif field_type == "date_input":
                    value = st.date_input(display_label, value=default if default else None, key=key)
                elif field_type == "time_input":
                    value = st.time_input(display_label, value=default if default else None, key=key)
                elif field_type == "text_area":
                    value = st.text_area(display_label, value=default if default else "", key=key)
                elif field_type == "checkbox":
                    value = st.checkbox(display_label, value=default if default is not None else False, key=key)
                elif field_type == "radio":
                    value = st.radio(display_label, options, index=options.index(default) if default in options else 0, key=key)
                else:
                    value = None
                
                values[field_config.get("key", i)] = value
        
        submitted = st.form_submit_button(submit_label)
        
        # Valida campos obrigatórios
        if submitted:
            for field_config in fields:
                key = field_config.get("key", "")
                required = field_config.get("required", False)
                if required and (values.get(key) is None or values.get(key) == ""):
                    st.error(f"O campo '{field_config.get('label', '')}' é obrigatório.")
                    submitted = False
                    break
        
        return submitted, values
