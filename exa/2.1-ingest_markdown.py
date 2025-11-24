import os
import json
import logging
from class_adw import OracleADBConnection
from class_vector import CohereOCIEmbedder
from config import DB_CONFIG, OCI_CONFIG, MARKDOWN_DIR, TABLE_NAME, CHUNK_SIZE, CHUNK_OVERLAP, BATCH_SIZE

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Divide el texto en chunks con solapamiento"""
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size

        if end < text_length:
            for delimiter in ['. ', '.\n', '\n\n', '\n']:
                last_delimiter = text.rfind(delimiter, start + chunk_size - 200, end)
                if last_delimiter != -1:
                    end = last_delimiter + len(delimiter)
                    break

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = end - overlap if end < text_length else text_length

    return chunks


def process_and_ingest_files():
    """Procesa archivos markdown y los ingesta en formato GenAI"""
    logger.info("Iniciando proceso de ingesta en formato GenAI...")

    try:
        db = OracleADBConnection(**DB_CONFIG)

        logger.info("Probando conexión a la base de datos...")
        with db.get_connection() as conn:
            logger.info(f"Conexión exitosa a Oracle DB version: {conn.version}")

        embedder = CohereOCIEmbedder(**OCI_CONFIG)
        logger.info("Embedder de Cohere OCI inicializado correctamente.")

    except Exception as e:
        logger.error(f"Error en la inicialización: {e}")
        return

    try:
        files_to_process = [f for f in os.listdir(MARKDOWN_DIR) if f.endswith('.md')]
        if not files_to_process:
            logger.warning(f"No se encontraron archivos .md en el directorio '{MARKDOWN_DIR}'.")
            return
        logger.info(f"Se encontraron {len(files_to_process)} archivos para procesar.")
    except FileNotFoundError:
        logger.error(f"El directorio '{MARKDOWN_DIR}' no existe.")
        return

    total_chunks_inserted = 0
    documents_batch = []

    for filename in files_to_process:
        file_path = os.path.join(MARKDOWN_DIR, filename)
        logger.info(f"Procesando archivo: {filename}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if not content.strip():
                logger.warning(f"El archivo {filename} está vacío. Saltando...")
                continue

            chunks = chunk_text(content)
            logger.info(f"Archivo dividido en {len(chunks)} chunks")

            for idx, chunk in enumerate(chunks, 1):
                try:
                    logger.info(f"Vectorizando chunk {idx}/{len(chunks)} de {filename}...")
                    embedding_response = embedder.embed_text(chunk)
                    vector = embedding_response.embeddings[0]

                    docid = f"{filename}_chunk_{idx}"
                    body = chunk[:4000]
                    title = filename
                    chunk_id = idx

                    metadata = {
                        "source_file": filename,
                        "chunk_index": idx,
                        "total_chunks": len(chunks),
                        "char_count": len(chunk),
                        "embedding_model": OCI_CONFIG["model_id"],
                        "chunk_size": CHUNK_SIZE,
                        "chunk_overlap": CHUNK_OVERLAP
                    }
                    metadata_json = json.dumps(metadata)

                    doc = {
                        'docid': docid,
                        'body': body,
                        'vector': vector,
                        'title': title,
                        'chunk_id': chunk_id,
                        'metadata': metadata_json
                    }
                    documents_batch.append(doc)

                    if len(documents_batch) >= BATCH_SIZE:
                        inserted = db.bulk_insert_genai(documents_batch, TABLE_NAME, BATCH_SIZE)
                        total_chunks_inserted += inserted
                        documents_batch = []

                    logger.info(f"✓ Chunk {idx}/{len(chunks)} de {filename} preparado.")

                except Exception as e:
                    logger.error(f"Error al procesar chunk {idx} del archivo {filename}: {e}")
                    continue

            logger.info(f"✓ Archivo {filename} completado. {len(chunks)} chunks procesados.")

        except Exception as e:
            logger.error(f"Error al procesar el archivo {filename}: {e}")
            continue

    if documents_batch:
        inserted = db.bulk_insert_genai(documents_batch, TABLE_NAME, BATCH_SIZE)
        total_chunks_inserted += inserted

    logger.info(f"Proceso de ingesta finalizado. Total de chunks insertados: {total_chunks_inserted}")

    try:
        stats = db.get_genai_stats(TABLE_NAME)
        logger.info("\n" + "=" * 50)
        logger.info("ESTADÍSTICAS DE LA TABLA GENAI")
        logger.info("=" * 50)
        logger.info(f"Total documentos: {stats['total_documents']}")
        logger.info(f"Archivos únicos: {stats['unique_source_documents']}")
        logger.info(f"Documentos con chunks: {stats['chunked_documents']}")
        logger.info(f"Longitud promedio body: {stats['body_avg_length']:.0f} caracteres")
        logger.info("=" * 50)
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas: {e}")


if __name__ == "__main__":
    process_and_ingest_files()