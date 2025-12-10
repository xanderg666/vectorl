import oci
from oci.auth.signers import InstancePrincipalsSecurityTokenSigner
from typing import List, Dict, Any, Optional
import logging
import sys
import os
import base64
import io
import json
import fitz
from PIL import Image

# Add parent directory to path to allow importing config if needed
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GrokOCIAssistant:
    """Clase para usar modelos Grok de OCI con búsqueda vectorial"""

    def __init__(self, config_file=None, profile=None,
                 compartment_id=None, endpoint=None, use_instance_principal=False):
        """Inicializar cliente Grok OCI"""
    def __init__(self, config_file=None, profile=None,
                 compartment_id=None, endpoint=None, use_instance_principal=None):
        """Inicializar cliente Grok OCI"""
        
        # Cargar variables de entorno desde ../.env
        try:
            from dotenv import load_dotenv
            env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
            load_dotenv(env_path)
            logger.info(f"Cargando configuración desde {env_path}")
        except ImportError:
            logger.warning("python-dotenv no está instalado. Asegúrese de que las variables de entorno estén configuradas.")

        # Prioridad: Argumentos > Variables de Entorno > Config por defecto
        self.compartment_id = compartment_id or os.getenv("OCI_COMPARTMENT_ID")
        endpoint = endpoint or os.getenv("OCI_ENDPOINT")
        config_file = config_file or os.getenv("OCI_CONFIG_FILE", "~/.oci/config")
        profile = profile or os.getenv("OCI_PROFILE", "DEFAULT")
        
        # Determinar si usar Instance Principal
        if use_instance_principal is None:
            use_ip_env = os.getenv("USE_INSTANCE_PRINCIPAL", "false").lower()
            use_instance_principal = use_ip_env == "true"

        if not self.compartment_id:
            logger.warning("Compartment ID no encontrado. Asegúrese de configurarlo en .env o pasarlo como argumento.")

        # Configurar autenticación
        if use_instance_principal:
            # Usar Instance Principal
            try:
                signer = InstancePrincipalsSecurityTokenSigner()
                self.client = oci.generative_ai_inference.GenerativeAiInferenceClient(
                    config={'region': 'us-chicago-1'},  # Ajustar región según necesidad
                    signer=signer,
                    service_endpoint=endpoint,
                    retry_strategy=oci.retry.NoneRetryStrategy(),
                    timeout=(15, 300)
                )
                logger.info("Autenticado usando Instance Principal")
            except Exception as e:
                logger.error(f"Error al autenticar con Instance Principal: {e}")
                raise
        else:
            # Usar archivo de configuración tradicional
            try:
                self.config = oci.config.from_file(config_file, profile)
                self.client = oci.generative_ai_inference.GenerativeAiInferenceClient(
                    config=self.config,
                    service_endpoint=endpoint,
                    retry_strategy=oci.retry.NoneRetryStrategy(),
                    timeout=(15, 300)
                )
                logger.info(f"Autenticado usando config file: {config_file} profile: {profile}")
            except Exception as e:
                logger.error(f"Error al autenticar con archivo de configuración: {e}")
                raise

        self.models = {
            "grok-3": "ocid1.generativeaimodel.oc1.us-chicago-1.amaaaaaask7dceya6dvgvvj3ovy4lerdl6fvx525x3yweacnrgn4ryfwwcoq",
            "grok-3-mini": "ocid1.generativeaimodel.oc1.us-chicago-1.amaaaaaask7dceyavwbgai5nlntsd5hngaileroifuoec5qxttmydhq7mykq",
            "grok-3-mini-fast": "ocid1.generativeaimodel.oc1.us-chicago-1.amaaaaaask7dceyaoukpjdotfk5fmhkps63szixxhfiyfamurrzkqea7sjva",
            "grok-3-fast": "ocid1.generativeaimodel.oc1.us-chicago-1.amaaaaaask7dceyat326ygnn5hesfplopdmkyrklzcehzxhk5262655bthjq",
            "grok-4": "ocid1.generativeaimodel.oc1.us-chicago-1.amaaaaaask7dceya3bsfz4ogiuv3yc7gcnlry7gi3zzx6tnikg6jltqszm2q"
        }

        self.model_configs = {
            "grok-3": {"max_tokens": 4000, "temperature": 0.7, "top_p": 0.9},
            "grok-3-mini": {"max_tokens": 3000, "temperature": 0.7, "top_p": 0.9},
            "grok-3-mini-fast": {"max_tokens": 2500, "temperature": 0.7, "top_p": 0.9},
            "grok-3-fast": {"max_tokens": 3000, "temperature": 0.7, "top_p": 0.9},
            "grok-4": {"max_tokens": 20000, "temperature": 1.0, "top_p": 1.0}
        }

    def process_pdf(self, file_path: str) -> List[str]:
        """
        Procesa un archivo PDF y convierte sus páginas a imágenes base64.
        """
        images_base64 = []
        try:
            pdf_document = fitz.open(file_path)
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                pix = page.get_pixmap(dpi=300, colorspace="rgb")
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=95, optimize=True)
                buffer.seek(0)
                
                img_str = base64.b64encode(buffer.read()).decode('utf-8')
                images_base64.append(img_str)
            
            pdf_document.close()
            return images_base64
        except Exception as e:
            logger.error(f"Error procesando PDF {file_path}: {e}")
            return []

    def process_image(self, file_path: str) -> Optional[str]:
        """
        Procesa una imagen y la convierte a base64.
        """
        try:
            with Image.open(file_path) as img:
                if img.mode == 'RGBA':
                    img = img.convert('RGB')
                
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG", quality=95, optimize=True)
                buffer.seek(0)
                
                return base64.b64encode(buffer.read()).decode('utf-8')
        except Exception as e:
            logger.error(f"Error procesando imagen {file_path}: {e}")
            return None

    def read_text_file(self, file_path: str) -> str:
        """
        Lee el contenido de archivos de texto (.txt, .md, .json).
        """
        try:
            ext = os.path.splitext(file_path)[1].lower()
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            if ext == '.json':
                try:
                    # Formatear JSON para mejor legibilidad
                    json_obj = json.loads(content)
                    return json.dumps(json_obj, indent=2, ensure_ascii=False)
                except json.JSONDecodeError:
                    return content
            return content
        except Exception as e:
            logger.error(f"Error leyendo archivo de texto {file_path}: {e}")
            return ""

    def generate_response(self, prompt: str, model_name: str = "grok-4",
                          system_prompt: Optional[str] = None,
                          max_tokens: Optional[int] = None,
                          temperature: Optional[float] = None,
                          images: Optional[List[str]] = None,
                          files: Optional[List[str]] = None) -> str:
        """
        Generar respuesta usando el modelo Grok
        
        Args:
            prompt: Texto del prompt
            model_name: Nombre del modelo
            system_prompt: Prompt del sistema opcional
            max_tokens: Máximo de tokens
            temperature: Temperatura
            images: Lista de rutas a archivos de imagen (para modelos multimodales) - DEPRECATED, use files
            files: Lista de rutas a archivos (imágenes, PDFs, texto, JSON, MD)
        """
        try:
            model_id = self.models.get(model_name, self.models["grok-4"])
            config = self.model_configs.get(model_name, self.model_configs["grok-4"])

            # Combinar images y files
            all_files = []
            if images:
                all_files.extend(images)
            if files:
                all_files.extend(files)
            
            # Eliminar duplicados preservando orden
            all_files = list(dict.fromkeys(all_files))

            messages = []
            
            # Procesar archivos de texto para contexto adicional
            context_content = ""
            processed_images = []
            
            if all_files:
                for file_path in all_files:
                    ext = os.path.splitext(file_path)[1].lower()
                    
                    # Archivos visuales
                    if ext == '.pdf':
                        pdf_images = self.process_pdf(file_path)
                        processed_images.extend(pdf_images)
                    elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp']:
                        img_data = self.process_image(file_path)
                        if img_data:
                            processed_images.append(img_data)
                    
                    # Archivos de texto
                    elif ext in ['.txt', '.md', '.json']:
                        text_content = self.read_text_file(file_path)
                        if text_content:
                            filename = os.path.basename(file_path)
                            context_content += f"\n\n--- CONTENIDO DE {filename} ---\n{text_content}\n"
                    
                    else:
                        logger.warning(f"Formato de archivo no soportado: {file_path}")

            # Construir System Prompt
            final_system_prompt = system_prompt or ""
            if context_content:
                final_system_prompt += f"\n\nTIENES ACCESO A LOS SIGUIENTES ARCHIVOS COMO CONTEXTO:{context_content}"

            if final_system_prompt:
                system_msg = oci.generative_ai_inference.models.Message()
                system_msg.role = "SYSTEM"
                system_msg.content = [
                    oci.generative_ai_inference.models.TextContent(text=final_system_prompt)
                ]
                messages.append(system_msg)

            user_msg = oci.generative_ai_inference.models.Message()
            user_msg.role = "USER"
            
            content_list = [oci.generative_ai_inference.models.TextContent(text=prompt)]
            
            # Agregar imágenes procesadas al contenido
            for img_b64 in processed_images:
                try:
                    # Crear ImageContent
                    image_content = oci.generative_ai_inference.models.ImageContent(
                        data=img_b64.encode('utf-8') if isinstance(img_b64, str) else img_b64,
                        format="jpeg"
                    )
                    content_list.append(image_content)
                except Exception as e:
                    logger.error(f"Error al crear objeto ImageContent: {e}")

            user_msg.content = content_list
            messages.append(user_msg)

            chat_request = oci.generative_ai_inference.models.GenericChatRequest()
            chat_request.api_format = oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_GENERIC
            chat_request.messages = messages
            chat_request.max_tokens = max_tokens or config["max_tokens"]
            chat_request.temperature = temperature or config["temperature"]
            chat_request.top_p = config["top_p"]

            chat_detail = oci.generative_ai_inference.models.ChatDetails()
            chat_detail.serving_mode = oci.generative_ai_inference.models.OnDemandServingMode(
                model_id=model_id
            )
            chat_detail.chat_request = chat_request
            chat_detail.compartment_id = self.compartment_id

            response = self.client.chat(chat_detail)
            return response.data.chat_response.choices[0].message.content[0].text

        except Exception as e:
            logger.error(f"Error generando respuesta: {e}")
            raise

    def answer_with_context(self, query: str, search_results: List[Dict[str, Any]],
                            model_name: str = "grok-4",
                            custom_system_prompt: Optional[str] = None) -> Dict[str, Any]:
        """
        Responder pregunta usando resultados de búsqueda vectorial como contexto

        Args:
            query: Pregunta del usuario
            search_results: DataFrame o lista de dicts con campos: title, body, docid, distance
            model_name: Modelo a usar
            custom_system_prompt: System prompt personalizado
        """
        try:
            context_parts = []

            # Convertir DataFrame a lista si es necesario
            if hasattr(search_results, 'iterrows'):
                results_list = []
                for idx, row in search_results.iterrows():
                    results_list.append({
                        'title': row.get('title', row.get('docid', 'Unknown')),
                        'body': row.get('body', ''),
                        'distance': row.get('distance', 0)
                    })
                search_results = results_list

            # Construir contexto
            for i, result in enumerate(search_results, 1):
                similarity = 1 - result.get('distance', 0)
                doc_title = result.get('title', result.get('docid', 'Unknown'))
                doc_content = result.get('body', result.get('contenido', ''))

                context_parts.append(
                    f"[Documento {i}: {doc_title} - Similitud: {similarity:.3f}]\n"
                    f"{doc_content}\n"
                )

            context = "\n---\n".join(context_parts)

            # System prompt
            if not custom_system_prompt:
                custom_system_prompt = """Eres un asistente experto que responde preguntas basándose en documentación proporcionada.

INSTRUCCIONES:
1. Usa SOLO la información de los documentos proporcionados
2. Si la información no está en los documentos, indícalo claramente
3. Cita los documentos relevantes cuando sea apropiado
4. Proporciona respuestas estructuradas y completas
5. Si encuentras información contradictoria, menciónalo"""

            # Prompt completo
            prompt = f"""Basándote en los siguientes documentos, responde la pregunta del usuario.

DOCUMENTOS RELEVANTES:
{context}

PREGUNTA DEL USUARIO:
{query}

RESPUESTA:"""

            # Generar respuesta
            response = self.generate_response(
                prompt=prompt,
                model_name=model_name,
                system_prompt=custom_system_prompt
            )

            # Extraer títulos para metadata
            doc_titles = []
            for r in search_results:
                title = r.get('title', r.get('docid', r.get('nombre_archivo', 'Unknown')))
                doc_titles.append(title)

            return {
                'answer': response,
                'query': query,
                'model': model_name,
                'num_documents': len(search_results),
                'documents_used': doc_titles
            }

        except Exception as e:
            logger.error(f"Error generando respuesta con contexto: {e}")
            raise

    def structured_answer(self, query: str, search_results: List[Dict[str, Any]],
                          model_name: str = "grok-4") -> Dict[str, Any]:
        """Generar respuesta estructurada con secciones específicas"""
        system_prompt = """Eres un asistente experto que proporciona respuestas estructuradas.

Estructura tu respuesta en las siguientes secciones:

## RESUMEN
[Respuesta concisa en 2-3 oraciones]

## DETALLES
[Información detallada y relevante]

## PUNTOS CLAVE
- [Punto importante 1]
- [Punto importante 2]
- [Punto importante 3]

## FUENTES CONSULTADAS
[Lista de documentos utilizados]"""

        return self.answer_with_context(
            query=query,
            search_results=search_results,
            model_name=model_name,
            custom_system_prompt=system_prompt
        )
