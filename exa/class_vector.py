import oci
from oci.generative_ai_inference import GenerativeAiInferenceClient
from oci.generative_ai_inference.models import EmbedTextDetails, OnDemandServingMode
from oci.auth.signers import InstancePrincipalsSecurityTokenSigner

class CohereOCIEmbedder:
    def __init__(self, config_file="~/.oci/config", profile="DEFAULT", compartment_id=None, 
                 endpoint=None, model_id=None, use_instance_principal=False):
        """
        Inicializa el embedder de Cohere en OCI
        
        Args:
            config_file: Ruta al archivo de configuración OCI
            profile: Perfil a usar del config file
            compartment_id: OCID del compartment
            endpoint: Endpoint del servicio GenAI
            model_id: ID del modelo de embedding
            use_instance_principal: Si True, usa Instance Principal en lugar de config file
        """
        self.compartment_id = compartment_id
        self.model_id = model_id
        
        # Configurar autenticación
        if use_instance_principal:
            # Usar Instance Principal (para VMs en OCI)
            signer = InstancePrincipalsSecurityTokenSigner()
            self.client = GenerativeAiInferenceClient(
                config={'region': 'us-chicago-1'},  # Ajustar región según necesidad
                signer=signer,
                service_endpoint=endpoint
            )
        else:
            # Usar archivo de configuración tradicional
            self.config = oci.config.from_file(config_file, profile)
            self.client = GenerativeAiInferenceClient(
                config=self.config, 
                service_endpoint=endpoint
            )

    def embed_text(self, text):
        """
        Genera embedding para un texto
        
        Args:
            text: Texto a vectorizar
            
        Returns:
            Response con el embedding generado
        """
        embed_text_detail = EmbedTextDetails()
        embed_text_detail.serving_mode = OnDemandServingMode(model_id=self.model_id)
        embed_text_detail.inputs = [text]
        embed_text_detail.truncate = "NONE"
        embed_text_detail.compartment_id = self.compartment_id
        
        response = self.client.embed_text(embed_text_detail)
        return response.data  # contiene la lista de vectores embeddings