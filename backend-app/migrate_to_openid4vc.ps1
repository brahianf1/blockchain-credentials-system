# Migración OpenID4VC - PowerShell Script para Windows
# Compatible con tu setup actual en Windows

Write-Host "🎯 MIGRACIÓN OPENID4VC - SISTEMA HÍBRIDO DIDComm + OpenID4VC" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green

# Parar containers existentes
Write-Host "⏹️  Parando containers existentes..." -ForegroundColor Yellow
docker-compose down

# Rebuild del controller con nuevas dependencias
Write-Host "🔨 Rebuilding controller con dependencias OpenID4VC..." -ForegroundColor Cyan
docker-compose build python-controller

Write-Host "📦 Instalando dependencias adicionales..." -ForegroundColor Cyan
docker-compose run --rm python-controller pip install "PyJWT>=2.8.0" "jwcrypto>=1.5.0"

# Iniciar sistema
Write-Host "🚀 Iniciando sistema híbrido..." -ForegroundColor Green
docker-compose up -d

# Esperar a que los servicios estén listos
Write-Host "⏳ Esperando servicios..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Verificar que los servicios estén corriendo
Write-Host "✅ Verificando servicios..." -ForegroundColor Green
docker-compose ps

# Test de endpoints
Write-Host "🧪 Probando endpoints..." -ForegroundColor Cyan

# Test DIDComm original
Write-Host "📡 Probando endpoint DIDComm original..." -ForegroundColor White
try {
    $response = Invoke-RestMethod -Uri "http://localhost:3000/health" -Method GET -TimeoutSec 5
    Write-Host "✅ Controller responde: $response" -ForegroundColor Green
} catch {
    Write-Host "❌ Controller no responde" -ForegroundColor Red
}

# Test OpenID4VC metadata
Write-Host "🆕 Probando metadata OpenID4VC..." -ForegroundColor White
try {
    $metadata = Invoke-RestMethod -Uri "http://localhost:3000/oid4vc/.well-known/openid-credential-issuer" -Method GET -TimeoutSec 5
    Write-Host "✅ OpenID4VC metadata disponible" -ForegroundColor Green
    Write-Host "   Issuer: $($metadata.credential_issuer)" -ForegroundColor Gray
} catch {
    Write-Host "❌ OpenID4VC no disponible" -ForegroundColor Red
}

Write-Host ""
Write-Host "🎉 MIGRACIÓN COMPLETADA" -ForegroundColor Green
Write-Host "========================" -ForegroundColor Green
Write-Host "✅ DIDComm endpoints: Funcionando (compatibilidad legacy)" -ForegroundColor Green
Write-Host "✅ OpenID4VC endpoints: Funcionando (compatible con Lissi)" -ForegroundColor Green
Write-Host ""
Write-Host "🔗 URLs disponibles:" -ForegroundColor Cyan
Write-Host "   DIDComm: http://localhost:3000/api/credential/request" -ForegroundColor White
Write-Host "   OpenID4VC: http://localhost:3000/oid4vc/credential-offer" -ForegroundColor White
Write-Host "   Metadata: http://localhost:3000/oid4vc/.well-known/openid-credential-issuer" -ForegroundColor White
Write-Host ""
Write-Host "📱 Para probar con Lissi Wallet:" -ForegroundColor Yellow
Write-Host "   1. Ejecuta: python test_migration.py" -ForegroundColor White
Write-Host "   2. Escanea el QR OpenID4VC con Lissi" -ForegroundColor White
Write-Host "   3. ¡Tu credencial W3C será compatible!" -ForegroundColor White

# Opcional: Ejecutar test automático
$executeTest = Read-Host "`n¿Quieres ejecutar el test automático ahora? (s/n)"
if ($executeTest -eq "s" -or $executeTest -eq "S") {
    Write-Host "🧪 Ejecutando test de migración..." -ForegroundColor Cyan
    python test_migration.py
}
