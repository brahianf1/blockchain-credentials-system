# Guía Hyperledger Fabric + Moodle - VERSIÓN WINDOWS (Enfoque Híbrido)

Esta guía te permite desplegar Hyperledger Fabric y Moodle en Windows usando WSL2, manteniendo los archivos editables en Windows pero ejecutando en Linux para máxima compatibilidad.

## ✅ **Requisitos**
- Windows 10/11 (Build 19041+)
- Docker Desktop para Windows
- WSL2 con Ubuntu 22.04
- 8 GB RAM mínimo, 16 GB recomendado
- 4 vCPUs mínimo
- 50 GB espacio libre en disco

---

## **🖥️ IMPORTANTE: Qué Terminal Usar**

Durante esta guía usarás **DOS tipos de terminal**:

### **PowerShell de Windows** 🔵
- **Prompt**: `PS C:\Users\TuNombre>`
- **Para comandos que empiecen con**: `wsl -d Ubuntu-22.04`
- **Para comandos normales de Windows**: `mkdir`, `cd`, etc.

### **Ubuntu WSL** 🟢  
- **Prompt**: `usuario@PC-Nombre:~$`
- **Para comandos directos de Linux**: `ls`, `docker`, `curl`, etc.
- **Se accede con**: `wsl -d Ubuntu-22.04` desde PowerShell

**🚨 REGLA SIMPLE**:
- Si el comando empieza con `wsl -d Ubuntu-22.04` → **PowerShell**
- Si es un comando directo → **Ubuntu WSL**

---

## **PARTE A: Preparación del Entorno Windows + WSL2**

### 1. Instalar WSL2 y Ubuntu
```powershell
# En PowerShell como administrador
wsl --install -d Ubuntu-22.04
```

Después de la instalación, se abrirá Ubuntu automáticamente. Completa la configuración inicial (usuario y contraseña).

**⚠️ IMPORTANTE**: Después de configurar Ubuntu, **sal de Ubuntu** y regresa a PowerShell para verificar:

```bash
# Desde Ubuntu WSL, ejecuta para salir:
exit
```

Luego en **PowerShell de Windows** (no en Ubuntu):
```powershell
# En PowerShell de Windows
wsl --list --verbose
```

**Salida esperada:**
```
  NAME            STATE           VERSION
* Ubuntu-22.04    Running         2
```

### 2. Instalar Docker Desktop
- Descargar de docker.com
- **IMPORTANTE**: Después de instalar, configurar integración WSL2:
  1. **Abrir Docker Desktop**
  2. **Settings** (⚙️) → **Resources** → **WSL Integration**
  3. **✅ Enable integration with my default WSL distro**
  4. **✅ Ubuntu-22.04** (activar específicamente)
  5. **Apply & Restart**
- Esperar a que Docker Desktop esté completamente iniciado (ícono verde)

### 3. Crear Directorio Base
```powershell
# En PowerShell de Windows
mkdir "$env:USERPROFILE\Documents\blockchain"
# En PowerShell de Windows
cd "$env:USERPROFILE\Documents\blockchain"
```

**💡 Nota:** `$env:USERPROFILE` es equivalente a `C:\Users\TuNombre` y funciona en cualquier PC Windows.

**🚨 IMPORTANTE - Dos Ubicaciones:**
- **Guía**: `$env:USERPROFILE\OneDrive\Documentos\blockchain` (archivos .md)
- **Proyecto**: `$env:USERPROFILE\Documents\blockchain` (fabric-samples, moodle)

### 4. Verificar Integración
```powershell
# En PowerShell de Windows (IMPORTANTE: NO en Ubuntu)
wsl -d Ubuntu-22.04 bash -c "docker --version"
```

**Salida esperada:**
```
Docker version 24.0.5, build ced0996
```

Si ves la versión de Docker, la integración WSL2 está funcionando correctamente.

**🚨 NOTA IMPORTANTE**: Los comandos que empiecen con `wsl -d Ubuntu-22.04` deben ejecutarse desde **PowerShell de Windows**, no desde dentro de Ubuntu.

---

## **PARTE B: Hyperledger Fabric**

### 1. Instalar Dependencias Ubuntu
```powershell
# En PowerShell de Windows - Actualizar Ubuntu e instalar herramientas necesarias
wsl -d Ubuntu-22.04 bash -c "sudo apt update && sudo apt install -y jq curl"
```

**Salida esperada:**
```
Reading package lists... Done
Building dependency tree... Done
The following NEW packages will be installed:
  jq curl
```

### 2. Descargar Fabric Samples
```powershell
# En PowerShell de Windows
git clone https://github.com/hyperledger/fabric-samples.git
```

### 2. Descargar Fabric Samples
```powershell
# En PowerShell de Windows
git clone https://github.com/hyperledger/fabric-samples.git
```

### 3. Instalar Binarios de Fabric
```powershell
# En PowerShell de Windows
wsl -d Ubuntu-22.04 bash -c "cd '/mnt/c/Users/$env:USERNAME/Documents/blockchain/fabric-samples' && curl -sSL https://raw.githubusercontent.com/hyperledger/fabric/main/scripts/install-fabric.sh | bash -s"
```

**Salida esperada:**
```
Installing Hyperledger Fabric binaries
===> Downloading version 2.5.12 platform specific fabric binaries
===> Downloading:  https://github.com/hyperledger/fabric/releases/download/v2.5.12/hyperledger-fabric-linux-amd64-2.5.12.tar.gz
===> Done.
```
La instalación demora 2-3 minutos dependiendo de la conexión.

### 3.1. Configurar Git para Compatibilidad Linux (IMPORTANTE)
```powershell
# En PowerShell de Windows - Ir al directorio fabric-samples (ubicación real)
cd "$env:USERPROFILE\Documents\blockchain\fabric-samples"

# En PowerShell de Windows - Configurar Git para mantener terminaciones LF
git config core.autocrlf input

# En PowerShell de Windows - Forzar reescritura de archivos con nueva configuración
git rm --cached -r .
git reset --hard HEAD

# En PowerShell de Windows - Verificar que se aplicó correctamente
git config core.autocrlf
```

**Salida esperada del último comando:** `input`

**⚠️ IMPORTANTE**: Este comando debe ejecutarse en el directorio fabric-samples real (`Documents\blockchain\fabric-samples`), no en el directorio de la guía (`OneDrive\Documentos\blockchain`).

### 4. Levantar Red de Prueba
```powershell
# En PowerShell de Windows - Limpiar cualquier red existente (seguro para primera vez)
wsl -d Ubuntu-22.04 bash -c "cd '/mnt/c/Users/$env:USERNAME/Documents/blockchain/fabric-samples/test-network' && ./network.sh down"

# En PowerShell de Windows - Limpiar volúmenes Docker para evitar conflictos
wsl -d Ubuntu-22.04 bash -c "docker volume prune -f"

# En PowerShell de Windows - Crear red limpia
wsl -d Ubuntu-22.04 bash -c "cd '/mnt/c/Users/$env:USERNAME/Documents/blockchain/fabric-samples/test-network' && ./network.sh up createChannel"
```

**Salida esperada:**
```
Creating channel 'mychannel'
+ peer channel create -o localhost:7050 --ordererTLSHostnameOverride orderer.example.com
Channel 'mychannel' created
+ peer channel join -b mychannel.block
peer0.org1.example.com joined channel 'mychannel'
+ peer channel join -b mychannel.block  
peer0.org2.example.com joined channel 'mychannel'
```

### 5. Verificar Fabric
```powershell
# En PowerShell de Windows
wsl -d Ubuntu-22.04 bash -c "docker ps"
```

**Salida esperada:**
```
CONTAINER ID   IMAGE                               COMMAND             CREATED         STATUS         PORTS                                            NAMES
1a2b3c4d5e6f   hyperledger/fabric-peer:2.5.12     "peer node start"   2 minutes ago   Up 2 minutes   0.0.0.0:7051->7051/tcp, 0.0.0.0:9444->9444/tcp   peer0.org1.example.com
2b3c4d5e6f7g   hyperledger/fabric-peer:2.5.12     "peer node start"   2 minutes ago   Up 2 minutes   0.0.0.0:9051->9051/tcp, 0.0.0.0:9445->9445/tcp   peer0.org2.example.com
3c4d5e6f7g8h   hyperledger/fabric-orderer:2.5.12  "orderer"           2 minutes ago   Up 2 minutes   0.0.0.0:7050->7050/tcp, 0.0.0.0:7053->7053/tcp   orderer.example.com
```

Deberías ver 3 contenedores ejecutándose: 2 peers + 1 orderer.

---

## **PARTE C: Moodle**

### 1. Crear Directorio
```powershell
# En PowerShell de Windows - Crear directorio en ubicación estándar
mkdir "$env:USERPROFILE\Documents\blockchain\moodle-project"
# En PowerShell de Windows - Navegar al directorio
cd "$env:USERPROFILE\Documents\blockchain\moodle-project"
```

### 2. Crear docker-compose.yml

**Opción A - Crear con PowerShell (Recomendado):**
```powershell
# En PowerShell de Windows - Crear archivo docker-compose.yml
New-Item -ItemType File -Name "docker-compose.yml" -Force
```

**Opción B - Crear con VS Code:**
```powershell
# En PowerShell de Windows - Abrir VS Code en el directorio actual
code .
# Luego crear nuevo archivo: docker-compose.yml
```

**Contenido del archivo docker-compose.yml:**
Copia y pega el siguiente contenido en el archivo:

```yaml
services:
  moodle-app:
    image: bitnami/moodle:4.3.5
    container_name: moodle-app-windows
    ports:
      - "8080:8080"
      - "8443:8443"
    environment:
      MOODLE_DATABASE_TYPE: pgsql
      MOODLE_DATABASE_HOST: moodle-db
      MOODLE_DATABASE_PORT_NUMBER: 5432
      MOODLE_DATABASE_NAME: moodle
      MOODLE_DATABASE_USER: moodle_user
      MOODLE_DATABASE_PASSWORD: secure_password
      MOODLE_USERNAME: admin
      MOODLE_PASSWORD: Admin123!
      MOODLE_EMAIL: admin@localhost.local
      MOODLE_SITE_NAME: "Moodle Híbrido"
      MOODLE_SKIP_BOOTSTRAP: 'no'
    volumes:
      - moodle_data:/bitnami/moodledata
    depends_on:
      - moodle-db
    networks:
      - moodle-network
    restart: unless-stopped

  moodle-db:
    image: postgres:15-alpine
    container_name: moodle-db-windows
    environment:
      POSTGRES_DB: moodle
      POSTGRES_USER: moodle_user
      POSTGRES_PASSWORD: secure_password
      POSTGRES_INITDB_ARGS: '--encoding=UTF8 --lc-collate=C --lc-ctype=C'
    volumes:
      - db_data:/var/lib/postgresql/data
    networks:
      - moodle-network
    restart: unless-stopped
    ports:
      - "5432:5432"

networks:
  moodle-network:
    driver: bridge

volumes:
  db_data:
    driver: local
  moodle_data:
    driver: local
```

### 3. Levantar Moodle
```powershell
# En PowerShell de Windows
wsl -d Ubuntu-22.04 bash -c "cd '/mnt/c/Users/$env:USERNAME/Documents/blockchain/moodle-project' && docker-compose up -d"
```

**Salida esperada:**
```
Creating network "moodle-project_moodle-network" with the default driver
Creating volume "moodle-project_db_data" with local driver
Creating volume "moodle-project_moodle_data" with local driver
Creating moodle-db-windows ... done
Creating moodle-app-windows ... done
```

⚠️ **Importante**: Moodle demora 1-2 minutos en arrancar completamente después de este comando.

### 4. Verificar Instalación
```powershell
# En PowerShell de Windows (ESPERAR 1-2 MINUTOS después del comando anterior)
wsl -d Ubuntu-22.04 bash -c "cd '/mnt/c/Users/$env:USERNAME/Documents/blockchain/moodle-project' && docker-compose ps"

# En PowerShell de Windows (esperar 2-3 minutos)
curl http://localhost:8080
```

**Salida esperada para `docker-compose ps`:**
```
       Name                     Command               State                       Ports                     
----------------------------------------------------------------------------------------------------------
moodle-app-windows    /opt/bitnami/scripts/moodl ...   Up      0.0.0.0:8080->8080/tcp, 0.0.0.0:8443->8443/tcp
moodle-db-windows     docker-entrypoint.sh postgres    Up      0.0.0.0:5432->5432/tcp
```

**Para `curl http://localhost:8080`:** Debería devolver código HTML de Moodle (no error 404 o conexión rechazada).

### 5. Acceder a Moodle
- **URL**: http://localhost:8080
- **Usuario**: admin
- **Contraseña**: Admin123!

⚠️ **Nota**: Si acabas de ejecutar `docker-compose up -d`, **espera 1-2 minutos** antes de acceder. Verás la página de configuración inicial de Moodle en el primer acceso.

---

## **Comandos Básicos de Gestión**

### Detener Todo
```powershell
# En PowerShell de Windows - Detener Moodle
wsl -d Ubuntu-22.04 bash -c "cd '/mnt/c/Users/$env:USERNAME/Documents/blockchain/moodle-project' && docker-compose down"

# En PowerShell de Windows - Detener Fabric
wsl -d Ubuntu-22.04 bash -c "cd '/mnt/c/Users/$env:USERNAME/Documents/blockchain/fabric-samples/test-network' && ./network.sh down"
```

### Iniciar Todo
```powershell
# En PowerShell de Windows - Limpiar y reiniciar Fabric (recomendado)
wsl -d Ubuntu-22.04 bash -c "cd '/mnt/c/Users/$env:USERNAME/Documents/blockchain/fabric-samples/test-network' && ./network.sh down"
wsl -d Ubuntu-22.04 bash -c "docker volume prune -f"
wsl -d Ubuntu-22.04 bash -c "cd '/mnt/c/Users/$env:USERNAME/Documents/blockchain/fabric-samples/test-network' && ./network.sh up createChannel"

# En PowerShell de Windows - Iniciar Moodle
wsl -d Ubuntu-22.04 bash -c "cd '/mnt/c/Users/$env:USERNAME/Documents/blockchain/moodle-project' && docker-compose up -d"
```

### Ver Estado
```powershell
# En PowerShell de Windows
wsl -d Ubuntu-22.04 bash -c "docker ps"
# En PowerShell de Windows
wsl -d Ubuntu-22.04 bash -c "docker network ls"
```

---

## **💡 Explicación de Variables Usadas**

### Variables de Entorno de Windows:
- **`$env:USERNAME`**: Nombre del usuario actual (ej: "flore", "juan", etc.)
- **`$env:USERPROFILE`**: Ruta completa del perfil (ej: "C:\Users\flore")

### ¿Por qué funcionan estas variables?
- Son **variables de entorno del sistema Windows**
- Están **siempre disponibles** en PowerShell
- **NO** necesitas definirlas antes de usarlas
- Funcionan en **cualquier PC Windows** sin importar el nombre del usuario

### Ejemplo práctico:
Si tu usuario es "maria", entonces:
- `$env:USERNAME` = "maria"
- `$env:USERPROFILE` = "C:\Users\maria"
- El comando se convierte en: `cd '/mnt/c/Users/maria/Documents/blockchain'`

---

## **Solución de Problemas**

### Problema: Variable $env:USERNAME no funciona
**Solución**: Ejecuta el comando completo manualmente:
```powershell
# En PowerShell de Windows - Reemplaza TUNOMBRE por tu nombre de usuario real
wsl -d Ubuntu-22.04 bash -c "cd '/mnt/c/Users/TUNOMBRE/Documents/blockchain/fabric-samples' && ..."
```

### Problema: Ruta no encontrada
**Verificar**: 
```powershell
# En PowerShell de Windows - Ver tu ruta actual
pwd
# En PowerShell de Windows - Ver tu nombre de usuario
echo $env:USERNAME
```

### Problema: Docker no responde en WSL
**Solución**:
```powershell
# En PowerShell de Windows - Reiniciar WSL
wsl --shutdown
# En PowerShell de Windows - Iniciar Ubuntu
wsl -d Ubuntu-22.04
```

### Problema: "docker command not found" en WSL
**Síntomas**: 
```
The command 'docker' could not be found in this WSL 2 distro.
We recommend to activate the WSL integration in Docker Desktop settings.
```

**Solución**:
1. **Verificar Docker Desktop está ejecutándose**:
```powershell
# En PowerShell de Windows
Get-Process *docker* | Select-Object Name, Id
```

2. **Reconfigurar integración WSL2**:
   - Abrir **Docker Desktop**
   - **Settings** → **Resources** → **WSL Integration**
   - **✅ Enable integration with my default WSL distro**
   - **✅ Ubuntu-22.04** (activar específicamente)
   - **Apply & Restart**

3. **Esperar y probar**:
```powershell
# En PowerShell de Windows - Esperar 30 segundos después del restart
wsl -d Ubuntu-22.04 bash -c "docker --version"
```

### Problema: "jq: command not found"
**Síntomas**:
```
/mnt/c/Users/.../configUpdate.sh: line 35: jq: command not found
Failed to parse channel configuration, make sure you have jq installed
```

**Causa**: Falta la herramienta `jq` (procesador JSON) en Ubuntu WSL, necesaria para configurar anchor peers.

**Solución**:
```powershell
# En PowerShell de Windows - Instalar jq
wsl -d Ubuntu-22.04 bash -c "sudo apt update && sudo apt install -y jq"

# En PowerShell de Windows - Reintentar comando que falló
wsl -d Ubuntu-22.04 bash -c "cd '/mnt/c/Users/$env:USERNAME/Documents/blockchain/fabric-samples/test-network' && ./network.sh up createChannel"
```

### Problema: "channel already exists" o "ledger already exists"
**Síntomas**:
```
"error": "cannot join: channel already exists"
cannot create ledger from genesis block: ledger [mychannel] already exists with state [ACTIVE]
```

**Causa**: Red Fabric anterior no se limpió completamente, causando conflictos de estado.

**Solución**:
```powershell
# En PowerShell de Windows - Limpiar red existente
wsl -d Ubuntu-22.04 bash -c "cd '/mnt/c/Users/$env:USERNAME/Documents/blockchain/fabric-samples/test-network' && ./network.sh down"

# En PowerShell de Windows - Limpiar volúmenes Docker
wsl -d Ubuntu-22.04 bash -c "docker volume prune -f"

# En PowerShell de Windows - Crear red limpia
wsl -d Ubuntu-22.04 bash -c "cd '/mnt/c/Users/$env:USERNAME/Documents/blockchain/fabric-samples/test-network' && ./network.sh up createChannel"
```

### Problema: "bash\r: No such file or directory"
**Síntomas**:
```
/usr/bin/env: 'bash\r': No such file or directory
```

**Causa Real**: Git configurado con `core.autocrlf=true` convierte LF→CRLF automáticamente, causando terminaciones Windows en scripts Linux.

**Solución Profesional**:
```powershell
# En PowerShell de Windows - Ir al directorio fabric-samples (ubicación real)
cd "$env:USERPROFILE\Documents\blockchain\fabric-samples"
# En PowerShell de Windows - Configurar Git para mantener terminaciones LF
git config core.autocrlf input
# En PowerShell de Windows - Forzar reescritura con nueva configuración
git rm --cached -r .
git reset --hard HEAD
# En PowerShell de Windows - Verificar configuración
git config core.autocrlf
```
**Debe mostrar:** `input`

**Alternativa (Solo si la solución profesional no funciona)**:
```powershell
# En PowerShell de Windows - Instalar dos2unix
wsl -d Ubuntu-22.04 bash -c "sudo apt update && sudo apt install -y dos2unix"

# En PowerShell de Windows - Convertir archivos manualmente
wsl -d Ubuntu-22.04 bash -c "cd '/mnt/c/Users/$env:USERNAME/Documents/blockchain/fabric-samples' && find . -name '*.sh' -type f -exec dos2unix {} \;"
```

**Alternativa (Solo si la solución profesional no funciona)**:
```powershell
# En PowerShell de Windows - Instalar dos2unix
wsl -d Ubuntu-22.04 bash -c "sudo apt update && sudo apt install -y dos2unix"

# En PowerShell de Windows - Convertir archivos manualmente
wsl -d Ubuntu-22.04 bash -c "cd '/mnt/c/Users/$env:USERNAME/Documents/blockchain/fabric-samples' && find . -name '*.sh' -type f -exec dos2unix {} \;"
```

---

## **✅ Resultado Final**

Tendrás:
- **Hyperledger Fabric**: Red test-network funcionando
- **Moodle**: LMS en http://localhost:8080
- **Aislamiento**: Cada sistema en su propia red Docker
- **Archivos editables**: En Windows para desarrollo fácil
- **Ejecución Linux**: En WSL2 para compatibilidad total

**🎯 Listo para la Fase 2**: Backend que conecte ambos sistemas.
