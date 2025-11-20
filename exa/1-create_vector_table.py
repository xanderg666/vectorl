import logging
from class_adw import OracleADBConnection
from config import DB_CONFIG, TABLE_NAME
import oracledb
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SQL_DROP_TABLE = f"DROP TABLE {TABLE_NAME} PURGE"

SQL_CREATE_TABLE = f"""
CREATE TABLE {TABLE_NAME}
(
    id             NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    docid          VARCHAR2(500),
    body           CLOB,
    vector         VECTOR(1536, FLOAT32),
    title          VARCHAR2(500),
    url            VARCHAR2(1000),
    chunk_id       NUMBER,
    page_numbers   VARCHAR2(100),
    metadata       JSON,
    fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""

SQL_CREATE_INDEX = f"""
CREATE VECTOR INDEX idx_vector_{TABLE_NAME}
ON {TABLE_NAME}(vector)
ORGANIZATION INMEMORY NEIGHBOR GRAPH
DISTANCE COSINE
WITH TARGET ACCURACY 95
"""


def setup_database_table():
    """Crea la tabla vectorial con su índice"""
    logger.info(f"Iniciando la configuración de la tabla '{TABLE_NAME}'...")

    try:
        # Validar que la configuración esencial está presente
        if not all([DB_CONFIG.get("user"), DB_CONFIG.get("password"), DB_CONFIG.get("dsn")]):
            logger.error("La configuración de la base de datos (user, password, dsn) está incompleta.")
            logger.error("Asegúrate de que las variables de entorno DB_USER, DB_PASSWORD y DB_DSN están definidas.")
            return

        db = OracleADBConnection(
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            dsn=DB_CONFIG["dsn"]
        )
        logger.info("Objeto de conexión creado.")

        logger.info("Verificando conexión a la base de datos...")
        with db.get_connection() as conn:
            logger.info(f"✓ Conexión exitosa. Versión Oracle: {conn.version}")

        try:
            logger.info(f"Intentando eliminar la tabla '{TABLE_NAME}' si existe...")
            db.execute_dml(SQL_DROP_TABLE)
            logger.info(f"✓ Tabla '{TABLE_NAME}' eliminada con éxito.")
        except oracledb.DatabaseError as e:
            # ORA-00942: table or view does not exist
            if 'ORA-00942' in str(e):
                logger.info(f"La tabla '{TABLE_NAME}' no existía, no fue necesario eliminarla.")
            else:
                raise

        logger.info(f"Creando la tabla '{TABLE_NAME}'...")
        db.execute_dml(SQL_CREATE_TABLE)
        logger.info(f"✓ Tabla '{TABLE_NAME}' creada con éxito.")

        logger.info(f"Creando el índice vectorial 'idx_vector_{TABLE_NAME}'...")
        db.execute_dml(SQL_CREATE_INDEX)
        logger.info(f"✓ Índice vectorial 'idx_vector_{TABLE_NAME}' creado con éxito.")

        logger.info("\n" + "=" * 60)
        logger.info("✓ Configuración de la base de datos finalizada exitosamente.")
        logger.info("=" * 60)

    except oracledb.DatabaseError as e:
        error_obj, = e.args
        logger.error(f"Error de Oracle Database: {error_obj.code} - {error_obj.message}")
        raise
    except Exception as e:
        logger.error(f"Ocurrió un error durante la configuración de la base de datos: {e}")
        logger.error("Por favor, revisa la configuración de conexión y los permisos del usuario.")
        raise


if __name__ == "__main__":
    setup_database_table()