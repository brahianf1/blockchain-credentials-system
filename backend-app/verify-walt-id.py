#!/usr/bin/env python3
"""
Verificación específica para compatibilidad con walt.id wallet
Prueba el formato exacto del credential offer según OpenID4VC Draft-16
"""

import json
import requests
from urllib.parse import unquote, quote
import base64

# Configuración
ISSUER_URL = "https://utnpf.site"
ENDPOINT = f"{ISSUER_URL}/oid4vc/credential-offer"

def test_credential_offer_format():
    """Prueba el formato del credential offer para walt.id"""
    
    print("🧪 === PRUEBA DE COMPATIBILIDAD WALT.ID ===")
    print(f"Endpoint: {ENDPOINT}")
    print()
    
    # Datos de prueba
    test_data = {
        "student_id": "walt-test-001", 
        "student_name": "Walt Test User",
        "student_email": "walt@test.example",
        "course_name": "OpenID4VC Compatibility Test",
        "completion_date": "2025-08-07T10:00:00Z",
        "grade": "A+"
    }
    
    try:
        # Crear credential offer
        print("📤 Enviando request para crear credential offer...")
        response = requests.post(ENDPOINT, json=test_data, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Error HTTP {response.status_code}: {response.text}")
            return False
            
        data = response.json()
        print("✅ Credential offer creado exitosamente")
        
        # Extraer QR URL
        qr_url = data.get('qr_url', '')
        if not qr_url:
            print("❌ No se encontró qr_url en la respuesta")
            return False
            
        print(f"📋 QR URL generada (longitud: {len(qr_url)} chars):")
        print(f"   {qr_url[:100]}..." if len(qr_url) > 100 else f"   {qr_url}")
        print()
        
        # Verificar esquema URI
        if not qr_url.startswith("openid-credential-offer://"):
            print(f"❌ Esquema URI incorrecto: {qr_url.split('://')[0]}")
            print("   ✅ Esperado: openid-credential-offer://")
            return False
        print("✅ Esquema URI correcto: openid-credential-offer://")
        
        # Extraer y decodificar credential offer
        if "?credential_offer=" not in qr_url:
            print("❌ Parámetro credential_offer no encontrado")
            return False
            
        encoded_offer = qr_url.split("?credential_offer=")[1]
        
        try:
            decoded_offer = unquote(encoded_offer)
            offer_obj = json.loads(decoded_offer)
            print("✅ Credential offer decodificado exitosamente")
        except Exception as e:
            print(f"❌ Error decodificando offer: {e}")
            return False
        
        # Verificar estructura según OpenID4VC Draft-16
        print("🔍 Verificando estructura OpenID4VC...")
        
        required_fields = ["credential_issuer", "credential_configuration_ids", "grants"]
        for field in required_fields:
            if field not in offer_obj:
                print(f"❌ Campo requerido faltante: {field}")
                return False
            print(f"✅ Campo {field}: presente")
        
        # Verificar grants específicos
        grants = offer_obj.get("grants", {})
        expected_grant = "urn:ietf:params:oauth:grant-type:pre-authorized_code"
        
        if expected_grant not in grants:
            print(f"❌ Grant type requerido faltante: {expected_grant}")
            return False
        print(f"✅ Grant type correcto: {expected_grant}")
        
        # Verificar pre-authorized_code
        grant_data = grants[expected_grant]
        if "pre-authorized_code" not in grant_data:
            print("❌ pre-authorized_code faltante en grant")
            return False
        print("✅ pre-authorized_code presente")
        
        # Verificar credential_issuer
        if offer_obj["credential_issuer"] != ISSUER_URL:
            print(f"❌ credential_issuer incorrecto: {offer_obj['credential_issuer']}")
            return False
        print(f"✅ credential_issuer correcto: {ISSUER_URL}")
        
        # Verificar credential_configuration_ids
        config_ids = offer_obj["credential_configuration_ids"]
        if not isinstance(config_ids, list) or len(config_ids) == 0:
            print("❌ credential_configuration_ids debe ser array no vacío")
            return False
        print(f"✅ credential_configuration_ids: {config_ids}")
        
        # Mostrar estructura completa
        print("\n📋 Estructura completa del credential offer:")
        print(json.dumps(offer_obj, indent=2))
        
        # Test de longitud para compatibilidad QR
        qr_length = len(qr_url)
        if qr_length > 1800:
            print(f"⚠️  Advertencia: QR muy largo ({qr_length} chars), puede fallar en algunos scanners")
        else:
            print(f"✅ Longitud QR aceptable: {qr_length} chars")
        
        print("\n🎉 ¡CREDENTIAL OFFER COMPATIBLE CON WALT.ID!")
        print("📱 Puedes usar esta URL en wallet.demo.walt.id")
        print(f"🔗 URL completa: {qr_url}")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_metadata_endpoint():
    """Prueba el endpoint de metadata OpenID4VC"""
    
    print("\n🔍 === VERIFICANDO METADATA OPENID4VC ===")
    
    metadata_url = f"{ISSUER_URL}/oid4vc/.well-known/openid-credential-issuer"
    print(f"Endpoint: {metadata_url}")
    
    try:
        response = requests.get(metadata_url, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Error HTTP {response.status_code}")
            return False
            
        metadata = response.json()
        
        # Verificar campos requeridos
        required_fields = [
            "credential_issuer", 
            "credential_endpoint", 
            "credential_configurations_supported"
        ]
        
        for field in required_fields:
            if field not in metadata:
                print(f"❌ Campo requerido faltante en metadata: {field}")
                return False
            print(f"✅ Metadata {field}: presente")
        
        # Verificar UniversityCredential config
        configs = metadata.get("credential_configurations_supported", {})
        if "UniversityCredential" not in configs:
            print("❌ UniversityCredential no encontrada en configuraciones")
            return False
        print("✅ UniversityCredential configurada correctamente")
        
        print("✅ Metadata OpenID4VC válida")
        return True
        
    except Exception as e:
        print(f"❌ Error verificando metadata: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando verificación de compatibilidad walt.id...\n")
    
    # Ejecutar todas las pruebas
    offer_ok = test_credential_offer_format()
    metadata_ok = test_metadata_endpoint()
    
    print("\n" + "="*60)
    print("📊 RESUMEN DE RESULTADOS:")
    print(f"   Credential Offer: {'✅ CORRECTO' if offer_ok else '❌ FALLO'}")
    print(f"   Metadata OpenID4VC: {'✅ CORRECTO' if metadata_ok else '❌ FALLO'}")
    
    if offer_ok and metadata_ok:
        print("\n🎉 ¡SISTEMA TOTALMENTE COMPATIBLE CON WALT.ID!")
        print("🔗 Prueba en: https://wallet.demo.walt.id/")
    else:
        print("\n❌ Se encontraron problemas que deben solucionarse")
    
    print("="*60)
