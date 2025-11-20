#!/usr/bin/env python3
"""
Test básico de embeddings con Instance Principal
Vectoriza la palabra "hola" usando Cohere en OCI
"""
import oci
from oci.auth.signers import InstancePrincipalsSecurityTokenSigner
from oci.generative_ai_inference import GenerativeAiInferenceClient
from oci.generative_ai_inference.models import EmbedTextDetails, OnDemandServingMode

# Configuración
COMPARTMENT_ID = "ocid1.compartment.oc1..aaaaaaaadrmmiknudkmzomyaqwmm6js7ed4sj23jkw7w7ugzgm7cdedsfcua"
ENDPOINT = "https://inference.generativeai.us-chicago-1.oci.oraclecloud.com"
MODEL_ID = "cohere.embed-v4.0"

print("=" * 60)
print("🧮 TEST DE EMBEDDINGS CON INSTANCE PRINCIPAL")
print("=" * 60)

try:
    # 1. Autenticación con Instance Principal
    print("\n🔐 Autenticando con Instance Principal...")
    signer = InstancePrincipalsSecurityTokenSigner()
    print("✅ Instance Principal configurado")
    
    # 2. Crear cliente GenAI
    print("\n📡 Conectando a OCI GenAI Service...")
    client = GenerativeAiInferenceClient(
        config={'region': 'us-chicago-1'},
        signer=signer,
        service_endpoint=ENDPOINT
    )
    print("✅ Cliente GenAI creado")
    
    # 3. Preparar request de embedding
    print("\n🧮 Generando embedding para: 'hola'")
    embed_request = EmbedTextDetails()
    embed_request.serving_mode = OnDemandServingMode(model_id=MODEL_ID)
    embed_request.inputs = ["hola"]
    embed_request.truncate = "NONE"
    embed_request.compartment_id = COMPARTMENT_ID
    
    # 4. Ejecutar embedding
    print("⏳ Llamando a Cohere Embed v4.0...")
    response = client.embed_text(embed_request)
    
    # 5. Mostrar resultado
    vector = response.data.embeddings[0]
    print(f"\n✅ ¡Embedding generado exitosamente!")
    print(f"📊 Dimensiones del vector: {len(vector)}")
    print(f"🔢 Primeros 10 valores: {vector[:10]}")
    print(f"🔢 Últimos 10 valores: {vector[-10:]}")
    
    print("\n" + "=" * 60)
    print("✅ TEST COMPLETADO CON ÉXITO")
    print("=" * 60)
    
except oci.exceptions.ServiceError as e:
    print(f"\n❌ Error de OCI Service:")
    print(f"   Código: {e.code}")
    print(f"   Mensaje: {e.message}")
    print("\n💡 Verifica:")
    print("   1. Que Instance Principal esté configurado")
    print("   2. Que el Dynamic Group tenga permisos")
    print("   3. Que la policy permita 'use generative-ai-family'")
    
except Exception as e:
    print(f"\n❌ Error inesperado: {e}")
    print("\n💡 Posibles causas:")
    print("   1. Instance Principal no configurado en esta VM")
    print("   2. Falta el Dynamic Group en OCI")
    print("   3. Falta la Policy para GenAI")