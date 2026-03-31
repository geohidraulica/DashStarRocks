import dash
from dash import html, dcc, dash_table, callback, Output, Input, State
import pandas as pd
from services import mantenimiento_service, airflow_service
from dash.dash_table.Format import Format, Scheme
from global_state import DAG_STATUS
import traceback
from excel_export import export_dataframe_to_excel_optimized, apply_filters_with_query

dash.register_page(__name__, path="/mantenimiento")


def cargar_datos():
    df = mantenimiento_service.get_fact_mantenimiento()
    
    df["Anio"] = df["Anio"].astype(str)
    
    for col in df.select_dtypes(include=['float64']).columns:
        df[col] = df[col].astype('float32')
    for col in df.select_dtypes(include=['int64']).columns:
        df[col] = df[col].astype('int32')
    return df

df_original = cargar_datos()


# =========================
# COLUMNAS
# =========================
columns = []
for col in df_original.columns:
    if pd.api.types.is_float_dtype(df_original[col]) or pd.api.types.is_integer_dtype(df_original[col]):
        columns.append({
            "name": col,
            "id": col,
            "type": "numeric",
            "format": Format(precision=4, scheme=Scheme.fixed)
        })
    else:
        columns.append({"name": col, "id": col, "type": "text"})
        
# =========================
# LAYOUT
# =========================
layout = html.Div([
    html.Link(rel="stylesheet",
              href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"),
    html.Meta(name="viewport", content="width=device-width, initial-scale=1.0"),

    html.Div([
        # HEADER
        html.Div([
            html.Div([html.H2("Detalle RQ-OC"), html.P("Seguimiento de compras")], className="title"),
            html.Div([html.Small("Última actualización:"), html.Small(id="ult_actualizacion_ot")], className="header-info")
        ], className="header-container"),

        # FILTROS
        html.Div([
            html.Div([
                html.Label("Año"),
                dcc.Dropdown(id="filtro_anio_ot", options=[], multi=True, placeholder="Seleccionar año(s)", className="professional-dropdown")
            ], className="filter-item"),

            html.Div([
                html.Label("Atención"),
                dcc.Dropdown(id="filtro_atencion_ot", options=[], multi=True, placeholder="Seleccionar atención", className="professional-dropdown")
            ], className="filter-item"),

            html.Div([
                html.Label("Stock"),
                dcc.Dropdown(id="filtro_stock_ot", options=[], multi=True, placeholder="Seleccionar stock", className="professional-dropdown")
            ], className="filter-item large"),

            html.Div([
                html.Label("Acciones"),
                html.Button("Sincronizar datos", id="btn_actualizar_ot", n_clicks=0, className="btn-primary"),
                dcc.Store(id="sync_trigger_ot", data=0),
            ], className="actions-item")
        ], className="filters-container"),

        # TABLA
        html.Div([
            html.Div([
                html.Div([
                    html.I(className="fas fa-table"), 
                    html.Span("Registros")
                ], className="table-header"),
                html.Button([
                    # html.I(className="fas fa-download"), 
                    html.Span("Descargar Excel")
                ], id="btn_descargar_ot", n_clicks=0, className="btn-download")
            ], className="table-header-container"),
            
            html.Div([dcc.Loading(
                id="loading_tabla",
                children=dash_table.DataTable(
                    id="tabla_mantenimiento",
                    columns=columns,
                    data=[],
                    page_size=20,
                    sort_action="native",
                    filter_action="native",
                    style_table={"overflowX": "auto", "height": "550px", "overflowY": "auto", "minWidth": "100%"},
                    style_cell={"textAlign": "left", "padding": "12px 8px", "fontFamily": "'Segoe UI', 'Roboto', 'Arial'",
                                "fontSize": "12px", "whiteSpace": "normal", "border": "none", "minWidth": "80px"},
                    style_header={"backgroundColor": "#f8f9fa", "fontWeight": "600",
                                  "textAlign": "center", "borderBottom": "2px solid #dee2e6"},
                    style_data_conditional=[{"if": {"row_index": "odd"}, "backgroundColor": "#fafbfc"},
                                            {"if": {"state": "active"}, "backgroundColor": "#e3f2fd"}],
                    virtualization=True,
                    css=[{'selector': '.dash-spreadsheet td div', 'rule': 'line-height: 20px; word-break: break-word;'}]
                )
            )], className="table-wrapper")
        ], className="table-container")
    ], className="main-container"),

    # MODAL
    html.Div(id="modal_sync_ot", className="modal-overlay", style={"display": "none"},
             children=html.Div([
                 html.Div(className="spinner"),
                 html.Div("Sincronizando datos...", className="modal-title"),
                 html.Div("Por favor espere mientras se actualiza la información", className="modal-subtitle")
             ], className="modal-content")),
    
    # MODAL PARA DESCARGA
    html.Div(id="modal_download_ot", className="modal-overlay", style={"display": "none"},
             children=html.Div([
                 html.Div(className="spinner"),
                 html.Div(id="download_modal_title_ot", children="Generando archivo Excel...", className="modal-title"),
                 html.Div(id="download_modal_subtitle_ot", children="Por favor espere mientras se procesa la información", className="modal-subtitle")
             ], className="modal-content")),
    
    # COMPONENTE PARA DESCARGAR EXCEL
    dcc.Download(id="download-excel-ot"),
    
    # COMPONENTE PARA MENSAJES DE NOTIFICACIÓN
    dcc.Store(id="download-status", data={"status": "idle"})
])

# =========================
# CALLBACK 0: Inicializar opciones de filtros
# =========================
@callback(
    Output("filtro_anio_ot", "options"),
    Output("filtro_atencion_ot", "options"),
    Output("filtro_stock_ot", "options"),
    Input("filtro_anio_ot", "options")
)
def inicializar_filtros(_):
    """Inicializa los filtros con todos los valores disponibles"""
    anios = sorted(df_original["Anio"].dropna().unique())
    atencion = sorted(df_original["EstadoAtencion"].dropna().unique())
    stock = sorted(df_original["EstadoStock"].dropna().unique())
    
    return (
        [{"label": str(i), "value": i} for i in anios],
        [{"label": str(i), "value": i} for i in atencion],
        [{"label": str(i), "value": i} for i in stock]
    )

# =========================
# CALLBACK 1: Mostrar modal y activar sincronización
# =========================
@callback(
    Output("modal_sync_ot", "style"),
    Output("sync_trigger_ot", "data"),
    Input("btn_actualizar_ot", "n_clicks"),
    prevent_initial_call=True
)
def mostrar_modal_y_activar_sincronizacion(n_clicks):
    """Muestra el modal de sincronización y activa el trigger"""
    if n_clicks > 0:
        return {"display": "flex"}, n_clicks
    return {"display": "none"}, 0

# =========================
# CALLBACK 2: Aplicar filtros y mostrar datos
# =========================
@callback(
    Output("tabla_mantenimiento", "data"),
    Output("ult_actualizacion_ot", "children"),
    Input("filtro_anio_ot", "value"),
    Input("filtro_atencion_ot", "value"),
    Input("filtro_stock_ot", "value"),
)
def aplicar_filtros(anio, atencion, stock):
    """Aplica los filtros seleccionados y muestra los datos filtrados"""
    mask = pd.Series(True, index=df_original.index)
    
    if anio:
        mask &= df_original["Anio"].isin([str(a) for a in anio])
    if atencion:
        mask &= df_original["EstadoAtencion"].isin([str(m) for m in atencion])
    if stock:
        mask &= df_original["EstadoStock"].isin([str(f) for f in stock])

    try:
        dag_id = "MasterMantenimiento"
        ultima = airflow_service.ultima_ejecucion_exitosa(dag_id) or "Nunca"
    except Exception:
        ultima = "Error"
    
    df_filtrado = df_original[mask]
    return df_filtrado.iloc[:10000].to_dict("records"), ultima

# =========================
# CALLBACK 3: Ejecutar sincronización y actualizar todo
# =========================
@callback(
    Output("modal_sync_ot", "style", allow_duplicate=True),
    Output("filtro_anio_ot", "options", allow_duplicate=True),
    Output("filtro_atencion_ot", "options", allow_duplicate=True),
    Output("filtro_stock_ot", "options", allow_duplicate=True),
    Output("filtro_anio_ot", "value"),
    Output("filtro_atencion_ot", "value"),
    Output("filtro_stock_ot", "value"),
    Input("sync_trigger_ot", "data"),
    prevent_initial_call=True
)
def ejecutar_sincronizacion(trigger):
    global df_original
    
    if trigger == 0:
        return (dash.no_update, dash.no_update, dash.no_update, 
                dash.no_update, dash.no_update, dash.no_update, dash.no_update)
    
    try:
        dag_id = "MasterMantenimiento"
        
        
        airflow_service.ejecutar_dag(dag_id)
        
        print("Esperando notificación de Airflow...")
        
        estado = DAG_STATUS.get("estado")

        print(f"DAG terminó con estado: {estado}")
        
        # Recargar datos actualizados
        df_original = cargar_datos()
        
        # Actualizar opciones de filtros
        anios = sorted(df_original["Anio"].dropna().unique())
        atencion = sorted(df_original["EstadoAtencion"].dropna().unique())
        stock = sorted(df_original["EstadoStock"].dropna().unique())
        
        anios_options = [{"label": str(i), "value": i} for i in anios]
        atencion_options = [{"label": str(i), "value": i} for i in atencion]
        stock_options = [{"label": str(i), "value": i} for i in stock]
        
        # Limpiar filtros después de sincronizar
        anios_cleared = None
        atencion_cleared = None
        stock_cleared = None
        
    except Exception as e:
        print(f"Error en sincronización: {e}")
        traceback.print_exc()
        anios_options = dash.no_update
        atencion_options = dash.no_update
        stock_options = dash.no_update
        anios_cleared = dash.no_update
        atencion_cleared = dash.no_update
        stock_cleared = dash.no_update
    
    # Cerrar modal y devolver opciones actualizadas
    return ({"display": "none"}, 
            anios_options, atencion_options, stock_options,
            anios_cleared, atencion_cleared, stock_cleared)


# =========================
# CALLBACK 6: Mostrar modal de descarga
# =========================
@callback(
    Output("modal_download_ot", "style"),
    Output("download_modal_title_ot", "children"),
    Output("download_modal_subtitle_ot", "children"),
    Input("btn_descargar_ot", "n_clicks"),
    prevent_initial_call=True
)
def mostrar_modal_descarga(n_clicks):
    """Muestra el modal de descarga con mensaje de progreso"""
    if n_clicks > 0:
        return {"display": "flex"}, "Preparando descarga...", "Iniciando proceso de generación del archivo"
    return dash.no_update, dash.no_update, dash.no_update

# =========================
# CALLBACK 7: Descargar Excel con todos los datos filtrados (Optimizado)
# =========================
@callback(
    Output("download-excel-ot", "data"),
    Output("modal_download_ot", "style", allow_duplicate=True),
    Input("btn_descargar_ot", "n_clicks"),
    State("filtro_anio_ot", "value"),
    State("filtro_atencion_ot", "value"),
    State("filtro_stock_ot", "value"),
    prevent_initial_call=True
)
def descargar_excel(n_clicks, anio, atencion, stock):
    """Genera y descarga un archivo Excel con todos los datos filtrados (optimizado)"""
    try:
        print(f"Iniciando descarga - Clicks: {n_clicks}")
        
        if n_clicks is None or n_clicks == 0:
            return dash.no_update, dash.no_update
    
        # Configurar filtros
        filters = {
            "Anio": anio,
            "EstadoAtencion": atencion,
            "EstadoStock": stock
        }
        
        # Aplicar filtros con query (optimizado)
        df_filtrado = apply_filters_with_query(df_original, filters)
        
        print(f"Total de registros filtrados: {len(df_filtrado)}")
        
        # Exportar a Excel usando la función optimizada
        excel_data, filename = export_dataframe_to_excel_optimized(
            df=df_filtrado,
            filename_prefix="rpt_mantenimiento",
            sheet_name="Mantenimiento",
            max_rows=1000000
        )
        
        # Verificar si se generó el archivo
        if excel_data is None:
            return None, {"display": "none"}
        
        # Devolver el archivo para descarga y cerrar modal
        return dcc.send_bytes(excel_data, filename), {"display": "none"}
        
    except Exception as e:
        print(f"ERROR en descargar_excel: {str(e)}")
        traceback.print_exc()
        return None, {"display": "none"}