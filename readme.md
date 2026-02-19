# 🚀 Manual de Replicación: OpenClaw con IA Potenciada en OCI

Este manual detalla la instalación paso a paso de **OpenClaw** como su asistente central, potenciado con un modelo de lenguaje local **Ollama (Mistral)**, capacidades de Procesamiento de Lenguaje Natural (PLN) con **SpaCy**, y un robusto sistema **RAG (Retrieval Augmented Generation) híbrido** con **SQLite y ChromaDB**, todo desplegado de forma segura en una máquina virtual de **Oracle Cloud Infrastructure (OCI)**.

El objetivo es replicar un entorno de IA robusto para administración, análisis y ciberseguridad controlada, específicamente adaptado para la gestión de información de PortalCentro Mulchén.

---

## 🎯 Objetivo de la Infraestructura

Una VM Linux en OCI configurada para:
1.  Alojar **OpenClaw**, el asistente de IA.
2.  Ejecutar **Ollama** con el modelo `mistral` para análisis de lenguaje local y generación de embeddings.
3.  Utilizar **SpaCy** para **procesamiento de lenguaje natural (PLN)** avanzado (instalado para futuras mejoras, pero no activamente integrado en el flujo de chunking del RAG actual).
4.  Gestionar datos estructurados con **SQLite**.
5.  Implementar una base de datos vectorial con **ChromaDB** para búsqueda semántica.
6.  Soportar un **Sistema RAG híbrido** para consultas complejas.
7.  Garantizar **acceso seguro y privado** a través de **Tailscale**.

---

## 📋 Prerrequisitos

*   Una **VM Linux (Ubuntu 22.04 LTS o superior, arquitectura ARM64)** en Oracle Cloud Infrastructure (idealmente, la capa "Always Free" con 4 OCPUs y 24 GB de RAM).
*   Acceso SSH a la VM con un usuario `sudo` (ej. `ubuntu`).
*   Cuenta de Tailscale activa.
*   Conocimiento básico de terminal Linux y `git`.

---

## 🛠️ Pasos de Instalación

### **Fase 1: Configuración Inicial de la VM y Seguridad Base**

1.  **Actualizar el Sistema Operativo:**
    ```bash
    sudo apt update && sudo apt upgrade -y
    ```

2.  **Instalar Dependencias Básicas (si no están presentes):**
    ```bash
    sudo apt install -y build-essential python3 python3-pip make g++ curl sqlite3
    ```
    *(Nota: `python3-pip` y `sqlite3` son importantes para la gestión de paquetes Python y la base de datos local.)*

3.  **Configurar Firewall (UFW):**
    Establece reglas de seguridad estrictas, permitiendo solo SSH y el puerto de Tailscale.
    ```bash
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow 22/tcp # Para SSH
    sudo ufw allow 41641/udp # Puerto de Tailscale
    sudo ufw enable
    sudo ufw status verbose
    ```

4.  **Endurecimiento de SSH (Opcional pero Recomendado):**
    Deshabilitar la autenticación por contraseña, solo permitiendo claves SSH.
    ```bash
    sudo nano /etc/ssh/sshd_config
    # Cambiar/asegurarse de que:
    # PasswordAuthentication no
    # PubkeyAuthentication yes
    sudo systemctl restart ssh
    ```

5.  **Instalar Fail2Ban (Opcional pero Recomendado):**
    Protección contra ataques de fuerza bruta.
    ```bash
    sudo apt install fail2ban -y
    sudo nano /etc/fail2ban/jail.local
    # Añadir:
    # [DEFAULT]
    # bantime = 1h
    # findtime = 10m
    # maxretry = 3
    # [sshd]
    # enabled = true
    sudo systemctl enable fail2ban
    sudo systemctl start fail2ban
    ```

### **Fase 2: Instalación de OpenClaw**

1.  **Instalar OpenClaw:**
    ```bash
    curl -fsSL https://openclaw.ai/install.sh | bash -s -- --beta
    ```
    Siga las instrucciones interactivas:
    *   Elija `y` para aceptar el aviso de seguridad.
    *   Seleccione `Quick Start`.
    *   Configure su modelo de IA (ej. OpenAI, siguiendo el enlace y pegando la URL de `localhost` que genera).
    *   Configure Telegram (o su canal preferido) usando `BotFather` y su API Key.
    *   Seleccione las `skills` iniciales (ej. `cloud`, `mcp`, `usage`).
    *   Elija su `hook` de memoria (ej. `.bot.md`).
    *   Cuando pregunte qué hacer, elija `Init`.

2.  **Configurar Acceso Seguro al Gateway de OpenClaw (Localhost):**
    ```bash
    openclaw config set gateway.bind loopback
    openclaw config set gateway.port 18789
    openclaw gateway restart
    ```
    Verifique que solo escucha en `127.0.0.1:18789` con:
    ```bash
    ss -ltnp | grep 18789
    ```

### **Fase 3: Configuración de Tailscale para Acceso Remoto Seguro**

1.  **Instalar Tailscale:**
    ```bash
    curl -fsSL https://tailscale.com/install.sh | sh
    ```

2.  **Iniciar Tailscale y Autenticarse:**
    ```bash
    sudo tailscale up
    ```
    Esto le mostrará un enlace para autenticarse con su cuenta de Tailscale en su navegador.

3.  **Exponer el Gateway de OpenClaw con `tailscale serve`:**
    ```bash
    sudo tailscale serve --bg 127.0.0.1:18789
    ```
    *   **Verificación:** `sudo tailscale serve status` debería mostrar una URL (`https://<nombre_vm>.tailnetID.ts.net`) que proxy a `http://127.0.0.1:18789`.
    *   **Acceso:** Desde un dispositivo conectado a su Tailnet, acceda a esa URL (`https://<nombre_vm>.tailnetID.ts.net/`) para entrar al panel de OpenClaw.

### **Fase 4: Instalación de Docker y Docker Compose**

1.  **Instalar Docker Engine:**
    ```bash
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    ```

2.  **Añadir Usuario al Grupo `docker` (Opcional, pero útil):**
    ```bash
    sudo usermod -aG docker ubuntu
    # Deberá cerrar y reabrir su sesión SSH para que los cambios surtan efecto.
    ```
    *   **Verificación:** `docker run hello-world` (después de reconectarse).

3.  **Instalar Docker Compose Plugin:**
    ```bash
    sudo apt install -y docker-compose-plugin
    ```
    *   **Verificación:** `docker compose version`

### **Fase 5: Instalación de Ollama y el Modelo Mistral**

1.  **Instalar Ollama:**
    ```bash
    curl -fsSL https://ollama.com/install.sh | sh
    ```
    *   **Verificación:** `systemctl status ollama.service` (debería mostrar "active (running)").

2.  **Descargar el Modelo `mistral` (cuantizado para CPU):**
    Este modelo es eficiente para la VM solo con CPU.
    ```bash
    ollama pull mistral:7b-instruct-v0.2-q4_K_M
    ```
    *   **Verificación:** `ollama list` debería mostrar `mistral:7b-instruct-v0.2-q4_K_M`.

### **Fase 6: Configuración del Sistema RAG (SQLite y ChromaDB)**

Este apartado detalla la configuración del sistema de Retrieval Augmented Generation (RAG) que permite al asistente de IA consultar una base de conocimiento híbrida (SQLite para datos estructurados y ChromaDB para búsqueda semántica).

1.  **Clonar el Repositorio de PortalCentro (si aplica):**
    Asegúrese de que el repositorio de PortalCentro esté clonado en su workspace en la ruta `memory/portalcentro/`.
    ```bash
    cd /home/ubuntu/.openclaw/workspace/
    git clone git@github.com:PortalCentroMulchen/crm-openclaw-hxh.git memory/portalcentro
    # Asegúrese de que su clave SSH esté configurada en GitHub para poder clonar.
    ```

2.  **Crear Entorno Virtual Python y Activar:**
    ```bash
    cd /home/ubuntu/.openclaw/workspace/
    python3 -m venv spacy_venv
    source spacy_venv/bin/activate
    ```

3.  **Instalar Dependencias de Python:**
    ```bash
    pip install -r requirements.txt
    # El archivo requirements.txt debe contener:
    # ollama
    # chromadb
    # spacy
    # python-dotenv
    ```
    *(Si `requirements.txt` no existe, créelo manualmente con las dependencias mencionadas o ejecute `pip freeze > requirements.txt` después de instalar cada una.)*

4.  **Descargar Modelo de Lenguaje SpaCy (Español):**
    ```bash
    python3 -m spacy download es_core_news_sm
    ```

5.  **Inicializar y Poblar la Base de Datos SQLite:**
    El script `portalcentro_db_manager.py` gestiona la base de datos `portalcentro.db`, sincronizando datos estructurados desde los archivos Markdown. Ejecútelo para inicializar la base de datos.
    ```bash
    python3 portalcentro_db_manager.py
    ```

6.  **Indexar la Memoria en ChromaDB:**
    El script `index_portalcentro_memory.py` procesa los archivos Markdown (`.md`) de la memoria de PortalCentro, los divide en `chunks`, genera embeddings utilizando Ollama y los indexa en ChromaDB. **Debe ejecutarse cada vez que haya cambios significativos en los archivos Markdown.**
    ```bash
    python3 index_portalcentro_memory.py
    ```

7.  **Desactivar Entorno Virtual:**
    ```bash
    deactivate
    ```

8.  **Configurar Automatización Diaria (Opcional, pero Recomendado):**
    Cree un script `sync_and_index_portalcentro.sh` (ubicado en la raíz de su workspace) y configure trabajos `cron` para ejecutarlo automáticamente. Esto mantendrá su sistema RAG siempre actualizado.
    *   **Contenido de `sync_and_index_portalcentro.sh`:** (Ver archivo `sync_and_index_portalcentro.sh` en este repositorio para el contenido exacto)
    *   **Hacer el script ejecutable:**
        ```bash
        chmod +x sync_and_index_portalcentro.sh
        ```
    *   **Añadir trabajos `cron`:** Utilice la herramienta `cron` de OpenClaw (o crontab) para programar la ejecución del script en los horarios deseados (ej. 7 AM, 1 PM, 5 PM, 9 PM). Cada trabajo debe usar una `sessionTarget: isolated` y un `payload.kind: agentTurn` con un `message: exec ./sync_and_index_portalcentro.sh`.

---

## ✅ Verificación Final de Componentes

*   **OpenClaw:** Acceder vía `https://<nombre_vm>.tailnetID.ts.net/` (su URL de Tailscale para OpenClaw).
*   **Ollama con Mistral:**
    *   Servicio activo: `systemctl status ollama.service`
    *   Modelo cargado: `ollama list`
    *   Probar inferencia local: `ollama run mistral "Hola, ¿cómo estás?"`
*   **SpaCy:** Instalado en el entorno virtual `spacy_venv` para futuras mejoras en el Procesamiento de Lenguaje Natural (PLN), aunque no es un componente activo y directo del flujo de chunking/embedding del RAG en su implementación actual.
    *   Entorno virtual existe: `ls -F spacy_venv/`
    *   Modelo cargado (ejemplo Python):
        ```bash
        source spacy_venv/bin/activate
        python3 -c "import spacy; nlp = spacy.load('es_core_news_sm'); doc = nlp('El sol brilla en el cielo.'); for ent in doc.ents: print(ent.text, ent.label_)"
        deactivate
        ```
*   **Sistema RAG (SQLite & ChromaDB):**
    *   Base de datos SQLite: `ls portalcentro.db` (debería existir en el workspace).
    *   ChromaDB datos: `ls -F chroma_db/` (debería mostrar archivos de la base de datos).
    *   Probar consultas RAG (ejemplo Python):
        ```bash
        source spacy_venv/bin/activate
        python3 -c "from query_portalcentro_rag import query_portalcentro_rag; print(query_portalcentro_rag('¿Cuál es la superficie del local 5?'))"
        deactivate
        ```

---

## 📝 Notas Post-Instalación

*   **Uso de Recursos:** Esta configuración utiliza la mayoría de los recursos de la capa "Always Free" de OCI. Monitoree su consumo.
*   **Actualizaciones:** Mantenga el sistema operativo (`sudo apt update && sudo apt upgrade -y`), Docker (`docker compose pull` para cualquier servicio futuro) y Ollama (`ollama pull <modelo>`) actualizados.
*   **Troubleshooting Git SSH:** Si experimenta problemas al clonar el repositorio de PortalCentro vía SSH, asegúrese de que su clave SSH pública esté añadida a su cuenta de GitHub y que `ssh-agent` esté configurado en su VM.

---

Este manual es un recurso completo para replicar y mantener su entorno de IA.
