# Backup de Archivos Node.js Obsoletos

## 📦 Contenido del Backup

Este directorio contiene los archivos del sistema anterior basado en **Node.js + Credo-TS** que fue reemplazado por el nuevo sistema **Python + ACA-Py**.

### 🗃️ Archivos respaldados:
- `agent.js` - Agente principal Credo-TS (PROBLEMÁTICO)
- `server.js` - Servidor Express Node.js
- `credentials.js` - Manejo de credenciales con Credo-TS
- `did-manager.js` - Gestión de DIDs
- `fabric-client.js` - Cliente Fabric en JavaScript  
- `qr-generator.js` - Generador de códigos QR
- `package.json` - Dependencias npm
- `node_modules/` - Módulos de Node.js
- `Dockerfile.nodejs` - Dockerfile original de Node.js

## ⚠️ Razón del Reemplazo

El sistema Node.js fue reemplazado porque:
- **Credo-TS fallaba constantemente** con error `Cannot read properties of undefined (reading 'storeOpen')`
- **Solo funcionaba en modo simulación**, no emitía credenciales W3C reales
- **Dependencias complejas** y problemas de compatibilidad
- **No se integraba correctamente** con wallets móviles

## ✅ Sistema Nuevo

Reemplazado por:
- **Python + FastAPI** (Controller)
- **ACA-Py oficial** (Hyperledger Aries Cloud Agent)
- **Docker Compose** orquestación completa
- **Credenciales W3C REALES** (no simuladas)
- **Integración completa** con Moodle y Hyperledger Fabric

## 📅 Fecha del Backup
Agosto 3, 2025

## 🔒 Conservación
Estos archivos se mantienen como backup por seguridad, pero el sistema actual es completamente funcional y no requiere estos componentes.