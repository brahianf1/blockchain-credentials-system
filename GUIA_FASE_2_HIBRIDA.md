# Guía Fase 2 del MVP - Creando el Puente (VERSIÓN WINDOWS HÍBRIDA)

En esta fase, construiremos el software que conecta la plataforma Moodle con nuestro futuro sistema de credenciales. Al finalizar, Moodle podrá enviar una notificación a nuestro backend cada vez que un alumno complete un curso.

## ✅ **Prerrequisitos**
- **Fase 1 completada**: Hyperledger Fabric y Moodle funcionando
- Windows 11 con WSL2 Ubuntu 22.04
- Docker Desktop funcionando
- VS Code con extensión WSL

---

## **🖥️ IMPORTANTE: Qué Terminal Usar**

### **PowerShell de Windows** 🔵
- **Prompt**: `PS C:\Users\TuNombre\Documents\blockchain>`
- **Para**: Comandos que empiecen con `wsl -d Ubuntu-22.04`
- **Para**: Navegación en Windows y edición con VS Code

### **Ubuntu WSL** 🟢  
- **Prompt**: `usuario@PC-Nombre:/mnt/c/Users/TuNombre/Documents/blockchain$`
- **Para**: Comandos Docker, Node.js, npm, curl
- **Se accede con**: `wsl -d Ubuntu-22.04` desde PowerShell

**🚨 REGLA SIMPLE**:
- Si el comando empieza con `wsl -d Ubuntu-22.04` → **PowerShell**
- Si es un comando directo → **Ubuntu WSL**

**📁 VARIABLES DE RUTA**:
- `$env:USERPROFILE` = Directorio del usuario en Windows (ej: `C:\Users\TuNombre`)
- `$env:USERNAME` = Nombre del usuario actual (ej: "flore", "juan", etc.)

**Ejemplo**: Si tu usuario es "maria":
- `$env:USERPROFILE` = `C:\Users\maria`  
- `$env:USERNAME` = "maria"
- Ruta final WSL: `/mnt/c/Users/maria/Documents/blockchain`

---

## **PARTE A: Creación del Backend en Python**

### 0. Verificar Python en Ubuntu WSL

```powershell
# En PowerShell - Verificar si Python está instalado en WSL
wsl -d Ubuntu-22.04 bash -c "python3 --version"
wsl -d Ubuntu-22.04 bash -c "pip3 --version"
```

Si no están instalados, instálalos desde PowerShell:

```powershell
# En PowerShell - Instalar Python 3 en Ubuntu WSL
wsl -d Ubuntu-22.04 bash -c "sudo apt update && sudo apt install -y python3 python3-pip python3-venv"

# Verificar instalación
wsl -d Ubuntu-22.04 bash -c "python3 --version"
wsl -d Ubuntu-22.04 bash -c "pip3 --version"
```

### 1. Preparación del Proyecto

**En PowerShell** - Crear directorio en Windows:
```powershell
# En PowerShell - Crear directorio para backend
cd "$env:USERPROFILE\Documents\blockchain"
mkdir backend-app
cd backend-app
mkdir controller
```

### 2. Creación del Servidor API Básico con FastAPI

**En PowerShell** - Crear requirements.txt:
```powershell
# En PowerShell - Crear archivo de dependencias
cd "$env:USERPROFILE\Documents\blockchain\backend-app\controller"
code requirements.txt
```

**Contenido para `requirements.txt`**:
```
# PEGAR AQUI el contenido del archivo requirements.txt del código fuente
```

**En PowerShell** - Crear archivo con VS Code:
```powershell
# En PowerShell - Crear y abrir archivo en VS Code
cd "$env:USERPROFILE\Documents\blockchain\backend-app\controller"
code app.py
```

**Contenido para `app.py`** (código simplificado para Fase 2):
```python
#!/usr/bin/env python3
"""
Controller Python - Integración Moodle + Backend (Fase 2)
Backend básico que recibe notificaciones de Moodle
"""

import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración FastAPI
app = FastAPI(
    title="Universidad - Backend Fase 2",
    description="Backend básico que recibe notificaciones de Moodle",
    version="1.0.0"
)

# CORS para Moodle
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelo para datos de Moodle
class MoodleCredentialRequest(BaseModel):
    """Solicitud de credencial desde Moodle"""
    userId: str = Field(..., description="ID del usuario en Moodle")
    userEmail: str = Field(..., description="Email del usuario")
    userName: str = Field(..., description="Nombre completo del usuario")
    courseId: str = Field(..., description="ID del curso en Moodle")
    courseName: str = Field(..., description="Nombre del curso")
    completionDate: str = Field(..., description="Fecha de finalización ISO 8601")

@app.get("/health")
async def health_check():
    """Health check del Backend"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "message": "Backend Fase 2 funcionando correctamente"
    }

@app.post("/api/issue-credential")
async def issue_credential(moodle_request: MoodleCredentialRequest):
    """
    Endpoint que recibe notificaciones desde Moodle
    En Fase 2: Solo registra los datos recibidos
    """
    try:
        logger.info("=" * 50)
        logger.info("🎓 ¡Notificación de curso completado recibida!")
        logger.info(f"👤 Estudiante: {moodle_request.userName}")
        logger.info(f"📧 Email: {moodle_request.userEmail}")
        logger.info(f"📚 Curso: {moodle_request.courseName}")
        logger.info(f"📅 Fecha: {moodle_request.completionDate}")
        logger.info("=" * 50)
        
        # En Fase 3: Aquí irá la lógica de emisión de credenciales
        
        return {
            "status": "success",
            "message": "Notificación recibida correctamente",
            "data": {
                "student": moodle_request.userName,
                "course": moodle_request.courseName,
                "processed_at": datetime.utcnow().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error procesando solicitud: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error procesando solicitud: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
```

Guarda el archivo (Ctrl + S) y cierra VS Code.

### 3. "Dockerizando" el Backend

**En PowerShell** - Crear Dockerfile:
```powershell
# En PowerShell - Crear Dockerfile con VS Code
cd "$env:USERPROFILE\Documents\blockchain\backend-app"
code Dockerfile.controller
```

**Contenido para `Dockerfile.controller`**:
```dockerfile
# Usar imagen oficial de Python
FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar requirements
COPY controller/requirements.txt .

# Instalar dependencias
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código del controller
COPY controller/ .

# Exponer puerto
EXPOSE 3000

# Comando para iniciar la aplicación
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "3000"]
```

Guarda y cierra VS Code.

---

## **PARTE B: Creación del Plugin para Moodle**

### 1. Creación de los Archivos del Plugin

**En PowerShell** - Crear estructura de directorios:
```powershell
# En PowerShell - Crear estructura del plugin
cd "$env:USERPROFILE\Documents\blockchain"
mkdir -p moodle-plugin\credenciales\classes\observer
mkdir -p moodle-plugin\credenciales\db
```

**En PowerShell** - Crear archivos del plugin:
```powershell
# En PowerShell - Crear archivos PHP con VS Code
cd "$env:USERPROFILE\Documents\blockchain\moodle-plugin\credenciales"
code version.php
```

**Contenido para `version.php`**:
```php
<?php
defined('MOODLE_INTERNAL') || die();
$plugin->component = 'local_credenciales';
$plugin->version   = 2024080200; // YYYYMMDDXX
$plugin->requires  = 2021112900; // Moodle 4.0
```

Guarda y crea el siguiente archivo:
```powershell
# En PowerShell
cd "$env:USERPROFILE\Documents\blockchain\moodle-plugin\credenciales\db"
code events.php
```

**Contenido para `events.php`**:
```php
<?php
defined('MOODLE_INTERNAL') || die();
$observers = array(
    array(
        'eventname'   => '\core\event\course_completed',
        'callback'    => '\local_credenciales\observer\credenciales_observer::course_completed',
    ),
);
```

Guarda y crea el archivo observador:
```powershell
# En PowerShell
cd "$env:USERPROFILE\Documents\blockchain\moodle-plugin\credenciales\classes\observer"
code credenciales_observer.php
```

**Contenido para `credenciales_observer.php`**:
```php
<?php
namespace local_credenciales\observer;

defined('MOODLE_INTERNAL') || die();

class credenciales_observer {
    public static function course_completed(\core\event\course_completed $event) {
        global $DB;

        // Obtener datos del evento
        $userid = $event->relateduserid;
        $courseid = $event->courseid;

        $user = $DB->get_record('user', array('id' => $userid));
        $course = $DB->get_record('course', array('id' => $courseid));

        // Preparar los datos para enviar al backend
        $data = array(
            'userId' => $user->id,
            'userEmail' => $user->email,
            'userName' => fullname($user),
            'courseId' => $course->id,
            'courseName' => $course->fullname,
            'completionDate' => date('c', $event->timecreated)
        );

        // URL del endpoint de nuestro backend
        $url = 'http://python-controller-fase2:3000/api/issue-credential';

        // Configurar la petición cURL
        $ch = curl_init($url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_POST, true);
        curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
        curl_setopt($ch, CURLOPT_HTTPHEADER, array(
            'Content-Type: application/json',
            'Content-Length: ' . strlen(json_encode($data))
        ));

        // Configurar timeout y manejo de errores
        curl_setopt($ch, CURLOPT_TIMEOUT, 30);
        curl_setopt($ch, CURLOPT_CONNECTTIMEOUT, 10);

        // Ejecutar la petición
        $response = curl_exec($ch);
        $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        
        if (curl_errno($ch)) {
            error_log('Error en cURL: ' . curl_error($ch));
        } else if ($httpCode !== 200) {
            error_log('Error HTTP: ' . $httpCode . ' - Respuesta: ' . $response);
        } else {
            error_log('Credencial enviada exitosamente para usuario: ' . $user->email);
        }
        
        curl_close($ch);
    }
}
```

---

## **PARTE C: Conexión y Despliegue Final**

### 1. Identificar Redes de Docker

**En PowerShell** - Ver redes existentes:
```powershell
# En PowerShell - Listar redes Docker
wsl -d Ubuntu-22.04 bash -c "docker network ls"
```

Busca las redes:
- `moodle-project_moodle-net` (o similar)
- `fabric_test` (o similar)

### 2. Crear docker-compose.yml para el Backend

**En PowerShell** - Crear docker-compose.yml:
```powershell
# En PowerShell - Crear docker-compose para backend
cd "$env:USERPROFILE\Documents\blockchain\backend-app"
code docker-compose.yml
```

**Contenido para `docker-compose.yml`** (ajusta los nombres de redes según tu output anterior):
```yaml
version: '3.8'

services:
  python-controller:
    build:
      context: .
      dockerfile: Dockerfile.controller
    container_name: python-controller-fase2
    restart: unless-stopped
    ports:
      - "3000:3000"
    networks:
      - moodle_network
    environment:
      - ENVIRONMENT=development

networks:
  moodle_network:
    external:
      name: moodle-project_moodle-network
```

### 3. Despliegue y Pruebas

**En PowerShell** - Construir y levantar backend:
```powershell
# En PowerShell - Navegar y construir backend
wsl -d Ubuntu-22.04 bash -c "cd '/mnt/c/Users/$env:USERNAME/Documents/blockchain/backend-app' && docker-compose up --build -d"
```

**En PowerShell** - Verificar que está funcionando:
```powershell
# En PowerShell - Verificar estado del contenedor
wsl -d Ubuntu-22.04 bash -c "docker ps | grep python-controller"

# Probar endpoint de salud
wsl -d Ubuntu-22.04 bash -c "curl http://localhost:3000/health"
```

**Salida esperada del health check:**
```json
{
  "status": "healthy",
  "timestamp": "2024-08-04T15:30:00.000Z",
  "message": "Backend Fase 2 funcionando correctamente"
}
```

### 4. Instalar Plugin en Moodle

**En PowerShell** - Copiar plugin a Moodle:
```powershell
# En PowerShell - Obtener nombre del contenedor de Moodle
wsl -d Ubuntu-22.04 bash -c "docker ps | grep moodle"

# Copiar plugin al contenedor (ajusta el nombre del contenedor)
wsl -d Ubuntu-22.04 bash -c "docker cp '/mnt/c/Users/$env:USERNAME/Documents/blockchain/moodle-plugin/credenciales/' moodle-app:/bitnami/moodle/local/"

# Reiniciar Moodle para detectar el plugin
wsl -d Ubuntu-22.04 bash -c "docker restart moodle-app"
```

### 5. Configurar Plugin en Moodle

1. **Abrir Moodle**: Ve a `http://localhost:8080`
2. **Iniciar sesión** como administrador
3. **Actualizar base de datos**: Moodle detectará el nuevo plugin y pedirá actualizar
4. **Seguir pasos** de instalación del plugin

### 6. Prueba Completa del Flujo

#### Crear Curso de Prueba:
1. En Moodle, crear un **nuevo curso**
2. Ir a **"Configuración del curso" > "Finalización del curso"**
3. Habilitar **"Seguimiento de finalización"**
4. Configurar criterio simple (ej: "El estudiante debe ver esta actividad para completar")

#### Crear Usuario de Prueba:
1. Crear un **nuevo usuario**
2. **Inscribir** al usuario en el curso

#### Probar Finalización:
1. **Iniciar sesión** como usuario de prueba
2. **Completar** la actividad del curso
3. **Verificar logs** del backend:

```powershell
# En PowerShell - Ver logs del backend
wsl -d Ubuntu-22.04 bash -c "docker logs python-controller-fase2 -f"
```

### 7. Solución de Problemas Comunes

**Si no ves logs en el backend:**
```powershell
# En PowerShell - Verificar conectividad de redes
wsl -d Ubuntu-22.04 bash -c "docker exec moodle-app ping python-controller-fase2"

# Verificar que el backend está corriendo
wsl -d Ubuntu-22.04 bash -c "docker exec python-controller-fase2 curl http://localhost:3000/health"
```

**Si hay problemas de permisos:**
```powershell
# En PowerShell - Verificar permisos del plugin
wsl -d Ubuntu-22.04 bash -c "docker exec moodle-app ls -la /bitnami/moodle/local/credenciales/"
```

---

## ✅ **Hito Final de la Fase 2**

¡Felicidades! Has construido el sistema nervioso de tu proyecto. Ahora tienes:

✅ **Backend robusto** en Python con FastAPI ejecutándose en contenedor Docker
✅ **Plugin de Moodle** que observa eventos de finalización de cursos  
✅ **Canal de comunicación** funcional entre Moodle y backend
✅ **Código editable** en Windows con VS Code pero ejecutándose en Linux
✅ **Logs y debugging** accesibles para solución de problemas

**Verificación final:**
- Backend responde en `http://localhost:3000/health`
- Plugin instalado y activo en Moodle
- Al completar un curso, aparecen logs en el backend con datos del estudiante

La Fase 3 utilizará estos datos para emitir credenciales verificables reales usando Hyperledger Aries y Fabric.

---

## **🚀 ATAJO RECOMENDADO: Saltar a Fase 4**

**Si quieres la implementación final y funcional**, puedes **saltar directamente a la Guía Fase 4** que contiene la implementación completa en Python + ACA-Py que está realmente funcionando en el código fuente.

**La Fase 4 incluye:**
- ✅ **Todo lo de la Fase 2** (backend + plugin Moodle)
- ✅ **Credenciales W3C reales** (no simulaciones)
- ✅ **ACA-Py integrado** (Aries Cloud Agent Python)
- ✅ **Script de inicio automatizado** (`start.sh`)
- ✅ **Documentación completa** de la implementación final

**La Fase 3** documenta la implementación original con Node.js que presentó problemas de dependencias y fue reemplazada por la solución Python de la Fase 4.
