import os
import sys
from grok_assistant import GrokOCIAssistant

# Ejemplo de uso para migrar de OpenAI a Grok 4
def main():
    print("Iniciando cliente Grok OCI...")
    
    # La configuración se carga automáticamente desde ../.env
    try:
        grok = GrokOCIAssistant()
        print("Cliente inicializado correctamente.")
    except Exception as e:
        print(f"Error al inicializar cliente: {e}")
        return

    # 1. Ejemplo básico: Saludo
    print("\n--- Ejemplo 1: Saludo ---")
    try:
        response = grok.generate_response(
            prompt="Hola, ¿cómo estás? Preséntate brevemente.",
            model_name="grok-4"
        )
        print(f"Grok: {response}")
    except Exception as e:
        print(f"Error: {e}")

    # 2. Ejemplo multimodal: Análisis de imagen
    print("\n--- Ejemplo 2: Análisis de Imagen ---")
    # Asegúrate de tener una imagen llamada 'test_image.jpg' en la misma carpeta o ajusta la ruta
    image_path = "test_image.jpg" 
    
    if os.path.exists(image_path):
        try:
            print(f"Analizando imagen: {image_path}...")
            response = grok.generate_response(
                prompt="Describe qué ves en esta imagen con detalle.",
                model_name="grok-4",
                images=[image_path]
            )
            print(f"Grok: {response}")
        except Exception as e:
            print(f"Error analizando imagen: {e}")
    else:
        print(f"Nota: No se encontró la imagen '{image_path}'. Para probar la capacidad de visión, coloca una imagen con ese nombre.")

    # 3. Ejemplo RAG (búsqueda vectorial)
    print("\n--- Ejemplo 3: RAG (Búsqueda Vectorial) ---")
    search_results = [
        {
            "title": "Introducción a OCI",
            "body": "Oracle Cloud Infrastructure (OCI) es un conjunto de servicios en la nube complementarios.",
            "distance": 0.1
        }
    ]
    
    try:
        rag_response = grok.answer_with_context(
            query="¿Qué es OCI?",
            search_results=search_results,
            model_name="grok-4"
        )
        print(f"Respuesta RAG: {rag_response['answer']}")
    except Exception as e:
        print(f"Error en RAG: {e}")

if __name__ == "__main__":
    main()
