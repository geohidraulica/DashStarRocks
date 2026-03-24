from database.connection import get_connection

try:
    conn = get_connection()

    if conn.is_connected():
        print("✅ Conexión exitosa a MySQL")

    conn.close()

except Exception as e:
    print("❌ Error de conexión:", e)


from services import compras_service

try:
    df_compras = compras_service.get_fact_compras()
    print("✅ Consulta exitosa. Número de registros:", len(df_compras))
except Exception as e:
    print("❌ Error al ejecutar consulta:", e)