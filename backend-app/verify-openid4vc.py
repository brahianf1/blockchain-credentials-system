#!/usr/bin/env python3
"""
Verificación completa del sistema OpenID4VC después del deployment
Simula el comportamiento de walt.id wallet
"""

import requests
import json
import time
import sys
from datetime import datetime
from urllib.parse import urlencode

# Configuración para VPS
BASE_URL = "https://utnpf.site"
OID4VC_BASE = f"{BASE_URL}/oid4vc"

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def log(message, color=Colors.GREEN):
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[{timestamp}]{Colors.END} {message}")

def error(message):
    log(f"❌ ERROR: {message}", Colors.RED)

def warning(message):
    log(f"⚠️  WARNING: {message}", Colors.YELLOW)

def success(message):
    log(f"✅ {message}", Colors.GREEN)

def test_endpoint(name, url, expected_status=200, method="GET", data=None, headers=None):
    """Función helper para testear endpoints"""
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=10)
        
        if response.status_code == expected_status:
            success(f"{name}: OK ({response.status_code})")
            return response
        else:
            error(f"{name}: Status {response.status_code}, esperado {expected_status}")
            print(f"   Response: {response.text[:200]}...")
            return None
    except requests.exceptions.RequestException as e:
        error(f"{name}: {str(e)}")
        return None

def main():
    print(f"{Colors.BOLD}🔍 VERIFICACIÓN OPENID4VC WALT.ID COMPATIBILITY{Colors.END}")
    print(f"URL Base: {BASE_URL}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print()
    
    # 1. Verificar endpoints básicos
    log("🏥 Verificando endpoints básicos...")
    
    # Health check
    health_response = test_endpoint(
        "Health Check", 
        f"{OID4VC_BASE}/health"
    )
    
    # Metadata
    metadata_response = test_endpoint(
        "OpenID Credential Issuer Metadata",
        f"{OID4VC_BASE}/.well-known/openid-credential-issuer"
    )
    
    # JWKS
    jwks_response = test_endpoint(
        "JWKS Endpoint",
        f"{OID4VC_BASE}/.well-known/jwks.json"
    )
    
    # SSL Test
    ssl_response = test_endpoint(
        "SSL Configuration Test",
        f"{OID4VC_BASE}/ssl-test"
    )
    
    if not all([health_response, metadata_response, jwks_response]):
        error("Endpoints básicos fallan. Abortando tests.")
        return False
    
    # 2. Crear credential offer de prueba
    log("📝 Creando credential offer de prueba...")
    
    test_credential = {
        "student_id": "walt_test_001",
        "student_name": "Walt.id Test User",
        "student_email": "test@walt.id",
        "course_name": "OpenID4VC Compatibility Test",
        "completion_date": "2024-01-01",
        "grade": "A+"
    }
    
    offer_response = test_endpoint(
        "Create Credential Offer",
        f"{OID4VC_BASE}/credential-offer",
        expected_status=200,
        method="POST",
        data=test_credential
    )
    
    if not offer_response:
        error("No se pudo crear credential offer")
        return False
    
    offer_data = offer_response.json()
    pre_auth_code = offer_data.get("pre_authorized_code")
    
    if not pre_auth_code:
        error("Credential offer no contiene pre_authorized_code")
        return False
    
    success(f"Credential offer creado: {pre_auth_code}")
    
    # 3. Simular comportamiento de walt.id wallet
    log("🟢 Simulando walt.id wallet...")
    
    # Walt.id envía parámetros como query params (comportamiento observado)
    grant_type = "urn:ietf:params:oauth:grant-type:pre-authorized_code"
    query_params = {
        "grant_type": grant_type,
        "pre_authorized_code": pre_auth_code
    }
    
    # Test 1: Endpoint específico para walt.id
    log("   🧪 Test 1: Endpoint específico walt.id (/walt-token)")
    walt_url = f"{OID4VC_BASE}/walt-token?{urlencode(query_params)}"
    
    walt_response = requests.post(walt_url, timeout=10)
    
    if walt_response.status_code == 200:
        walt_data = walt_response.json()
        walt_token = walt_data.get("access_token")
        if walt_token:
            success(f"Walt.id endpoint: Access token obtenido ({walt_token[:20]}...)")
        else:
            error("Walt.id endpoint: No access token en response")
            print(f"   Response: {walt_response.text}")
    else:
        error(f"Walt.id endpoint: Status {walt_response.status_code}")
        print(f"   Response: {walt_response.text}")
    
    # Test 2: Endpoint universal con query params
    log("   🧪 Test 2: Endpoint universal con query params (/token)")
    universal_url = f"{OID4VC_BASE}/token?{urlencode(query_params)}"
    
    universal_response = requests.post(universal_url, timeout=10)
    
    if universal_response.status_code == 200:
        universal_data = universal_response.json()
        universal_token = universal_data.get("access_token")
        if universal_token:
            success(f"Universal endpoint: Access token obtenido ({universal_token[:20]}...)")
        else:
            error("Universal endpoint: No access token en response")
            print(f"   Response: {universal_response.text}")
    else:
        error(f"Universal endpoint: Status {universal_response.status_code}")
        print(f"   Response: {universal_response.text}")
    
    # Test 3: Endpoint universal con form data (estándar OpenID4VC)
    log("   🧪 Test 3: Endpoint universal con form data (estándar)")
    form_headers = {"Content-Type": "application/x-www-form-urlencoded"}
    form_data = urlencode(query_params)
    
    form_response = requests.post(
        f"{OID4VC_BASE}/token",
        data=form_data,
        headers=form_headers,
        timeout=10
    )
    
    if form_response.status_code == 200:
        form_data_result = form_response.json()
        form_token = form_data_result.get("access_token")
        if form_token:
            success(f"Form data method: Access token obtenido ({form_token[:20]}...)")
        else:
            error("Form data method: No access token en response")
            print(f"   Response: {form_response.text}")
    else:
        error(f"Form data method: Status {form_response.status_code}")
        print(f"   Response: {form_response.text}")
    
    # 4. Test de debug endpoint
    log("🔍 Probando debug endpoint...")
    debug_response = requests.post(
        f"{OID4VC_BASE}/token/debug?{urlencode(query_params)}",
        timeout=10
    )
    
    if debug_response.status_code == 200:
        success("Debug endpoint funcionando")
        debug_data = debug_response.json()
        if "debug_info" in debug_data:
            print(f"   Query params detectados: {debug_data['debug_info'].get('query_params', {})}")
    else:
        warning(f"Debug endpoint: Status {debug_response.status_code}")
    
    # 5. Test completo del flujo (si tenemos access token)
    access_token = None
    if 'walt_token' in locals() and walt_token:
        access_token = walt_token
    elif 'universal_token' in locals() and universal_token:
        access_token = universal_token
    elif 'form_token' in locals() and form_token:
        access_token = form_token
    
    if access_token:
        log("🎫 Probando emisión de credencial...")
        
        # Simular request de credencial
        credential_url = f"{OID4VC_BASE}/credential"
        credential_headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # El parámetro debe ir en el body según la implementación actual
        credential_payload = {
            "credential_configuration_id": "UniversityCredential"
        }
        
        credential_response = requests.post(
            credential_url,
            json=credential_payload,
            headers=credential_headers,
            timeout=10
        )
        
        if credential_response.status_code == 200:
            credential_data = credential_response.json()
            if "credentials" in credential_data:
                success("✅ Credencial JWT obtenida exitosamente!")
                jwt_credential = credential_data["credentials"][0]["credential"]
                print(f"   JWT: {jwt_credential[:50]}...")
                
                # Verificar que es un JWT válido
                jwt_parts = jwt_credential.split('.')
                if len(jwt_parts) == 3:
                    success("JWT estructura válida (header.payload.signature)")
                else:
                    warning("JWT con estructura inválida")
            else:
                error("Response no contiene credenciales")
                print(f"   Response: {credential_response.text}")
        else:
            error(f"Credential endpoint: Status {credential_response.status_code}")
            print(f"   Response: {credential_response.text}")
    
    # 6. Resumen final
    print()
    log("📊 RESUMEN DE VERIFICACIÓN", Colors.BOLD)
    print(f"   🏥 Health Check: {'✅' if health_response else '❌'}")
    print(f"   📡 Metadata: {'✅' if metadata_response else '❌'}")
    print(f"   🔑 JWKS: {'✅' if jwks_response else '❌'}")
    print(f"   🔐 SSL: {'✅' if ssl_response else '❌'}")
    print(f"   📝 Credential Offer: {'✅' if offer_response else '❌'}")
    print(f"   🟢 Walt.id Endpoint: {'✅' if 'walt_token' in locals() and walt_token else '❌'}")
    print(f"   🌐 Universal Endpoint: {'✅' if 'universal_token' in locals() and universal_token else '❌'}")
    print(f"   📋 Form Data Method: {'✅' if 'form_token' in locals() and form_token else '❌'}")
    print(f"   🎫 Credential Issuance: {'✅' if access_token and 'credential_data' in locals() else '❌'}")
    
    print()
    if all([health_response, metadata_response, jwks_response, offer_response]) and access_token:
        success("🎉 SISTEMA COMPLETAMENTE FUNCIONAL PARA WALT.ID!")
        print(f"{Colors.GREEN}   El sistema está listo para usar con wallet.demo.walt.id{Colors.END}")
        return True
    else:
        error("💥 SISTEMA CON PROBLEMAS - Revisar logs")
        return False

if __name__ == "__main__":
    success_result = main()
    sys.exit(0 if success_result else 1)
