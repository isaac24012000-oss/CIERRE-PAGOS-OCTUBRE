import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import io

# Configuración de la página
st.set_page_config(page_title="Dashboard Finanzas - Octubre 2025", layout="wide", initial_sidebar_state="expanded")

# Título principal
st.title("💰 Dashboard de Finanzas - Octubre 2025")

# Cargar datos
@st.cache_data
def cargar_datos():
    excel_file = "CIERRE GASTOS ADMINISTRATIVOS OCTUBRE 2025.xlsx"
    
    # Leer la hoja
    df = pd.read_excel(excel_file, sheet_name="Hoja1")
    
    # Excluir filas que no tengan ASESOR (son filas de totales)
    df = df.dropna(subset=['ASESOR'])
    
    # Convertir columnas de fechas a strings para evitar problemas de serialización
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.strftime('%Y-%m-%d')
    
    return df

try:
    df = cargar_datos()
    
    # ============ ANÁLISIS PRINCIPAL: VALOR VENTA, IGV, MONTO ============
    st.markdown("---")
    st.subheader("💵 Indicadores Financieros Principales")
    st.markdown("---")
    
    # Calcular KPIs
    total_valor_venta = pd.to_numeric(df['VALOR VENTA'], errors='coerce').sum()
    total_igv = pd.to_numeric(df['IGV'], errors='coerce').sum()
    total_monto = pd.to_numeric(df['MONTO'], errors='coerce').sum()
    
    # Gráficos principales en 3 columnas grandes
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Monto por Cartera - PRINCIPAL
        df_cartera_monto = df.groupby('CARTERA')['MONTO'].sum().reset_index().sort_values('MONTO', ascending=True)
        
        fig = px.bar(df_cartera_monto, x='MONTO', y='CARTERA',
                     title=f"<b>MONTO TOTAL</b><br>S/ {total_monto:,.2f}",
                     labels={'MONTO': 'Monto (S/)', 'CARTERA': 'Cartera'},
                     color='MONTO', color_continuous_scale="Greens",
                     orientation='h')
        fig.update_layout(height=550, showlegend=False, template='plotly_white')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Composición del MONTO: Valor Venta vs IGV
        descomposicion = pd.DataFrame({
            'Componente': ['Valor Venta', 'IGV'],
            'Monto': [total_valor_venta, total_igv]
        })
        
        fig = px.pie(descomposicion, values='Monto', names='Componente',
                     title=f"<b>COMPOSICIÓN DEL MONTO</b><br>Valor Venta: S/ {total_valor_venta:,.2f}<br>IGV: S/ {total_igv:,.2f}",
                     color_discrete_map={'Valor Venta': '#1f77b4', 'IGV': '#ff7f0e'},
                     hole=0.3)
        fig.update_layout(height=550, showlegend=True, template='plotly_white')
        st.plotly_chart(fig, use_container_width=True)
    
    with col3:
        # Descomposición por Cartera: Valor Venta e IGV apilados
        df_cartera_comp = df.groupby('CARTERA').agg({
            'VALOR VENTA': 'sum',
            'IGV': 'sum'
        }).reset_index().sort_values('VALOR VENTA', ascending=True)
        
        fig = px.bar(df_cartera_comp, x=['VALOR VENTA', 'IGV'], y='CARTERA',
                     title="<b>DESCOMPOSICIÓN POR CARTERA</b><br>Valor Venta e IGV",
                     labels={'value': 'Monto (S/)', 'CARTERA': 'Cartera'},
                     barmode='stack',
                     color_discrete_map={
                        'VALOR VENTA': '#1f77b4',
                        'IGV': '#ff7f0e'
                    },
                     orientation='h')
        fig.update_layout(height=550, showlegend=True, template='plotly_white')
        st.plotly_chart(fig, use_container_width=True)
    
    # ============ ANÁLISIS DETALLADO POR ASESOR ============
    st.markdown("---")
    st.subheader("👥 Análisis Detallado por Asesor")
    st.markdown("---")
    
    # Top Asesores por Monto
    df_asesor = df.groupby('ASESOR').agg({
        'VALOR VENTA': 'sum',
        'IGV': 'sum',
        'MONTO': 'sum'
    }).reset_index().sort_values('MONTO', ascending=False).head(15)
    
    fig = px.bar(df_asesor, y='ASESOR', x='MONTO',
                title="<b>Top 15 Asesores - Monto</b>",
                labels={'MONTO': 'Monto (S/)', 'ASESOR': 'Asesor'},
                color='MONTO', color_continuous_scale="Blues",
                orientation='h')
    fig.update_layout(height=550, showlegend=False, template='plotly_white', 
                     yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig, use_container_width=True)
    
    # ============ LÍNEA DE TIEMPO FINANCIERA ============
    st.markdown("---")
    st.subheader("📅 Evolución Financiera por Fecha")
    st.markdown("---")
    
    # Preparar datos de línea de tiempo
    df_timeline = df[['FECHA_DE_PAGO', 'VALOR VENTA', 'IGV', 'MONTO']].copy()
    df_timeline['FECHA_DE_PAGO'] = pd.to_datetime(df_timeline['FECHA_DE_PAGO'], errors='coerce')
    
    # Agrupar por fecha
    df_timeline_agg = df_timeline.dropna(subset=['FECHA_DE_PAGO']).groupby('FECHA_DE_PAGO').agg({
        'VALOR VENTA': 'sum',
        'IGV': 'sum',
        'MONTO': 'sum'
    }).reset_index().sort_values('FECHA_DE_PAGO')
    
    if len(df_timeline_agg) > 0:
        col_timeline1, col_timeline2 = st.columns(2)
        
        with col_timeline1:
            # Crear gráfico de línea mejorado - Solo Monto Total
            fig_timeline = go.Figure()
            
            fig_timeline.add_trace(go.Scatter(
                x=df_timeline_agg['FECHA_DE_PAGO'], 
                y=df_timeline_agg['MONTO'],
                mode='lines+markers',
                name='Monto Diario',
                line=dict(color='#2ca02c', width=3),
                marker=dict(size=8),
                fill='tozeroy',
                fillcolor='rgba(44, 160, 44, 0.3)'
            ))
            
            fig_timeline.update_layout(
                title='<b>Monto Diario - Noviembre 2025</b>',
                xaxis_title='Fecha',
                yaxis_title='Monto (S/)',
                hovermode='x unified',
                height=500,
                template='plotly_white',
                showlegend=False
            )
            st.plotly_chart(fig_timeline, use_container_width=True)
        
        with col_timeline2:
            # Crear gráfico acumulado
            df_timeline_agg['MONTO_ACUMULADO'] = df_timeline_agg['MONTO'].cumsum()
            
            fig_acumulado = go.Figure()
            
            fig_acumulado.add_trace(go.Scatter(
                x=df_timeline_agg['FECHA_DE_PAGO'], 
                y=df_timeline_agg['MONTO_ACUMULADO'],
                mode='lines+markers',
                name='Acumulado',
                line=dict(color='#d62728', width=3),
                marker=dict(size=8),
                fill='tozeroy',
                fillcolor='rgba(214, 39, 40, 0.3)'
            ))
            
            fig_acumulado.update_layout(
                title='<b>Monto Acumulado - Progresión en Noviembre</b>',
                xaxis_title='Fecha',
                yaxis_title='Monto Acumulado (S/)',
                hovermode='x unified',
                height=500,
                template='plotly_white',
                showlegend=False
            )
            st.plotly_chart(fig_acumulado, use_container_width=True)
    
    # ============ ANÁLISIS POR CAMPAÑA ============
    st.markdown("---")
    st.subheader("🎯 Análisis por Campaña")
    st.markdown("---")
    
    df_campana = df.groupby('CAMPANA').agg({
        'VALOR VENTA': 'sum',
        'IGV': 'sum',
        'MONTO': 'sum'
    }).reset_index().sort_values('MONTO', ascending=False)
    
    fig = px.bar(df_campana, x='CAMPANA', y=['VALOR VENTA', 'IGV', 'MONTO'],
                title="<b>Análisis Financiero por Campaña</b>",
                labels={'value': 'Monto (S/)', 'CAMPANA': 'Campaña'},
                barmode='group',
                color_discrete_map={
                    'VALOR VENTA': '#1f77b4',
                    'IGV': '#ff7f0e',
                    'MONTO': '#2ca02c'
                })
    fig.update_layout(xaxis_tickangle=-45, height=500, template='plotly_white')
    st.plotly_chart(fig, use_container_width=True)
    
    # ============ ANÁLISIS POR ESTADO DE PLANILLA ============
    st.markdown("---")
    st.subheader("📋 Distribución por Estado de Planilla")
    st.markdown("---")
    
    # Monto por Estado de Planilla
    df_estado = df.groupby('ESTADO_PLANILLA').agg({
        'MONTO': 'sum'
    }).reset_index().sort_values('MONTO', ascending=False)
    
    fig = px.pie(df_estado, values='MONTO', names='ESTADO_PLANILLA',
                title='<b>Distribución de Monto por Estado de Planilla</b>',
                color_discrete_sequence=px.colors.qualitative.Set2,
                hole=0.3)
    fig.update_layout(height=500, template='plotly_white')
    st.plotly_chart(fig, use_container_width=True)
    
    # ============ TABLA DE DATOS DETALLADOS ============
    st.markdown("---")
    st.subheader("📊 Datos Detallados")
    st.markdown("---")
    
    # Crear una copia para mostrar - Seleccionar solo columnas importantes
    df_display = df[['ASESOR', 'CAMPANA', 'CARTERA', 'RAZON_SOCIAL', 'FECHA_DE_PAGO', 
                     'VALOR VENTA', 'IGV', 'MONTO', 'ESTADO_PLANILLA', 'NUMERO_FACTURA']].copy()
    
    # Crear versión sin formato para exportar a Excel
    df_export = df_display.copy()
    for col in ['VALOR VENTA', 'IGV', 'MONTO']:
        if col in df_export.columns:
            df_export[col] = pd.to_numeric(df_export[col], errors='coerce')
    
    # Formatear columnas numéricas para mostrar
    for col in ['VALOR VENTA', 'IGV', 'MONTO']:
        if col in df_display.columns:
            df_display[col] = pd.to_numeric(df_display[col], errors='coerce').apply(lambda x: f"S/ {x:,.2f}" if pd.notna(x) else "")
    
    # Botón para descargar Excel
    col_export1, col_export2 = st.columns([3, 1])
    
    with col_export2:
        # Crear archivo Excel en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_export.to_excel(writer, sheet_name='Datos', index=False)
        output.seek(0)
        
        st.download_button(
            label="📥 Descargar Excel",
            data=output.getvalue(),
            file_name="Datos_Finanzas_Noviembre_2025.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_excel"
        )
    
    st.dataframe(df_display, use_container_width=True, height=400)

except Exception as e:
    st.error(f"Error al cargar los datos: {e}")
    st.info("Asegúrate de que el archivo 'CIERRE GASTOS ADMINISTRATIVOS NOVIEMBRE 2025.xlsx' esté en el mismo directorio que este script.")
