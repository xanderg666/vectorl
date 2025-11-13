import oci
from typing import List, Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GrokOCIAssistant:
    """Clase para usar modelos Grok de OCI con búsqueda vectorial"""

    def __init__(self, config_file=None, profile=None,
                 compartment_id=None, endpoint=None):
        """Inicializar cliente Grok OCI"""
        # Importar config solo si no se proveen parámetros
        if config_file is None or compartment_id is None or endpoint is None:
            from config import OCI_CONFIG
            config_file = config_file or OCI_CONFIG["config_file"]
            profile = profile or OCI_CONFIG["profile"]
            compartment_id = compartment_id or OCI_CONFIG["compartment_id"]
            endpoint = endpoint or OCI_CONFIG["endpoint"]

        self.config = oci.config.from_file(config_file, profile)
        self.client = oci.generative_ai_inference.GenerativeAiInferenceClient(
            config=self.config,
            service_endpoint=endpoint,
            retry_strategy=oci.retry.NoneRetryStrategy(),
            timeout=(15, 300)
        )
        self.compartment_id = compartment_id

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

    def generate_response(self, prompt: str, model_name: str = "grok-3-mini",
                          system_prompt: Optional[str] = None,
                          max_tokens: Optional[int] = None,
                          temperature: Optional[float] = None) -> str:
        """Generar respuesta usando el modelo Grok"""
        try:
            model_id = self.models.get(model_name, self.models["grok-3-mini"])
            config = self.model_configs.get(model_name, self.model_configs["grok-3-mini"])

            messages = []

            if system_prompt:
                system_msg = oci.generative_ai_inference.models.Message()
                system_msg.role = "SYSTEM"
                system_msg.content = [
                    oci.generative_ai_inference.models.TextContent(text=system_prompt)
                ]
                messages.append(system_msg)

            user_msg = oci.generative_ai_inference.models.Message()
            user_msg.role = "USER"
            user_msg.content = [
                oci.generative_ai_inference.models.TextContent(text=prompt)
            ]
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
                            model_name: str = "grok-3-mini",
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
                          model_name: str = "grok-3-mini") -> Dict[str, Any]:
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