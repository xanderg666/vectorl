

## ⚙️ Configuración

### 1. Configurar variables de entorno

Copia el archivo de ejemplo y edítalo con tus credenciales:

```bash
cp .env.example .env
```

Edita `.env` con tus valores:

```bash
OCI_COMPARTMENT_ID=ocid1.compartment.oc1..your_compartment_id_here
OCI_ENDPOINT=https://inference.generativeai.us-chicago-1.oci.oraclecloud.com
OCI_CONFIG_FILE=~/.oci/config
OCI_PROFILE=DEFAULT
USE_INSTANCE_PRINCIPAL=false
```

### 2. Asegurar configuración OCI

Verifica que tienes tu archivo de configuración OCI en `~/.oci/config`:

```ini
[DEFAULT]
user=ocid1.user.oc1..your_user_id
fingerprint=your_fingerprint
tenancy=ocid1.tenancy.oc1..your_tenancy_id
region=us-chicago-1
key_file=~/.oci/oci_api_key.pem
```

## 🚀 Ejecución

### Opción 1: Podman

#### Con archivo de configuración OCI

```bash
# Construir imagen
podman build -t grok-chat:latest .

# Ejecutar contenedor
podman run -p 8501:8501 \
  --env-file .env \
  -v ~/.oci:/root/.oci:ro \
  grok-chat:latest
```

#### Con Instance Principal (para OCI Compute)

```bash
# Construir imagen
podman build -t grok-chat:latest .

# Ejecutar contenedor (sin montar ~/.oci)
podman run -p 8501:8501 \
  --env-file .env \
  grok-chat:latest
```

> **Nota**: Cuando `USE_INSTANCE_PRINCIPAL=true` en el archivo `.env`, la aplicación usará Instance Principal para autenticación y no necesita el archivo `~/.oci/config`.

### Opción 2: Ejecución Local (sin contenedor)

```bash
# Instalar dependencias
pip install -r requirements.txt

# Ejecutar aplicación
streamlit run app.py
```
