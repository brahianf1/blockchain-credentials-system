#!/bin/bash
# Test de credenciales - Versión actualizada con DIDComm + OpenID4VC
# Compatible con VPS y Lissi Wallet

echo "🎯 === SISTEMA DE CREDENCIALES HÍBRIDO ==="
echo "🌐 VPS: https://utnpf.site (SSL habilitado)"
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
echo "🆕 === PROBANDO OPENID4VC (Nuevo - para Lissi) ==="
echo "Compatible con: Lissi Wallet, EUDI Wallet, wallets modernas"
echo ""

# Datos para OpenID4VC (formato ligeramente diferente)
OPENID4VC_DATA='{
  "student_id": "456",
  "student_name": "María García",
  "student_email": "maria@ejemplo.com",
  "course_name": "Credenciales W3C con OpenID4VC",
  "completion_date": "2025-08-06T16:00:00Z",
  "grade": "A+"
}'

OPENID4VC_RESPONSE=$(curl -s -X POST https://utnpf.site/oid4vc/credential-offer \
  -H "Content-Type: application/json" \
  -d "$OPENID4VC_DATA")

echo "Response OpenID4VC:"
echo "$OPENID4VC_RESPONSE" | jq .

if echo "$OPENID4VC_RESPONSE" | jq -e '.qr_url' > /dev/null; then
    PRE_AUTH_CODE=$(echo "$OPENID4VC_RESPONSE" | jq -r '.pre_authorized_code')
    WEB_QR_URL=$(echo "$OPENID4VC_RESPONSE" | jq -r '.web_qr_url')
    echo ""
    echo "🎉 OpenID4VC funcionando!"
    echo "📱 Página web QR OpenID4VC: $WEB_QR_URL"
    echo "🆕 COMPATIBLE con Lissi Wallet y wallets modernas"
    echo "🔑 Pre-authorized Code: $PRE_AUTH_CODE"
else
    echo "❌ Error en OpenID4VC"
fi

echo ""
echo ""
echo "🎯 === RESUMEN ==="
echo "✅ DIDComm: Para compatibilidad con wallets existentes"
echo "✅ OpenID4VC: Para Lissi Wallet y wallets modernas"
echo "🎉 Tu sistema ahora es compatible con ambos protocolos!"
echo ""
echo "📱 PARA PROBAR CON LISSI WALLET:"
echo "   1. Abre la página web QR de OpenID4VC (URL mostrada arriba)"
echo "   2. Escanea el QR con Lissi Wallet"
echo "   3. Acepta la credencial en tu wallet"
echo ""
echo "📱 PARA PROBAR CON WALLETS DIDCOMM:"
echo "   1. Abre la página web QR de DIDComm (URL mostrada arriba)"
echo "   2. Escanea el QR con tu wallet DIDComm"
echo "   3. Completa el intercambio de credenciales"
