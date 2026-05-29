import sys
from pathlib import Path

# Add backend to path so we can import app.config
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from google import genai
from app.config import get_settings

def main():
    settings = get_settings()
    
    if not settings.use_vertex:
        print("❌ Vertex AI credentials not configured in .env")
        sys.exit(1)
        
    print(f"🔑 Auth mode: Vertex AI (GCP service account)")
    print(f"📦 Project:   {settings.gcp_project}")
    print(f"🌍 Location:  {settings.gcp_location}")
    print()
    
    client = genai.Client(
        vertexai=True,
        project=settings.gcp_project,
        location=settings.gcp_location,
        credentials=settings.google_credentials(),
    )
    
    print("Available Gemini 3 models:")
    print("-" * 50)
    
    found_flash = False
    
    try:
        # Paginator for models
        for model in client.models.list():
            if "gemini-3" in model.name or "flash" in model.name.lower():
                print(f"- {model.name}")
                if "gemini-3" in model.name and "flash" in model.name.lower():
                    found_flash = True
    except Exception as e:
        print(f"❌ Error fetching models: {e}")
        
    print("-" * 50)
    if found_flash:
        print("✅ Found a Gemini 3 Flash model!")
    else:
        print("❌ Did not find a Gemini 3 Flash model in the list.")

if __name__ == "__main__":
    main()
