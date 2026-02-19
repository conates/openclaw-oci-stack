# Sistema RAG con IA para PortalCentro Mulchén

## 🚀 Visión General del Proyecto

Este proyecto implementa un sistema de Generación Aumentada por Recuperación (RAG) híbrido, potenciado por IA, diseñado para la gestión y análisis de información de PortalCentro Mulchén. El objetivo principal es asistir en la administración y arriendo de las unidades comerciales restantes, proporcionando capacidades avanzadas de consulta sobre la base de conocimiento de la propiedad.

El sistema es administrado por **Maha Zoldyck**, una IA con una personalidad de "Gerente General": concisa, directa, técnicamente rigurosa, orientada a la crítica constructiva, con un léxico sofisticado y ocasionalmente humorístico, siempre priorizando la eficacia y la seguridad.

## 🏛️ Arquitectura del Sistema RAG

Se ha desarrollado una arquitectura RAG híbrida que combina el acceso estructurado a datos con la búsqueda semántica, optimizada para un entorno de bajo costo (Oracle Cloud Free Tier) y alta seguridad.

-   **Fuente de Verdad**: Archivos Markdown (`.md`) en el repositorio `memory/portalcentro/`.
-   **Base de Datos Estructurada**: **SQLite** (`portalcentro.db`) para consultas precisas sobre datos tabulares (ej. información de locales por número).
-   **Base de Datos Vectorial**: **ChromaDB** para almacenar embeddings vectoriales de los documentos Markdown, facilitando la búsqueda semántica.
-   **Modelo de Lenguaje Grande (LLM)**: **Ollama** con el modelo `mistral:7b-instruct-v0.2-q4_K_M` para generar embeddings y respuestas contextualizadas.
-   **Orquestador RAG**: Un script Python (`query_portalcentro_rag.py`) que decide inteligentemente si usar SQLite para consultas estructuradas o ChromaDB/Ollama para búsquedas semánticas.

## 🧩 Componentes Clave

-   `portalcentro_db_manager.py`: Script Python encargado de inicializar y gestionar la base de datos SQLite (`portalcentro.db`), sincronizando los datos estructurados desde los archivos Markdown.
-   `index_portalcentro_memory.py`: Script Python que procesa los archivos Markdown de la memoria de PortalCentro, los divide en `chunks`, genera embeddings utilizando Ollama y los indexa en ChromaDB.
-   `query_portalcentro_rag.py`: El orquestador principal. Recibe una consulta del usuario, determina la estrategia de búsqueda (SQLite o ChromaDB), recupera el contexto relevante y formula una respuesta utilizando Ollama.

## ⚙️ Configuración y Requisitos Previos

El sistema está diseñado para ejecutarse en una máquina virtual de Oracle Cloud Free Tier (4 OCPUs, 24 GB RAM, 200 GB disco, Ubuntu Server ARM64).

1.  **Tailscale**: Configurado para acceso seguro a la interfaz web de OpenClaw.
2.  **Docker & Docker Compose**: Para la gestión de servicios contenerizados (aunque ChromaDB se ejecuta de forma persistente a nivel de archivo en este setup).
3.  **Ollama**: Instalado y ejecutando el modelo `mistral:7b-instruct-v0.2-q4_K_M` en `http://localhost:11434`.
4.  **Python y entorno virtual**:
    -   `python3 -m venv spacy_venv`
    -   `source spacy_venv/bin/activate`
    -   `pip install -r requirements.txt` (asegúrate de que `requirements.txt` incluya `ollama`, `chromadb`, `spacy`, `python-dotenv`, `qdrant-client` si aún está en uso, etc.)
    -   `python3 -m spacy download es_core_news_sm`
5.  **SQLite3**: Instalado en el sistema operativo.

**Nota**: Para una guía de instalación paso a paso y detallada, consulte el manual completo en `/home/ubuntu/manual_openclaw_ia_potenciada.md`.

## 🚀 Uso

### 1. Inicializar y Poblar la Base de Datos SQLite

Antes de usar el sistema RAG, asegúrese de que la base de datos SQLite esté actualizada con la información de los locales.

```bash
source spacy_venv/bin/activate
python3 portalcentro_db_manager.py
deactivate
```

### 2. Indexar la Memoria en ChromaDB

Este paso procesará todos los archivos Markdown en `memory/portalcentro/` (excluyendo `99-Templates`), generará sus embeddings y los almacenará en ChromaDB. **Debe ejecutarse cada vez que haya cambios significativos en los archivos Markdown.**

```bash
source spacy_venv/bin/activate
python3 index_portalcentro_memory.py
deactivate
```

### 3. Realizar Consultas RAG

Una vez que la memoria está indexada, puede realizar consultas utilizando el script `query_portalcentro_rag.py`.

```bash
source spacy_venv/bin/activate
python3 -c "from query_portalcentro_rag import query_portalcentro_rag; print(query_portalcentro_rag('¿Cuál es la superficie del local 5?'))"
python3 -c "from query_portalcentro_rag import query_portalcentro_rag; print(query_portalcentro_rag('¿Qué locales están actualmente arrendados?'))"
python3 -c "from query_portalcentro_rag import query_portalcentro_rag; print(query_portalcentro_rag('Dime algo sobre el representante legal de Ricco Bambino.'))"
deactivate
```

## ✅ Estado y Características

-   **RAG Híbrido Funcional**: Capacidad para responder consultas estructuradas (vía SQLite) y semánticas (vía ChromaDB/Ollama).
-   **Maha Zoldyck Persona**: Interacción con una IA con personalidad definida, enfocada en la eficiencia y la seguridad.
-   **Optimización de Costes**: Diseño para operar eficientemente en la capa gratuita de Oracle Cloud.
-   **Seguridad y Restricciones**: Implementación de reglas estrictas contra la exfiltración de secretos y para la confirmación de acciones peligrosas.
-   **Base de Conocimiento Dinámica**: Los archivos Markdown pueden ser actualizados por el usuario y re-indexados fácilmente.

---

_Este README es una guía concisa. Para detalles técnicos y de implementación, consulte los scripts Python y el manual de instalación._
