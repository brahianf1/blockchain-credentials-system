#!/bin/bash
# Pre-deployment checklist para OpenID4VC Walt.id compatibility

echo "🔍 PRE-DEPLOYMENT CHECKLIST - OpenID4VC Walt.id"
echo "=============================================="

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

SUCCESS=0
WARNINGS=0
ERRORS=0

check_file() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅${NC} $1"
        ((SUCCESS++))
    else
        echo -e "${RED}❌${NC} $1 - FALTANTE"
        ((ERRORS++))
    fi
}

check_command() {
    if command -v "$1" &> /dev/null; then
        echo -e "${GREEN}✅${NC} $1 disponible"
        ((SUCCESS++))
    else
        echo -e "${RED}❌${NC} $1 - NO ENCONTRADO"
        ((ERRORS++))
    fi
}

warn_if_missing() {
    if [ -f "$1" ]; then
        echo -e "${GREEN}✅${NC} $1"
        ((SUCCESS++))
    else
        echo -e "${YELLOW}⚠️${NC} $1 - OPCIONAL pero recomendado"
        ((WARNINGS++))
    fi
}

echo ""
echo "📁 Verificando archivos necesarios..."

# Archivos críticos
check_file "controller/openid4vc_endpoints.py"
check_file "controller/requirements.txt"
check_file "controller/app.py"
check_file "docker-compose.yml"
check_file "Dockerfile.controller"

echo ""
echo "🔧 Verificando archivos de deployment..."

# Scripts de deployment
check_file "deploy-openid4vc.sh"
check_file "verify-openid4vc.py"
warn_if_missing "test_openid4vc_compatibility.py"

echo ""
echo "⚙️ Verificando comandos requeridos..."

# Comandos necesarios
check_command "docker"
check_command "docker-compose"
check_command "curl"
check_command "jq"

echo ""
echo "🔍 Verificando contenido de archivos críticos..."

# Verificar que openid4vc_endpoints.py tiene las funciones walt.id
if grep -q "walt_token_endpoint" controller/openid4vc_endpoints.py; then
    echo -e "${GREEN}✅${NC} walt_token_endpoint presente en openid4vc_endpoints.py"
    ((SUCCESS++))
else
    echo -e "${RED}❌${NC} walt_token_endpoint NO ENCONTRADO en openid4vc_endpoints.py"
    ((ERRORS++))
fi

# Verificar endpoint universal
if grep -q "# MÉTODO 2: Query Parameters (walt.id" controller/openid4vc_endpoints.py; then
    echo -e "${GREEN}✅${NC} Compatibilidad walt.id en endpoint universal"
    ((SUCCESS++))
else
    echo -e "${YELLOW}⚠️${NC} Endpoint universal puede no tener compatibilidad walt.id"
    ((WARNINGS++))
fi

# Verificar imports de FastAPI Query
if grep -q "from fastapi import.*Query" controller/openid4vc_endpoints.py; then
    echo -e "${GREEN}✅${NC} Import de Query presente para walt.id endpoint"
    ((SUCCESS++))
else
    echo -e "${RED}❌${NC} Import de Query FALTANTE - walt.id endpoint fallará"
    ((ERRORS++))
fi

echo ""
echo "🐳 Verificando configuración Docker..."

# Verificar docker-compose
if grep -q "python-controller" docker-compose.yml; then
    echo -e "${GREEN}✅${NC} Servicio python-controller en docker-compose.yml"
    ((SUCCESS++))
else
    echo -e "${RED}❌${NC} Servicio python-controller NO ENCONTRADO"
    ((ERRORS++))
fi

# Verificar puerto 3000
if grep -q "3000:3000" docker-compose.yml; then
    echo -e "${GREEN}✅${NC} Puerto 3000 mapeado correctamente"
    ((SUCCESS++))
else
    echo -e "${YELLOW}⚠️${NC} Puerto 3000 puede no estar mapeado correctamente"
    ((WARNINGS++))
fi

echo ""
echo "🌐 Verificando configuración de red..."

# Verificar que estamos usando HTTPS en producción
if grep -q "https://utnpf.site" controller/openid4vc_endpoints.py; then
    echo -e "${GREEN}✅${NC} URL HTTPS configurada para producción"
    ((SUCCESS++))
else
    echo -e "${YELLOW}⚠️${NC} Verificar URL de producción en openid4vc_endpoints.py"
    ((WARNINGS++))
fi

echo ""
echo "📋 RESUMEN PRE-DEPLOYMENT"
echo "========================"
echo -e "${GREEN}✅ Éxitos: $SUCCESS${NC}"
echo -e "${YELLOW}⚠️  Warnings: $WARNINGS${NC}"
echo -e "${RED}❌ Errores: $ERRORS${NC}"

echo ""
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}🎉 ¡LISTO PARA DEPLOYMENT!${NC}"
    echo ""
    echo "📝 Próximos pasos:"
    echo "1. Subir código a VPS (git push o scp)"
    echo "2. En VPS: cd backend-app && ./deploy-openid4vc.sh"
    echo "3. Verificar: python3 verify-openid4vc.py"
    echo "4. Probar con wallet.demo.walt.id"
    echo ""
    exit 0
else
    echo -e "${RED}🚫 HAY ERRORES QUE DEBEN CORREGIRSE ANTES DEL DEPLOYMENT${NC}"
    echo ""
    echo "🔧 Errores encontrados:"
    echo "- Archivos faltantes o configuración incorrecta"
    echo "- Revisar la lista de ❌ arriba"
    echo ""
    exit 1
fi
