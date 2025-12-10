# 📦 Guía de Instalación de Podman en Oracle Linux 9

Esta guía proporciona instrucciones paso a paso para instalar y configurar Podman en Oracle Linux 9.

## 📋 Prerequisitos

- Oracle Linux 9 instalado y actualizado
- Acceso root o privilegios sudo
- Conexión a Internet

## 🚀 Instalación

### Paso 1: Actualizar el sistema

```bash
sudo dnf update -y
```

### Paso 2: Instalar Podman

Podman está disponible en los repositorios oficiales de Oracle Linux 9:

```bash
sudo dnf install -y podman
```

### Paso 3: Verificar la instalación

```bash
podman --version
```

Deberías ver algo como:
```
podman version 4.x.x
```

## ⚙️ Configuración Inicial

### Configurar registros de contenedores

Edita el archivo de configuración de registros:

```bash
sudo vi /etc/containers/registries.conf
```

Asegúrate de que incluya los registros principales:

```toml
[registries.search]
registries = ['docker.io', 'quay.io', 'registry.access.redhat.com']

[registries.insecure]
registries = []

[registries.block]
registries = []
```

### Configurar almacenamiento (opcional)

Si necesitas ajustar la configuración de almacenamiento:

```bash
sudo vi /etc/containers/storage.conf
```

## 🔧 Configuración para Usuario No-Root (Rootless)

Podman puede ejecutarse sin privilegios root. Para configurarlo:

### Paso 1: Habilitar namespaces de usuario

```bash
# Verificar si están habilitados
cat /proc/sys/user/max_user_namespaces

# Si el valor es 0, habilitarlos
echo "user.max_user_namespaces=28633" | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### Paso 2: Configurar subuid y subgid

```bash
# Verificar configuración actual
grep $USER /etc/subuid
grep $USER /etc/subgid

# Si no existen, agregarlos (reemplaza 'username' con tu usuario)
echo "username:100000:65536" | sudo tee -a /etc/subuid
echo "username:100000:65536" | sudo tee -a /etc/subgid
```

### Paso 3: Probar ejecución rootless

```bash
# Como usuario normal (sin sudo)
podman run --rm hello-world
```

## 🐳 Comandos Básicos de Podman

### Gestión de imágenes

```bash
# Buscar imágenes
podman search python

# Descargar imagen
podman pull python:3.11-slim

# Listar imágenes locales
podman images

# Eliminar imagen
podman rmi python:3.11-slim
```

### Gestión de contenedores

```bash
# Ejecutar contenedor
podman run -d --name mi-contenedor python:3.11-slim sleep infinity

# Listar contenedores en ejecución
podman ps

# Listar todos los contenedores
podman ps -a

# Detener contenedor
podman stop mi-contenedor

# Iniciar contenedor
podman start mi-contenedor

# Eliminar contenedor
podman rm mi-contenedor

# Ver logs
podman logs mi-contenedor

# Ejecutar comando en contenedor
podman exec -it mi-contenedor bash
```

### Construcción de imágenes

```bash
# Construir desde Dockerfile
podman build -t mi-imagen:latest .

# Construir con nombre específico
podman build -f Dockerfile -t mi-app:v1.0 .
```

## 🔥 Configuración de Firewall

Si necesitas exponer puertos, configura el firewall:

```bash
# Abrir puerto 8501 (ejemplo para Streamlit)
sudo firewall-cmd --permanent --add-port=8501/tcp
sudo firewall-cmd --reload

# Verificar
sudo firewall-cmd --list-ports
```

## 🌐 Habilitar Podman Socket (opcional)

Para usar Podman con herramientas que esperan Docker socket:

```bash
# Habilitar socket de usuario
systemctl --user enable --now podman.socket

# Verificar estado
systemctl --user status podman.socket

# Obtener ruta del socket
echo $XDG_RUNTIME_DIR/podman/podman.sock
```

## 📊 Podman Compose

Para usar archivos docker-compose.yml con Podman:

```bash
# Instalar podman-compose
sudo dnf install -y podman-compose

# Verificar instalación
podman-compose --version

# Usar igual que docker-compose
podman-compose up -d
podman-compose down
```

## ✅ Verificación Completa

Ejecuta estos comandos para verificar que todo funciona:

```bash
# 1. Verificar versión
podman --version

# 2. Verificar información del sistema
podman info

# 3. Ejecutar contenedor de prueba
podman run --rm hello-world

# 4. Verificar que puede construir imágenes
echo "FROM alpine:latest" > Dockerfile.test
echo "CMD echo 'Podman funciona correctamente'" >> Dockerfile.test
podman build -t test:latest -f Dockerfile.test .
podman run --rm test:latest
rm Dockerfile.test

# 5. Verificar networking
podman run --rm -p 8080:80 nginx:alpine
# Presiona Ctrl+C para detener
```

## 🔍 Solución de Problemas

### Error: "permission denied"

```bash
# Verificar permisos de usuario
id -u
id -g

# Reiniciar sesión después de cambios en subuid/subgid
```

### Error: "network not found"

```bash
# Recrear red por defecto
podman network create podman

# Listar redes
podman network ls
```

### Error: "storage configuration"

```bash
# Limpiar almacenamiento
podman system prune -a

# Reiniciar servicio (rootless)
systemctl --user restart podman
```

### Verificar logs del sistema

```bash
# Logs de Podman
journalctl --user -u podman

# Logs del sistema
sudo journalctl -xe | grep podman
```

## 📚 Recursos Adicionales

- [Documentación oficial de Podman](https://docs.podman.io/)
- [Podman en Oracle Linux](https://docs.oracle.com/en/operating-systems/oracle-linux/podman/)
- [Migración de Docker a Podman](https://podman.io/getting-started/migration)

## 🎯 Siguiente Paso

Una vez instalado Podman, puedes desplegar la aplicación Grok-4 Chat:

```bash
cd app-podman
podman build -t grok-chat:latest .
podman run -p 8501:8501 --env-file .env grok-chat:latest
```

---

**Nota**: Podman es compatible con comandos de Docker. Puedes crear un alias si prefieres usar `docker` en lugar de `podman`:

```bash
echo "alias docker=podman" >> ~/.bashrc
source ~/.bashrc
```
