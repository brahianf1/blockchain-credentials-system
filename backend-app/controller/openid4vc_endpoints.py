#!/usr/bin/env python3
"""
OpenID4VC Endpoints - Migración desde DIDComm a OpenID4VC
Mantiene compatibilidad con tu código existente mientras añade soporte para Lissi Wallet
"""

import json
import jwt
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Header
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import httpx
import structlog

logger = structlog.get_logger()

# Router para endpoints OpenID4VC
oid4vc_router = APIRouter(prefix="/oid4vc", tags=["OpenID4VC"])

# Configuración - VPS Digital Ocean con SSL habilitado
ISSUER_URL = "https://utnpf.site"  # Producción con SSL
# ISSUER_URL = "http://utnpf.site:3000"  # Solo para desarrollo sin SSL
ISSUER_BASE_URL = f"{ISSUER_URL}/oid4vc"
PRIVATE_KEY = """-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgK7ZB1X2QR3vN8YPf
J4x5K9aZ3QhM2nF7vE8wL6vN4xShRANCAATt7eP9kR5F3gN2vQ8mL6yE2nF7K9aZ
3QhM2nF7vE8wL6vN4xShRANCAATt7eP9kR5F3gN2vQ8mL6yE2nF7K9aZ3QhM2nF7
-----END PRIVATE KEY-----"""

# Modelos para OpenID4VC
class OpenIDCredentialRequest(BaseModel):
    pre_authorized_code: str
    tx_code: Optional[str] = None

class CredentialOfferRequest(BaseModel):
    student_id: str
    student_name: str
    student_email: str
    course_name: str
    completion_date: str
    grade: str

# ENDPOINT 1: Metadata del Issuer (requerido por OpenID4VC)
@oid4vc_router.get("/.well-known/openid-credential-issuer")
async def credential_issuer_metadata():
    """Metadata requerido por wallets OpenID4VC como Lissi"""
    return {
        "credential_issuer": ISSUER_URL,
        "credential_endpoint": f"{ISSUER_URL}/oid4vc/credential",
        "token_endpoint": f"{ISSUER_URL}/oid4vc/token",
        "authorization_servers": [ISSUER_URL],
        "credential_configurations_supported": {
            "UniversityCredential": {
                "format": "jwt_vc_json",
                "cryptographic_binding_methods_supported": ["jwk"],
                "credential_signing_alg_values_supported": ["ES256"],
                "credential_definition": {
                    "type": ["VerifiableCredential", "UniversityCredential"]
                },
                "display": [{
                    "name": "Credencial Universitaria",
                    "locale": "es-ES",
                    "background_color": "#1976d2",
                    "text_color": "#FFFFFF"
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

# ENDPOINT 2: Crear Credential Offer compatible con Lissi
@oid4vc_router.post("/credential-offer")
async def create_openid_credential_offer(request: CredentialOfferRequest):
    """
    Crear Credential Offer compatible con Lissi Wallet
    REEMPLAZA tu endpoint /api/credential/request para wallets modernas
    """
    try:
        logger.info(f"🆕 Creando Credential Offer OpenID4VC para: {request.student_name}")
        
        # Generar pre-authorized code único
        pre_auth_code = f"pre_auth_{request.student_id}_{int(datetime.now().timestamp())}"
        
        # Almacenar datos pendientes (usa tu sistema actual de almacenamiento temporal)
        await store_pending_openid_credential(pre_auth_code, request.dict())
        
        # Crear Credential Offer según OpenID4VCI Draft-16 (formato estricto para Lissi)
        offer = {
            "credential_issuer": ISSUER_URL,
            "credential_configuration_ids": ["UniversityCredential"],
            "grants": {
                "urn:ietf:params:oauth:grant-type:pre-authorized_code": {
                    "pre-authorized_code": pre_auth_code
                    # tx_code se omite completamente cuando no se requiere
                }
            }
        }
        
        # Codificar offer para QR compatible con Lissi
        offer_json = json.dumps(offer)
        encoded_offer = base64.urlsafe_b64encode(offer_json.encode()).decode()
        
        # Codificar offer directamente en el QR (formato OpenID4VCI Draft-16 para Lissi)
        from urllib.parse import quote
        offer_encoded = quote(json.dumps(offer))
        qr_url = f"openid-credential-offer://?credential_offer={offer_encoded}"
        
        # Generar QR usando tu QRGenerator existente
        from qr_generator import QRGenerator
        qr_gen = QRGenerator()
        qr_code_full = qr_gen.generate_qr(qr_url)
        
        # Extraer solo el base64 (QRGenerator devuelve "data:image/png;base64,{base64}")
        if qr_code_full.startswith("data:image/png;base64,"):
            qr_code_base64 = qr_code_full.split(",", 1)[1]
        else:
            qr_code_base64 = qr_code_full
        
        # Almacenar solo para la página web de display
        global qr_storage
        if 'qr_storage' not in globals():
            qr_storage = {}
        
        qr_storage[pre_auth_code] = {
            "qr_code_base64": qr_code_base64,
            "qr_url": qr_url,
            "student_name": request.student_name,
            "course_name": request.course_name,
            "timestamp": datetime.now().isoformat(),
            "type": "openid4vc"
        }
        
        logger.info(f"✅ Credential Offer OpenID4VC creado: {pre_auth_code}")
        
        return {
            "qr_url": qr_url,
            "qr_code_base64": qr_code_base64,
            "pre_authorized_code": pre_auth_code,
            "offer": offer,
            "web_qr_url": f"{ISSUER_URL}/oid4vc/qr/{pre_auth_code}",
            "instructions": "Escanea con Lissi Wallet u otra wallet OpenID4VC compatible"
        }
        
    except Exception as e:
        logger.error(f"❌ Error creando Credential Offer OpenID4VC: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ENDPOINT 3: Token endpoint (OAuth 2.0)
@oid4vc_router.post("/token")
async def token_endpoint(
    grant_type: str,
    pre_authorized_code: str,
    tx_code: Optional[str] = None
):
    """Token endpoint para intercambiar pre-authorized code por access token"""
    try:
        if grant_type != "urn:ietf:params:oauth:grant-type:pre-authorized_code":
            raise HTTPException(status_code=400, detail="grant_type no soportado")
        
        # Validar pre-authorized code
        credential_data = await get_pending_openid_credential(pre_authorized_code)
        if not credential_data:
            raise HTTPException(status_code=400, detail="pre-authorized_code inválido")
        
        # Para este flujo sin tx_code requerido, aceptamos cualquier valor o ausencia
        # En producción, aquí validarías el tx_code si es requerido según la configuración
        
        # Generar access token
        access_token = jwt.encode({
            "sub": credential_data["student_id"],
            "iss": ISSUER_URL,
            "aud": ISSUER_URL,
            "iat": int(datetime.now().timestamp()),
            "exp": int((datetime.now() + timedelta(minutes=10)).timestamp()),
            "pre_auth_code": pre_authorized_code
        }, PRIVATE_KEY, algorithm="ES256")
        
        return {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": 600
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error en token endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ENDPOINT 4: Credential endpoint - Emisión final
@oid4vc_router.post("/credential")
async def issue_openid_credential(
    credential_configuration_id: str,
    authorization: str = Header(...)
):
    """
    Emitir credencial W3C en formato JWT compatible con Lissi
    REEMPLAZA la emisión DIDComm/AnonCreds
    """
    try:
        # Validar access token
        access_token = authorization.replace("Bearer ", "")
        try:
            token_data = jwt.decode(access_token, PRIVATE_KEY, algorithms=["ES256"])
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Access token inválido")
        
        # Obtener datos de credencial
        pre_auth_code = token_data["pre_auth_code"]
        credential_data = await get_pending_openid_credential(pre_auth_code)
        
        if not credential_data:
            raise HTTPException(status_code=404, detail="Datos de credencial no encontrados")
        
        # Crear W3C Verifiable Credential en formato JWT
        vc_payload = {
            "iss": ISSUER_URL,
            "sub": f"did:web:{ISSUER_URL.replace('https://', '')}#{credential_data['student_id']}",
            "iat": int(datetime.now().timestamp()),
            "exp": int((datetime.now() + timedelta(days=365)).timestamp()),
            "vc": {
                "@context": [
                    "https://www.w3.org/2018/credentials/v1",
                    "https://www.w3.org/2018/credentials/examples/v1"
                ],
                "type": ["VerifiableCredential", "UniversityCredential"],
                "issuer": ISSUER_URL,
                "issuanceDate": datetime.now().isoformat() + "Z",
                "credentialSubject": {
                    "id": f"did:web:{ISSUER_URL.replace('https://', '')}#{credential_data['student_id']}",
                    "student_name": credential_data["student_name"],
                    "student_email": credential_data["student_email"],
                    "course_name": credential_data["course_name"],
                    "completion_date": credential_data["completion_date"],
                    "grade": credential_data["grade"],
                    "university": "Tu Universidad"
                }
            }
        }
        
        # Firmar credencial
        vc_jwt = jwt.encode(vc_payload, PRIVATE_KEY, algorithm="ES256")
        
        # Limpiar datos pendientes
        await clear_pending_openid_credential(pre_auth_code)
        
        logger.info(f"✅ Credencial OpenID4VC emitida para: {credential_data['student_name']}")
        
        return {
            "credentials": [{"credential": vc_jwt}]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error emitiendo credencial OpenID4VC: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Funciones auxiliares (reutilizan tu lógica existente)
async def store_pending_openid_credential(code: str, data: Dict[str, Any]):
    """Almacenar datos pendientes - reutiliza tu sistema actual"""
    import tempfile
    temp_file = f"/tmp/pending_openid_credential_{code}.json"
    with open(temp_file, 'w') as f:
        json.dump(data, f)

async def get_pending_openid_credential(code: str) -> Optional[Dict[str, Any]]:
    """Obtener datos pendientes"""
    try:
        temp_file = f"/tmp/pending_openid_credential_{code}.json"
        with open(temp_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

async def clear_pending_openid_credential(code: str):
    """Limpiar datos pendientes"""
    try:
        import os
        temp_file = f"/tmp/pending_openid_credential_{code}.json"
        os.remove(temp_file)
    except:
        pass

# ==================== ENDPOINT PARA MOSTRAR QR OPENID4VC ====================

@oid4vc_router.get("/qr/{pre_auth_code}", response_class=HTMLResponse)
async def show_openid_qr_page(pre_auth_code: str):
    """
    Mostrar página HTML con QR Code OpenID4VC compatible con Lissi Wallet
    Similar a tu endpoint /qr/{connection_id} pero para OpenID4VC
    """
    try:
        # Buscar QR en storage temporal
        global qr_storage
        if 'qr_storage' not in globals():
            qr_storage = {}
            
        if pre_auth_code not in qr_storage:
            raise HTTPException(status_code=404, detail="QR Code OpenID4VC no encontrado o expirado")
        
        qr_data = qr_storage[pre_auth_code]
        
        # Página HTML específica para OpenID4VC
        html_content = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Credencial W3C OpenID4VC - Compatible con Lissi Wallet</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
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
                    box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                    text-align: center;
                    max-width: 500px;
                    width: 100%;
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
                .instructions {{
                    background: #fff3e0;
                    border-radius: 10px;
                    padding: 15px;
                    margin: 20px 0;
                    border-left: 4px solid #ff9800;
                }}
                .compatible {{
                    color: #4CAF50;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎓 Credencial Universitaria</h1>
                <div class="protocol-badge">OpenID4VC Compatible</div>
                
                <div class="course-info">
                    <div class="student-name">{qr_data.get('student_name', 'Estudiante')}</div>
                    <div>{qr_data.get('course_name', 'Curso')}</div>
                </div>
                
                <div class="qr-container">
                    <img src="data:image/png;base64,{qr_data['qr_code_base64']}" 
                         alt="QR Code OpenID4VC" class="qr-code">
                </div>
                
                <div class="instructions">
                    <h3>📱 Compatible con Lissi Wallet</h3>
                    <p><strong>Instrucciones:</strong></p>
                    <ol style="text-align: left;">
                        <li>Abre Lissi Wallet en tu móvil</li>
                        <li>Escanea este código QR</li>
                        <li>¡Recibe tu credencial W3C!</li>
                    </ol>
                </div>
            </div>
        </body>
        </html>
        """
        
        return HTMLResponse(content=html_content)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error mostrando QR OpenID4VC: {e}")
        raise HTTPException(status_code=500, detail=f"Error mostrando QR: {str(e)}")
