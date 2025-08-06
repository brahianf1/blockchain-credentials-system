#!/usr/bin/env python3
"""
Test OpenID4VC - Prueba de tu nueva implementación compatible con Lissi Wallet
Reemplaza test_endpoint.py con soporte para ambos protocolos
"""

import requests
import json
import time

# URLs de tu controller
BASE_URL = "http://localhost:3000"

def test_didcomm_flow():
    """Probar flujo DIDComm original (tu implementación actual)"""
    print("🧪 === PROBANDO FLUJO DIDCOMM (ACTUAL) ===")
    
    data = {
        "student_id": "123",
        "student_name": "Juan Pérez", 
        "student_email": "estudiante@ejemplo.com",
        "course_id": "curso-001",
        "course_name": "Introducción a Blockchain",
        "completion_date": "2025-08-03T10:30:00Z",
        "grade": "A",
        "instructor_name": "Prof. García"
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/credential/request",
            json=data,
            timeout=10
        )
        
        print(f"✅ DIDComm Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"🔗 DIDComm Invitation URL: {result['invitation_url'][:100]}...")
            print(f"📱 QR Code disponible: {len(result['qr_code_base64'])} caracteres")
            print("⚠️  COMPATIBLE CON: Wallets DIDComm antiguas")
        else:
            print(f"❌ Error DIDComm: {response.text}")
            
    except Exception as e:
        print(f"💥 Error probando DIDComm: {e}")

def test_openid4vc_flow():
    """Probar nuevo flujo OpenID4VC (compatible con Lissi)"""
    print("\n🆕 === PROBANDO FLUJO OPENID4VC (NUEVO) ===")
    
    data = {
        "student_id": "456",
        "student_name": "María García", 
        "student_email": "maria@ejemplo.com",
        "course_name": "Credenciales Verificables W3C",
        "completion_date": "2025-08-06T15:30:00Z",
        "grade": "A+"
    }
    
    try:
        # 1. Verificar metadata del issuer
        print("📋 Verificando metadata del issuer...")
        metadata_response = requests.get(f"{BASE_URL}/oid4vc/.well-known/openid-credential-issuer")
        
        if metadata_response.status_code == 200:
            print("✅ Metadata del issuer disponible")
            metadata = metadata_response.json()
            print(f"🎯 Credential Issuer: {metadata['credential_issuer']}")
        else:
            print(f"❌ Metadata no disponible: {metadata_response.status_code}")
            return
        
        # 2. Crear credential offer
        print("🎫 Creando Credential Offer...")
        offer_response = requests.post(
            f"{BASE_URL}/oid4vc/credential-offer",
            json=data,
            timeout=10
        )
        
        if offer_response.status_code == 200:
            result = offer_response.json()
            print(f"✅ OpenID4VC Status: {offer_response.status_code}")
            print(f"🔗 OpenID4VC URL: {result['qr_url'][:100]}...")
            print(f"📱 QR Code disponible: {len(result['qr_code_base64'])} caracteres")
            print(f"🔑 Pre-auth Code: {result['pre_authorized_code']}")
            print("✅ COMPATIBLE CON: Lissi Wallet, wallets OpenID4VC modernas")
            
            # Mostrar información del offer
            offer = result['offer']
            print(f"📋 Credential Types: {offer['credential_configuration_ids']}")
            
        else:
            print(f"❌ Error OpenID4VC: {offer_response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: Controller no está ejecutándose en puerto 3000")
        print("💡 Ejecuta: docker-compose up -d python-controller")
    except Exception as e:
        print(f"💥 Error probando OpenID4VC: {e}")

def compare_protocols():
    """Comparar ambos protocolos"""
    print("\n📊 === COMPARACIÓN DE PROTOCOLOS ===")
    
    comparison = """
    | Característica          | DIDComm (Actual)     | OpenID4VC (Nuevo)      |
    |------------------------|---------------------|------------------------|
    | Compatible con Lissi   | ❌ NO               | ✅ SÍ                  |
    | Formato QR             | invitation_url      | openid-credential-offer|
    | Protocolo              | RFC 0434 DIDComm    | OpenID4VCI Draft-16    |
    | Wallets compatibles    | ACA-Py, Credo       | Lissi, EUDI, modernas  |
    | Estándar europeo       | ❌ NO               | ✅ SÍ (eIDAS 2.0)      |
    | Complejidad            | Media               | Baja                   |
    | Futuro                 | ⚠️  Legacy          | ✅ Estándar actual     |
    """
    
    print(comparison)

def main():
    print("🎯 SISTEMA DE CREDENCIALES W3C - TEST DE PROTOCOLOS")
    print("=" * 60)
    
    # Probar flujo actual (DIDComm)
    test_didcomm_flow()
    
    # Probar nuevo flujo (OpenID4VC)
    test_openid4vc_flow()
    
    # Comparación
    compare_protocols()
    
    print("\n💡 RECOMENDACIÓN:")
    print("   1. Mantén DIDComm para compatibilidad con sistemas existentes")
    print("   2. Usa OpenID4VC para nuevos usuarios y wallets modernas como Lissi")
    print("   3. Migra gradualmente todos los endpoints a OpenID4VC")

if __name__ == "__main__":
    main()
