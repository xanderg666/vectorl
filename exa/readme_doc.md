# Oracle Vector RAG System

Sistema de Retrieval-Augmented Generation (RAG) usando Oracle Autonomous Database 23ai con búsqueda vectorial y modelos Grok de OCI.

## Características

- **Embeddings vectoriales** con Cohere via OCI GenAI
- **Búsqueda semántica** usando vectores de 1536 dimensiones
- **Chunking inteligente** de documentos Markdown con solapamiento
- **Almacenamiento optimizado** en Oracle 23ai con índices vectoriales HNSW
- **Generación de respuestas** usando modelos Grok (grok-3, grok-4)
- **Configuración centralizada** mediante variables de entorno

## Requisitos

- Python 3.8+
- Oracle Autonomous Database 23ai
- OCI Account con acceso a GenAI
- Wallet de conexión a Oracle ADB

## Instalación

```bash
# Clonar repositorio
git clone <repository-url>
cd <project-directory>

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales
```

## Configuración

### 1. Archivo `.env`

```env
# Database Configuration
DB_USER=agente
DB_PASSWORD=tu_password
DB_CONFIG_DIR=/ruta/a/wallet
DB_WALLET_LOCATION=/ruta/a/wallet
DB_WALLET_PASSWORD=wallet_password
DB_DSN=agent_medium

# OCI Configuration
OCI_CONFIG_FILE=~/.oci/config
OCI_PROFILE=DEFAULT
OCI_COMPARTMENT_ID=ocid1.compartment.oc1...
OCI_ENDPOINT=https://inference.generativeai.us-chicago-1.oci.oraclecloud.com
OCI_EMBED_MODEL_ID=cohere.embed-v4.0

# Application Configuration
MARKDOWN_DIR=md
TABLE_NAME=documentos_vectoriales_genai
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
BATCH_SIZE=50
```

### 2. Wallet de Oracle

1. Descarga el wallet desde OCI Console
2. Extrae el contenido en el directorio especificado en `DB_WALLET_LOCATION`
3. Verifica que `tnsnames.ora` contenga el DSN configurado

### 3. Configuración OCI

Configura tu archivo `~/.oci/config`:

```ini
[DEFAULT]
user=ocid1.user.oc1...
fingerprint=aa:bb:cc...
tenancy=ocid1.tenancy.oc1...
region=us-chicago-1
key_file=~/.oci/oci_api_key.pem
```

## Uso

### 1. Probar conexión

```bash
python 0-test_connection.py
```

### 2. Crear tabla vectorial

1- crear el usuario




```bash
python 1-create_vector_table.py
```

Crea la tabla con estructura:
- `id`: Primary key autoincremental
- `docid`: Identificador único del documento/chunk
- `body`: Contenido del documento (CLOB, máx 4000 chars)
- `vector`: Vector embedding (1536 dimensiones, FLOAT32)
- `title`: Título del documento
- `chunk_id`: Número de chunk
- `metadata`: Metadatos en formato JSON
- Índice vectorial HNSW con COSINE distance

### 3. Ingestar documentos

```bash
# Colocar archivos .md en el directorio especificado (default: ./md)
python 2-ingest_markdown.py
```

Proceso:
1. Lee archivos Markdown del directorio `MARKDOWN_DIR`
2. Divide en chunks con solapamiento configurable
3. Genera embeddings usando Cohere via OCI
4. Inserta en lotes en la base de datos
5. Muestra estadísticas finales

### 4. Búsqueda y generación de respuestas

```python
from class_adw import OracleADBConnection
from class_vector import CohereOCIEmbedder
from class_llm_grok import GrokOCIAssistant
from config import DB_CONFIG, OCI_CONFIG, TABLE_NAME

# Inicializar
db = OracleADBConnection(**DB_CONFIG)
embedder = CohereOCIEmbedder(**OCI_CONFIG)
grok = GrokOCIAssistant(**OCI_CONFIG)

# Consulta del usuario
query = "¿Cómo configurar Oracle Vector Search?"

# Generar embedding de la consulta
query_embedding = embedder.embed_text(query).embeddings[0]

# Búsqueda vectorial
results = db.vector_similarity_search_genai(
    query_vector=query_embedding,
    top_k=5,
    distance_metric='COSINE',
    table_name=TABLE_NAME
)

# Generar respuesta con contexto
response = grok.answer_with_context(
    query=query,
    search_results=results,
    model_name="grok-3-mini"
)

print(response['answer'])
```

## Estructura del Proyecto

```
.
├── .env                      # Variables de entorno (NO versionar)
├── config.py                 # Carga configuración desde .env
├── class_adw.py             # Clase para conexión Oracle ADB
├── class_vector.py          # Clase para embeddings Cohere
├── class_llm_grok.py        # Clase para modelos Grok
├── 0-test_connection.py     # Script de prueba de conexión
├── create_vector_table.py   # Script para crear tabla vectorial
├── ingest_markdown.py       # Script para ingestar documentos
├── requirements.txt         # Dependencias Python
├── wallet/                  # Directorio para wallet Oracle (NO versionar)
└── md/                      # Directorio para archivos Markdown
```

## Modelos Disponibles

### Embeddings
- **cohere.embed-v4.0**: 1536 dimensiones (recomendado)

### Generación (Grok)
- **grok-3**: 4000 tokens, uso general
- **grok-3-mini**: 3000 tokens, rápido y eficiente
- **grok-3-mini-fast**: 2500 tokens, máxima velocidad
- **grok-3-fast**: 3000 tokens, balance velocidad/calidad
- **grok-4**: 20000 tokens, máxima capacidad

## Métricas de Distancia

- **COSINE**: Similitud angular (recomendado para texto)
- **EUCLIDEAN**: Distancia euclidiana
- **DOT**: Producto punto

## API Reference

### OracleADBConnection

```python
# Insertar documento individual
db.insert_vector_document_genai(
    docid="doc_1",
    body="contenido",
    vector=[0.1, 0.2, ...],
    title="Mi Documento",
    metadata='{"key": "value"}',
    table_name="mi_tabla"
)

# Inserción en lote
db.bulk_insert_genai(
    documents=[{
        'docid': 'doc_1',
        'body': 'contenido',
        'vector': [0.1, 0.2, ...],
        'title': 'título',
        'metadata': '{}'
    }],
    table_name="mi_tabla",
    batch_size=50
)

# Búsqueda vectorial
results = db.vector_similarity_search_genai(
    query_vector=[0.1, 0.2, ...],
    top_k=5,
    distance_metric='COSINE',
    filter_conditions="chunk_id > 10",
    table_name="mi_tabla"
)

# Estadísticas
stats = db.get_genai_stats(table_name="mi_tabla")
```

### GrokOCIAssistant

```python
# Respuesta simple
response = grok.generate_response(
    prompt="¿Qué es RAG?",
    model_name="grok-3-mini",
    system_prompt="Eres un experto en IA"
)

# Respuesta con contexto RAG
response = grok.answer_with_context(
    query="¿Cómo usar vectores?",
    search_results=df_results,
    model_name="grok-3-mini"
)

# Respuesta estructurada
response = grok.structured_answer(
    query="Explica vector search",
    search_results=df_results
)
```


# conexion a RAG en OCI

crear una conexion ewallet.p12 en el vault PKCS12

## Troubleshooting

### Error DPY-4000
Verifica que el DSN en `.env` coincida con los nombres en `wallet/tnsnames.ora`

### Error de conexión a OCI
Verifica credenciales en `~/.oci/config` y permisos en el compartment

### Embeddings fallan
Confirma que el modelo está disponible en tu región de OCI

### Tabla no existe
Ejecuta `create_vector_table.py` antes de `ingest_markdown.py`

## Seguridad

- Nunca versionar `.env` ni `wallet/` (agregar a `.gitignore`)
- Rotar credenciales periódicamente
- Usar permisos mínimos necesarios en Oracle y OCI
- Encriptar backups que contengan datos sensibles

## Licencia

[Especificar licencia]

## Contribuciones

[Especificar proceso de contribución]

## Contacto

[Información de contacto]