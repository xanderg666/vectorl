import oci
from oci.generative_ai_inference import GenerativeAiInferenceClient
from oci.generative_ai_inference.models import EmbedTextDetails, OnDemandServingMode

class CohereOCIEmbedder:
    def __init__(self, config_file="~/.oci/config", profile="DEFAULT", compartment_id=None, endpoint=None, model_id=None):
        self.config = oci.config.from_file(config_file, profile)
        self.client = GenerativeAiInferenceClient(config=self.config, service_endpoint=endpoint)
        self.compartment_id = compartment_id
        self.model_id = model_id

    def embed_text(self, text):
        embed_text_detail = EmbedTextDetails()
        embed_text_detail.serving_mode = OnDemandServingMode(model_id=self.model_id)
        embed_text_detail.inputs = [text]
        embed_text_detail.truncate = "NONE"
        embed_text_detail.compartment_id = self.compartment_id
        
        response = self.client.embed_text(embed_text_detail)
        return response.data  # contiene la lista de vectores embeddings


