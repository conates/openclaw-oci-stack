import sqlite3
import os
import re
import yaml # For parsing frontmatter

# --- Configuration ---
DB_NAME = "portalcentro.db"
MEMORY_PATH = "memory/portalcentro/"

def init_db():
    """Initializes the SQLite database and creates necessary tables."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Create 'locales' table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS locales (
            numero INTEGER PRIMARY KEY,
            nombre_local TEXT,
            piso TEXT,
            metros_cuadrados INTEGER,
            monto_arriendo_uf REAL,
            estado TEXT,
            arrendatario TEXT,
            contrato TEXT,
            tiene_bano BOOLEAN,
            tiene_bodega BOOLEAN,
            medidor_luz BOOLEAN,
            source_file TEXT UNIQUE
        )
    """)
    
    # Add other tables as needed (arrendatarios, contratos, etc.)
    # This is an initial version, we will expand it.

    conn.commit()
    conn.close()
    print(f"Database '{DB_NAME}' initialized with 'locales' table.")

def parse_md_file(file_path):
    """Parses a Markdown file, extracting YAML frontmatter."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    if match:
        frontmatter = yaml.safe_load(match.group(1))
        return frontmatter
    return {}

def synchronize_locales_from_md():
    """
    Reads local .md files, extracts locale data, and synchronizes with the DB.
    Only processes files in memory/portalcentro/02-Locales/
    """
    init_db() # Ensure DB is initialized
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    locale_files = []
    for root, _, files in os.walk(os.path.join(MEMORY_PATH, "02-Locales")):
        for file in files:
            if file.endswith(".md"):
                locale_files.append(os.path.join(root, file))

    for file_path in locale_files:
        data = parse_md_file(file_path)
        if data.get('tipo') == 'Local Comercial':
            try:
                cursor.execute("""
                    INSERT OR REPLACE INTO locales (
                        numero, nombre_local, piso, metros_cuadrados, monto_arriendo_uf,
                        estado, arrendatario, contrato, tiene_bano, tiene_bodega,
                        medidor_luz, source_file
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data.get('numero'), data.get('nombre_local'), data.get('piso'),
                    data.get('metros_cuadrados'), data.get('monto_arriendo_uf'),
                    data.get('estado'), data.get('arrendatario'), data.get('contrato'),
                    data.get('tiene_baño') == 'Si', data.get('tiene_bodega') == 'Si',
                    data.get('medidor_luz') == 'Si', file_path
                ))
            except Exception as e:
                print(f"Error synchronizing {file_path}: {e}")
    
    conn.commit()
    conn.close()
    print(f"Synchronized {len(locale_files)} locale files into '{DB_NAME}'.")

def get_locale_info(numero=None, estado=None):
    """Retrieves locale information based on criteria."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    query = "SELECT * FROM locales WHERE 1=1"
    params = []

    if numero is not None:
        query += " AND numero = ?"
        params.append(numero)
    if estado is not None:
        query += " AND estado = ?"
        params.append(estado)
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    return results

if __name__ == "__main__":
    init_db()
    synchronize_locales_from_md()
    print("\nExample Query: All available locales")
    available_locales = get_locale_info(estado="Disponible")
    for locale in available_locales:
        print(locale)
    
    print("\nExample Query: Info for Local 3")
    local_3_info = get_locale_info(numero=3)
    for locale in local_3_info:
        print(locale)
