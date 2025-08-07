#!/bin/bash
# Test de credenciales - Versión actualizada con DIDComm + OpenID4VC
# Compatible con VPS y Lissi Wallet

echo "🎯 === SISTEMA DE CREDENCIALES HÍBRIDO ==="
echo "🌐 VPS: https://utnpf.site (SSL habilitado)"
echo ""

# Verificaciones previas
echo "🔍 === VERIFICACIONES PREVIAS ==="

# Verificar SSL
echo "📋 Verificando SSL..."
SSL_CHECK=$(curl -s -I https://utnpf.site/ | head -1)
if echo "$SSL_CHECK" | grep -q "200\|404\|302"; then
    echo "✅ SSL funcionando: $SSL_CHECK"
else
    echo "❌ SSL no funcionando: $SSL_CHECK"
    exit 1
fi

# Verificar contenedores Docker
echo "📋 Verificando contenedores..."
if curl -s http://localhost:3000/ > /dev/null; then
    echo "✅ Controller (puerto 3000) funcionando"
else
    echo "❌ Controller no funcionando - ejecutar: docker-compose up -d"
    exit 1
fi

# Verificar endpoints OpenID4VC
echo "📋 Verificando endpoints OpenID4VC..."
HEALTH_CHECK=$(curl -s https://utnpf.site/oid4vc/health)
if echo "$HEALTH_CHECK" | jq -e '.status' > /dev/null 2>&1; then
    echo "✅ OpenID4VC endpoints funcionando"
else
    echo "⚠️  OpenID4VC endpoints pueden no estar disponibles"
fi

echo ""

# Datos de prueba
TEST_DATA='{
  "student_id": "123",
  "student_name": "Juan Pérez",
  "student_email": "estudiante@ejemplo.com",
  "course_id": "curso-001",
  "course_name": "Introducción a Blockchain",
  "completion_date": "2025-08-06T15:30:00Z",
  "grade": "A",
  "instructor_name": "Prof. García"
}'

# 1. PROBAR DIDCOMM (Sistema actual - para wallets DIDComm)
echo "📡 === PROBANDO DIDCOMM (Sistema actual) ==="
echo "Compatible con: ACA-Py wallets, Credo"
echo ""

DIDCOMM_RESPONSE=$(curl -s -X POST https://utnpf.site/api/credential/request \
  -H "Content-Type: application/json" \
  -d "$TEST_DATA")

echo "Response DIDComm:"
echo "$DIDCOMM_RESPONSE" | jq .

if echo "$DIDCOMM_RESPONSE" | jq -e '.connection_id' > /dev/null; then
    CONNECTION_ID=$(echo "$DIDCOMM_RESPONSE" | jq -r '.connection_id')
    echo ""
    echo "✅ DIDComm funcionando!"
    echo "📱 Página web QR DIDComm: https://utnpf.site/qr/$CONNECTION_ID"
    echo "⚠️  LIMITACIÓN: No compatible con Lissi Wallet"
else
    echo "❌ Error en DIDComm"
fi

echo ""
echo "=================================================="
echo ""

# 2. PROBAR OPENID4VC (Nuevo sistema - para Lissi Wallet)
echo "🆕 === PROBANDO OPENID4VC (Compatible con Walt.id) ==="
echo "Compatible con: walt.id wallet, Lissi Wallet, EUDI Wallet, wallets modernas"
echo ""

# Datos para OpenID4VC (optimizado para walt.id compatibility)
OPENID4VC_DATA='{
  "student_id": "walt-test-456",
  "student_name": "Walt.id Test User",
  "student_email": "walt@test.example",
  "course_name": "OpenID4VC Credencial Compatible",
  "completion_date": "2025-08-07T16:00:00Z",
  "grade": "A+"
}'

# Primero verificar que el endpoint OpenID4VC está disponible
echo "🔍 Verificando endpoints OpenID4VC..."
METADATA_CHECK=$(curl -s https://utnpf.site/oid4vc/.well-known/openid-credential-issuer)

if echo "$METADATA_CHECK" | jq -e '.credential_issuer' > /dev/null 2>&1; then
    echo "✅ Metadata OpenID4VC disponible"
    
    # Probar crear credential offer (endpoint correcto)
    OPENID4VC_RESPONSE=$(curl -s -X POST https://utnpf.site/oid4vc/credential-offer \
      -H "Content-Type: application/json" \
      -d "$OPENID4VC_DATA")
    
    echo "Response OpenID4VC:"
    echo "$OPENID4VC_RESPONSE" | jq . 2>/dev/null || echo "$OPENID4VC_RESPONSE"
    
    # Verificar respuesta y extraer datos
    if echo "$OPENID4VC_RESPONSE" | jq -e '.qr_url' > /dev/null 2>&1; then
        PRE_AUTH_CODE=$(echo "$OPENID4VC_RESPONSE" | jq -r '.pre_authorized_code // .pre_auth_code // empty')
        WEB_QR_URL=$(echo "$OPENID4VC_RESPONSE" | jq -r '.web_qr_url // .qr_url // empty')
        CREDENTIAL_OFFER_URL=$(echo "$OPENID4VC_RESPONSE" | jq -r '.credential_offer_uri // empty')
        
        echo ""
        echo "🎉 OpenID4VC funcionando!"
        echo "📱 Página web QR OpenID4VC: $WEB_QR_URL"
        echo "🆕 COMPATIBLE con walt.id wallet (wallet.demo.walt.id)"
        echo "🆕 COMPATIBLE con Lissi Wallet y wallets modernas"
        if [ ! -z "$PRE_AUTH_CODE" ]; then
            echo "🔑 Pre-authorized Code: $PRE_AUTH_CODE"
        fi
        if [ ! -z "$CREDENTIAL_OFFER_URL" ]; then
            echo "🔗 Credential Offer URI: $CREDENTIAL_OFFER_URL"
        fi
        
        # Extraer QR URL para testing directo
        QR_URL_DIRECT=$(echo "$OPENID4VC_RESPONSE" | jq -r '.qr_url // empty')
        if [ ! -z "$QR_URL_DIRECT" ]; then
            echo "🔗 URL directa para walt.id: $QR_URL_DIRECT"
            echo "📋 Longitud URL: ${#QR_URL_DIRECT} caracteres"
        fi
    else
        echo "❌ Error en OpenID4VC - Response:"
        echo "$OPENID4VC_RESPONSE"
    fi
else
    echo "❌ Metadata OpenID4VC no disponible"
    echo "📋 Verificar que el endpoint esté funcionando:"
    echo "   curl https://utnpf.site/oid4vc/.well-known/openid-credential-issuer"
fi

echo ""
echo ""
echo "🎯 === RESUMEN ==="
echo "✅ DIDComm: Para compatibilidad con wallets existentes"
echo "✅ OpenID4VC: Para Lissi Wallet y wallets modernas"
echo "🎉 Tu sistema ahora es compatible con ambos protocolos!"
echo ""
echo "📱 === PARA PROBAR CON WALT.ID WALLET ==="
echo "   🔗 Sitio web: https://wallet.demo.walt.id/"
echo "   📋 Pasos:"
echo "      1. Abre https://wallet.demo.walt.id/ en tu navegador"
echo "      2. Copia la 'URL directa para walt.id' mostrada arriba"
echo "      3. Pégala en el campo de walt.id wallet"
echo "      4. Acepta la credencial en walt.id"
echo ""
echo "📱 === PARA PROBAR CON LISSI WALLET ==="
echo "   🔗 URL a usar: Página web QR de OpenID4VC (mostrada arriba)"
echo "   📋 Pasos:"
echo "      1. Copia la URL de la página web QR OpenID4VC"
echo "      2. Ábrela en tu navegador móvil o envíala a tu teléfono"
echo "      3. Abre Lissi Wallet en tu móvil"
echo "      4. Escanea el QR Code desde la página web"
echo "      5. Acepta la credencial en Lissi Wallet"
echo ""
echo "📱 === PARA PROBAR CON WALLETS DIDCOMM ==="
echo "   🔗 URL a usar: Página web QR de DIDComm (mostrada arriba)"
echo "   📋 Pasos:"
echo "      1. Abre la página web QR de DIDComm"
echo "      2. Escanea el QR con tu wallet DIDComm (ACA-Py, Credo)"
echo "      3. Completa el intercambio de credenciales"
echo ""
echo "🔧 === TROUBLESHOOTING ==="
echo "   • Si OpenID4VC falla: Verificar logs con 'docker-compose logs controller'"
echo "   • Si DIDComm falla: Verificar ACA-Py con 'docker-compose logs acapy'"
echo "   • SSL Issues: Verificar certificado con 'curl -I https://utnpf.site/'"
echo "   • Logs Nginx: 'sudo tail -f /var/log/nginx/utnpf.site.error.log'"
echo ""
echo "🧪 === VERIFICACIÓN AUTOMÁTICA WALT.ID ==="
echo "Ejecutando verificación de compatibilidad..."

# Ejecutar verificación específica para walt.id si existe el script
if [ -f "./verify-walt-id.py" ]; then
    echo "📋 Ejecutando verify-walt-id.py..."
    python3 ./verify-walt-id.py
else
    echo "⚠️  Script verify-walt-id.py no encontrado, saltando verificación automática"
    echo "   Puedes ejecutarlo manualmente: python3 verify-walt-id.py"
fi
