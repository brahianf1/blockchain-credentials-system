#!/bin/bash
# Script de inicio para el Sistema de Credenciales W3C
# Universidad - Integración Moodle + ACA-Py + Hyperledger Fabric

set -e

echo "🚀 Iniciando Sistema de Credenciales W3C Verificables..."
echo "=========================================="

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para logging
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar prerequisitos
check_prerequisites() {
    log_info "Verificando prerequisitos..."
    
    # Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker no está instalado"
        exit 1
    fi
    
    # Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose no está instalado"
        exit 1
    fi
    
    # Verificar que Fabric esté ejecutándose
    if ! docker network ls | grep -q fabric_test; then
        log_warning "Red de Fabric 'fabric_test' no encontrada"
        log_info "Asegúrate de que Hyperledger Fabric esté ejecutándose"
        log_info "Desde fabric-samples/test-network ejecuta: ./network.sh up createChannel -ca"
    fi
    
    # Verificar que Moodle esté ejecutándose
    if ! docker network ls | grep -q moodle-project_moodle-network; then
        log_warning "Red de Moodle no encontrada"
        log_info "Asegúrate de que Moodle esté ejecutándose"
        log_info "Desde moodle-project ejecuta: docker-compose up -d"
    fi
    
    log_success "Prerequisitos verificados"
}

# Preparar configuraciones
prepare_configs() {
    log_info "Preparando configuraciones..."
    
    # Verificar crypto-config
    if [ ! -d "./crypto-config" ]; then
        log_error "Directorio crypto-config no encontrado"
        log_info "Copia los archivos de crypto-config desde fabric-samples/test-network/organizations/"
        exit 1
    fi
    
    # Verificar archivos de certificados
    if [ ! -f "./crypto-config/connection-org1.json" ]; then
        log_error "Archivo de conexión connection-org1.json no encontrado"
        exit 1
    fi
    
    log_success "Configuraciones preparadas"
}

# Construir imágenes Docker
build_images() {
    log_info "Construyendo imágenes Docker..."
    
    # Construir Controller Python
    log_info "Construyendo Controller Python..."
    docker build -f Dockerfile.controller -t universidad-controller:latest .
    
    # Construir ACA-Py personalizado
    log_info "Construyendo ACA-Py personalizado..."
    docker build -f acapy/Dockerfile.acapy -t universidad-acapy:latest ./acapy/
    
    log_success "Imágenes construidas exitosamente"
}

# Iniciar servicios
start_services() {
    log_info "Iniciando servicios..."
    
    # Detener servicios existentes si existen
    docker-compose down 2>/dev/null || true
    
    # Limpiar volúmenes huérfanos
    docker volume prune -f
    
    # Iniciar servicios
    log_info "Levantando contenedores..."
    docker-compose up -d
    
    # Esperar a que servicios estén listos
    log_info "Esperando que servicios estén listos..."
    sleep 10
    
    # Verificar salud de ACA-Py
    for i in {1..30}; do
        if curl -f http://localhost:8020/status/live &>/dev/null; then
            log_success "ACA-Py está saludable"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "ACA-Py no responde después de 30 intentos"
            docker-compose logs acapy-agent
            exit 1
        fi
        sleep 2
    done
    
    # Verificar Controller Python
    for i in {1..30}; do
        if curl -f http://localhost:3000/health &>/dev/null; then
            log_success "Controller Python está saludable"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "Controller Python no responde después de 30 intentos"
            docker-compose logs python-controller
            exit 1
        fi
        sleep 2
    done
    
    log_success "Todos los servicios están ejecutándose"
}

# Mostrar información de estado
show_status() {
    echo ""
    echo "============================================"
    echo "🎓 SISTEMA DE CREDENCIALES W3C INICIADO"
    echo "============================================"
    echo ""
    echo "📊 ESTADO DE SERVICIOS:"
    echo "  • ACA-Py Agent:     http://localhost:8020 (Admin API)"
    echo "  • ACA-Py Public:    http://localhost:8021 (Public DIDComm)"
    echo "  • Controller API:   http://localhost:3000"
    echo ""
    echo "🔗 ENDPOINTS PRINCIPALES:"
    echo "  • Health Check:     GET  http://localhost:3000/health"  
    echo "  • Solicitar Credencial: POST http://localhost:3000/api/credential/request"
    echo "  • Endpoint Moodle:  POST http://localhost:3000/api/credenciales"
    echo ""
    echo "📱 PARA PROBAR CON WALLET:"
    echo "  1. Instala un wallet compatible (Aries Mobile Agent, etc.)"
    echo "  2. Solicita credencial vía API"
    echo "  3. Escanea código QR generado"
    echo "  4. Acepta credencial en tu wallet"
    echo ""
    echo "📋 LOGS EN TIEMPO REAL:"
    echo "  • docker-compose logs -f acapy-agent"
    echo "  • docker-compose logs -f python-controller"
    echo ""
    echo "🛑 DETENER SISTEMA:"
    echo "  • docker-compose down"
    echo ""
}

# Función para mostrar logs
show_logs() {
    log_info "Mostrando logs en tiempo real..."
    log_info "Presiona Ctrl+C para salir"
    docker-compose logs -f
}

# Función para detener servicios
stop_services() {
    log_info "Deteniendo servicios..."
    docker-compose down
    log_success "Servicios detenidos"
}

# Función de ayuda
show_help() {
    echo "Sistema de Credenciales W3C - Universidad"
    echo ""
    echo "Uso: $0 [COMANDO]"
    echo ""
    echo "COMANDOS:"
    echo "  start     Iniciar todos los servicios (por defecto)"
    echo "  stop      Detener todos los servicios"
    echo "  restart   Reiniciar todos los servicios"
    echo "  logs      Mostrar logs en tiempo real"
    echo "  status    Mostrar estado actual"
    echo "  build     Solo construir imágenes Docker"
    echo "  help      Mostrar esta ayuda"
    echo ""
}

# Función para reiniciar
restart_services() {
    stop_services
    sleep 2
    start_services
    show_status
}

# Función para mostrar estado actual
check_status() {
    log_info "Verificando estado de servicios..."
    
    echo ""
    echo "🐳 CONTENEDORES:"
    docker-compose ps
    
    echo ""
    echo "🌐 CONECTIVIDAD:"
    if curl -f http://localhost:8020/status/live &>/dev/null; then
        log_success "ACA-Py Admin API: ✅ Disponible"
    else
        log_error "ACA-Py Admin API: ❌ No disponible"
    fi
    
    if curl -f http://localhost:3000/health &>/dev/null; then
        log_success "Controller API: ✅ Disponible"
    else
        log_error "Controller API: ❌ No disponible"
    fi
    
    echo ""
    echo "📊 REDES DOCKER:"
    docker network ls | grep -E "(fabric_test|moodle|acapy)" || log_warning "Algunas redes pueden no estar disponibles"
}

# Procesamiento de argumentos
case "${1:-start}" in
    "start")
        check_prerequisites
        prepare_configs
        build_images
        start_services
        show_status
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        restart_services
        ;;
    "logs")
        show_logs
        ;;
    "status")
        check_status
        ;;
    "build")
        build_images
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        log_error "Comando desconocido: $1"
        show_help
        exit 1
        ;;
esac