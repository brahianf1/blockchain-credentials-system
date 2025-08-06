#!/usr/bin/env python3
"""
Test específico para VPS Digital Ocean - http://209.38.151.153
Prueba tanto el sistema actual (DIDComm) como el nuevo (OpenID4VC)
"""

import requests
import json
import time

VPS_URL = "http://209.38.151.153"

def test_current_didcomm_system():
    """Probar el sistema DIDComm actual que ya funciona en el VPS"""
    print("🧪 === PROBANDO SISTEMA ACTUAL (DIDComm) ===")
    print(f"🌐 VPS: {VPS_URL}")
    
    try:
        # Test health endpoint
        print("\n📡 Verificando health endpoint...")
        health_response = requests.get(f"{VPS_URL}/health", timeout=10)
        
        if health_response.status_code == 200:
            print("✅ VPS responde correctamente")
        else:
            print(f"⚠️ Health status: {health_response.status_code}")
        
        # Test el endpoint real que usas para credenciales
        print(f"\n📋 Probando endpoint principal: /api/credential/request")
        
        test_data = {
            "student_id": "vps-test-001",
            "student_name": "Estudiante Prueba VPS", 
            "student_email": "test@universidad-vps.com",
            "course_id": "curso-blockchain-001",
            "course_name": "Blockchain y Credenciales Verificables",
            "completion_date": "2025-08-06T15:30:00Z",
            "grade": "A",
            "instructor_name": "Prof. Blockchain"
        }
        
        print("   Enviando solicitud de credencial...")
        didcomm_response = requests.post(
            f"{VPS_URL}/api/credential/request",
            json=test_data,
            timeout=20  # Más tiempo para el VPS
        )
        
        if didcomm_response.status_code == 200:
            result = didcomm_response.json()
            print("✅ DIDComm funciona perfectamente en VPS!")
            print(f"🔗 Invitation URL: {result['invitation_url'][:70]}...")
            print(f"📱 QR Code: {len(result['qr_code_base64'])} caracteres")
            print(f"🆔 Connection ID: {result['connection_id']}")
            print("⚠️  LIMITACIÓN: No compatible con Lissi Wallet")
            return True
        else:
            print(f"❌ Error DIDComm: {didcomm_response.status_code}")
            print(f"   Response: {didcomm_response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ No se puede conectar al VPS: {VPS_URL}")
        print("   Verifica que el servidor esté ejecutándose")
        return False
    except Exception as e:
        print(f"💥 Error probando DIDComm: {e}")
        return False

def test_new_openid4vc_system():
    """Probar el nuevo sistema OpenID4VC (solo funciona después del git pull)"""
    print("\n🆕 === PROBANDO SISTEMA NUEVO (OpenID4VC) ===")
    
    try:
        # Test metadata endpoint
        print("📋 Verificando metadata de OpenID4VC...")
        metadata_response = requests.get(
            f"{VPS_URL}/oid4vc/.well-known/openid-credential-issuer",
            timeout=10
        )
        
        if metadata_response.status_code == 200:
            metadata = metadata_response.json()
            print("✅ OpenID4VC metadata disponible!")
            print(f"   Issuer: {metadata.get('credential_issuer', 'N/A')}")
            print(f"   Credential Endpoint: {metadata.get('credential_endpoint', 'N/A')}")
            
            # Test credential offer
            print("\n🎫 Probando creación de credential offer...")
            
            offer_data = {
                "student_id": "vps-openid4vc-001",
                "student_name": "Estudiante OpenID4VC VPS",
                "student_email": "openid4vc@universidad-vps.com", 
                "course_name": "Migración a OpenID4VC",
                "completion_date": "2025-08-06T16:00:00Z",
                "grade": "A+"
            }
            
            offer_response = requests.post(
                f"{VPS_URL}/oid4vc/credential-offer",
                json=offer_data,
                timeout=20
            )
            
            if offer_response.status_code == 200:
                result = offer_response.json()
                print("✅ OpenID4VC credential offer creado!")
                print(f"🔗 OpenID4VC URL: {result['qr_url'][:70]}...")
                print(f"📱 QR Code: {len(result['qr_code_base64'])} caracteres")
                print(f"🔑 Pre-auth Code: {result['pre_authorized_code']}")
                print("✅ COMPATIBLE CON: Lissi Wallet, EUDI Wallet, wallets modernas")
                return True
            else:
                print(f"❌ Error creando offer: {offer_response.status_code}")
                print(f"   Response: {offer_response.text[:200]}")
                return False
                
        else:
            print("⏳ OpenID4VC aún no disponible en VPS")
            print(f"   Status: {metadata_response.status_code}")
            if metadata_response.status_code == 404:
                print("💡 Necesitas hacer 'git pull' y rebuild en el VPS")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ No se puede conectar al VPS: {VPS_URL}")
        return False
    except Exception as e:
        print(f"⏳ OpenID4VC no disponible aún: {e}")
        print("💡 Ejecuta primero en el VPS:")
        print("   git pull origin main")
        print("   docker-compose down && docker-compose build && docker-compose up -d")
        return False

def show_migration_summary():
    """Mostrar resumen de la migración"""
    print("\n📊 === RESUMEN DE LA MIGRACIÓN ===")
    
    comparison = """
    | Aspecto                | DIDComm (Actual)        | OpenID4VC (Nuevo)       |
    |------------------------|-------------------------|-------------------------|
    | URL VPS               | ✅ http://209.38.151.153| ✅ http://209.38.151.153|
    | Endpoint              | /api/credential/request | /oid4vc/credential-offer|
    | Compatible con Lissi  | ❌ NO                   | ✅ SÍ                   |
    | Protocolo             | RFC 0434 DIDComm        | OpenID4VCI              |
    | QR Format             | didcomm://...           | openid-credential-offer:|
    | Estado en VPS         | ✅ Funcionando          | ⏳ Pendiente git pull   |
    | Wallets compatibles   | ACA-Py, Credo          | Lissi, EUDI, modernas   |
    """
    
    print(comparison)

def main():
    print("🎯 MIGRACIÓN OPENID4VC - TEST VPS DIGITAL OCEAN")
    print("=" * 55)
    print(f"🌐 VPS: {VPS_URL}")
    print(f"📅 Fecha: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test sistema actual
    didcomm_works = test_current_didcomm_system()
    
    # Test nuevo sistema
    openid4vc_works = test_new_openid4vc_system()
    
    # Mostrar resumen
    show_migration_summary()
    
    print("\n🎯 ESTADO DE LA MIGRACIÓN:")
    print("=" * 30)
    
    if didcomm_works:
        print("✅ DIDComm: Funcionando en VPS")
    else:
        print("❌ DIDComm: Problemas en VPS")
    
    if openid4vc_works:
        print("✅ OpenID4VC: Funcionando en VPS")
        print("🎉 ¡Migración completada! Tu sistema es compatible con Lissi Wallet")
    else:
        print("⏳ OpenID4VC: Pendiente migración")
        print("\n📋 PASOS PARA COMPLETAR:")
        print("1. Conectar al VPS: ssh root@209.38.151.153")
        print("2. Navegar al proyecto: cd /root/blockchain-credentials-system")
        print("3. Actualizar código: git pull origin main")
        print("4. Instalar dependencias: docker-compose run --rm python-controller pip install PyJWT jwcrypto")
        print("5. Rebuild: docker-compose down && docker-compose build && docker-compose up -d")
        print("6. Probar de nuevo: python test_vps_migration.py")
    
    print(f"\n🔗 URLs finales:")
    print(f"   DIDComm: {VPS_URL}/api/credential/request")
    print(f"   OpenID4VC: {VPS_URL}/oid4vc/credential-offer")
    print(f"   Metadata: {VPS_URL}/oid4vc/.well-known/openid-credential-issuer")

if __name__ == "__main__":
    main()
