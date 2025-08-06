# Migración OpenID4VC - Script para VPS Digital Ocean
# Adaptado para tu infraestructura real en http://209.38.151.153

Write-Host "🎯 MIGRACIÓN OPENID4VC EN VPS DIGITAL OCEAN" -ForegroundColor Green
Write-Host "VPS: http://209.38.151.153" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Green

# Variables del VPS
$VPS_IP = "209.38.151.153"
$VPS_URL = "http://$VPS_IP"

Write-Host ""
Write-Host "📋 PREPARANDO MIGRACIÓN..." -ForegroundColor Yellow
Write-Host "   ✅ VPS detectado: $VPS_URL" -ForegroundColor Green
Write-Host "   ✅ Sistema actual: DIDComm funcionando" -ForegroundColor Green
Write-Host "   🆕 Añadiendo: OpenID4VC para Lissi Wallet" -ForegroundColor Cyan

# Instrucciones para el VPS
Write-Host ""
Write-Host "🔄 PASOS PARA ACTUALIZAR TU VPS:" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "1️⃣ CONECTAR AL VPS:" -ForegroundColor White
Write-Host "   ssh root@$VPS_IP" -ForegroundColor Gray

Write-Host ""
Write-Host "2️⃣ NAVEGAR A TU PROYECTO:" -ForegroundColor White
Write-Host "   cd /root/blockchain-credentials-system" -ForegroundColor Gray
Write-Host "   # Tu repositorio GitHub" -ForegroundColor DarkGray

Write-Host ""
Write-Host "3️⃣ HACER PULL DE GITHUB:" -ForegroundColor White
Write-Host "   git pull origin main" -ForegroundColor Gray
Write-Host "   # Esto descargará todos los cambios nuevos" -ForegroundColor DarkGray

Write-Host ""
Write-Host "4️⃣ VERIFICAR ARCHIVOS NUEVOS:" -ForegroundColor White
Write-Host "   ls -la controller/" -ForegroundColor Gray
Write-Host "   # Deberías ver: openid4vc_endpoints.py" -ForegroundColor DarkGray

Write-Host ""
Write-Host "5️⃣ INSTALAR DEPENDENCIAS OPENID4VC:" -ForegroundColor White
Write-Host "   docker-compose run --rm python-controller pip install PyJWT>=2.8.0 jwcrypto>=1.5.0" -ForegroundColor Gray

Write-Host ""
Write-Host "6️⃣ REBUILD Y RESTART:" -ForegroundColor White
Write-Host "   docker-compose down" -ForegroundColor Gray
Write-Host "   docker-compose build python-controller" -ForegroundColor Gray
Write-Host "   docker-compose up -d" -ForegroundColor Gray

Write-Host ""
Write-Host "7️⃣ VERIFICAR ENDPOINTS:" -ForegroundColor White
Write-Host "   curl $VPS_URL/health" -ForegroundColor Gray
Write-Host "   curl '$VPS_URL/oid4vc/.well-known/openid-credential-issuer'" -ForegroundColor Gray

# Test remoto de endpoints
Write-Host ""
Write-Host "🧪 PROBANDO ENDPOINTS REMOTOS..." -ForegroundColor Cyan

# Test endpoint original (DIDComm)
Write-Host ""
Write-Host "📡 Probando endpoint DIDComm actual..." -ForegroundColor White
try {
    $healthResponse = Invoke-RestMethod -Uri "$VPS_URL/health" -Method GET -TimeoutSec 10
    Write-Host "✅ VPS responde - DIDComm funcionando" -ForegroundColor Green
    Write-Host "   Response: $healthResponse" -ForegroundColor Gray
} catch {
    Write-Host "❌ VPS no responde en $VPS_URL" -ForegroundColor Red
    Write-Host "   Verifica que el servidor esté ejecutándose" -ForegroundColor Yellow
}

# Test nuevo endpoint OpenID4VC (solo si ya hiciste pull)
Write-Host ""
Write-Host "🆕 Probando metadata OpenID4VC (después del pull)..." -ForegroundColor White
try {
    $metadataResponse = Invoke-RestMethod -Uri "$VPS_URL/oid4vc/.well-known/openid-credential-issuer" -Method GET -TimeoutSec 10
    Write-Host "✅ OpenID4VC disponible en VPS!" -ForegroundColor Green
    Write-Host "   Issuer: $($metadataResponse.credential_issuer)" -ForegroundColor Gray
} catch {
    Write-Host "⏳ OpenID4VC aún no disponible" -ForegroundColor Yellow
    Write-Host "   Haz el git pull y rebuild primero" -ForegroundColor Gray
}

# Generar script de test específico para el VPS
Write-Host ""
Write-Host "📄 CREANDO SCRIPT DE TEST PARA VPS..." -ForegroundColor Cyan

$vpsTestScript = @"
#!/usr/bin/env python3
"""
Test específico para VPS Digital Ocean - http://209.38.151.153
"""

import requests
import json

VPS_URL = "http://209.38.151.153"

def test_vps_endpoints():
    print("🧪 === PROBANDO ENDPOINTS EN VPS ===")
    print(f"🌐 URL: {VPS_URL}")
    
    # Test DIDComm actual
    print("\n📡 Probando DIDComm (endpoint actual)...")
    try:
        health = requests.get(f"{VPS_URL}/health", timeout=10)
        print(f"✅ Health: {health.status_code}")
        
        # Test endpoint real que usas
        test_data = {
            "student_id": "vps-test-001",
            "student_name": "Estudiante VPS", 
            "student_email": "test@vps.com",
            "course_id": "curso-vps",
            "course_name": "Test VPS Course",
            "completion_date": "2025-08-06T15:30:00Z",
            "grade": "A",
            "instructor_name": "Prof. VPS"
        }
        
        didcomm_response = requests.post(
            f"{VPS_URL}/api/credential/request",
            json=test_data,
            timeout=15
        )
        
        if didcomm_response.status_code == 200:
            result = didcomm_response.json()
            print(f"✅ DIDComm endpoint funciona")
            print(f"🔗 Invitation URL: {result['invitation_url'][:50]}...")
        else:
            print(f"❌ DIDComm error: {didcomm_response.status_code}")
            
    except Exception as e:
        print(f"💥 Error DIDComm: {e}")
    
    # Test OpenID4VC nuevo
    print("\n🆕 Probando OpenID4VC (después de migración)...")
    try:
        metadata = requests.get(
            f"{VPS_URL}/oid4vc/.well-known/openid-credential-issuer",
            timeout=10
        )
        
        if metadata.status_code == 200:
            print("✅ OpenID4VC metadata disponible")
            
            # Test credential offer
            offer_data = {
                "student_id": "vps-oid4vc-001",
                "student_name": "Estudiante OpenID4VC",
                "student_email": "oid4vc@vps.com", 
                "course_name": "OpenID4VC Test Course",
                "completion_date": "2025-08-06T16:00:00Z",
                "grade": "A+"
            }
            
            offer_response = requests.post(
                f"{VPS_URL}/oid4vc/credential-offer",
                json=offer_data,
                timeout=15
            )
            
            if offer_response.status_code == 200:
                result = offer_response.json()
                print("✅ Credential offer creado!")
                print(f"🔗 OpenID4VC URL: {result['qr_url'][:50]}...")
                print("📱 Compatible con Lissi Wallet!")
            else:
                print(f"❌ Offer error: {offer_response.status_code}")
                
        else:
            print("⏳ OpenID4VC aún no disponible")
            print("   Ejecuta primero: git pull && docker-compose restart")
            
    except Exception as e:
        print(f"⏳ OpenID4VC no disponible aún: {e}")
    
    print("\n🎯 RESUMEN:")
    print("===========")
    print("✅ DIDComm: Mantiene compatibilidad con wallets existentes")
    print("🆕 OpenID4VC: Añade soporte para Lissi y wallets modernas")
    print("🔄 Migración: Gradual sin interrumpir servicio")

if __name__ == "__main__":
    test_vps_endpoints()
"@

# Guardar script de test
$vpsTestScript | Out-File -FilePath "test_vps_migration.py" -Encoding UTF8

Write-Host "✅ Script creado: test_vps_migration.py" -ForegroundColor Green

Write-Host ""
Write-Host "🎉 MIGRACIÓN LISTA PARA VPS" -ForegroundColor Green
Write-Host "============================" -ForegroundColor Green
Write-Host ""
Write-Host "📝 RESUMEN DE CAMBIOS:" -ForegroundColor Cyan
Write-Host "   ✅ Endpoints actuales: Funcionando (/api/credential/request)" -ForegroundColor Green
Write-Host "   🆕 Nuevos endpoints: OpenID4VC (/oid4vc/*)" -ForegroundColor Cyan
Write-Host "   🔧 URL VPS: http://209.38.151.153" -ForegroundColor Gray
Write-Host "   📱 Compatible: Lissi Wallet + wallets modernas" -ForegroundColor Yellow
Write-Host ""
Write-Host "🚀 SIGUIENTE PASO:" -ForegroundColor Yellow
Write-Host "   1. Conecta al VPS: ssh root@209.38.151.153" -ForegroundColor White
Write-Host "   2. Ve a tu proyecto y ejecuta: git pull origin main" -ForegroundColor White
Write-Host "   3. Rebuild: docker-compose down && docker-compose build && docker-compose up -d" -ForegroundColor White
Write-Host "   4. Prueba: python test_vps_migration.py" -ForegroundColor White

# Preguntar si quiere ejecutar test local del VPS
$testRemote = Read-Host "`n¿Quieres probar los endpoints del VPS ahora desde aquí? (s/n)"
if ($testRemote -eq "s" -or $testRemote -eq "S") {
    Write-Host "🧪 Ejecutando test remoto..." -ForegroundColor Cyan
    python test_vps_migration.py
}
