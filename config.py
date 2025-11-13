import os
from dotenv import load_dotenv

load_dotenv()

# Database Configuration
DB_CONFIG = {
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", "1522")), # Default to 1522 if not set
    "service_name": os.getenv("DB_SERVICE_NAME")
}

# OCI Configuration
OCI_CONFIG = {
    "config_file": os.getenv("OCI_CONFIG_FILE", "~/.oci/config"),
    "profile": os.getenv("OCI_PROFILE", "DEFAULT"),
    "compartment_id": os.getenv("OCI_COMPARTMENT_ID"),
    "endpoint": os.getenv("OCI_ENDPOINT"),
    "model_id": os.getenv("OCI_EMBED_MODEL_ID")
}

# Application Configuration
MARKDOWN_DIR = os.getenv("MARKDOWN_DIR", "md")
TABLE_NAME = os.getenv("TABLE_NAME", "documentos_vectoriales_genai")
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "50"))