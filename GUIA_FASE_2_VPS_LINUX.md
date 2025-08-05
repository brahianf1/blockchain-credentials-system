# Guía Fase 2 del MVP - Creando el Puente (VERSIÓN VPS LINUX)

En esta fase, construiremos el software que conecta la plataforma Moodle con nuestro futuro sistema de credenciales. Al finalizar, Moodle podrá enviar una notificación a nuestro backend cada vez que un alumno complete un curso.

## ✅ **Prerrequisitos**
- **Fase 1 completada**: Hyperledger Fabric y Moodle funcionando en VPS
- VPS Ubuntu 22.04 LTS
- Docker y Docker Compose instalados
- Acceso SSH al VPS

---

## **PARTE A: Creación del Backend en Node.js**

Este servicio será una API REST que escuchará las peticiones de nuestro plugin de Moodle. Lo construiremos y ejecutaremos también en un contenedor Docker.

### 0. Instalar Node.js (si no está instalado)

Para poder ejecutar comandos como npm, nuestro VPS necesita tener instalado Node.js.

**Instalar Node.js y npm:**
```bash
# Añadir el repositorio oficial de NodeSource
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -

# Instalar Node.js (que incluye npm)
sudo apt-get install -y nodejs

# Verificar la instalación
node -v
npm -v
```

Deberías ver las versiones de Node.js y npm instaladas.

### 1. Preparación del Proyecto

**Crear directorio para el proyecto:**
```bash
# Crear y navegar al directorio del backend
cd ~
mkdir backend-app
cd backend-app
```

**Inicializar proyecto Node.js:**
```bash
# Crear package.json
npm init -y

# Instalar dependencias necesarias
npm install express
```

### 2. Creación del Servidor API Básico

**Crear el archivo principal:**
```bash
nano index.js
```

**Contenido para `index.js`:**
```javascript
const express = require('express');
const app = express();
const PORT = 3000;

// Middleware para que Express pueda entender JSON en el cuerpo de las peticiones
app.use(express.json());

// Endpoint que recibirá la notificación de Moodle
app.post('/api/issue-credential', (req, res) => {
  console.log('============================================');
  console.log('¡Notificación recibida desde Moodle!');
  console.log('Datos recibidos:', req.body);
  console.log('============================================');

  // En un futuro, aquí irá la lógica para emitir la credencial con Aries y Fabric.

  res.status(200).json({ message: 'Notificación recibida correctamente.' });
});

// Endpoint de salud para verificar que el servidor está funcionando
app.get('/health', (req, res) => {
  res.status(200).json({ status: 'OK', message: 'Backend funcionando correctamente' });
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`Servidor backend escuchando en el puerto ${PORT}`);
});
```

Guarda y cierra el archivo (Ctrl + X, Y, Enter).

### 3. "Dockerizando" el Backend

**Crear Dockerfile:**
```bash
# Crear Dockerfile en el directorio backend-app
nano Dockerfile
```

**Contenido para `Dockerfile`:**
```dockerfile
# Usar una imagen oficial de Node.js como base
FROM node:18-alpine

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR /usr/src/app

# Copiar los archivos de dependencias
COPY package*.json ./

# Instalar las dependencias del proyecto
RUN npm install

# Copiar el resto del código de la aplicación
COPY . .

# Exponer el puerto en el que corre la aplicación
EXPOSE 3000

# Comando para iniciar la aplicación
CMD [ "node", "index.js" ]
```

Guarda y cierra el archivo.

---

## **PARTE B: Creación del Plugin para Moodle**

Este plugin es el que "observará" Moodle y activará la llamada a nuestra API.

### 1. Creación de los Archivos del Plugin

**Crear la estructura de directorios:**
```bash
cd ~
mkdir -p moodle-plugin/credenciales/classes/observer
mkdir -p moodle-plugin/credenciales/db
```

**Crear el archivo de versión (version.php):**
```bash
nano moodle-plugin/credenciales/version.php
```

**Contenido:**
```php
<?php
defined('MOODLE_INTERNAL') || die();
$plugin->component = 'local_credenciales';
$plugin->version   = 2024080200; // YYYYMMDDXX
$plugin->requires  = 2021112900; // Moodle 4.0
```

**Crear el archivo de eventos (events.php):**
```bash
nano moodle-plugin/credenciales/db/events.php
```

**Contenido:**
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

**Crear el archivo observador (credenciales_observer.php):**
```bash
nano moodle-plugin/credenciales/classes/observer/credenciales_observer.php
```

**Contenido:**
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
        $url = 'http://backend-app:3000/api/issue-credential';

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

Ahora que tenemos todos los componentes, los conectaremos y los desplegaremos.

### 1. Conectando las Redes de Docker

**Identificar los nombres de las redes:**
```bash
docker network ls
```

Busca los nombres de las redes de Moodle y Fabric. Deberían ser similares a:
- `moodle-project_moodle-net` 
- `fabric_test`

**Crear el docker-compose.yml para el backend:**
```bash
cd ~/backend-app
nano docker-compose.yml
```

**Contenido (ajusta los nombres de las redes según tu output anterior):**
```yaml
version: '3.8'

services:
  backend-app:
    build: .
    container_name: backend-app
    restart: unless-stopped
    ports:
      - "3000:3000" # Exponer el puerto 3000 del contenedor al puerto 3000 del VPS
    networks:
      - moodle_network # Conectar a la red de Moodle
      - fabric_network # Conectar a la red de Fabric
    environment:
      - NODE_ENV=production

networks:
  moodle_network:
    external:
      name: moodle-project_moodle-net # Nombre externo de la red de Moodle
  fabric_network:
    external:
      name: fabric_test # Nombre externo de la red de Fabric
```

### 2. Despliegue y Pruebas

**Levantar el contenedor del backend:**
```bash
cd ~/backend-app
docker-compose up --build -d
```

**Verificar que está funcionando:**
```bash
# Verificar estado del contenedor
docker ps | grep backend-app

# Probar endpoint de salud
curl http://localhost:3000/health
```

**Instalar el plugin en Moodle:**

1. **Obtener el nombre del contenedor de Moodle:**
```bash
docker ps | grep moodle
```

2. **Copiar el plugin al contenedor** (ajusta el nombre del contenedor):
```bash
# Ejemplo: si tu contenedor se llama moodle-app
docker cp ~/moodle-plugin/credenciales/ moodle-app:/bitnami/moodle/local/
```

3. **Reiniciar el contenedor de Moodle:**
```bash
docker restart moodle-app
```

### 3. Configurar Plugin en Moodle

1. **Abrir Moodle**: Ve a `http://TU_DIRECCION_IP:8080`
2. **Iniciar sesión** como administrador
3. **Actualizar base de datos**: Moodle detectará el nuevo plugin y pedirá actualizar
4. **Seguir pasos** de instalación del plugin

### 4. Prueba del Flujo Completo

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

```bash
docker logs backend-app -f
```

¡Deberías ver el mensaje "¡Notificación recibida desde Moodle!" junto con los datos del usuario y del curso!

### 5. Solución de Problemas Comunes

**Si no ves logs en el backend:**
```bash
# Verificar conectividad de redes
docker exec moodle-app ping backend-app

# Verificar que el backend está corriendo
docker exec backend-app wget -qO- http://localhost:3000/health
```

**Si hay problemas de permisos:**
```bash
# Verificar permisos del plugin
docker exec moodle-app ls -la /bitnami/moodle/local/credenciales/
```

**Si el contenedor no se conecta a las redes:**
```bash
# Verificar redes disponibles
docker network ls

# Inspeccionar una red específica
docker network inspect moodle-project_moodle-net
```

---

## ✅ **Hito Final de la Fase 2**

¡Felicidades! Has construido el sistema nervioso de tu proyecto. Ahora tienes:

✅ **Backend robusto** en Node.js "dockerizado" y ejecutándose en tu VPS
✅ **Plugin de Moodle** que observa eventos de finalización de cursos
✅ **Canal de comunicación** funcional y seguro entre Moodle y backend
✅ **Redes Docker** configuradas para comunicación entre servicios
✅ **Manejo de errores** y logging para debugging

**Verificación final:**
- Backend responde en `http://TU_DIRECCION_IP:3000/health`
- Plugin instalado y activo en Moodle
- Al completar un curso, aparecen logs en el backend con datos del estudiante

La Fase 3 utilizará estos datos para emitir credenciales verificables reales usando Hyperledger Aries y Fabric.
