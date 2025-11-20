import oracledb
import pandas as pd
import array
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OracleADBConnection:
    """Clase para manejar conexiones a Oracle Autonomous Database"""
    
    def __init__(self, user: str, password: str, dsn: str, **kwargs):
        """
        Inicializar conexión a Oracle Database
        
        Args:
            user: Usuario de la base de datos
            password: Contraseña
            dsn: Cadena de conexión completa (connection string)
        """
        self.user = user
        self.password = password
        self.dsn = dsn
        self.connection = None
        
        logger.info(f"✓ Conexión configurada para usuario: {user}")

    def connect(self):
        """Establecer conexiÃ³n a la base de datos"""
        try:
            self.connection = oracledb.connect(
                user=self.user,
                password=self.password,
                dsn=self.dsn
            )
            logger.info("âœ“ ConexiÃ³n establecida exitosamente")
            return self.connection
        except oracledb.Error as e:
            logger.error(f"Error al conectar: {e}")
            raise

    def disconnect(self):
        """Cerrar conexiÃ³n"""
        if self.connection:
            self.connection.close()
            logger.info("âœ“ ConexiÃ³n cerrada")
            self.connection = None

    @contextmanager
    def get_connection(self):
        """Context manager para manejar conexiones automÃ¡ticamente"""
        conn = None
        try:
            conn = oracledb.connect(
                user=self.user,
                password=self.password,
                dsn=self.dsn
            )
            yield conn
        except oracledb.Error as e:
            logger.error(f"Error en la conexiÃ³n: {e}")
            raise
        finally:
            if conn:
                conn.close()

    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[tuple]:
        """Ejecutar una consulta SELECT"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            return results

    def execute_query_df(self, query: str, params: Optional[Dict] = None) -> pd.DataFrame:
        """Ejecutar consulta y retornar DataFrame"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            columns = [col[0].lower() for col in cursor.description]
            results = []

            for row in cursor.fetchall():
                row_data = []
                for item in row:
                    if hasattr(item, 'read'):
                        row_data.append(item.read())
                    else:
                        row_data.append(item)
                results.append(tuple(row_data))

            cursor.close()
            return pd.DataFrame(results, columns=columns)

    def execute_dml(self, query: str, params: Optional[Dict] = None, commit: bool = True) -> int:
        """Ejecutar INSERT, UPDATE, DELETE"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            rows_affected = cursor.rowcount

            if commit:
                conn.commit()

            cursor.close()
            return rows_affected

    # ==================== FUNCIONES VECTORIALES GENAI ====================

    def insert_vector_document_genai(self, docid: str, body: str, vector: List[float],
                                     title: str = None, url: str = None,
                                     chunk_id: int = None, page_numbers: str = None,
                                     metadata: str = None, table_name: str = None) -> int:
        """Insertar documento con vector embedding en formato GenAI"""
        if table_name is None:
            raise ValueError("table_name es requerido")

        with self.get_connection() as conn:
            cursor = conn.cursor()

            body_truncated = body[:4000] if len(body) > 4000 else body
            vector_array = array.array('f', vector)

            columns = ['docid', 'body', 'vector']
            values = [docid, body_truncated, vector_array]
            placeholders = [':1', ':2', ':3']
            param_count = 3

            if title:
                param_count += 1
                columns.append('title')
                values.append(title)
                placeholders.append(f':{param_count}')

            if url:
                param_count += 1
                columns.append('url')
                values.append(url)
                placeholders.append(f':{param_count}')

            if chunk_id is not None:
                param_count += 1
                columns.append('chunk_id')
                values.append(chunk_id)
                placeholders.append(f':{param_count}')

            if page_numbers:
                param_count += 1
                columns.append('page_numbers')
                values.append(page_numbers)
                placeholders.append(f':{param_count}')

            if metadata:
                param_count += 1
                columns.append('metadata')
                values.append(metadata)
                placeholders.append(f':{param_count}')

            query = f"""
                INSERT INTO {table_name} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
            """

            cursor.execute(query, values)
            conn.commit()
            rows_affected = cursor.rowcount
            cursor.close()
            return rows_affected

    def bulk_insert_genai(self, documents: List[Dict[str, Any]],
                          table_name: str = None,
                          batch_size: int = 100) -> int:
        """InserciÃ³n masiva de documentos en formato GenAI"""
        if table_name is None:
            raise ValueError("table_name es requerido")

        total_inserted = 0

        with self.get_connection() as conn:
            cursor = conn.cursor()

            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]

                for doc in batch:
                    try:
                        docid = doc['docid']
                        body = doc['body'][:4000]
                        vector = array.array('f', doc['vector'])

                        title = doc.get('title')
                        url = doc.get('url')
                        chunk_id = doc.get('chunk_id')
                        page_numbers = doc.get('page_numbers')
                        metadata = doc.get('metadata')

                        columns = ['docid', 'body', 'vector']
                        values = [docid, body, vector]
                        placeholders = [':1', ':2', ':3']
                        param_count = 3

                        if title:
                            param_count += 1
                            columns.append('title')
                            values.append(title)
                            placeholders.append(f':{param_count}')

                        if url:
                            param_count += 1
                            columns.append('url')
                            values.append(url)
                            placeholders.append(f':{param_count}')

                        if chunk_id is not None:
                            param_count += 1
                            columns.append('chunk_id')
                            values.append(chunk_id)
                            placeholders.append(f':{param_count}')

                        if page_numbers:
                            param_count += 1
                            columns.append('page_numbers')
                            values.append(page_numbers)
                            placeholders.append(f':{param_count}')

                        if metadata:
                            param_count += 1
                            columns.append('metadata')
                            values.append(metadata)
                            placeholders.append(f':{param_count}')

                        query = f"""
                            INSERT INTO {table_name} ({', '.join(columns)})
                            VALUES ({', '.join(placeholders)})
                        """

                        cursor.execute(query, values)
                        total_inserted += 1

                    except Exception as e:
                        logger.error(f"Error insertando documento {doc.get('docid', 'unknown')}: {e}")
                        continue

                conn.commit()
                logger.info(f"Batch {i // batch_size + 1}: {len(batch)} documentos procesados")

            cursor.close()

        logger.info(f"âœ“ Total insertado: {total_inserted} documentos")
        return total_inserted

    def vector_similarity_search_genai(self, query_vector: List[float],
                                       top_k: int = 5,
                                       distance_metric: str = 'COSINE',
                                       filter_conditions: str = None,
                                       table_name: str = None) -> pd.DataFrame:
        """BÃºsqueda por similitud vectorial en tabla GenAI"""
        if table_name is None:
            raise ValueError("table_name es requerido")

        vector_array = array.array('f', query_vector)

        base_query = f"""
            SELECT docid, body, title, url, chunk_id, page_numbers, metadata,
                   VECTOR_DISTANCE(vector, :1, {distance_metric}) as distance
            FROM {table_name}
        """

        if filter_conditions:
            query = f"{base_query} WHERE {filter_conditions} ORDER BY distance FETCH FIRST :2 ROWS ONLY"
        else:
            query = f"{base_query} ORDER BY distance FETCH FIRST :2 ROWS ONLY"

        return self.execute_query_df(query, [vector_array, top_k])

    def get_genai_stats(self, table_name: str = None) -> Dict[str, Any]:
        """Obtener estadÃ­sticas de la tabla GenAI"""
        if table_name is None:
            raise ValueError("table_name es requerido")

        with self.get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            total_docs = cursor.fetchone()[0]

            cursor.execute(f"""
                SELECT 
                    COUNT(DISTINCT REGEXP_SUBSTR(docid, '^[^_]+')) as unique_docs,
                    COUNT(CASE WHEN chunk_id IS NOT NULL THEN 1 END) as chunked_docs
                FROM {table_name}
            """)
            doc_stats = cursor.fetchone()

            cursor.execute(f"""
                SELECT 
                    AVG(LENGTH(body)) as avg_length,
                    MAX(LENGTH(body)) as max_length,
                    MIN(LENGTH(body)) as min_length
                FROM {table_name}
            """)
            content_stats = cursor.fetchone()

            cursor.close()

            return {
                'total_documents': total_docs,
                'unique_source_documents': doc_stats[0] if doc_stats[0] else 0,
                'chunked_documents': doc_stats[1] if doc_stats[1] else 0,
                'body_avg_length': float(content_stats[0]) if content_stats[0] else 0,
                'body_max_length': content_stats[1] if content_stats[1] else 0,
                'body_min_length': content_stats[2] if content_stats[2] else 0
            }

    def vector_similarity_search(self, table_name: str, query_vector: List[float],
                                 top_k: int = 5, distance_metric: str = 'COSINE',
                                 return_columns: List[str] = None) -> pd.DataFrame:
        """MÃ©todo original mantenido para compatibilidad"""
        if return_columns is None:
            return_columns = ['id', 'nombre_archivo', 'contenido', 'metadata', 'fecha_creacion']

        columns_str = ', '.join(return_columns)
        vector_array = array.array('f', query_vector)

        query = f"""
            SELECT {columns_str},
                   VECTOR_DISTANCE(vector, :1, {distance_metric}) as distance
            FROM {table_name}
            ORDER BY distance
            FETCH FIRST :2 ROWS ONLY
        """

        return self.execute_query_df(query, [vector_array, top_k])