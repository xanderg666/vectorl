import logging
from class_adw import OracleADBConnection
from config import DB_CONFIG
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_db_connection():
    """Prueba la conexión a la base de datos Oracle ADB usando DSN."""
    logger.info("Iniciando prueba de conexión a la base de datos con DSN...")

    # Validar que la configuración esencial está presente
    if not all([DB_CONFIG.get("user"), DB_CONFIG.get("password"), 
                DB_CONFIG.get("host"), DB_CONFIG.get("port"), DB_CONFIG.get("service_name")]):
        logger.error("La configuración de la base de datos (user, password, host, port, service_name) está incompleta.")
        logger.error("Asegúrate de que las variables de entorno DB_USER, DB_PASSWORD, DB_HOST, DB_PORT y DB_SERVICE_NAME están definidas.")
        return

    try:
        # La clase OracleADBConnection ahora acepta host, port, service_name
        db = OracleADBConnection(
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"],
            service_name=DB_CONFIG["service_name"]
        )

        logger.info("Intentando establecer conexión...")
        with db.get_connection() as conn:
            logger.info("¡Conexión exitosa!")
            logger.info(f"Versión de Oracle DB: {conn.version}")

        logger.info("La prueba de conexión ha finalizado exitosamente.")

    except Exception as e:
        logger.error(f"Ocurrió un error durante la prueba de conexión: {e}")
        logger.error("Por favor, verifica los siguientes puntos:")
        logger.error("1. Que las credenciales (DB_USER, DB_PASSWORD) son correctas.")
        logger.error("2. Que los detalles de conexión (DB_HOST, DB_PORT, DB_SERVICE_NAME) son correctos y accesibles.")
        logger.error("3. Que no hay firewalls o grupos de seguridad de red bloqueando la conexión al puerto especificado.")


if __name__ == "__main__":
    test_db_connection()