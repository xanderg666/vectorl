import logging
import pandas as pd
from class_adw import OracleADBConnection
from config import DB_CONFIG

# Configurar logging básico para ver errores, pero no info de conexión cada vez
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

def print_help():
    print("\n--- Comandos Disponibles ---")
    print("  SELECT ... : Ejecuta cualquier consulta SQL (ej: SELECT * FROM tabla)")
    print("  tables     : Lista todas las tablas del usuario")
    print("  count <tabla> : Cuenta los registros de una tabla")
    print("  desc <tabla>  : Muestra la estructura de una tabla (columnas)")
    print("  help       : Muestra esta ayuda")
    print("  exit / quit: Salir")
    print("----------------------------\n")

def list_tables(db):
    query = "SELECT table_name FROM user_tables ORDER BY table_name"
    try:
        df = db.execute_query_df(query)
        if not df.empty:
            print("\nTablas encontradas:")
            print(df.to_string(index=False))
        else:
            print("\nNo se encontraron tablas.")
    except Exception as e:
        print(f"Error al listar tablas: {e}")

def count_records(db, table_name):
    query = f"SELECT COUNT(*) as total FROM {table_name}"
    try:
        df = db.execute_query_df(query)
        print(f"\nTotal registros en '{table_name}': {df.iloc[0, 0]}")
    except Exception as e:
        print(f"Error al contar registros: {e}")

def describe_table(db, table_name):
    query = f"""
        SELECT column_name, data_type, data_length, nullable 
        FROM user_tab_columns 
        WHERE table_name = UPPER(:1)
        ORDER BY column_id
    """
    try:
        df = db.execute_query_df(query, [table_name])
        if not df.empty:
            print(f"\nEstructura de '{table_name}':")
            print(df.to_string(index=False))
        else:
            print(f"\nNo se encontró información para la tabla '{table_name}'.")
    except Exception as e:
        print(f"Error al describir tabla: {e}")

def execute_custom_query(db, query):
    try:
        # Detectar si es un SELECT para mostrar resultados, o DML para mostrar filas afectadas
        if query.strip().upper().startswith("SELECT") or query.strip().upper().startswith("WITH"):
            df = db.execute_query_df(query)
            if not df.empty:
                print(f"\nResultados ({len(df)} filas):")
                # Ajustar opciones de pandas para mostrar mejor en consola
                with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.width', 1000):
                    print(df)
            else:
                print("\nLa consulta no retornó resultados.")
        else:
            # Asumir DML (INSERT, UPDATE, DELETE, CREATE, DROP, etc)
            # Nota: class_adw.execute_dml hace commit por defecto
            rows = db.execute_dml(query)
            print(f"\nOperación ejecutada. Filas afectadas: {rows}")

    except Exception as e:
        print(f"Error SQL: {e}")

def main():
    print("Iniciando cliente de base de datos...")
    try:
        db = OracleADBConnection(**DB_CONFIG)
        # Probar conexión rápida
        with db.get_connection() as conn:
            print(f"Conectado exitosamente a: {conn.version}")
    except Exception as e:
        print(f"Error crítico de conexión: {e}")
        return

    print_help()

    while True:
        try:
            user_input = input("\nSQL> ").strip()
            
            if not user_input:
                continue

            command = user_input.lower()

            if command in ['exit', 'quit']:
                print("Hasta luego!")
                break
            
            elif command == 'help':
                print_help()
            
            elif command == 'tables':
                list_tables(db)
            
            elif command.startswith('count '):
                parts = user_input.split()
                if len(parts) > 1:
                    count_records(db, parts[1])
                else:
                    print("Uso: count <nombre_tabla>")
            
            elif command.startswith('desc '):
                parts = user_input.split()
                if len(parts) > 1:
                    describe_table(db, parts[1])
                else:
                    print("Uso: desc <nombre_tabla>")

            else:
                # Asumir que es una query SQL directa
                # Permitir queries multilínea si terminan en ; (opcional, por ahora simple)
                execute_custom_query(db, user_input)

        except KeyboardInterrupt:
            print("\nOperación cancelada.")
        except Exception as e:
            print(f"Error inesperado: {e}")

if __name__ == "__main__":
    main()
