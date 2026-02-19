#!/bin/bash

# Configuration
REPO_PATH="/home/ubuntu/.openclaw/workspace/memory/portalcentro/"
WORKSPACE_PATH="/home/ubuntu/.openclaw/workspace/"
VENV_PATH="${WORKSPACE_PATH}spacy_venv/bin/activate"
INDEX_SCRIPT="${WORKSPACE_PATH}index_portalcentro_memory.py"
USER_TELEGRAM_ID="5781693795" # ID de Telegram de Shaka
CHANNEL_NAME="telegram"

cd "$REPO_PATH" || { echo "ERROR: No se pudo cambiar al directorio del repositorio de PortalCentro."; exit 1; }

# Fetch latest changes
echo "INFO: Obteniendo últimos cambios de origin/master..."
git fetch origin master

# Compare local HEAD with remote HEAD
LOCAL_HEAD=$(git rev-parse HEAD)
REMOTE_HEAD=$(git rev-parse origin/master)

if [ "$LOCAL_HEAD" != "$REMOTE_HEAD" ]; then
    echo "INFO: Cambios detectados en el repositorio remoto. Realizando pull..."
    
    # Intenta hacer pull con fast-forward para evitar conflictos complejos
    PULL_OUTPUT=$(git pull --ff-only origin master 2>&1)
    PULL_STATUS=$?

    if [ $PULL_STATUS -eq 0 ]; then
        # Envía la notificación inicial ANTES de re-indexar
        echo "MESSAGE_TO_USER: Shaka, la memoria de PortalCentro ha detectado nuevos cambios en el repositorio. Procediendo a actualizar el sistema RAG."
        
        echo "INFO: Actualizando la memoria del sistema RAG (índice de ChromaDB)..."
        cd "$WORKSPACE_PATH" || { echo "ERROR: No se pudo cambiar al directorio del workspace."; exit 1; }
        source "$VENV_PATH"
        python3 "$INDEX_SCRIPT"
        deactivate
        echo "INFO: Actualización de la memoria del sistema RAG completa."
        
        # Envía la notificación de finalización
        echo "MESSAGE_TO_USER: Shaka, la memoria del sistema RAG (índice de ChromaDB) para PortalCentro ha sido actualizada exitosamente."
    else
        echo "ERROR: Falló la actualización del repositorio: $PULL_OUTPUT"
        echo "MESSAGE_TO_USER: Shaka, ha ocurrido un ERROR al intentar actualizar la memoria de PortalCentro desde el repositorio. Falló el 'git pull'."
        exit 1
    fi
else
    echo "INFO: No se detectaron nuevos cambios en el repositorio remoto. No se requiere ninguna acción."
    # No se envía notificación si no hay cambios, según su directriz.
fi

exit 0
