# 🚀 Manual de Replicación: OpenClaw con IA Potenciada en OCI

Este manual detalla la instalación paso a paso de **OpenClaw** como su asistente central, potenciado con un modelo de lenguaje local **Ollama (Mistral)** y capacidades de Procesamiento de Lenguaje Natural (PLN) con **SpaCy**, todo desplegado de forma segura en una máquina virtual de **Oracle Cloud Infrastructure (OCI)**.

El objetivo es replicar un entorno de IA robusto para administración, análisis y ciberseguridad controlada.

---

## 🎯 Objetivo de la Infraestructura

Una VM Linux en OCI configurada para:
1.  Alojar **OpenClaw**, el asistente de IA.
2.  Ejecutar **Ollama** con el modelo `mistral` para análisis de lenguaje local.
3.  Utilizar **SpaCy** para **procesamiento de lenguaje natural (PLN)** avanzado.
4.  Garantizar **acceso seguro y privado** a través de **Tailscale**.

---

## 📋 Prerrequisitos

*   Una **VM Linux (Ubuntu 22.04 LTS o superior, arquitectura ARM64)** en Oracle Cloud Infrastructure (idealmente, la capa "Always Free" con 4 OCPUs y 24 GB de RAM).
*   Acceso SSH a la VM con un usuario `sudo` (ej. `ubuntu`).
*   Dominio o subdominio configurado si desea acceso web público con Caddy (opcional, no incluido en este manual para mantener el foco en Tailscale).
*   Cuenta de Tailscale activa.
*   Conocimiento básico de terminal Linux.

---

## 🛠️ Pasos de Instalación

### **Fase 1: Configuración Inicial de la VM y Seguridad Base**

1.  **Actualizar el Sistema Operativo:**
    ```bash
    sudo apt update && sudo apt upgrade -y
    ```

2.  **Instalar Dependencias Básicas (si no están presentes):**
    ```bash
    sudo apt install -y build-essential python3 python3-pip make g++ curl
    ```
    *(Nota: `python3-pip` es importante para la gestión de paquetes Python.)*

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

### **Fase 6: Instalación de Qdrant (Base de Datos Vectorial)**

1.  **Crear Directorio de Datos:**
    ```bash
    mkdir -p qdrant_data
    ```

2.  **Crear `docker-compose.yml` para Qdrant:**
    ```bash
    cat <<EOL > docker-compose-qdrant.yml
    version: '3.8'
    services:
      qdrant:
        image: qdrant/qdrant
        restart: always
        ports:
          - "6333:6333" # REST API
          - "6334:6334" # gRPC API
        volumes:
          - ./qdrant_data:/qdrant/data
        environment:
          - QDRANT__SERVICE__GRPC_PORT=6334
          - QDRANT__SERVICE__HTTP_PORT=6333
    EOL
    ```

3.  **Iniciar Qdrant con Docker Compose:**
    ```bash
    docker compose -f docker-compose-qdrant.yml up -d
    ```
    *   **Verificación:** `docker ps | grep qdrant` (debería mostrar el contenedor "Up").

### **Fase 7: Instalación de SpaCy (Procesamiento de Lenguaje Natural)**

1.  **Instalar `python3-venv` (si no está):**
    ```bash
    sudo apt install -y python3-venv
    ```

2.  **Crear Entorno Virtual Python:**
    ```bash
    python3 -m venv spacy_venv
    ```

3.  **Instalar SpaCy en el Entorno Virtual:**
    ```bash
    source spacy_venv/bin/activate && python3 -m pip install spacy && deactivate
    ```

4.  **Descargar Modelo de Lenguaje para SpaCy (Español):**
    ```bash
    source spacy_venv/bin/activate && python3 -m spacy download es_core_news_sm && deactivate
    ```
    *   **Verificación:** Puede activar el venv y ejecutar `python3 -c "import spacy; nlp = spacy.load('es_core_news_sm'); doc = nlp('Hola mundo'); print(doc.text)"`

---

## ✅ Verificación Final de Componentes

*   **OpenClaw:** Acceder vía `https://<nombre_vm>.tailnetID.ts.net/` (su URL de Tailscale para OpenClaw).
*   **Qdrant:**
    *   Contenedor activo: `docker ps | grep qdrant`
    *   Accesible localmente: `curl http://127.0.0.1:6333/collections` (debería retornar un JSON).
*   **Ollama con Mistral:**
    *   Servicio activo: `systemctl status ollama.service`
    *   Modelo cargado: `ollama list`
    *   Probar inferencia local: `ollama run mistral "Hola, ¿cómo estás?"`
*   **SpaCy:**
    *   Entorno virtual existe: `ls -F spacy_venv/`
    *   Modelo cargado (ejemplo Python):
        ```python
        import spacy
        nlp = spacy.load("es_core_news_sm")
        doc = nlp("El sol brilla en el cielo.")
        for ent in doc.ents:
            print(ent.text, ent.label_)
        ```

---

## 📝 Notas Post-Instalación

*   **Uso de Recursos:** Esta configuración utiliza la mayoría de los recursos de la capa "Always Free" de OCI. Monitoree su consumo.
*   **Actualizaciones:** Mantenga el sistema operativo (`sudo apt update && sudo apt upgrade -y`), Docker (`docker compose pull` para Qdrant) y Ollama (`ollama pull <modelo>`) actualizados.
*   **Tailscale MagicDNS:** Si experimenta problemas de resolución de nombres *dentro de la VM* para las URLs de Tailscale, podría ser necesario investigar más a fondo la interacción con `systemd-resolved` o ajustar `resolv.conf`, aunque el acceso externo desde su cliente Tailscale debería funcionar.

---

Este manual está diseñado para ser un recurso completo para replicar su entorno de IA.