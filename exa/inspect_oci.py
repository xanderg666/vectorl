import oci
import inspect

try:
    print("Inspecting oci.generative_ai_inference.models.ImageContent...")
    print(inspect.signature(oci.generative_ai_inference.models.ImageContent.__init__))
    print(dir(oci.generative_ai_inference.models.ImageContent))
except Exception as e:
    print(f"Error inspecting ImageContent: {e}")

try:
    print("\nInspecting oci.generative_ai_inference.models.TextContent...")
    print(inspect.signature(oci.generative_ai_inference.models.TextContent.__init__))
except Exception as e:
    print(f"Error inspecting TextContent: {e}")

try:
    print("\nList of classes in oci.generative_ai_inference.models:")
    print([m for m in dir(oci.generative_ai_inference.models) if 'Content' in m])
except Exception as e:
    print(f"Error listing models: {e}")
