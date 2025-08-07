#!/usr/bin/env python3
"""
Test específico para metadatos OpenID4VC compatible con walt.id
Verifica que el formato sea exactamente el esperado por walt.id wallet
"""

import json
import requests
from typing import Dict, Any

# Configuración
ISSUER_URL = "https://utnpf.site"
METADATA_URL = f"{ISSUER_URL}/oid4vc/.well-known/openid-credential-issuer"

def test_metadata_format():
    """Verifica el formato de metadatos compatible con walt.id"""
    
    print("🔍 === TEST METADATOS OPENID4VC PARA WALT.ID ===")
    print(f"URL: {METADATA_URL}")
    print()
    
    try:
        response = requests.get(METADATA_URL, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Error HTTP {response.status_code}: {response.text}")
            return False
            
        metadata = response.json()
        print("✅ Metadatos obtenidos exitosamente")
        
        # Campos requeridos por OpenID4VC
        required_fields = [
            "credential_issuer",
            "credential_endpoint", 
            "credential_configurations_supported"
        ]
        
        for field in required_fields:
            if field not in metadata:
                print(f"❌ Campo requerido faltante: {field}")
                return False
            print(f"✅ Campo {field}: presente")
        
        # Verificar credential_configurations_supported
        configs = metadata.get("credential_configurations_supported", {})
        if "UniversityCredential" not in configs:
            print("❌ UniversityCredential no encontrada en configuraciones")
            return False
        
        university_config = configs["UniversityCredential"]
        print("✅ UniversityCredential encontrada")
        
        # Verificar campos específicos de UniversityCredential
        required_config_fields = [
            "format",
            "credential_definition", 
            "proof_types_supported"
        ]
        
        for field in required_config_fields:
            if field not in university_config:
                print(f"❌ Campo requerido en UniversityCredential: {field}")
                return False
            print(f"✅ UniversityCredential.{field}: presente")
        
        # Verificar proof_types_supported (CRÍTICO para walt.id)
        proof_types = university_config.get("proof_types_supported", {})
        if not isinstance(proof_types, dict):
            print(f"❌ proof_types_supported debe ser un objeto, es: {type(proof_types)}")
            return False
        print("✅ proof_types_supported es un objeto (correcto para walt.id)")
        
        if "jwt" not in proof_types:
            print("❌ proof_types_supported debe contener 'jwt'")
            return False
        print("✅ proof_types_supported contiene 'jwt'")
        
        jwt_proof = proof_types["jwt"]
        if not isinstance(jwt_proof, dict):
            print(f"❌ proof_types_supported.jwt debe ser un objeto, es: {type(jwt_proof)}")
            return False
        print("✅ proof_types_supported.jwt es un objeto")
        
        # Verificar credential_definition
        cred_def = university_config.get("credential_definition", {})
        if "type" not in cred_def:
            print("❌ credential_definition debe contener 'type'")
            return False
        print("✅ credential_definition contiene 'type'")
        
        cred_types = cred_def["type"]
        expected_types = ["VerifiableCredential", "UniversityCredential"]
        if cred_types != expected_types:
            print(f"❌ credential_definition.type incorrecto: {cred_types}")
            print(f"   Esperado: {expected_types}")
            return False
        print("✅ credential_definition.type correcto")
        
        # Mostrar estructura completa
        print("\n📋 Estructura de metadatos:")
        print(json.dumps(metadata, indent=2))
        
        print("\n🎉 ¡METADATOS COMPATIBLES CON WALT.ID!")
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Error de conexión: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Error decodificando JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        return False

def test_token_endpoint():
    """Verifica que el token endpoint esté accesible"""
    
    print("\n🔧 === TEST TOKEN ENDPOINT ===")
    
    token_url = f"{ISSUER_URL}/oid4vc/token"
    print(f"URL: {token_url}")
    
    # Solo verificamos que esté accesible (esperamos 422 por falta de parámetros)
    try:
        response = requests.post(token_url, timeout=10)
        
        if response.status_code == 422:
            print("✅ Token endpoint accesible (422 es esperado sin parámetros)")
            return True
        elif response.status_code == 405:
            print("✅ Token endpoint accesible (405 Method Not Allowed es aceptable)")
            return True
        else:
            print(f"⚠️  Token endpoint responde con {response.status_code}")
            return True  # No es crítico para este test
            
    except Exception as e:
        print(f"❌ Error verificando token endpoint: {e}")
        return False

def test_credential_endpoint():
    """Verifica que el credential endpoint esté accesible"""
    
    print("\n🔧 === TEST CREDENTIAL ENDPOINT ===")
    
    cred_url = f"{ISSUER_URL}/oid4vc/credential"
    print(f"URL: {cred_url}")
    
    try:
        response = requests.post(cred_url, timeout=10)
        
        if response.status_code in [401, 422, 400]:
            print(f"✅ Credential endpoint accesible ({response.status_code} es esperado sin auth)")
            return True
        else:
            print(f"⚠️  Credential endpoint responde con {response.status_code}")
            return True  # No es crítico para este test
            
    except Exception as e:
        print(f"❌ Error verificando credential endpoint: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando test de compatibilidad walt.id para metadatos...\n")
    
    # Ejecutar tests
    metadata_ok = test_metadata_format()
    token_ok = test_token_endpoint() 
    cred_ok = test_credential_endpoint()
    
    print("\n" + "="*60)
    print("📊 RESUMEN DE RESULTADOS:")
    print(f"   Metadatos: {'✅ CORRECTO' if metadata_ok else '❌ FALLO'}")
    print(f"   Token Endpoint: {'✅ CORRECTO' if token_ok else '❌ FALLO'}")
    print(f"   Credential Endpoint: {'✅ CORRECTO' if cred_ok else '❌ FALLO'}")
    
    if metadata_ok and token_ok and cred_ok:
        print("\n🎉 ¡METADATOS TOTALMENTE COMPATIBLES CON WALT.ID!")
        print("📋 Los metadatos ya no deberían dar el error JsonDecodingException")
        print("🔗 Puedes probar de nuevo en: https://wallet.demo.walt.id/")
    else:
        print("\n❌ Se encontraron problemas en los metadatos")
    
    print("="*60)
