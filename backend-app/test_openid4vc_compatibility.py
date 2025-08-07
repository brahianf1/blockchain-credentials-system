#!/usr/bin/env python3
"""
Script de prueba para verificar compatibilidad del endpoint /oid4vc/token
con diferentes formatos de envío de parámetros
"""

import requests
import json
from urllib.parse import urlencode

# Configuración
BASE_URL = "https://utnpf.site"
TOKEN_ENDPOINT = f"{BASE_URL}/oid4vc/token"
DEBUG_ENDPOINT = f"{BASE_URL}/oid4vc/token/debug"

def test_form_data_method():
    """
    Prueba el método estándar con form data (OpenID4VC spec)
    """
    print("🧪 Probando método con FORM DATA (estándar OpenID4VC)...")
    
    data = {
        "grant_type": "urn:ietf:params:oauth:grant-type:pre-authorized_code",
        "pre_authorized_code": "test_code_123"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    try:
        response = requests.post(
            TOKEN_ENDPOINT,
            data=data,
            headers=headers,
            verify=True,  # Verificar SSL
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        return response.status_code, response.json() if response.content else None
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None, str(e)

def test_query_params_method():
    """
    Prueba el método con query parameters (lo que wallet.demo.walt.id podría estar haciendo)
    """
    print("🧪 Probando método con QUERY PARAMETERS...")
    
    params = {
        "grant_type": "urn:ietf:params:oauth:grant-type:pre-authorized_code",
        "pre_authorized_code": "test_code_123"
    }
    
    headers = {
        "Accept": "application/json"
    }
    
    try:
        response = requests.post(
            TOKEN_ENDPOINT,
            params=params,
            headers=headers,
            verify=True,
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        return response.status_code, response.json() if response.content else None
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None, str(e)

def test_mixed_method():
    """
    Prueba método mixto: algunos parámetros en query, otros en form
    """
    print("🧪 Probando método MIXTO...")
    
    # Query params
    params = {
        "grant_type": "urn:ietf:params:oauth:grant-type:pre-authorized_code"
    }
    
    # Form data
    data = {
        "pre_authorized_code": "test_code_123"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    try:
        response = requests.post(
            TOKEN_ENDPOINT,
            params=params,
            data=data,
            headers=headers,
            verify=True,
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response: {response.text}")
        
        return response.status_code, response.json() if response.content else None
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None, str(e)

def test_debug_endpoint():
    """
    Prueba el endpoint de debug para ver qué recibe el servidor
    """
    print("🔍 Probando ENDPOINT DEBUG...")
    
    # Simular request como wallet.demo.walt.id
    params = {
        "grant_type": "urn:ietf:params:oauth:grant-type:pre-authorized_code",
        "pre_authorized_code": "debug_test_code"
    }
    
    try:
        response = requests.post(
            DEBUG_ENDPOINT,
            params=params,
            verify=True,
            timeout=10
        )
        
        print(f"   Status Code: {response.status_code}")
        if response.content:
            debug_data = response.json()
            print(f"   Debug Info:")
            for key, value in debug_data.get("debug_info", {}).items():
                print(f"     {key}: {value}")
        
        return response.status_code, response.json() if response.content else None
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None, str(e)

def main():
    print("🚀 INICIANDO PRUEBAS DE COMPATIBILIDAD OpenID4VC")
    print("=" * 60)
    
    # Probar endpoint debug primero
    print("\n1. DEBUGGING:")
    test_debug_endpoint()
    
    print("\n2. MÉTODOS DE ENVÍO:")
    
    # Probar método estándar (form data)
    print("\n" + "-" * 40)
    status1, resp1 = test_form_data_method()
    
    # Probar método query params
    print("\n" + "-" * 40)
    status2, resp2 = test_query_params_method()
    
    # Probar método mixto
    print("\n" + "-" * 40)
    status3, resp3 = test_mixed_method()
    
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE RESULTADOS:")
    print(f"   Form Data: {status1}")
    print(f"   Query Params: {status2}")
    print(f"   Mixto: {status3}")
    
    # Determinar el método preferido
    if status2 and status2 != 422:
        print("\n✅ El servidor ahora acepta query parameters!")
    elif status1 and status1 != 422:
        print("\n✅ El servidor acepta form data estándar")
    else:
        print("\n❌ Hay problemas con ambos métodos")

if __name__ == "__main__":
    main()
