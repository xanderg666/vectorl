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


def verificar_tnsnames():
    """Verifica y muestra los DSN disponibles en tnsnames.ora"""
    tnsnames_path = os.path.join(DB_CONFIG["config_dir"], "tnsnames.ora")

    if not os.path.exists(tnsnames_path):
        logger.error(f"No se encuentra el archivo tnsnames.ora en: {tnsnames_path}")
        return []

    try:
        with open(tnsnames_path, 'r') as f:
            content = f.read()
            import re
            dsn_names = re.findall(r'^(\w+)\s*=', content, re.MULTILINE)

            if dsn_names:
                logger.info(f"DSN disponibles en tnsnames.ora: {', '.join(dsn_names)}")
                return dsn_names
            else:
                logger.warning("No se pudieron extraer nombres de DSN del archivo")
                return []
    except Exception as e:
        logger.error(f"Error leyendo tnsnames.ora: {e}")
        return []


def setup_database_table():
    """Crea la tabla vectorial con su índice"""
    logger.info(f"Iniciando la configuración de la tabla '{TABLE_NAME}'...")

    dsn_disponibles = verificar_tnsnames()
    if dsn_disponibles:
        logger.info(f"Usando DSN: {DB_CONFIG['dsn']}")
        if DB_CONFIG['dsn'] not in dsn_disponibles:
            logger.warning(f"⚠ El DSN '{DB_CONFIG['dsn']}' no está en la lista de disponibles.")
            logger.warning(f"Considera usar uno de estos: {', '.join(dsn_disponibles)}")

    try:
        db = OracleADBConnection(**DB_CONFIG)
        logger.info("Objeto de conexión creado.")

        logger.info("Verificando conexión a la base de datos...")
        with db.get_connection() as conn:
            logger.info(f"✓ Conexión exitosa. Versión Oracle: {conn.version}")

        try:
            logger.info(f"Intentando eliminar la tabla '{TABLE_NAME}' si existe...")
            db.execute_dml(SQL_DROP_TABLE)
            logger.info(f"✓ Tabla '{TABLE_NAME}' eliminada con éxito.")
        except oracledb.DatabaseError as e:
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

        if error_obj.code == 4000:
            logger.error("\n" + "=" * 60)
            logger.error("SOLUCIÓN AL ERROR DPY-4000:")
            logger.error("=" * 60)
            logger.error("1. Abre el archivo tnsnames.ora en:")
            logger.error(f"   {os.path.join(DB_CONFIG['config_dir'], 'tnsnames.ora')}")
            logger.error("2. Busca los nombres de servicio (líneas que terminan con =)")
            logger.error("3. Usa uno de esos nombres como 'dsn' en DB_CONFIG")
            logger.error("   Ejemplos comunes: agent_high, agent_medium, agent_low")
            logger.error("=" * 60)

        raise
    except Exception as e:
        logger.error(f"Ocurrió un error durante la configuración de la base de datos: {e}")
        logger.error("Por favor, revisa la configuración de conexión y los permisos del usuario.")
        raise


if __name__ == "__main__":
    setup_database_table()