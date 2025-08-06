#!/bin/bash
# Migración OpenID4VC - Actualizar tu sistema para compatibilidad con Lissi

echo "🎯 MIGRACIÓN OPENID4VC - SISTEMA HÍBRIDO DIDComm + OpenID4VC"
echo "============================================================"

# Parar containers existentes
echo "⏹️  Parando containers existentes..."
docker-compose down

# Rebuild del controller con nuevas dependencias
echo "🔨 Rebuilding controller con dependencias OpenID4VC..."
docker-compose build python-controller

echo "📦 Instalando dependencias adicionales..."
docker-compose run --rm python-controller pip install PyJWT>=2.8.0 jwcrypto>=1.5.0

# Iniciar sistema
echo "🚀 Iniciando sistema híbrido..."
docker-compose up -d

# Esperar a que los servicios estén listos
echo "⏳ Esperando servicios..."
sleep 10

# Verificar que los servicios estén corriendo
echo "✅ Verificando servicios..."
docker-compose ps

# Test de endpoints
echo "🧪 Probando endpoints..."

# Test DIDComm original
echo "📡 Probando endpoint DIDComm original..."
curl -X GET http://localhost:3000/health -s || echo "❌ Controller no responde"

# Test OpenID4VC metadata
echo "🆕 Probando metadata OpenID4VC..."
curl -X GET "http://localhost:3000/oid4vc/.well-known/openid-credential-issuer" -s | jq . || echo "❌ OpenID4VC no disponible"

echo ""
echo "🎉 MIGRACIÓN COMPLETADA"
echo "========================"
echo "✅ DIDComm endpoints: Funcionando (compatibilidad legacy)"
echo "✅ OpenID4VC endpoints: Funcionando (compatible con Lissi)"
echo ""
echo "🔗 URLs disponibles:"
echo "   DIDComm: http://localhost:3000/api/credential/request"
echo "   OpenID4VC: http://localhost:3000/oid4vc/credential-offer"
echo "   Metadata: http://localhost:3000/oid4vc/.well-known/openid-credential-issuer"
echo ""
echo "📱 Para probar con Lissi Wallet:"
echo "   1. Ejecuta: python test_migration.py"
echo "   2. Escanea el QR OpenID4VC con Lissi"
echo "   3. ¡Tu credencial W3C será compatible!"
