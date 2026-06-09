import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Configure API
api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    # Try importing from config if env var not set directly
    try:
        from config import settings
        api_key = settings.GOOGLE_API_KEY
    except ImportError:
        print("Error: GOOGLE_API_KEY not found.")
        exit(1)

genai.configure(api_key=api_key)

def list_files():
    print("Listing files on Gemini Cloud...")
    try:
        for f in genai.list_files():
            print(f"ID: {f.name} | Display Name: {f.display_name} | URI: {f.uri}")
    except Exception as e:
        print(f"Error listing files: {e}")

def delete_file(file_name_id):
    print(f"Attempting to delete {file_name_id}...")
    try:
        genai.delete_file(file_name_id)
        print(f"Successfully deleted {file_name_id}")
    except Exception as e:
        print(f"Error deleting file: {e}")

def delete_all():
    print("Deleting ALL files from Gemini Cloud...")
    try:
        files = list(genai.list_files())
        if not files:
            print("No files to delete.")
            return
        
        print(f"Found {len(files)} files. Deleting...")
        for f in files:
            try:
                genai.delete_file(f.name)
                print(f"  Deleted: {f.display_name}")
            except Exception as e:
                print(f"  Failed to delete {f.name}: {e}")
        print("Done!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "list":
            list_files()
        elif command == "delete" and len(sys.argv) > 2:
            delete_file(sys.argv[2])
        elif command == "delete_all":
            delete_all()
        else:
            print("Usage: python manage_gemini_files.py [list|delete <id>|delete_all]")
    else:
        list_files()
