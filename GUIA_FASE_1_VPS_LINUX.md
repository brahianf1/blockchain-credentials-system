# Guía Hyperledger Fabric + Moodle - VERSIÓN VPS LINUX

Esta guía actualizada te permite desplegar Hyperledger Fabric y Moodle en un servidor virtual (VPS) con Ubuntu 22.04, ideal para producción o desarrollo remoto.

## ✅ **Requisitos**
- VPS Ubuntu 22.04 LTS
- 4 GB RAM mínimo, 8 GB recomendado  
- 2 vCPUs mínimo, 4 vCPUs recomendado
- 40 GB espacio en disco
- Acceso SSH root

---

## **PARTE A: Preparación del VPS**

### 1. Conectar al VPS
```bash
ssh root@TU_DIRECCION_IP
```

### 2. Actualizar Sistema
```bash
apt update && apt upgrade -y
```

### 3. Instalar Herramientas Esenciales
```bash
apt install git curl wget docker.io docker-compose jq nano -y
```

### 4. Verificar Instalación
```bash
docker --version
docker-compose --version
```

**Salida esperada:**
```
Docker version 24.0.5, build ced0996
Docker Compose version v2.20.2
```
Si ves las versiones, Docker está correctamente instalado.

### 5. Configurar Docker (opcional)
```bash
# Agregar usuario al grupo docker (si no usas root)
usermod -aG docker $USER
newgrp docker
```

---

## **PARTE B: Hyperledger Fabric**

### 1. Descargar Fabric Samples
```bash
cd ~
git clone https://github.com/hyperledger/fabric-samples.git
```

### 2. Instalar Binarios de Fabric
```bash
cd fabric-samples
curl -sSL https://raw.githubusercontent.com/hyperledger/fabric/main/scripts/install-fabric.sh | bash -s
```

**Salida esperada:**
```
Installing Hyperledger Fabric binaries
===> Downloading version 2.5.12 platform specific fabric binaries
===> Downloading:  https://github.com/hyperledger/fabric/releases/download/v2.5.12/hyperledger-fabric-linux-amd64-2.5.12.tar.gz
===> Done.
```
La instalación puede tomar 2-3 minutos dependiendo de la conexión.

### 3. Levantar Red de Prueba
```bash
cd test-network
./network.sh up createChannel
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
Si ves "joined channel 'mychannel'" para ambos peers, la red está funcionando correctamente.

### 4. Verificar Fabric
```bash
docker ps
docker network ls
```

**Salida esperada para `docker ps`:**
```
CONTAINER ID   IMAGE                               COMMAND             CREATED         STATUS         PORTS                                            NAMES
1a2b3c4d5e6f   hyperledger/fabric-peer:2.5.12     "peer node start"   2 minutes ago   Up 2 minutes   0.0.0.0:7051->7051/tcp, 0.0.0.0:9444->9444/tcp   peer0.org1.example.com
2b3c4d5e6f7g   hyperledger/fabric-peer:2.5.12     "peer node start"   2 minutes ago   Up 2 minutes   0.0.0.0:9051->9051/tcp, 0.0.0.0:9445->9445/tcp   peer0.org2.example.com
3c4d5e6f7g8h   hyperledger/fabric-orderer:2.5.12  "orderer"           2 minutes ago   Up 2 minutes   0.0.0.0:7050->7050/tcp, 0.0.0.0:7053->7053/tcp   orderer.example.com
```

**Salida esperada para `docker network ls`:**
```
NETWORK ID     NAME                         DRIVER    SCOPE
abcd1234efgh   fabric_test                  bridge    local
```

Deberías ver 3 contenedores ejecutándose (2 peers + 1 orderer) y la red "fabric_test".

---

## **PARTE C: Moodle**

### 1. Crear Directorio del Proyecto
```bash
cd ~
mkdir moodle-project
cd moodle-project
```

### 2. Crear docker-compose.yml
```bash
nano docker-compose.yml
```

Pega este contenido:

```yaml
services:
  moodle-app:
    image: bitnami/moodle:4.3.5
    container_name: moodle-app-vps
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
      MOODLE_EMAIL: admin@example.com
      MOODLE_SITE_NAME: "Moodle VPS"
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
    container_name: moodle-db-vps
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

networks:
  moodle-network:
    driver: bridge

volumes:
  db_data:
    driver: local
  moodle_data:
    driver: local
```

Guarda y cierra (Ctrl+X, Y, Enter).

### 3. Levantar Moodle
```bash
docker-compose up -d
```

**Salida esperada:**
```
Creating network "moodle-project_moodle-network" with the default driver
Creating volume "moodle-project_db_data" with local driver
Creating volume "moodle-project_moodle_data" with local driver
Creating moodle-db-vps ... done
Creating moodle-app-vps ... done
```

⚠️ **Importante**: Moodle demora 1-2 minutos en arrancar completamente. NO te preocupes si no responde inmediatamente.

### 4. Verificar Instalación
```bash
# Ver estado de contenedores
docker-compose ps

# Ver logs si hay problemas (ESPERAR 1-2 MINUTOS después de docker-compose up)
docker-compose logs moodle-app
```

**Salida esperada para `docker-compose ps`:**
```
       Name                     Command               State                       Ports                     
----------------------------------------------------------------------------------------------------------
moodle-app-vps    /opt/bitnami/scripts/moodl ...   Up      0.0.0.0:8080->8080/tcp, 0.0.0.0:8443->8443/tcp
moodle-db-vps     docker-entrypoint.sh postgres    Up      5432/tcp                                        
```

**Salida esperada para `docker-compose logs moodle-app` (después de 1-2 minutos):**
```
moodle-app-vps | INFO  ==> ** Starting Moodle setup **
moodle-app-vps | INFO  ==> Validating settings
moodle-app-vps | INFO  ==> Initializing Moodle
moodle-app-vps | INFO  ==> ** Moodle setup finished! **
moodle-app-vps | INFO  ==> ** Starting Apache **
```

Si ves "Moodle setup finished!" y "Starting Apache", Moodle está listo.

---

## **PARTE D: Configurar Firewall**

### Opción 1: UFW (Ubuntu Firewall)
```bash
# Habilitar UFW
ufw enable

# Permitir SSH (importante, no te bloquees)
ufw allow ssh

# Permitir puerto de Moodle
ufw allow 8080

# Ver estado
ufw status
```

**Salida esperada para `ufw status`:**
```
Status: active

To                         Action      From
--                         ------      ----
22/tcp                     ALLOW       Anywhere
8080/tcp                   ALLOW       Anywhere
22/tcp (v6)                ALLOW       Anywhere (v6)
8080/tcp (v6)              ALLOW       Anywhere (v6)
```

### Opción 2: iptables
```bash
# Permitir tráfico SSH
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Permitir puerto de Moodle
iptables -A INPUT -p tcp --dport 8080 -j ACCEPT

# Guardar reglas (en Ubuntu)
iptables-save > /etc/iptables/rules.v4
```

### Opción 3: Firewall del Proveedor
Si usas DigitalOcean, AWS, etc.:
1. Ve a la consola del proveedor
2. Configura Security Groups/Firewall
3. Abre puerto TCP 8080 para tráfico HTTP
4. Mantén SSH (22) abierto

---

## **PARTE E: Acceso Final**

### 1. Acceder a Moodle
Abre navegador y ve a: `http://TU_DIRECCION_IP:8080`

⚠️ **Nota**: Si acabas de ejecutar `docker-compose up -d`, **espera 1-2 minutos** antes de intentar acceder. Moodle necesita tiempo para configurarse.

**Credenciales:**
- Usuario: admin
- Contraseña: Admin123!

**Primera vez**: Verás la página de configuración inicial de Moodle. Simplemente sigue los pasos o usa las credenciales arriba.

### 2. Verificar Fabric
```bash
cd ~/fabric-samples/test-network
docker ps
```

**Salida esperada:**
```
CONTAINER ID   IMAGE                               COMMAND             CREATED         STATUS         PORTS                                            NAMES
1a2b3c4d5e6f   hyperledger/fabric-peer:2.5.12     "peer node start"   X minutes ago   Up X minutes   0.0.0.0:7051->7051/tcp, 0.0.0.0:9444->9444/tcp   peer0.org1.example.com
2b3c4d5e6f7g   hyperledger/fabric-peer:2.5.12     "peer node start"   X minutes ago   Up X minutes   0.0.0.0:9051->9051/tcp, 0.0.0.0:9445->9445/tcp   peer0.org2.example.com
3c4d5e6f7g8h   hyperledger/fabric-orderer:2.5.12  "orderer"           X minutes ago   Up X minutes   0.0.0.0:7050->7050/tcp, 0.0.0.0:7053->7053/tcp   orderer.example.com
```

Si ves los 3 contenedores con STATUS "Up", Fabric está funcionando correctamente.

---

## **Comandos de Gestión Diaria**

### Gestión de Fabric
```bash
# Detener red
cd ~/fabric-samples/test-network
./network.sh down

# Iniciar red
./network.sh up createChannel

# Ver estado
docker ps
```

### Gestión de Moodle
```bash
# Detener Moodle
cd ~/moodle-project
docker-compose down

# Iniciar Moodle
docker-compose up -d

# Ver logs (ESPERAR 1-2 MINUTOS después de 'up -d')
docker-compose logs moodle-app

# Ver estado
docker-compose ps
```

**Salida esperada para `docker-compose ps`:**
```
       Name                     Command               State                       Ports                     
----------------------------------------------------------------------------------------------------------
moodle-app-vps    /opt/bitnami/scripts/moodl ...   Up      0.0.0.0:8080->8080/tcp, 0.0.0.0:8443->8443/tcp
moodle-db-vps     docker-entrypoint.sh postgres    Up      5432/tcp
```

### Mantenimiento del Sistema
```bash
# Ver uso de disco
df -h

# Ver memoria
free -h

# Limpiar Docker
docker system prune -f

# Ver todos los contenedores
docker ps -a

# Ver redes Docker
docker network ls
```

---

## **Backup y Restauración**

### Backup de Base de Datos
```bash
cd ~/moodle-project
docker-compose exec moodle-db pg_dump -U moodle_user moodle > moodle_backup_$(date +%Y%m%d).sql
```

### Backup de Datos de Moodle
```bash
docker-compose exec moodle-app tar -czf /tmp/moodledata_backup_$(date +%Y%m%d).tar.gz /bitnami/moodledata
docker cp moodle-app-vps:/tmp/moodledata_backup_$(date +%Y%m%d).tar.gz ./
```

### Restaurar Base de Datos
```bash
# Copiar backup al contenedor
docker cp moodle_backup_FECHA.sql moodle-db-vps:/tmp/

# Restaurar
docker-compose exec moodle-db psql -U moodle_user -d moodle -f /tmp/moodle_backup_FECHA.sql
```

---

## **Solución de Problemas**

### Problema: Puerto 8080 no accesible
**Verificar:**
1. Firewall del VPS: `ufw status`
2. Firewall del proveedor (Security Groups)
3. Estado del contenedor: `docker-compose ps`
4. **Tiempo de espera**: ¿Has esperado 1-2 minutos después de `docker-compose up -d`?

**Salidas a verificar:**
- `ufw status` debe mostrar puerto 8080 ALLOW
- `docker-compose ps` debe mostrar STATE "Up" para ambos contenedores
- `docker-compose logs moodle-app` debe mostrar "Moodle setup finished!"

### Problema: Contenedores no inician
**Solución:**
```bash
# Ver logs para identificar el problema
docker-compose logs

# Limpiar y reiniciar
docker-compose down
docker system prune -f
docker-compose up -d

# Esperar 1-2 minutos y verificar
docker-compose ps
```

**Si los contenedores siguen fallando, revisa:**
- Memoria disponible: `free -h`
- Espacio en disco: `df -h`
- Logs específicos: `docker-compose logs moodle-db`

### Problema: Sin espacio en disco
**Solución:**
```bash
# Ver uso
df -h

# Limpiar Docker
docker system prune -a -f

# Limpiar logs del sistema
journalctl --vacuum-size=100M
```

### Problema: Memoria insuficiente
**Verificar:**
```bash
free -h
htop  # si está instalado
```

---

## **✅ Resultado Final**

Tendrás un VPS con:
- **Hyperledger Fabric**: Red blockchain funcionando
- **Moodle**: LMS accesible desde internet en http://TU_IP:8080
- **Aislamiento**: Cada sistema en su propia red Docker  
- **Persistencia**: Datos guardados en volúmenes Docker
- **Firewall**: Configurado para acceso seguro

**🎯 Listo para Fase 2**: Backend que conecte Fabric con Moodle.

---

## **Migración desde Desarrollo Local**

Si ya tienes el sistema funcionando en Windows y quieres migrarlo:

1. **Copiar archivos**: Sube `fabric-samples/` y `moodle-project/` al VPS
2. **Ejecutar comandos**: Usa los mismos comandos pero sin `wsl -d Ubuntu-22.04`
3. **Configurar firewall**: Permitir puerto 8080
4. **Probar acceso**: Verificar http://TU_IP:8080

La configuración es idéntica, solo cambia el entorno de ejecución.
