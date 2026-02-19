import os
import re
import ollama
import spacy
import chromadb # Import ChromaDB client
from dotenv import load_dotenv

# Load environment variables (for future API keys if needed)
load_dotenv()

# --- Configuration ---
CHROMADB_PATH = "./chroma_db" # Path for ChromaDB persistent storage
COLLECTION_NAME = "portalcentro_memory"
OLLAMA_MODEL = "mistral:7b-instruct-v0.2-q4_K_M"
OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
MEMORY_PATH = "memory/portalcentro/"
CHUNK_SIZE = 500  # Characters per chunk
CHUNK_OVERLAP = 50 # Overlap for better context

# Initialize ChromaDB Client (persistent client)
chroma_client = chromadb.PersistentClient(path=CHROMADB_PATH)

# Initialize SpaCy for text processing (optional, can be integrated for better chunking)
# try:
#     nlp = spacy.load("es_core_news_sm")
# except:
#     print("SpaCy model 'es_core_news_sm' not found. Please run 'python3 -m spacy download es_core_news_sm' in your venv.")
#     nlp = None

def get_files_to_index(base_path):
    """Recursively finds all .md files, excluding templates."""
    # For debugging, process only a specific file
    # return [os.path.join(base_path, "02-Locales/local-03.md")]
    indexed_files = []
    for root, _, files in os.walk(base_path):
        for file in files:
            if file.endswith(".md") and "99-Templates" not in root:
                indexed_files.append(os.path.join(root, file))
    return indexed_files

def chunk_text(text, file_path, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    """Splits text into chunks with overlap, adding file_path as metadata."""
    chunks = []
    current_chunk = ""
    for line in text.splitlines():
        if len(current_chunk) + len(line) < chunk_size:
            current_chunk += line + "\n"
        else:
            chunks.append({"text": current_chunk.strip(), "source": file_path})
            current_chunk = current_chunk[-chunk_overlap:] + line + "\n"
    if current_chunk:
        chunks.append({"text": current_chunk.strip(), "source": file_path})
    return chunks

def generate_embedding(text):
    """Generates an embedding for the given text using Ollama."""
    response = ollama.embeddings(
        model=OLLAMA_MODEL,
        prompt=text
    )
    return response['embedding']

def index_memory(files_to_index):
    """Indexes the given files into ChromaDB."""
    try:
        collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
        print(f"Collection '{COLLECTION_NAME}' accessed/created in ChromaDB.")
    except Exception as e:
        print(f"Error accessing/creating collection in ChromaDB: {e}")
        return

    documents = []
    metadatas = []
    ids = []
    embeddings = [] # To store embeddings
    
    point_id = 0
    for file_path in files_to_index:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Basic cleanup (remove frontmatter, code blocks)
            content = re.sub(r'---\n.*?\n---', '', content, flags=re.DOTALL) # Remove YAML frontmatter
            content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)     # Remove code blocks
            
            chunks = chunk_text(content, file_path)
            for chunk in chunks:
                embedding = generate_embedding(chunk["text"])
                
                embeddings.append(embedding) # Collect embedding
                documents.append(chunk["text"])
                metadatas.append({"source": chunk["source"]})
                ids.append(str(point_id)) # ChromaDB expects string IDs
                point_id += 1
            print(f"Processed file: {file_path}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    if documents:
        # Before adding, we can try to clear if there are existing points to prevent duplicates on re-run
        # if collection.count() > 0:
        #     collection.delete(ids=collection.get()['ids'])
        
        collection.add(
            embeddings=embeddings, # Now passing embeddings list
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Successfully indexed {len(documents)} points into '{COLLECTION_NAME}'.")
    else:
        print("No documents to index.")

if __name__ == "__main__":
    print("Starting PortalCentro memory indexing with ChromaDB...")
    files = get_files_to_index(MEMORY_PATH)
    print(f"Found {len(files)} files to index.")
    
    # Ensure ChromaDB data directory exists
    os.makedirs(CHROMADB_PATH, exist_ok=True)
    
    # IMPORTANT: To clear a ChromaDB persistent client, you usually delete the directory.
    # For a clean re-index during development, you might delete the directory.
    # For now, we'll let 'add' handle potential duplicates or re-indexing over existing IDs.
    
    index_memory(files)
    print("Indexing complete.")

# [DUPLICATE CODE REMOVED]