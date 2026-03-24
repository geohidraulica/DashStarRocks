import dash
from dash import html, dcc, callback, Input, Output, dash_table
import pandas as pd
from dash.dash_table.Format import Format, Scheme
from services import compras_service
from services import airflow_service
import time

dash.register_page(__name__, path="/compras")

# =========================
# CARGAR DATOS
# =========================
def cargar_datos():
    df = compras_service.get_fact_compras()
    
    # Convertir columnas a string para filtros nativos
    df["Anio"] = df["Anio"].astype(str)
    df["MesAnio"] = df["MesAnio"].astype(str)
    df["DescripcionFlujoCompra"] = df["DescripcionFlujoCompra"].astype(str)
    
    # Optimizar tipos numéricos
    for col in df.select_dtypes(include=['float64']).columns:
        df[col] = df[col].astype('float32')
    for col in df.select_dtypes(include=['int64']).columns:
        df[col] = df[col].astype('int32')
    return df

df = cargar_datos()

# =========================
# COLUMNAS DE LA TABLA
# =========================
columns = []
for col in df.columns:
    if pd.api.types.is_float_dtype(df[col]) or pd.api.types.is_integer_dtype(df[col]):
        columns.append({
            "name": col,
            "id": col,
            "type": "numeric",
            "format": Format(precision=4, scheme=Scheme.fixed)
        })
    else:
        columns.append({"name": col, "id": col, "type": "text"})  # columnas filtrables como texto

anios = sorted(df["Anio"].dropna().unique())
meses = sorted(df["MesAnio"].dropna().unique())
flujos = sorted(df["DescripcionFlujoCompra"].dropna().unique())

# =========================
# CSS personalizado
# =========================
external_css = """
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.professional-dropdown .Select-control {
    border-radius: 6px;
    border: 1px solid #dee2e6;
    transition: all 0.2s ease;
}

.professional-dropdown .Select-control:hover {
    border-color: #3498db;
}

.professional-dropdown .Select-menu-outer {
    border-radius: 6px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

#btn_actualizar:hover {
    background-color: #2980b9 !important;
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
}

#btn_actualizar:active {
    transform: translateY(0px);
}

.dash-spreadsheet .dash-filter {
    font-family: 'Segoe UI', sans-serif;
}
"""

# =========================
# LAYOUT
# =========================

layout = html.Div([
    # CSS externo usando html.Link (corregido)
    html.Link(
        rel="stylesheet",
        href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"
    ),
    
    # CSS personalizado inyectado
    html.Div(external_css, style={"display": "none"}),
    
    # Container principal con padding y fondo
    html.Div([
        # Header con título y metadata
        html.Div([
            html.Div([
                html.H2("Detalle de Requisiciones y Órdenes de Compra", 
                       style={
                           "margin": "0",
                           "color": "#2c3e50",
                           "fontSize": "24px",
                           "fontWeight": "600",
                           "letterSpacing": "-0.5px"
                       }),
                html.P("Gestión y seguimiento de compras", 
                      style={
                          "margin": "4px 0 0 0",
                          "color": "#7f8c8d",
                          "fontSize": "14px"
                      })
            ]),
            html.Div([
                html.Small("Última actualización", 
                          style={
                              "fontSize": "11px", 
                              "color": "#95a5a6",
                              "display": "block",
                              "textAlign": "right"
                          }),
                html.Small(id="ult_actualizacion", 
                          style={
                              "fontSize": "12px", 
                              "fontWeight": "500",
                              "color": "#2c3e50"
                          })
            ])
        ], style={
            "display": "flex", 
            "justifyContent": "space-between", 
            "alignItems": "flex-end",
            "marginBottom": "30px",
            "paddingBottom": "20px",
            "borderBottom": "2px solid #ecf0f1"
        }),
        
        # Panel de filtros
        html.Div([
            html.Div([
                html.Label("Año", style={
                    "fontSize": "12px", 
                    "fontWeight": "600", 
                    "color": "#34495e",
                    "marginBottom": "6px",
                    "display": "block"
                }),
                dcc.Dropdown(
                    id="filtro_anio",
                    options=[{"label": str(i), "value": i} for i in anios],
                    multi=True,
                    placeholder="Seleccionar año(s)",
                    style={"width": "200px"},
                    className="professional-dropdown"
                )
            ]),
            html.Div([
                html.Label("Mes", style={
                    "fontSize": "12px", 
                    "fontWeight": "600", 
                    "color": "#34495e",
                    "marginBottom": "6px",
                    "display": "block"
                }),
                dcc.Dropdown(
                    id="filtro_mes",
                    options=[{"label": str(i), "value": i} for i in meses],
                    multi=True,
                    placeholder="Seleccionar mes(es)",
                    style={"width": "200px"},
                    className="professional-dropdown"
                )
            ]),
            html.Div([
                html.Label("Flujo de Compra", style={
                    "fontSize": "12px", 
                    "fontWeight": "600", 
                    "color": "#34495e",
                    "marginBottom": "6px",
                    "display": "block"
                }),
                dcc.Dropdown(
                    id="filtro_flujo",
                    options=[{"label": str(i), "value": i} for i in flujos],
                    multi=True,
                    placeholder="Seleccionar flujo(s)",
                    style={"width": "250px"},
                    className="professional-dropdown"
                )
            ]),
            html.Div([
                html.Label("Acciones", style={
                    "fontSize": "12px", 
                    "fontWeight": "600", 
                    "color": "#34495e",
                    "marginBottom": "6px",
                    "display": "block"
                }),
                html.Div([
                    html.Button(
                        "Sincronizar datos",
                        id="btn_actualizar",
                        n_clicks=0,
                        style={
                            "backgroundColor": "#3498db",
                            "color": "white",
                            "border": "none",
                            "padding": "8px 20px",
                            "borderRadius": "6px",
                            "cursor": "pointer",
                            "fontWeight": "500",
                            "fontSize": "13px",
                            "transition": "all 0.3s ease",
                            "boxShadow": "0 2px 4px rgba(0,0,0,0.1)"
                        }
                    )
                ])
            ])
        ], style={
            "display": "flex", 
            "gap": "25px", 
            "marginBottom": "30px",
            "padding": "20px",
            "backgroundColor": "#f8f9fa",
            "borderRadius": "8px",
            "border": "1px solid #e9ecef"
        }),
        
        # Tabla con estilo profesional
        html.Div([
            html.Div([
                html.I(className="fas fa-table", style={"marginRight": "8px"}),
                html.Span("Registros", style={"marginLeft": "8px", "fontWeight": "500"})
            ], style={
                "padding": "12px 16px",
                "backgroundColor": "#f8f9fa",
                "borderBottom": "1px solid #e9ecef",
                "fontSize": "13px",
                "color": "#495057"
            }),
            dcc.Loading(
                id="loading_tabla",
                type="default",
                children=dash_table.DataTable(
                    id="tabla_compras",
                    columns=columns,
                    data=df.head(5000).to_dict("records"),
                    page_size=20,
                    sort_action="native",
                    filter_action="native",
                    style_table={
                        "overflowX": "auto",
                        "height": "550px",
                        "overflowY": "auto"
                    },
                    style_cell={
                        "textAlign": "left",
                        "padding": "12px 8px",
                        "fontFamily": "'Segoe UI', 'Roboto', 'Arial', sans-serif",
                        "fontSize": "12px",
                        "whiteSpace": "nowrap",
                        "border": "none"
                    },
                    style_header={
                        "backgroundColor": "#f8f9fa",
                        "color": "#495057",
                        "fontWeight": "600",
                        "textAlign": "center",
                        "borderBottom": "2px solid #dee2e6",
                        "padding": "12px 8px"
                    },
                    style_data={
                        "backgroundColor": "white",
                        "borderBottom": "1px solid #f0f0f0"
                    },
                    style_data_conditional=[
                        {
                            "if": {"row_index": "odd"},
                            "backgroundColor": "#fafbfc"
                        },
                        {
                            "if": {"state": "active"},
                            "backgroundColor": "#e3f2fd",
                            "border": "none"
                        }
                    ],
                    virtualization=True,
                    css=[{
                        'selector': '.dash-spreadsheet td div',
                        'rule': 'line-height: 20px'
                    }]
                )
            )
        ], style={
            "border": "1px solid #e9ecef",
            "borderRadius": "8px",
            "overflow": "hidden",
            "backgroundColor": "white",
            "boxShadow": "0 1px 3px rgba(0,0,0,0.05)"
        })
    ], style={
        "width": "100%",
        "margin": "0 auto",
        "padding": "30px",
        "backgroundColor": "white"
    }),
    
    # Modal bloqueante
    html.Div(
        id="modal_sync",
        children=html.Div([
            html.Div([
                # Spinner animado con CSS puro
                html.Div(style={
                    "width": "40px",
                    "height": "40px",
                    "border": "3px solid #f3f3f3",
                    "borderTop": "3px solid #3498db",
                    "borderRadius": "50%",
                    "animation": "spin 1s linear infinite",
                    "margin": "0 auto 15px auto"
                }),
                html.Div("Sincronizando datos...", style={
                    "fontSize": "18px", 
                    "fontWeight": "500",
                    "marginBottom": "8px"
                }),
                html.Div("Por favor espere mientras se actualiza la información", style={
                    "fontSize": "13px",
                    "color": "#95a5a6"
                })
            ], style={
                "backgroundColor": "white",
                "padding": "30px 40px",
                "borderRadius": "12px",
                "textAlign": "center",
                "boxShadow": "0 10px 40px rgba(0,0,0,0.2)"
            })
        ]),
        style={
            "position": "fixed",
            "top": 0,
            "left": 0,
            "width": "100%",
            "height": "100%",
            "backgroundColor": "rgba(0,0,0,0.6)",
            "display": "none",
            "justifyContent": "center",
            "alignItems": "center",
            "zIndex": 9999,
            "backdropFilter": "blur(3px)"
        }
    )
])

# =========================
# CALLBACK PARA FILTROS Y BOTÓN
# =========================
@callback(
    Output("tabla_compras", "data"),
    Output("ult_actualizacion", "children"),
    Output("modal_sync", "style"),
    Input("filtro_anio", "value"),
    Input("filtro_mes", "value"),
    Input("filtro_flujo", "value"),
    Input("btn_actualizar", "n_clicks"),
)
def actualizar_tabla(anio, mes, flujo, n_clicks):
    ctx = dash.callback_context
    trigger_id = ctx.triggered_id

    # Modal por defecto oculto
    modal_style = {"display": "none"}

    # Por defecto, obtener última ejecución
    ultima = airflow_service.ultima_ejecucion_exitosa("MasterCompras") or "Nunca"

    global df

    # Si presionaron el botón, ejecutar DAG y mostrar modal
    if trigger_id == "btn_actualizar":
        modal_style = {
            "position": "fixed",
            "top": 0,
            "left": 0,
            "width": "100%",
            "height": "100%",
            "backgroundColor": "rgba(0,0,0,0.6)",
            "display": "flex",
            "justifyContent": "center",
            "alignItems": "center",
            "zIndex": 9999,
            "backdropFilter": "blur(3px)"
        }

        # Renderiza modal primero
        time.sleep(0.1)  # permite que Dash renderice modal

        try:
            dag_id = "MasterCompras"
            dag_run_id = airflow_service.ejecutar_dag(dag_id)

            # Esperar a que termine DAG
            estado = airflow_service.estado_dag(dag_id, dag_run_id)
            while estado not in ["success", "failed"]:
                time.sleep(2)
                estado = airflow_service.estado_dag(dag_id, dag_run_id)

            # Recargar datos
            df = cargar_datos()

            # Obtener última actualización
            ultima = airflow_service.ultima_ejecucion_exitosa(dag_id) or "Nunca"
        except Exception as e:
            print(e)
            ultima = "Error"

        # Ocultar modal
        modal_style["display"] = "none"

    # Filtrar tabla según dropdowns
    mask = pd.Series(True, index=df.index)
    if anio:
        mask &= df["Anio"].isin([str(a) for a in anio])
    if mes:
        mask &= df["MesAnio"].isin([str(m) for m in mes])
    if flujo:
        mask &= df["DescripcionFlujoCompra"].isin([str(f) for f in flujo])

    data = df[mask].iloc[:10000].to_dict("records")

    return data, ultima, modal_style