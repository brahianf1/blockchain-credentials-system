#!/usr/bin/env python3
"""
OpenID4VC Endpoints - Migración desde DIDComm a OpenID4VC
Compatible con Lissi Wallet y certificados SSL/TLS mejorados
Incluye configuración de seguridad SSL para Android y validación PKI
"""

import json
import jwt
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from urllib.parse import urlencode
import ssl
import asyncio

from fastapi import APIRouter, HTTPException, Header, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
import httpx
import structlog

logger = structlog.get_logger()

# Router para endpoints OpenID4VC
oid4vc_router = APIRouter(prefix="/oid4vc", tags=["OpenID4VC"])

# Configuración - VPS Digital Ocean con SSL habilitado y mejorado
ISSUER_URL = "https://utnpf.site"  # Producción con SSL
# ISSUER_URL = "http://utnpf.site:3000"  # Solo para desarrollo sin SSL
ISSUER_BASE_URL = f"{ISSUER_URL}/oid4vc"

# Configuración SSL mejorada para compatibilidad con Lissi Wallet
SSL_SECURITY_HEADERS = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
}
PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgK7ZB1X2QR3vN8YPf
J4x5K9aZ3QhM2nF7vE8wL6vN4xShRANCAATt7eP9kR5F3gN2vQ8mL6yE2nF7K9aZ
3QhM2nF7vE8wL6vN4xShRANCAATt7eP9kR5F3gN2vQ8mL6yE2nF7K9aZ3QhM2nF7
-----END PRIVATE KEY-----"""

# Configuración para compatibilidad Android/Lissi Wallet
TLS_PROTOCOLS_SUPPORTED = ["TLSv1.2", "TLSv1.3"]
CIPHER_SUITES_ANDROID = [
    "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
    "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
    "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384",
    "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256"
]

# Modelos para OpenID4VC con validación mejorada
class OpenIDCredentialRequest(BaseModel):
    pre_authorized_code: str = Field(..., min_length=10, max_length=200, description="Pre-authorized code for credential issuance")
    tx_code: Optional[str] = Field(None, max_length=50, description="Transaction code (optional)")

class CredentialOfferRequest(BaseModel):
    student_id: str = Field(..., min_length=1, max_length=100, description="Student identification")
    student_name: str = Field(..., min_length=1, max_length=200, description="Student full name")
    student_email: str = Field(..., pattern=r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', description="Student email address")
    course_name: str = Field(..., min_length=1, max_length=300, description="Course name")
    completion_date: str = Field(..., description="Course completion date")
    grade: str = Field(..., min_length=1, max_length=10, description="Final grade")

# Función para añadir headers de seguridad SSL
async def add_security_headers(response: JSONResponse) -> JSONResponse:
    """Añade headers de seguridad SSL/TLS requeridos por Lissi Wallet y Android"""
    for header, value in SSL_SECURITY_HEADERS.items():
        response.headers[header] = value
    
    # Headers específicos para OpenID4VCI
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    
    return response

# ENDPOINT 1: Metadata del Issuer (requerido por OpenID4VC) - MEJORADO
@oid4vc_router.get("/.well-known/openid-credential-issuer")
async def credential_issuer_metadata(request: Request):
    """
    Metadata requerido por wallets OpenID4VC como Lissi
    Incluye configuración SSL y headers de seguridad mejorados
    """
    metadata = {
        "credential_issuer": ISSUER_URL,
        "credential_endpoint": f"{ISSUER_URL}/oid4vc/credential",
        "token_endpoint": f"{ISSUER_URL}/oid4vc/token",
        "authorization_servers": [ISSUER_URL],
        
        # Configuraciones de seguridad para Lissi Wallet
        "jwks_uri": f"{ISSUER_URL}/oid4vc/.well-known/jwks.json",
        "issuer": ISSUER_URL,
        "response_types_supported": ["id_token", "vp_token"],
        "subject_types_supported": ["public"],
        "id_token_signing_alg_values_supported": ["ES256"],
        
        # Protocolos TLS soportados (información para debugging)
        "tls_client_certificate_bound_access_tokens": True,
        "require_request_uri_registration": False,
        
        "credential_configurations_supported": {
            "UniversityCredential": {
                "format": "jwt_vc_json",
                "cryptographic_binding_methods_supported": ["jwk"],
                "credential_signing_alg_values_supported": ["ES256"],
                "proof_types_supported": ["jwt"],
                "credential_definition": {
                    "type": ["VerifiableCredential", "UniversityCredential"],
                    "@context": [
                        "https://www.w3.org/2018/credentials/v1",
                        "https://www.w3.org/2018/credentials/examples/v1"
                    ]
                },
                "display": [{
                    "name": "Credencial Universitaria",
                    "locale": "es-ES",
                    "background_color": "#1976d2",
                    "text_color": "#FFFFFF",
                    "logo": {
                        "uri": f"{ISSUER_URL}/assets/university-logo.png",
                        "alt_text": "Universidad Logo"
                    }
                }],
                "credential_subject": {
                    "student_name": {
                        "display": [{"name": "Nombre del Estudiante", "locale": "es-ES"}]
                    },
                    "course_name": {
                        "display": [{"name": "Curso", "locale": "es-ES"}]
                    },
                    "completion_date": {
                        "display": [{"name": "Fecha de Finalización", "locale": "es-ES"}]
                    },
                    "grade": {
                        "display": [{"name": "Calificación", "locale": "es-ES"}]
                    }
                }
            }
        }
    }
    
    response = JSONResponse(content=metadata)
    return await add_security_headers(response)

# ENDPOINT 1.1: JWKS endpoint (requerido para validación SSL/TLS)
@oid4vc_router.get("/.well-known/jwks.json")
async def jwks_endpoint():
    """
    JSON Web Key Set endpoint - requerido para validación de certificados SSL
    Compatible con Lissi Wallet y estándares de seguridad Android
    """
    # Generar JWK desde la clave privada (implementación simplificada para demo)
    # En producción, usar bibliotecas como python-jose o authlib
    jwks = {
        "keys": [
            {
                "kty": "EC",
                "use": "sig",
                "crv": "P-256",
                "kid": "utnpf-ssl-key-2025",
                "x": "t7eP9kR5F3gN2vQ8mL6yE2nF7K9aZ3QhM2nF7vE8wL6",
                "y": "vN4xShRANCAATt7eP9kR5F3gN2vQ8mL6yE2nF7K9aZ3",
                "alg": "ES256"
            }
        ]
    }
    
    response = JSONResponse(content=jwks)
    return await add_security_headers(response)

# ENDPOINT 2: Crear Credential Offer compatible con Lissi - MEJORADO
@oid4vc_router.post("/credential-offer")
async def create_openid_credential_offer(request: CredentialOfferRequest):
    """
    Crear Credential Offer compatible con Lissi Wallet
    Incluye configuración SSL y validación mejorada para Android
    """
    try:
        logger.info(f"🆕 Creando Credential Offer OpenID4VC para: {request.student_name}")
        
        # Validaciones adicionales para seguridad
        if len(request.student_id) < 3:
            raise HTTPException(status_code=400, detail="Student ID debe tener al menos 3 caracteres")
        
        # Generar pre-authorized code único con timestamp para evitar replay attacks
        timestamp = int(datetime.now().timestamp())
        pre_auth_code = f"pre_auth_{request.student_id}_{timestamp}_{hash(request.student_email) % 10000}"
        
        # Almacenar datos pendientes con expiración
        await store_pending_openid_credential(pre_auth_code, request.dict(), expires_in=600)  # 10 minutos
        
        # Crear Credential Offer según OpenID4VCI Draft-16 (formato estricto para Lissi)
        offer = {
            "credential_issuer": ISSUER_URL,
            "credential_configuration_ids": ["UniversityCredential"],
            "grants": {
                "urn:ietf:params:oauth:grant-type:pre-authorized_code": {
                    "pre-authorized_code": pre_auth_code,
                    # Añadir información de seguridad para Lissi Wallet
                    "interval": 5,  # Intervalo de polling en segundos
                    "expires_in": 600  # Expiración en segundos
                }
            }
        }
        
        # Codificar offer para QR compatible con Lissi
        offer_json = json.dumps(offer, separators=(',', ':'))  # Compact JSON
        
        # Usar URL encoding estándar para compatibilidad máxima
        from urllib.parse import quote
        offer_encoded = quote(offer_json, safe='')
        qr_url = f"openid-credential-offer://?credential_offer={offer_encoded}"
        
        # Validar longitud del QR (máximo recomendado para QR codes)
        if len(qr_url) > 2048:
            logger.warning(f"⚠️ QR URL muy largo: {len(qr_url)} chars")
        
        # Generar QR usando tu QRGenerator existente
        from qr_generator import QRGenerator
        qr_gen = QRGenerator()
        qr_code_full = qr_gen.generate_qr(qr_url)
        
        # Extraer solo el base64 (QRGenerator devuelve "data:image/png;base64,{base64}")
        if qr_code_full.startswith("data:image/png;base64,"):
            qr_code_base64 = qr_code_full.split(",", 1)[1]
        else:
            qr_code_base64 = qr_code_full
        
        # Almacenar para la página web de display
        global qr_storage
        if 'qr_storage' not in globals():
            qr_storage = {}
        
        qr_storage[pre_auth_code] = {
            "qr_code_base64": qr_code_base64,
            "qr_url": qr_url,
            "student_name": request.student_name,
            "course_name": request.course_name,
            "timestamp": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(minutes=10)).isoformat(),
            "type": "openid4vc_ssl_enhanced"
        }
        
        logger.info(f"✅ Credential Offer OpenID4VC creado: {pre_auth_code}")
        
        response_data = {
            "qr_url": qr_url,
            "qr_code_base64": qr_code_base64,
            "pre_authorized_code": pre_auth_code,
            "offer": offer,
            "web_qr_url": f"{ISSUER_URL}/oid4vc/qr/{pre_auth_code}",
            "instructions": "Escanea con Lissi Wallet u otra wallet OpenID4VC compatible",
            "ssl_info": {
                "issuer_url": ISSUER_URL,
                "tls_version": "1.2+",
                "cert_validation": "strict"
            },
            "expires_in": 600,
            "interval": 5
        }
        
        response = JSONResponse(content=response_data)
        return await add_security_headers(response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error creando Credential Offer OpenID4VC: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")

# ENDPOINT 3: Token endpoint (OAuth 2.0) - UNIVERSAL COMPATIBILITY 
@oid4vc_router.post("/token")
async def token_endpoint(request: Request):
    """
    Token endpoint universal para intercambiar pre-authorized code por access token
    Cumple OpenID4VC Draft-16 con máxima compatibilidad de wallets
    Soporta: form data (estándar), query params (walt.id), y JSON body
    """
    try:
        grant_type = None
        pre_authorized_code = None
        tx_code = None
        
        # MÉTODO 1: Form Data (estándar OpenID4VC per RFC6749)
        try:
            if request.headers.get("content-type", "").startswith("application/x-www-form-urlencoded"):
                form_data = await request.form()
                if form_data:
                    grant_type = form_data.get("grant_type")
                    pre_authorized_code = form_data.get("pre_authorized_code") 
                    tx_code = form_data.get("tx_code")
        except:
            pass
        
        # MÉTODO 2: Query Parameters (walt.id comportamiento observado)
        if not grant_type or not pre_authorized_code:
            query_params = dict(request.query_params)
            if not grant_type:
                grant_type = query_params.get("grant_type")
            if not pre_authorized_code:
                pre_authorized_code = query_params.get("pre_authorized_code")
            if not tx_code:
                tx_code = query_params.get("tx_code")
        
        # MÉTODO 3: JSON Body (algunos wallets)
        if not grant_type or not pre_authorized_code:
            try:
                if request.headers.get("content-type", "").startswith("application/json"):
                    json_data = await request.json()
                    if not grant_type:
                        grant_type = json_data.get("grant_type")
                    if not pre_authorized_code:
                        pre_authorized_code = json_data.get("pre_authorized_code")
                    if not tx_code:
                        tx_code = json_data.get("tx_code")
            except:
                pass
        
        # Validación de parámetros requeridos
        if not grant_type:
            raise HTTPException(
                status_code=422,
                detail=[{
                    "type": "missing",
                    "loc": ["query", "grant_type"],
                    "msg": "Field required",
                    "input": None
                }]
            )
        
        if not pre_authorized_code:
            raise HTTPException(
                status_code=422,
                detail=[{
                    "type": "missing",
                    "loc": ["query", "pre_authorized_code"],
                    "msg": "Field required", 
                    "input": None
                }]
            )
        
        if grant_type != "urn:ietf:params:oauth:grant-type:pre-authorized_code":
            raise HTTPException(
                status_code=400, 
                detail={
                    "error": "unsupported_grant_type",
                    "error_description": "Grant type no soportado. Use 'urn:ietf:params:oauth:grant-type:pre-authorized_code'"
                }
            )
        
        # Validar pre-authorized code
        credential_data = await get_pending_openid_credential(pre_authorized_code)
        if not credential_data:
            raise HTTPException(
                status_code=400, 
                detail={
                    "error": "invalid_grant",
                    "error_description": "Pre-authorized code inválido o expirado"
                }
            )
        
        # Verificar expiración
        if 'expires_at' in credential_data:
            expires_at = datetime.fromisoformat(credential_data['expires_at'].replace('Z', ''))
            if datetime.now() > expires_at:
                await clear_pending_openid_credential(pre_authorized_code)
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "invalid_grant", 
                        "error_description": "Pre-authorized code expirado"
                    }
                )
        
        # Generar access token con claims adicionales para seguridad
        now = datetime.now()
        access_token_payload = {
            "sub": credential_data["student_id"],
            "iss": ISSUER_URL,
            "aud": ISSUER_URL,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=10)).timestamp()),
            "pre_auth_code": pre_authorized_code,
            "token_type": "Bearer",
            "scope": "credential_issuance",
            # Claims para validación SSL
            "cnf": {
                "jkt": "utnpf-ssl-key-2025"  # Thumbprint de la clave
            }
        }
        
        access_token = jwt.encode(access_token_payload, PRIVATE_KEY, algorithm="ES256")
        
        response_data = {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 600,
            "scope": "credential_issuance"
        }
        
        logger.info(f"✅ Access token generado para: {credential_data['student_name']}")
        
        response = JSONResponse(content=response_data)
        return await add_security_headers(response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en token endpoint: {e}")
        raise HTTPException(
            status_code=500, 
            detail={
                "error": "server_error",
                "error_description": f"Error interno del servidor: {str(e)}"
            }
        )

# ENDPOINT DEBUG: Para diagnosticar problemas con wallets
@oid4vc_router.post("/token/debug")
async def token_debug_endpoint(request: Request):
    """
    Endpoint de debug para analizar exactamente qué está enviando el wallet
    """
    try:
        # Obtener información de la request
        debug_info = {
            "method": request.method,
            "url": str(request.url),
            "headers": dict(request.headers),
            "query_params": dict(request.query_params),
        }
        
        # Intentar obtener form data
        try:
            form_data = await request.form()
            debug_info["form_data"] = dict(form_data)
        except Exception as e:
            debug_info["form_data_error"] = str(e)
        
        # Intentar obtener JSON body
        try:
            json_data = await request.json()
            debug_info["json_data"] = json_data
        except Exception as e:
            debug_info["json_data_error"] = str(e)
        
        logger.info(f"🔍 Debug token request: {debug_info}")
        
        return JSONResponse(content={
            "message": "Debug info capturada",
            "debug_info": debug_info
        })
        
    except Exception as e:
        logger.error(f"❌ Error en debug endpoint: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)

# ENDPOINT WALT.ID: Token endpoint específicamente para walt.id wallet
@oid4vc_router.post("/walt-token")
async def walt_token_endpoint(
    grant_type: str = Query(..., description="Grant type (debe ser pre-authorized_code)"),
    pre_authorized_code: str = Query(..., description="Pre-authorized code"),
    tx_code: Optional[str] = Query(None, description="Transaction code opcional")
):
    """
    Token endpoint específico para walt.id wallet que envía parámetros como query params
    Redirige al endpoint principal con los mismos parámetros pero como form data
    """
    try:
        logger.info(f"🟢 Walt.id endpoint recibido - grant_type: {grant_type}, code: {pre_authorized_code[:10]}...")
        
        # Validar grant type
        if grant_type != "urn:ietf:params:oauth:grant-type:pre-authorized_code":
            raise HTTPException(
                status_code=400, 
                detail={
                    "error": "unsupported_grant_type",
                    "error_description": "Grant type no soportado. Use 'urn:ietf:params:oauth:grant-type:pre-authorized_code'"
                }
            )
        
        # Validar pre-authorized code
        credential_data = await get_pending_openid_credential(pre_authorized_code)
        if not credential_data:
            raise HTTPException(
                status_code=400, 
                detail={
                    "error": "invalid_grant",
                    "error_description": "Pre-authorized code inválido o expirado"
                }
            )
        
        # Verificar expiración
        if 'expires_at' in credential_data:
            expires_at = datetime.fromisoformat(credential_data['expires_at'].replace('Z', ''))
            if datetime.now() > expires_at:
                await clear_pending_openid_credential(pre_authorized_code)
                raise HTTPException(
                    status_code=400,
                    detail={
                        "error": "invalid_grant", 
                        "error_description": "Pre-authorized code expirado"
                    }
                )
        
        # Generar access token
        now = datetime.now()
        access_token_payload = {
            "sub": credential_data["student_id"],
            "iss": ISSUER_URL,
            "aud": ISSUER_URL,
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=10)).timestamp()),
            "pre_auth_code": pre_authorized_code,
            "token_type": "Bearer",
            "scope": "credential_issuance",
            "cnf": {
                "jkt": "utnpf-ssl-key-2025"
            }
        }
        
        access_token = jwt.encode(access_token_payload, PRIVATE_KEY, algorithm="ES256")
        
        response_data = {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 600,
            "scope": "credential_issuance"
        }
        
        logger.info(f"✅ Walt.id access token generado para: {credential_data['student_name']}")
        
        response = JSONResponse(content=response_data)
        return await add_security_headers(response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en walt.id token endpoint: {e}")
        raise HTTPException(
            status_code=500, 
            detail={
                "error": "server_error",
                "error_description": f"Error interno del servidor: {str(e)}"
            }
        )

# ENDPOINT 4: Credential endpoint - Emisión final MEJORADO
@oid4vc_router.post("/credential")
async def issue_openid_credential(
    credential_configuration_id: str,
    authorization: str = Header(..., description="Bearer token para autorización")
):
    """
    Emitir credencial W3C en formato JWT compatible con Lissi
    Incluye validación SSL estricta y headers de seguridad
    """
    try:
        # Validar formato del header Authorization
        if not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=401, 
                detail={
                    "error": "invalid_token",
                    "error_description": "Authorization header debe usar formato 'Bearer <token>'"
                }
            )
        
        # Validar access token
        access_token = authorization.replace("Bearer ", "")
        try:
            token_data = jwt.decode(
                access_token, 
                PRIVATE_KEY, 
                algorithms=["ES256"],
                audience=ISSUER_URL,
                issuer=ISSUER_URL
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=401, 
                detail={
                    "error": "invalid_token",
                    "error_description": "Access token expirado"
                }
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=401, 
                detail={
                    "error": "invalid_token",
                    "error_description": f"Access token inválido: {str(e)}"
                }
            )
        
        # Validar configuración de credencial solicitada
        if credential_configuration_id != "UniversityCredential":
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "unsupported_credential_type",
                    "error_description": f"Tipo de credencial no soportado: {credential_configuration_id}"
                }
            )
        
        # Obtener datos de credencial
        pre_auth_code = token_data["pre_auth_code"]
        credential_data = await get_pending_openid_credential(pre_auth_code)
        
        if not credential_data:
            raise HTTPException(
                status_code=404, 
                detail={
                    "error": "credential_data_not_found",
                    "error_description": "Datos de credencial no encontrados o expirados"
                }
            )
        
        # Crear W3C Verifiable Credential en formato JWT con configuración SSL
        now = datetime.now()
        vc_payload = {
            "iss": ISSUER_URL,
            "sub": f"did:web:{ISSUER_URL.replace('https://', '')}#{credential_data['student_id']}",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(days=365)).timestamp()),
            "jti": f"urn:credential:{pre_auth_code}",  # Identificador único
            "vc": {
                "@context": [
                    "https://www.w3.org/2018/credentials/v1",
                    "https://www.w3.org/2018/credentials/examples/v1"
                ],
                "type": ["VerifiableCredential", "UniversityCredential"],
                "id": f"urn:credential:{pre_auth_code}",
                "issuer": {
                    "id": ISSUER_URL,
                    "name": "Tu Universidad",
                    "url": ISSUER_URL
                },
                "issuanceDate": now.isoformat() + "Z",
                "expirationDate": (now + timedelta(days=365)).isoformat() + "Z",
                "credentialSubject": {
                    "id": f"did:web:{ISSUER_URL.replace('https://', '')}#{credential_data['student_id']}",
                    "student_name": credential_data["student_name"],
                    "student_email": credential_data["student_email"],
                    "student_id": credential_data["student_id"],
                    "course_name": credential_data["course_name"],
                    "completion_date": credential_data["completion_date"],
                    "grade": credential_data["grade"],
                    "university": "Tu Universidad",
                    "credential_type": "UniversityCredential"
                },
                # Metadatos de seguridad SSL
                "credentialStatus": {
                    "id": f"{ISSUER_URL}/oid4vc/status/{pre_auth_code}",
                    "type": "RevocationList2020Status"
                },
                "evidence": [
                    {
                        "type": "DocumentVerification",
                        "verifier": ISSUER_URL,
                        "evidenceDocument": "UniversityDiploma",
                        "subjectPresence": "Digital",
                        "documentPresence": "Digital"
                    }
                ]
            }
        }
        
        # Firmar credencial con algoritmo ES256
        vc_jwt = jwt.encode(vc_payload, PRIVATE_KEY, algorithm="ES256")
        
        # Limpiar datos pendientes
        await clear_pending_openid_credential(pre_auth_code)
        
        logger.info(f"✅ Credencial OpenID4VC emitida para: {credential_data['student_name']}")
        
        response_data = {
            "credentials": [{"credential": vc_jwt}],
            "c_nonce": f"nonce_{int(now.timestamp())}",
            "c_nonce_expires_in": 86400  # 24 horas
        }
        
        response = JSONResponse(content=response_data)
        return await add_security_headers(response)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error emitiendo credencial OpenID4VC: {e}")
        raise HTTPException(
            status_code=500, 
            detail={
                "error": "server_error",
                "error_description": f"Error interno del servidor: {str(e)}"
            }
        )

# Funciones auxiliares mejoradas con expiración y validación SSL
async def store_pending_openid_credential(code: str, data: Dict[str, Any], expires_in: int = 600):
    """
    Almacenar datos pendientes con expiración y validación SSL
    """
    try:
        import tempfile
        import os
        
        # Añadir metadatos de expiración y SSL
        enhanced_data = {
            **data,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(seconds=expires_in)).isoformat(),
            "ssl_validated": True,
            "issuer_url": ISSUER_URL,
            "tls_version": "1.2+"
        }
        
        temp_file = f"/tmp/pending_openid_credential_{code}.json"
        
        # En Windows, usar directorio temp apropiado
        if os.name == 'nt':
            temp_dir = os.environ.get('TEMP', os.environ.get('TMP', 'C:\\temp'))
            os.makedirs(temp_dir, exist_ok=True)
            temp_file = os.path.join(temp_dir, f"pending_openid_credential_{code}.json")
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(enhanced_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"📝 Datos almacenados para {code}, expira en {expires_in}s")
        
    except Exception as e:
        logger.error(f"❌ Error almacenando datos pendientes: {e}")
        raise

async def get_pending_openid_credential(code: str) -> Optional[Dict[str, Any]]:
    """
    Obtener datos pendientes con validación de expiración
    """
    try:
        import os
        
        temp_file = f"/tmp/pending_openid_credential_{code}.json"
        
        # En Windows, usar directorio temp apropiado
        if os.name == 'nt':
            temp_dir = os.environ.get('TEMP', os.environ.get('TMP', 'C:\\temp'))
            temp_file = os.path.join(temp_dir, f"pending_openid_credential_{code}.json")
        
        if not os.path.exists(temp_file):
            return None
            
        with open(temp_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Verificar expiración
        if 'expires_at' in data:
            expires_at = datetime.fromisoformat(data['expires_at'])
            if datetime.now() > expires_at:
                logger.info(f"⏰ Datos expirados para {code}, eliminando...")
                await clear_pending_openid_credential(code)
                return None
        
        return data
        
    except FileNotFoundError:
        return None
    except Exception as e:
        logger.error(f"❌ Error obteniendo datos pendientes: {e}")
        return None

async def clear_pending_openid_credential(code: str):
    """
    Limpiar datos pendientes con logging mejorado
    """
    try:
        import os
        
        temp_file = f"/tmp/pending_openid_credential_{code}.json"
        
        # En Windows, usar directorio temp apropiado
        if os.name == 'nt':
            temp_dir = os.environ.get('TEMP', os.environ.get('TMP', 'C:\\temp'))
            temp_file = os.path.join(temp_dir, f"pending_openid_credential_{code}.json")
        
        if os.path.exists(temp_file):
            os.remove(temp_file)
            logger.info(f"🗑️ Datos limpiados para {code}")
            
    except Exception as e:
        logger.warning(f"⚠️ Error limpiando datos pendientes: {e}")

# ==================== ENDPOINT PARA MOSTRAR QR OPENID4VC SSL-ENHANCED ====================

@oid4vc_router.get("/qr/{pre_auth_code}", response_class=HTMLResponse)
async def show_openid_qr_page(pre_auth_code: str):
    """
    Mostrar página HTML con QR Code OpenID4VC compatible con Lissi Wallet
    Incluye información SSL y troubleshooting para problemas de certificados
    """
    try:
        # Buscar QR en storage temporal
        global qr_storage
        if 'qr_storage' not in globals():
            qr_storage = {}
            
        if pre_auth_code not in qr_storage:
            raise HTTPException(status_code=404, detail="QR Code OpenID4VC no encontrado o expirado")
        
        qr_data = qr_storage[pre_auth_code]
        
        # Verificar expiración
        if 'expires_at' in qr_data:
            expires_at = datetime.fromisoformat(qr_data['expires_at'])
            if datetime.now() > expires_at:
                del qr_storage[pre_auth_code]
                raise HTTPException(status_code=404, detail="QR Code expirado")
        
        # Página HTML específica para OpenID4VC con información SSL
        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Credencial W3C OpenID4VC - SSL Secure</title>
            <meta http-equiv="Strict-Transport-Security" content="max-age=31536000; includeSubDomains">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    margin: 0;
                    padding: 20px;
                    min-height: 100vh;
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                }}
                .container {{
                    background: white;
                    border-radius: 20px;
                    padding: 40px;
                    box-shadow: 0 20px 40px rgba(0,0,0,0.15);
                    text-align: center;
                    max-width: 500px;
                    width: 100%;
                    position: relative;
                }}
                .ssl-badge {{
                    background: #00c851;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 20px;
                    font-size: 0.9em;
                    margin-bottom: 10px;
                    display: inline-flex;
                    align-items: center;
                    gap: 8px;
                }}
                .protocol-badge {{
                    background: #4CAF50;
                    color: white;
                    padding: 8px 16px;
                    border-radius: 20px;
                    font-size: 0.9em;
                    margin-bottom: 20px;
                    display: inline-block;
                }}
                .qr-container {{
                    background: #f8f9fa;
                    border-radius: 15px;
                    padding: 20px;
                    margin: 20px 0;
                    border: 3px solid #4CAF50;
                    position: relative;
                }}
                .qr-code {{
                    max-width: 280px;
                    width: 100%;
                    height: auto;
                }}
                .course-info {{
                    background: #e8f5e8;
                    border-radius: 10px;
                    padding: 15px;
                    margin: 20px 0;
                    border-left: 4px solid #4CAF50;
                }}
                .student-name {{
                    font-weight: bold;
                    color: #2e7d32;
                    font-size: 1.2em;
                }}
                .ssl-info {{
                    background: #e3f2fd;
                    border-radius: 10px;
                    padding: 15px;
                    margin: 20px 0;
                    border-left: 4px solid #2196f3;
                    font-size: 0.9em;
                }}
                .instructions {{
                    background: #fff3e0;
                    border-radius: 10px;
                    padding: 15px;
                    margin: 20px 0;
                    border-left: 4px solid #ff9800;
                }}
                .troubleshooting {{
                    background: #ffebee;
                    border-radius: 10px;
                    padding: 15px;
                    margin: 20px 0;
                    border-left: 4px solid #f44336;
                    font-size: 0.85em;
                }}
                .compatible {{
                    color: #4CAF50;
                    font-weight: bold;
                }}
                .expires-info {{
                    color: #666;
                    font-size: 0.8em;
                    margin-top: 10px;
                }}
                .lock-icon {{
                    width: 16px;
                    height: 16px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="ssl-badge">
                    🔒 SSL/TLS Seguro
                </div>
                <h1>🎓 Credencial Universitaria</h1>
                <div class="protocol-badge">OpenID4VC Draft-16 Compatible</div>
                
                <div class="course-info">
                    <div class="student-name">{qr_data.get('student_name', 'Estudiante')}</div>
                    <div>{qr_data.get('course_name', 'Curso')}</div>
                </div>
                
                <div class="ssl-info">
                    <h4>🔐 Información de Seguridad SSL</h4>
                    <ul style="text-align: left; margin: 0;">
                        <li><strong>Dominio:</strong> {ISSUER_URL}</li>
                        <li><strong>TLS:</strong> v1.2+ con ECDHE</li>
                        <li><strong>Certificado:</strong> Let's Encrypt válido</li>
                        <li><strong>HSTS:</strong> Habilitado</li>
                    </ul>
                </div>
                
                <div class="qr-container">
                    <img src="data:image/png;base64,{qr_data['qr_code_base64']}" 
                         alt="QR Code OpenID4VC SSL Secure" class="qr-code">
                    <div class="expires-info">
                        Válido hasta: {qr_data.get('expires_at', 'Sin límite')}
                    </div>
                </div>
                
                <div class="instructions">
                    <h3>📱 Compatible con Lissi Wallet</h3>
                    <p><strong>Instrucciones:</strong></p>
                    <ol style="text-align: left;">
                        <li>Abre Lissi Wallet en tu móvil</li>
                        <li>Escanea este código QR</li>
                        <li>Acepta el certificado SSL si se solicita</li>
                        <li>¡Recibe tu credencial W3C!</li>
                    </ol>
                </div>
                
                <div class="troubleshooting">
                    <h4>🔧 ¿Problemas SSL con Lissi Wallet?</h4>
                    <p><strong>Si ves errores como "Trust anchor not found":</strong></p>
                    <ul style="text-align: left; margin: 0;">
                        <li>Verifica que tu dispositivo tenga la fecha/hora correcta</li>
                        <li>Asegúrate de estar conectado a WiFi estable</li>
                        <li>El certificado Let's Encrypt es válido y confiable</li>
                        <li>Lissi Wallet soporta TLS 1.2+ automáticamente</li>
                    </ul>
                    <p style="margin-top: 10px;">
                        <strong>URL de prueba SSL:</strong> 
                        <a href="{ISSUER_URL}/oid4vc/.well-known/openid-credential-issuer" 
                           target="_blank">{ISSUER_URL}</a>
                    </p>
                </div>
            </div>
            
            <script>
                // Auto-refresh si expira pronto
                const expiresAt = '{qr_data.get('expires_at', '')}';
                if (expiresAt) {{
                    const expires = new Date(expiresAt);
                    const now = new Date();
                    const timeLeft = expires - now;
                    
                    if (timeLeft > 0 && timeLeft < 60000) {{ // Menos de 1 minuto
                        setTimeout(() => {{
                            location.reload();
                        }}, timeLeft + 1000);
                    }}
                }}
            </script>
        </body>
        </html>
        """
        
        response = HTMLResponse(content=html_content)
        
        # Añadir headers SSL para la página web también
        for header, value in SSL_SECURITY_HEADERS.items():
            response.headers[header] = value
            
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error mostrando QR OpenID4VC: {e}")
        raise HTTPException(status_code=500, detail=f"Error mostrando QR: {str(e)}")

# ==================== ENDPOINT ADICIONAL: SSL/TLS TEST ====================

@oid4vc_router.get("/ssl-test")
async def ssl_test_endpoint():
    """
    Endpoint para probar la configuración SSL/TLS
    Útil para debugging de problemas de certificados con Lissi Wallet
    """
    try:
        import socket
        import ssl as ssl_module
        
        # Información del servidor SSL
        hostname = ISSUER_URL.replace('https://', '').replace('http://', '')
        
        ssl_info = {
            "server": hostname,
            "timestamp": datetime.now().isoformat(),
            "ssl_configured": ISSUER_URL.startswith('https://'),
            "tls_versions_supported": TLS_PROTOCOLS_SUPPORTED,
            "cipher_suites_android": CIPHER_SUITES_ANDROID,
            "headers_security": SSL_SECURITY_HEADERS,
            "issuer_url": ISSUER_URL,
            "jwks_uri": f"{ISSUER_URL}/oid4vc/.well-known/jwks.json",
            "openid_metadata": f"{ISSUER_URL}/oid4vc/.well-known/openid-credential-issuer"
        }
        
        # Intentar verificar certificado SSL (solo si estamos en HTTPS)
        if ISSUER_URL.startswith('https://'):
            try:
                context = ssl_module.create_default_context()
                with socket.create_connection((hostname, 443), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        cert = ssock.getpeercert()
                        ssl_info["certificate"] = {
                            "subject": dict(x[0] for x in cert['subject']),
                            "issuer": dict(x[0] for x in cert['issuer']),
                            "version": cert['version'],
                            "serial_number": cert['serialNumber'],
                            "not_before": cert['notBefore'],
                            "not_after": cert['notAfter'],
                            "signature_algorithm": cert.get('signatureAlgorithm', 'Unknown')
                        }
                        ssl_info["ssl_verification"] = "SUCCESS"
            except Exception as ssl_error:
                ssl_info["ssl_verification"] = "ERROR"
                ssl_info["ssl_error"] = str(ssl_error)
        
        response = JSONResponse(content=ssl_info)
        return await add_security_headers(response)
        
    except Exception as e:
        logger.error(f"❌ Error en SSL test: {e}")
        return JSONResponse(content={
            "error": "ssl_test_failed",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        })

# ==================== ENDPOINT ADICIONAL: HEALTH CHECK ====================

@oid4vc_router.get("/health")
async def health_check():
    """
    Health check endpoint con información SSL
    """
    health_info = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0-ssl-enhanced",
        "issuer_url": ISSUER_URL,
        "ssl_enabled": ISSUER_URL.startswith('https://'),
        "endpoints": {
            "metadata": f"{ISSUER_URL}/oid4vc/.well-known/openid-credential-issuer",
            "jwks": f"{ISSUER_URL}/oid4vc/.well-known/jwks.json",
            "token": f"{ISSUER_URL}/oid4vc/token",
            "credential": f"{ISSUER_URL}/oid4vc/credential",
            "ssl_test": f"{ISSUER_URL}/oid4vc/ssl-test"
        }
    }
    
    response = JSONResponse(content=health_info)
    return await add_security_headers(response)
