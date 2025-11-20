import logging
from class_adw import OracleADBConnection
from class_vector import CohereOCIEmbedder
from class_llm_grok import GrokOCIAssistant
from config import DB_CONFIG, OCI_CONFIG, TABLE_NAME

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_rag_pipeline():
    """Prueba completa del pipeline RAG"""

    logger.info("Inicializando componentes del sistema RAG...")

    try:
        # Inicializar conexiones
        db = OracleADBConnection(**DB_CONFIG)
        embedder = CohereOCIEmbedder(**OCI_CONFIG)
        grok = GrokOCIAssistant()  # Usa configuración del .env

        logger.info("✓ Componentes inicializados correctamente")

        # Verificar conexión a BD
        with db.get_connection() as conn:
            logger.info(f"✓ Conectado a Oracle DB versión: {conn.version}")

    except Exception as e:
        logger.error(f"Error inicializando componentes: {e}")
        return

    # Consulta de prueba
    query = "¿que es bre-b?"
    logger.info(f"\n{'=' * 60}")
    logger.info(f"CONSULTA: {query}")
    logger.info(f"{'=' * 60}\n")

    try:
        # 1. Vectorizar consulta
        logger.info("1. Generando embedding de la consulta...")
        query_embedding = embedder.embed_text(query)
        query_vector = query_embedding.embeddings[0]
        logger.info(f"✓ Vector generado: {len(query_vector)} dimensiones")

        # 2. Búsqueda vectorial
        logger.info("\n2. Buscando documentos similares...")
        search_results = db.vector_similarity_search_genai(
            query_vector=query_vector,
            top_k=3,
            distance_metric='COSINE',
            table_name=TABLE_NAME
        )

        logger.info(f"✓ Encontrados {len(search_results)} documentos relevantes")

        # Mostrar resultados de búsqueda
        logger.info("\nDocumentos encontrados:")
        for idx, row in search_results.iterrows():
            similarity = 1 - row['distance']
            logger.info(f"  [{idx + 1}] {row['title']} (similitud: {similarity:.3f})")

        # 3. Generar respuesta con Grok
        logger.info("\n3. Generando respuesta con contexto...")

        # Grok ahora acepta DataFrame directamente
        result = grok.structured_answer(
            query=query,
            search_results=search_results,
            model_name="grok-3-mini"
        )

        # Mostrar respuesta
        logger.info("\n" + "=" * 60)
        logger.info("RESPUESTA GENERADA")
        logger.info("=" * 60)
        print(f"\n{result['answer']}\n")
        logger.info("=" * 60)
        logger.info(f"Modelo: {result['model']}")
        logger.info(f"Documentos consultados: {result['num_documents']}")
        logger.info(f"Fuentes: {', '.join(result['documents_used'])}")
        logger.info("=" * 60)

        logger.info("\n✓ Prueba RAG completada exitosamente")

    except Exception as e:
        logger.error(f"Error durante la prueba RAG: {e}")
        raise


if __name__ == "__main__":
    test_rag_pipeline()