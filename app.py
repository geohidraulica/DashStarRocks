# app.py
import dash
from dash import html, dcc, Input, Output, callback, State
import dash_bootstrap_components as dbc

# Crear la app
app = dash.Dash(
    __name__,
    use_pages=True,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP, 
        dbc.icons.FONT_AWESOME
    ],
    suppress_callback_exceptions=True,
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1, maximum-scale=1, user-scalable=yes"}
    ]
)

server = app.server

# --- CONFIGURACIÓN DE PÁGINAS CON ICONOS ---
PAGES = [
    {"name": "Compras", "href": "/compras", "id": "link-compras", "icon": "fas fa-shopping-cart"},
    {"name": "Ventas", "href": "/ventas", "id": "link-ventas", "icon": "fas fa-chart-line"},
    {"name": "Inventario", "href": "/inventario", "id": "link-inventario", "icon": "fas fa-boxes"},
    {"name": "Clientes", "href": "/clientes", "id": "link-clientes", "icon": "fas fa-users"},
    {"name": "Proveedores", "href": "/proveedores", "id": "link-proveedores", "icon": "fas fa-truck"},
    {"name": "Reportes", "href": "/reportes", "id": "link-reportes", "icon": "fas fa-file-alt"},
    {"name": "Configuración", "href": "/configuracion", "id": "link-configuracion", "icon": "fas fa-cog"},
]

# --- LAYOUT PRINCIPAL ---
app.layout = dbc.Container([
    dcc.Location(id='url', refresh=False),
    dcc.Store(id='sidebar-state', data='expanded'),
    dcc.Store(id='viewport-size', data='desktop'),
    
    html.Div([  # Contenedor flex principal
        # Sidebar para desktop
        html.Div([
            html.Div([
                html.Div([
                    html.Img(
                        src='/assets/logo_geohidraulica.png',
                        id='sidebar-logo',
                        className='sidebar-logo-img'
                    ),
                ], id='logo-container', className='logo-wrapper'),
                
                html.Hr(id='sidebar-hr', className='sidebar-divider'),
                
                dbc.Nav([
                    dbc.NavLink(
                        [html.I(className=f"{page['icon']} nav-icon"),
                         html.Span(page["name"], className='nav-text', id=f"{page['id']}-text")],
                        href=page["href"], 
                        id=page["id"],
                        className='sidebar-nav-link'
                    ) for page in PAGES
                ], vertical=True, pills=True, id="sidebar-nav", className='sidebar-nav')
            ], id='sidebar-content', className='sidebar-content')
        ], id="sidebar", className="sidebar-col d-none d-md-block"),
        
        # Offcanvas para móvil
        dbc.Offcanvas(
            [
                html.Div([
                    html.Img(
                        src='/assets/logo_geohidraulica.png',
                        className='sidebar-logo-img mb-4'
                    ),
                ], className='text-center'),
                
                dbc.Nav([
                    dbc.NavLink(
                        [html.I(className=f"{page['icon']} nav-icon me-3"),
                         page["name"]],
                        href=page["href"], 
                        id=f"{page['id']}-mobile",
                        className='sidebar-nav-link'
                    ) for page in PAGES
                ], vertical=True, pills=True),
            ],
            id="mobile-sidebar",
            title=None,
            placement="start",
            is_open=False,
            className='mobile-sidebar'
        ),
        
        # Contenido principal
        html.Div([
            # Header
            html.Div([
                html.Div([
                    html.Div([
                        # Botón para desktop
                        html.Div([
                            dbc.Button(
                                html.I(className="fas fa-bars", id="toggle-icon"),
                                id="btn-sidebar-toggle",
                                color="light",
                                className="desktop-toggle me-3 d-none d-md-inline-block",
                            ),
                        ]),
                        
                        # Botón para móvil
                        html.Div([
                            dbc.Button(
                                html.I(className="fas fa-bars"),
                                id="btn-mobile-toggle",
                                color="light",
                                className="mobile-toggle d-md-none me-3",
                            ),
                        ]),
                        
                        html.H5("GeoHidráulica", className="mb-0 text-white d-none d-sm-inline-block"),
                    ], className="d-flex align-items-center")
                ], className="header-content")
            ], className="header-row"),
            
            # Contenido de la página
            html.Div(
                dash.page_container,
                id="page-content",
                className="page-content"
            )
        ], id="content-col", className="content-col")
    ], className="app-flex-container")
], fluid=True, id="main-container", className="app-container")
# --- CALLBACKS ---

# Callback para activar los links
@callback(
    [Output(page["id"], "active") for page in PAGES] +
    [Output(f"{page['id']}-mobile", "active") for page in PAGES],
    Input("url", "pathname")
)
def update_active_links(pathname):
    desktop_active = [pathname == page["href"] for page in PAGES]
    mobile_active = [pathname == page["href"] for page in PAGES]
    return desktop_active + mobile_active

# Callback para detectar tamaño de pantalla (opcional, para lógica adicional)
@callback(
    Output("viewport-size", "data"),
    Input("url", "pathname")  # Usamos esto como trigger, en producción podrías usar window events
)
def check_viewport(pathname):
    # Esto se puede mejorar con clientside callback para detectar resize
    return "mobile"  # Placeholder

# Callback para toggle del sidebar desktop
@callback(
    [Output("sidebar", "className"),
     Output("toggle-icon", "className"),
     Output("sidebar-state", "data"),
     Output("sidebar-logo", "className"),
     Output("logo-container", "className"),
     Output("sidebar-hr", "className")] + 
    [Output(f"{page['id']}-text", "className") for page in PAGES],
    [Input("btn-sidebar-toggle", "n_clicks")],
    [State("sidebar-state", "data")]
)
def toggle_sidebar(n_clicks, current_state):
    if not n_clicks:
        # Estado inicial: expandido
        base_class = "sidebar-col d-none d-md-block"
        return (
            base_class,  # sidebar className
            "fas fa-bars",  # icono
            "expanded",  # state
            "sidebar-logo-img expanded",  # logo class
            "logo-wrapper expanded",  # logo container class
            "sidebar-divider expanded",  # hr class
            *["nav-text expanded" for _ in PAGES]  # textos visibles
        )
    
    if current_state == "expanded":
        # Contraer sidebar
        return (
            "sidebar-col collapsed d-none d-md-block",  # sidebar className
            "fas fa-bars fa-rotate-90",  # icono girado
            "collapsed",  # state
            "sidebar-logo-img collapsed",  # logo class
            "logo-wrapper collapsed",  # logo container class
            "sidebar-divider collapsed",  # hr class
            *["nav-text collapsed" for _ in PAGES]  # textos ocultos
        )
    else:
        # Expandir sidebar
        return (
            "sidebar-col d-none d-md-block",  # sidebar className
            "fas fa-bars",  # icono
            "expanded",  # state
            "sidebar-logo-img expanded",  # logo class
            "logo-wrapper expanded",  # logo container class
            "sidebar-divider expanded",  # hr class
            *["nav-text expanded" for _ in PAGES]  # textos visibles
        )

# Callback para manejar offcanvas móvil
@callback(
    Output("mobile-sidebar", "is_open"),
    [Input("btn-mobile-toggle", "n_clicks")],
    [State("mobile-sidebar", "is_open")],
    prevent_initial_call=True
)
def toggle_mobile_sidebar(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

# Callback para cerrar offcanvas al hacer clic en un link
@callback(
    Output("mobile-sidebar", "is_open", allow_duplicate=True),
    [Input(f"{page['id']}-mobile", "n_clicks") for page in PAGES],
    prevent_initial_call=True
)
def close_mobile_sidebar(*args):
    return False

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)