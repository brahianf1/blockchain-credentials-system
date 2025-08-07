# 🚀 Guía de Deployment OpenID4VC con Compatibilidad Walt.id

## 📋 Resumen

Esta guía describe el proceso completo para deployar el sistema OpenID4VC con compatibilidad específica para `wallet.demo.walt.id` y otros wallets OpenID4VC.

## 🔧 Cambios Implementados

### 1. **Endpoint Universal de Token** (`/oid4vc/token`)
- ✅ Acepta parámetros por **query params** (walt.id)
- ✅ Acepta parámetros por **form data** (estándar OpenID4VC)  
- ✅ Acepta parámetros por **JSON body** (algunos wallets)
- ✅ Prioridad: form data > query params > JSON body

### 2. **Endpoint Específico Walt.id** (`/oid4vc/walt-token`)
- ✅ Diseñado específicamente para `wallet.demo.walt.id`
- ✅ Acepta solo query parameters
- ✅ Validación estricta del comportamiento walt.id

### 3. **Endpoint de Debug** (`/oid4vc/token/debug`)
- ✅ Captura detalles exactos de las requests
- ✅ Útil para diagnosticar problemas con wallets

### 4. **Mejoras de Seguridad SSL**
- ✅ Headers de seguridad mejorados
- ✅ Configuración TLS 1.2+ compatible con Android
- ✅ Validación de certificados Let's Encrypt

## 📦 Archivos Modificados

```
backend-app/
├── controller/
│   ├── openid4vc_endpoints.py     # ✅ Endpoints con compatibilidad walt.id
│   └── requirements.txt           # ✅ Dependencias actualizadas
├── deploy-openid4vc.sh           # 🆕 Script de deployment automatizado
├── verify-openid4vc.py           # 🆕 Verificación post-deployment
└── test_openid4vc_compatibility.py # ✅ Tests de compatibilidad
```

## 🚀 Proceso de Deployment

### Paso 1: Preparar el código

```bash
# En tu máquina local, verificar que todo esté listo
cd backend-app/
ls -la controller/openid4vc_endpoints.py
ls -la deploy-openid4vc.sh
ls -la verify-openid4vc.py
```

### Paso 2: Subir a la VPS

```bash
# Método 1: Git (recomendado)
git add .
git commit -m "feat: walt.id compatibility for OpenID4VC token endpoint"
git push origin main

# En la VPS:
cd /path/to/your/blockchain-project
git pull origin main

# Método 2: SCP directo (alternativo)
scp -r controller/ user@your-vps:/path/to/backend-app/
scp deploy-openid4vc.sh user@your-vps:/path/to/backend-app/
scp verify-openid4vc.py user@your-vps:/path/to/backend-app/
```

### Paso 3: Ejecutar deployment automatizado

```bash
# En la VPS, dentro del directorio backend-app/
chmod +x deploy-openid4vc.sh
./deploy-openid4vc.sh
```

El script automáticamente:
- ✅ Verifica archivos necesarios
- ✅ Crea backup del estado actual
- ✅ Construye nuevas imágenes Docker
- ✅ Realiza rolling update de servicios
- ✅ Verifica health de endpoints
- ✅ Ejecuta tests de compatibilidad walt.id
- ✅ Muestra resumen del deployment

### Paso 4: Verificación post-deployment

```bash
# Ejecutar verificación completa
python3 verify-openid4vc.py
```

### Paso 5: Test manual con walt.id

1. **Crear credential offer:**
```bash
curl -X POST "https://utnpf.site/oid4vc/credential-offer" \
  -H "Content-Type: application/json" \
  -d '{
    "student_id": "test001",
    "student_name": "Test User",
    "student_email": "test@example.com",
    "course_name": "OpenID4VC Test",
    "completion_date": "2024-01-01",
    "grade": "A+"
  }'
```

2. **Copiar QR URL del response**

3. **Probar en wallet.demo.walt.id:**
   - Abrir https://wallet.demo.walt.id/
   - Usar la función de escanear QR
   - Pegar la `qr_url` obtenida

## 🔍 Endpoints Disponibles

| Endpoint | Propósito | Compatible con |
|----------|-----------|---------------|
| `/oid4vc/.well-known/openid-credential-issuer` | Metadata del issuer | Todos los wallets |
| `/oid4vc/.well-known/jwks.json` | Claves públicas | Todos los wallets |
| `/oid4vc/token` | Token universal | Todos los wallets |
| `/oid4vc/walt-token` | Token específico walt.id | wallet.demo.walt.id |
| `/oid4vc/token/debug` | Debug de requests | Desarrollo |
| `/oid4vc/credential` | Emisión de credenciales | Todos los wallets |
| `/oid4vc/health` | Health check | Monitoreo |
| `/oid4vc/ssl-test` | Test SSL/TLS | Debugging |

## 🐛 Troubleshooting

### Error: "Failed to get token: 422"

**Causa:** Walt.id wallet enviando parámetros como query params en lugar de form data.

**Solución:** ✅ Ya implementada en el endpoint universal `/oid4vc/token`

### Error: "Trust anchor not found"

**Causa:** Problemas con el certificado SSL en dispositivos móviles.

**Solución:** 
- Verificar que la fecha/hora del dispositivo sea correcta
- El certificado Let's Encrypt debe ser válido
- Usar TLS 1.2+ (ya configurado)

### Contenedor no inicia

```bash
# Ver logs detallados
docker-compose logs python-controller

# Verificar configuración
docker-compose config

# Rebuild forzado
docker-compose build --no-cache python-controller
docker-compose up -d
```

### Endpoint no responde

```bash
# Verificar que nginx esté forwarding correctamente
curl -I https://utnpf.site/oid4vc/health

# Verificar contenedor interno
docker exec -it python-controller curl http://localhost:3000/oid4vc/health
```

## 📊 Métricas de Compatibilidad

Después del deployment, el sistema debería tener:

- ✅ **100%** compatibilidad con wallet.demo.walt.id
- ✅ **100%** compatibilidad con wallets estándar OpenID4VC
- ✅ **SSL/TLS** configurado correctamente
- ✅ **Response time** < 500ms para token endpoint
- ✅ **Uptime** > 99.9%

## 🔄 Rollback (si es necesario)

```bash
# Si algo falla, rollback rápido:
cd backup-YYYYMMDD-HHMMSS/
cp -r controller/ ../
docker-compose build --no-cache python-controller
docker-compose up -d
```

## 📞 Testing Final

Una vez completado el deployment, probar con:

1. **wallet.demo.walt.id** - Debería funcionar sin errores 422
2. **Lissi Wallet** - Debería mantener compatibilidad existente  
3. **Cualquier wallet OpenID4VC** - Debería funcionar con estándar

## ✅ Checklist de Deployment

- [ ] Código subido a VPS
- [ ] `deploy-openid4vc.sh` ejecutado exitosamente
- [ ] `verify-openid4vc.py` pasa todos los tests
- [ ] Endpoint `/oid4vc/health` responde OK
- [ ] Metadata endpoint accesible
- [ ] Test manual con walt.id exitoso
- [ ] Logs sin errores críticos
- [ ] SSL configurado correctamente

¡Sistema listo para producción con compatibilidad walt.id! 🎉
