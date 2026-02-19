import ollama
import chromadb # Import ChromaDB client
# import httpx # Not needed for ChromaDB local
# import json # Not needed for ChromaDB local
import re # For regex parsing of queries
from portalcentro_db_manager import get_locale_info # Import DB query function
from dotenv import load_dotenv
import os

# Load environment variables (for future API keys if needed)
load_dotenv()

# --- Configuration ---
CHROMADB_PATH = "./chroma_db" # Path for ChromaDB persistent storage
COLLECTION_NAME = "portalcentro_memory"
OLLAMA_MODEL = "mistral:7b-instruct-v0.2-q4_K_M"
OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings" # Ollama URL

# Initialize ChromaDB Client (persistent client)
chroma_client = chromadb.PersistentClient(path=CHROMADB_PATH)
# Get the collection
try:
    chroma_collection = chroma_client.get_or_create_collection(name=COLLECTION_NAME)
except Exception as e:
    print(f"ERROR: Could not access/create ChromaDB collection '{COLLECTION_NAME}': {e}")
    chroma_collection = None # Handle case where collection creation fails

def generate_embedding(text):
    """Generates an embedding for the given text using Ollama."""
    response = ollama.embeddings(
        model=OLLAMA_MODEL,
        prompt=text
    )
    return response['embedding']

def query_portalcentro_rag(user_query, top_k=3):
    """
    Orchestrates the RAG process for PortalCentro memory.
    1. Detects if query is structured for SQLite.
    2. If so, queries SQLite and returns result.
    3. Otherwise, generates embedding for user_query.
    4. Searches ChromaDB for top_k most relevant context chunks.
    5. Constructs a prompt for Ollama with the user_query and retrieved context.
    6. Generates a response using Ollama.
    """

    # --- Try to answer with SQLite first (Structured Query Detection) ---
    locale_match = re.search(r'local\s*(\d+)', user_query, re.IGNORECASE)
    monto_match = re.search(r'(monto|arriendo|precio)\s*(de)?\s*(local)?\s*(\d+)', user_query, re.IGNORECASE)
    superficie_match = re.search(r'(superficie|metros cuadrados)\s*(del)?\s*(local)?\s*(\d+)', user_query, re.IGNORECASE)
    estado_match = re.search(r'(estado)\s*(del)?\s*(local)?\s*(\d+)', user_query, re.IGNORECASE)

    if locale_match or monto_match or superficie_match or estado_match:
        locale_num = None
        if locale_match: locale_num = int(locale_match.group(1))
        elif monto_match: locale_num = int(monto_match.group(4))
        elif superficie_match: locale_num = int(superficie_match.group(4))
        elif estado_match: locale_num = int(estado_match.group(4))

        if locale_num:
            locale_info = get_locale_info(numero=locale_num)
            if locale_info:
                # Format the SQLite response nicely
                info = locale_info[0] # Assuming one result for specific locale number
                response_str = f"Información del Local {info[0]}:\n"
                response_str += f"  - Nombre: {info[1]}\n"
                response_str += f"  - Piso: {info[2]}\n"
                response_str += f"  - Superficie: {info[3]} m²\n"
                response_str += f"  - Monto de Arriendo: {info[4]} UF\n"
                response_str += f"  - Estado: {info[5]}"
                # Add other fields as needed
                return response_str
            else:
                return f"No se encontró información para el Local {locale_num} en la base de datos." 
        
    # --- Fallback to RAG if not a structured query or SQLite has no direct answer ---
    if not chroma_collection:
        return "ERROR: La colección ChromaDB no está disponible."
    
    if chroma_collection.count() == 0:
        return "ERROR: La base de conocimiento vectorial de PortalCentro no contiene vectores indexados. Ejecute el script de indexación de ChromaDB primero."

    # 3. Generates embedding for user_query
    query_embedding = generate_embedding(user_query)

    # 4. Searches ChromaDB for top_k most relevant context chunks
    # ChromaDB expects a list of query embeddings
    search_result = chroma_collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=['documents', 'metadatas', 'distances'] # Request documents and metadatas
    )

    context_chunks = []
    if search_result and 'documents' in search_result and search_result['documents']:
        # search_result['documents'] is a list of lists, take the first inner list
        for doc in search_result['documents'][0]:
            context_chunks.append(doc)

    if not context_chunks:
        return "ERROR: No se encontró información relevante en la base de conocimiento de PortalCentro mediante RAG."

    # 5. Construct a prompt for Ollama
    context_str = "\n".join(context_chunks)
    
    # Critical: Ensure Ollama is instructed to use the provided context
    ollama_prompt = f"""
    Basándote EXCLUSIVAMENTE en el siguiente CONTEXTO de PortalCentro Mulchén, responde a la pregunta. 
    Si la respuesta no se puede inferir del contexto, indica que la información no está disponible.
    
    CONTEXTO:
    {context_str}
    
    PREGUNTA:
    {user_query}
    
    RESPUESTA:
    """

    # 6. Generate a response using Ollama
    try:
        response = ollama.generate(
            model=OLLAMA_MODEL,
            prompt=ollama_prompt,
            stream=False
        )
        return response['response'].strip()
    except Exception as e:
        return f"ERROR al generar respuesta con Ollama: {e}"

if __name__ == "__main__":
    # Example usage (for testing)
    print("Orquestador RAG de PortalCentro iniciado. Escriba 'salir' para terminar.")
    while True:
        user_input = input("Su pregunta sobre PortalCentro: ")
        if user_input.lower() == 'salir':
            break
        
        result = query_portalcentro_rag(user_input)
        print("\nRespuesta del RAG:\n", result)
        print("-" * 50)
