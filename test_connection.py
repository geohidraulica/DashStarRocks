# test_connection.py
from database.connection import get_engine
from sqlalchemy import text

def test_connection():
    """
    Prueba la conexión usando tu archivo connection.py
    """
    print("=" * 50)
    print("PROBANDO CONEXIÓN A STARROCKS")
    print("=" * 50)
    
    try:
        print("\n🔄 Creando engine...")
        engine = get_engine()
        
        print("🔄 Intentando conectar...")
        with engine.connect() as conn:
            print("✅ Conexión establecida")
            
            # Probar consulta simple
            result = conn.execute(text("SELECT VERSION()"))
            version = result.fetchone()
            
            print(f"\n✅ CONEXIÓN EXITOSA")
            print(f"   Versión: {version[0]}")
            print(f"   Base de datos: fuxion_dw")
            
            return True
            
    except Exception as e:
        print(f"\n❌ ERROR DE CONEXIÓN")
        print(f"   {e}")
        return False

if __name__ == "__main__":
    resultado = test_connection()
    
    print("\n" + "=" * 50)
    if resultado:
        print("RESULTADO: CONEXIÓN EXITOSA ✅")
    else:
        print("RESULTADO: CONEXIÓN FALLIDA ❌")
    print("=" * 50)