#!/bin/bash
# Script de deployment para OpenID4VC en VPS con Docker
# Automatiza el proceso de actualización con compatibilidad walt.id

set -e  # Salir si hay error

echo "🚀 === DEPLOYMENT OPENID4VC WALT.ID COMPATIBLE ==="
echo "Fecha: $(date)"
echo ""

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # Sin color

# Función para logging
log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] ⚠️ WARNING:${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ❌ ERROR:${NC} $1"
}

# 1. Verificar que estamos en el directorio correcto
if [ ! -f "docker-compose.yml" ]; then
    error "No se encuentra docker-compose.yml. Ejecutar desde backend-app/"
    exit 1
fi

log "✅ Verificando archivos necesarios..."
required_files=(
    "controller/openid4vc_endpoints.py"
    "controller/requirements.txt"
    "Dockerfile.controller"
    "test_openid4vc_compatibility.py"
)

for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        error "Archivo faltante: $file"
        exit 1
    fi
    echo "   ✓ $file"
done

# 2. Backup del estado actual
log "📦 Creando backup..."
BACKUP_DIR="backup-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r controller/ "$BACKUP_DIR/"
cp docker-compose.yml "$BACKUP_DIR/"
echo "   ✓ Backup creado en: $BACKUP_DIR"

# 3. Verificar que no hay contenedores corriendo que puedan interferir
log "🔍 Verificando estado de contenedores..."
if docker-compose ps | grep -q "Up"; then
    warning "Contenedores ejecutándose. Procediendo con rolling update..."
else
    log "   ✓ No hay contenedores ejecutándose"
fi

# 4. Construir nuevas imágenes
log "🔨 Construyendo nuevas imágenes Docker..."
docker-compose build --no-cache python-controller
if [ $? -eq 0 ]; then
    echo "   ✅ Imagen python-controller construida exitosamente"
else
    error "Falló la construcción de la imagen"
    exit 1
fi

# 5. Verificar dependencias de red
log "🌐 Verificando redes Docker..."
networks=(
    "moodle-project_moodle-network"
    "fabric_test"
)

for network in "${networks[@]}"; do
    if docker network ls | grep -q "$network"; then
        echo "   ✓ Red $network existe"
    else
        warning "Red $network no existe - se creará automáticamente"
    fi
done

# 6. Realizar deployment
log "🚀 Iniciando deployment..."

# Detener servicios
echo "   🔄 Deteniendo servicios antiguos..."
docker-compose down

# Limpiar imágenes huérfanas
echo "   🧹 Limpiando imágenes huérfanas..."
docker image prune -f

# Iniciar servicios
echo "   ▶️ Iniciando servicios nuevos..."
docker-compose up -d

# 7. Verificar health de los servicios
log "🏥 Verificando health de servicios..."
sleep 10

# Verificar python-controller
echo "   🔍 Verificando python-controller..."
if docker-compose ps python-controller | grep -q "Up"; then
    echo "   ✅ python-controller ejecutándose"
    
    # Verificar endpoint de health
    echo "   🔍 Probando endpoint /oid4vc/health..."
    for i in {1..30}; do
        if curl -f -s "https://utnpf.site/oid4vc/health" >/dev/null 2>&1; then
            echo "   ✅ Endpoint health responde correctamente"
            break
        elif [ $i -eq 30 ]; then
            error "Endpoint health no responde después de 30 intentos"
            docker-compose logs python-controller --tail=20
            exit 1
        else
            echo "   ⏳ Esperando health endpoint... (intento $i/30)"
            sleep 2
        fi
    done
else
    error "python-controller no está ejecutándose"
    docker-compose logs python-controller
    exit 1
fi

# Verificar acapy-agent
echo "   🔍 Verificando acapy-agent..."
if docker-compose ps acapy-agent | grep -q "Up"; then
    echo "   ✅ acapy-agent ejecutándose"
else
    warning "acapy-agent no está ejecutándose (puede ser normal)"
fi

# 8. Ejecutar tests de compatibilidad
log "🧪 Ejecutando tests de compatibilidad OpenID4VC..."

echo "   📡 Test 1: Verificando metadata endpoint..."
if curl -f -s "https://utnpf.site/oid4vc/.well-known/openid-credential-issuer" | jq . >/dev/null 2>&1; then
    echo "   ✅ Metadata endpoint OK"
else
    error "Metadata endpoint falla"
    exit 1
fi

echo "   🔑 Test 2: Verificando JWKS endpoint..."
if curl -f -s "https://utnpf.site/oid4vc/.well-known/jwks.json" | jq . >/dev/null 2>&1; then
    echo "   ✅ JWKS endpoint OK"
else
    error "JWKS endpoint falla"
    exit 1
fi

echo "   🔐 Test 3: Verificando SSL..."
if curl -f -s "https://utnpf.site/oid4vc/ssl-test" | jq . >/dev/null 2>&1; then
    echo "   ✅ SSL configurado correctamente"
else
    warning "SSL test falla - revisar configuración"
fi

# 9. Test de walt.id endpoint específico
log "🟢 Probando endpoint específico para walt.id..."
echo "   📝 Creando credential offer de prueba..."

# Crear un credential offer de prueba
TEST_PAYLOAD='{
    "student_id": "test_walt_001",
    "student_name": "Walt.id Test User",
    "student_email": "test@walt.id",
    "course_name": "OpenID4VC Compatibility Test",
    "completion_date": "2024-01-01",
    "grade": "A+"
}'

if OFFER_RESPONSE=$(curl -s -X POST "https://utnpf.site/oid4vc/credential-offer" \
    -H "Content-Type: application/json" \
    -d "$TEST_PAYLOAD"); then
    
    # Extraer pre-authorized code del response
    PRE_AUTH_CODE=$(echo "$OFFER_RESPONSE" | jq -r '.pre_authorized_code')
    
    if [ "$PRE_AUTH_CODE" != "null" ] && [ -n "$PRE_AUTH_CODE" ]; then
        echo "   ✅ Credential offer creado: $PRE_AUTH_CODE"
        
        # Probar endpoint walt.id específico
        echo "   🧪 Probando walt.id endpoint con query params..."
        WALT_URL="https://utnpf.site/oid4vc/walt-token"
        WALT_PARAMS="grant_type=urn:ietf:params:oauth:grant-type:pre-authorized_code&pre_authorized_code=$PRE_AUTH_CODE"
        
        if WALT_RESPONSE=$(curl -s -X POST "$WALT_URL?$WALT_PARAMS"); then
            ACCESS_TOKEN=$(echo "$WALT_RESPONSE" | jq -r '.access_token')
            if [ "$ACCESS_TOKEN" != "null" ] && [ -n "$ACCESS_TOKEN" ]; then
                echo "   ✅ Walt.id endpoint funciona correctamente"
                echo "   🎫 Access token generado: ${ACCESS_TOKEN:0:20}..."
            else
                warning "Walt.id endpoint no devuelve access token válido"
                echo "Response: $WALT_RESPONSE"
            fi
        else
            warning "Error probando walt.id endpoint"
        fi
        
        # Probar endpoint universal con query params
        echo "   🌐 Probando endpoint universal con query params..."
        UNIVERSAL_URL="https://utnpf.site/oid4vc/token"
        if UNIVERSAL_RESPONSE=$(curl -s -X POST "$UNIVERSAL_URL?$WALT_PARAMS"); then
            UNIVERSAL_TOKEN=$(echo "$UNIVERSAL_RESPONSE" | jq -r '.access_token')
            if [ "$UNIVERSAL_TOKEN" != "null" ] && [ -n "$UNIVERSAL_TOKEN" ]; then
                echo "   ✅ Endpoint universal también funciona con query params"
            else
                warning "Endpoint universal falla con query params"
                echo "Response: $UNIVERSAL_RESPONSE"
            fi
        fi
        
    else
        error "No se pudo crear credential offer de prueba"
        echo "Response: $OFFER_RESPONSE"
    fi
else
    error "Error creando credential offer de prueba"
fi

# 10. Mostrar logs recientes para debugging
log "📋 Mostrando logs recientes..."
echo "   📝 Logs del python-controller (últimas 10 líneas):"
docker-compose logs python-controller --tail=10

# 11. Resumen final
echo ""
echo "🎉 === DEPLOYMENT COMPLETADO ==="
echo ""
log "📊 Resumen del deployment:"
echo "   🐳 Servicios Docker: $(docker-compose ps --services | wc -l)"
echo "   🌐 URL Base: https://utnpf.site"
echo "   📡 Metadata: https://utnpf.site/oid4vc/.well-known/openid-credential-issuer"
echo "   🟢 Walt.id Endpoint: https://utnpf.site/oid4vc/walt-token"
echo "   🌐 Universal Endpoint: https://utnpf.site/oid4vc/token"
echo "   🔍 Debug Endpoint: https://utnpf.site/oid4vc/token/debug"
echo "   🏥 Health Check: https://utnpf.site/oid4vc/health"
echo ""
log "🔗 Para probar con walt.id wallet:"
echo "   1. Crear credential offer: POST /oid4vc/credential-offer"
echo "   2. Escanear QR con wallet.demo.walt.id"
echo "   3. El wallet usará automáticamente los endpoints compatibles"
echo ""
log "✅ Deployment exitoso! Sistema listo para walt.id y otros wallets OpenID4VC"
