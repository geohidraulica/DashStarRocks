# utils/excel_export.py
import io
import pandas as pd
import traceback
from datetime import datetime
from dash import dcc

def export_dataframe_to_excel_optimized(df, filename_prefix="export", sheet_name="Data", 
                                        max_rows=1000000):
    """
    Función genérica para exportar un DataFrame a Excel con todas las optimizaciones
    
    Args:
        df: DataFrame a exportar
        filename_prefix: Prefijo para el nombre del archivo
        sheet_name: Nombre de la hoja de Excel
        max_rows: Número máximo de filas a exportar
    
    Returns:
        Tuple (excel_data, filename) para usar con dcc.send_bytes
    """
    try:
        # Verificar si hay datos
        if df.empty:
            print("No hay datos para exportar")
            return None, None
        
        # Limitar tamaño si es necesario
        if len(df) > max_rows:
            print(f"ADVERTENCIA: Demasiados registros ({len(df)}). Limitando a {max_rows}")
            df = df.head(max_rows)
        
        # Crear el archivo Excel en memoria
        output = io.BytesIO()
        
        print("Generando archivo Excel...")
        
        # Usar xlsxwriter con todas las optimizaciones
        try:
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Escribir dataframe
                df.to_excel(writer, sheet_name=sheet_name, index=False)
                
                # Obtener el worksheet
                worksheet = writer.sheets[sheet_name]
                
                # Ajuste inteligente de columnas
                if len(df) < 500000:  # Solo ajustar si no es muy grande
                    # Limitar número de columnas a ajustar
                    cols_to_adjust = min(20, len(df.columns))
                    
                    # Usar muestra para calcular ancho (más rápido)
                    sample_size = min(500, len(df))
                    df_sample = df.head(sample_size) if sample_size > 0 else df
                    
                    for i, col in enumerate(df.columns[:cols_to_adjust]):
                        try:
                            # Calcular ancho basado en tipo de dato
                            if df[col].dtype in ['object', 'category', 'string']:
                                max_len = len(str(col))
                                if len(df_sample) > 0:
                                    # Manejar valores nulos
                                    col_values = df_sample[col].fillna('').astype(str)
                                    if len(col_values) > 0:
                                        sample_max = col_values.str.len().max()
                                        if pd.notna(sample_max):
                                            max_len = max(max_len, sample_max)
                                adjusted_width = min(max_len + 2, 35)
                            else:
                                # Para columnas numéricas
                                adjusted_width = min(len(str(col)) + 2, 15)
                            
                            worksheet.set_column(i, i, adjusted_width)
                        except Exception as e:
                            print(f"Error ajustando columna {col}: {e}")
                            worksheet.set_column(i, i, 12)
                    
                    # Columnas restantes con ancho fijo
                    if len(df.columns) > cols_to_adjust:
                        for i in range(cols_to_adjust, len(df.columns)):
                            worksheet.set_column(i, i, 12)
                else:
                    # Para datasets grandes, ancho fijo en todas las columnas
                    for i, col in enumerate(df.columns):
                        worksheet.set_column(i, i, 12)
                
                # Agregar funcionalidades útiles
                worksheet.freeze_panes(1, 0)  # Congelar primera fila
                worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)  # Agregar autofiltro
                        
        except ImportError as e:
            print(f"Error con xlsxwriter: {e}. Usando openpyxl...")
            # Fallback a openpyxl
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        output.seek(0)
        
        # Crear nombre del archivo con fecha y hora
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.xlsx"
        
        print(f"Archivo generado exitosamente: {filename} (Filas: {len(df)})")
        
        return output.getvalue(), filename
        
    except Exception as e:
        print(f"ERROR en export_dataframe_to_excel_optimized: {str(e)}")
        traceback.print_exc()
        raise

def apply_filters_with_query(df, filters_config):
    conditions = []
    
    for column, values in filters_config.items():
        if values and column in df.columns:
            # Convertir valores a string para comparación consistente
            values_str = "', '".join([str(v) for v in values])
            conditions.append(f"{column} in ['{values_str}']")
    
    # Aplicar filtros con query
    if conditions:
        query_str = " & ".join(conditions)
        try:
            df_filtrado = df.query(query_str)
        except Exception as e:
            print(f"Error en query, usando método alternativo: {e}")
            # Fallback a método tradicional
            df_filtrado = df.copy()
            for column, values in filters_config.items():
                if values and column in df.columns:
                    df_filtrado = df_filtrado[df_filtrado[column].isin([str(v) for v in values])]
    else:
        df_filtrado = df.copy()
    
    return df_filtrado