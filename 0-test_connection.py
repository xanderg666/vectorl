import logging
from class_adw import OracleADBConnection
from config import DB_CONFIG
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_db_connection():
    """Prueba la conexión a la base de datos Oracle ADB usando una wallet."""
    logger.info("Iniciando prueba de conexión a la base de datos con wallet...")

    if not os.path.isdir(DB_CONFIG["config_dir"]):
        wallet_path = os.path.abspath(DB_CONFIG['config_dir'])
        logger.error(f"El directorio de la wallet '{wallet_path}' no fue encontrado.")
        logger.error("Asegúrate de que la wallet está en el lugar correcto.")
        return

    try:
        db = OracleADBConnection(**DB_CONFIG)

        logger.info("Intentando establecer conexión...")
        with db.get_connection() as conn:
            logger.info(f"¡Conexión exitosa!")
            logger.info(f"Versión de Oracle DB: {conn.version}")

        logger.info("La prueba de conexión ha finalizado exitosamente.")

    except Exception as e:
        logger.error(f"Ocurrió un error durante la prueba de conexión: {e}")
        logger.error("Por favor, verifica los siguientes puntos:")
        logger.error("1. Que las credenciales (usuario/contraseña) son correctas.")
        logger.error("2. Que el DSN es correcto.")
        logger.error("3. Que el contenido del directorio de la wallet es válido.")


if __name__ == "__main__":
    test_db_connection()