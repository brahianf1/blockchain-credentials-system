#!/bin/bash

# ==================== SCRIPT DE CONFIGURACIÓN SSL AUTOMÁTICA ====================
# Configuración SSL/TLS para OpenID4VC compatible con Lissi Wallet
# Dominio: utnpf.site
# VPS: 209.38.151.153

set -e

echo "🔒 Iniciando configuración SSL para OpenID4VC compatible con Lissi Wallet..."

# ==================== VARIABLES DE CONFIGURACIÓN ====================
DOMAIN="utnpf.site"
EMAIL="admin@utnpf.site"  # Cambiar por email real
NGINX_CONFIG="/etc/nginx/sites-available/openid4vc"
NGINX_ENABLED="/etc/nginx/sites-enabled/openid4vc"

# ==================== VERIFICACIONES PREVIAS ====================
echo "📋 Verificando requisitos previos..."

# Verificar que estamos en el VPS correcto
PUBLIC_IP=$(curl -s ifconfig.me || curl -s ipinfo.io/ip)
echo "🌐 IP Pública detectada: $PUBLIC_IP"

if [ "$PUBLIC_IP" != "209.38.151.153" ]; then
    echo "⚠️  ADVERTENCIA: Este script está configurado para IP 209.38.151.153"
    echo "   IP actual: $PUBLIC_IP"
    read -p "¿Continuar de todos modos? (y/N): " confirm
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        exit 1
    fi
fi

# Verificar resolución DNS
echo "🔍 Verificando resolución DNS para $DOMAIN..."
RESOLVED_IP=$(dig +short $DOMAIN)
if [ "$RESOLVED_IP" != "$PUBLIC_IP" ]; then
    echo "❌ ERROR: $DOMAIN no resuelve a $PUBLIC_IP"
    echo "   Resuelve a: $RESOLVED_IP"
    echo "   Configura el DNS antes de continuar"
    exit 1
fi

echo "✅ DNS configurado correctamente"

# ==================== INSTALACIÓN DE DEPENDENCIAS ====================
echo "📦 Instalando dependencias..."

# Actualizar sistema
sudo apt update

# Instalar Nginx si no está instalado
if ! command -v nginx &> /dev/null; then
    echo "🔧 Instalando Nginx..."
    sudo apt install nginx -y
    sudo systemctl enable nginx
else
    echo "✅ Nginx ya está instalado"
fi

# Instalar Certbot si no está instalado
if ! command -v certbot &> /dev/null; then
    echo "🔧 Instalando Certbot..."
    sudo apt install certbot python3-certbot-nginx -y
else
    echo "✅ Certbot ya está instalado"
fi

# ==================== GENERAR DHPARAM ====================
echo "🔐 Generando parámetros DH para Perfect Forward Secrecy..."
if [ ! -f /etc/ssl/certs/dhparam.pem ]; then
    sudo openssl dhparam -out /etc/ssl/certs/dhparam.pem 2048
    echo "✅ Parámetros DH generados"
else
    echo "✅ Parámetros DH ya existen"
fi

# ==================== CONFIGURACIÓN INICIAL NGINX ====================
echo "⚙️  Configurando Nginx (configuración temporal para certificado)..."

# Crear configuración temporal para obtener certificado
sudo tee $NGINX_CONFIG > /dev/null << EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Permitir Let's Encrypt
    location /.well-known/acme-challenge/ {
        root /var/www/html;
    }
}
EOF

# Habilitar sitio
sudo ln -sf $NGINX_CONFIG $NGINX_ENABLED

# Remover configuración por defecto si existe
sudo rm -f /etc/nginx/sites-enabled/default

# Verificar configuración
echo "🔍 Verificando configuración de Nginx..."
if sudo nginx -t; then
    echo "✅ Configuración de Nginx válida"
    sudo systemctl reload nginx
else
    echo "❌ Error en configuración de Nginx"
    exit 1
fi

# ==================== OBTENER CERTIFICADO SSL ====================
echo "🔒 Obteniendo certificado SSL de Let's Encrypt..."

# Verificar que el servidor está respondiendo
echo "🌐 Verificando que el servidor responde en puerto 80..."
if curl -s -o /dev/null -w "%{http_code}" http://$DOMAIN/ | grep -q "200\|404\|500"; then
    echo "✅ Servidor responde correctamente"
else
    echo "❌ Servidor no responde. Verifica que Docker esté ejecutándose"
    echo "   Ejecuta: docker-compose up -d"
    exit 1
fi

# Obtener certificado
if [ ! -d "/etc/letsencrypt/live/$DOMAIN" ]; then
    echo "📜 Obteniendo certificado SSL..."
    sudo certbot certonly --nginx \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        -d $DOMAIN
    
    if [ $? -eq 0 ]; then
        echo "✅ Certificado SSL obtenido exitosamente"
    else
        echo "❌ Error obteniendo certificado SSL"
        exit 1
    fi
else
    echo "✅ Certificado SSL ya existe"
fi

# ==================== CONFIGURACIÓN NGINX FINAL ====================
echo "🔧 Aplicando configuración final de Nginx optimizada para Lissi Wallet..."

# Crear configuración completa con SSL
sudo tee $NGINX_CONFIG > /dev/null << 'EOF'
# Redirección HTTP a HTTPS
server {
    listen 80;
    server_name utnpf.site;
    return 301 https://$server_name$request_uri;
}

# Configuración HTTPS principal
server {
    listen 443 ssl;
    http2 on;
    server_name utnpf.site;
    
    # Certificados SSL
    ssl_certificate /etc/letsencrypt/live/utnpf.site/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/utnpf.site/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/utnpf.site/chain.pem;
    
    # Configuración TLS para Android/Lissi Wallet
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers 'ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256';
    ssl_prefer_server_ciphers on;
    ssl_dhparam /etc/ssl/certs/dhparam.pem;
    
    # Optimizaciones SSL
    ssl_session_timeout 10m;
    ssl_session_cache shared:SSL:10m;
    ssl_session_tickets off;
    
    # OCSP Stapling (importante para Android)
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;
    
    # Headers de seguridad
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # Configuración proxy principal
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $server_name;
        
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Proxy para ACA-Py
    location /acapy/ {
        proxy_pass http://localhost:8021/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # OpenID4VC endpoints con CORS
    location /oid4vc/ {
        proxy_pass http://localhost:3000/oid4vc/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        add_header Access-Control-Allow-Origin "*" always;
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
        add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
        
        if ($request_method = 'OPTIONS') {
            add_header Access-Control-Allow-Origin "*" always;
            add_header Access-Control-Allow-Methods "GET, POST, OPTIONS" always;
            add_header Access-Control-Allow-Headers "Content-Type, Authorization" always;
            add_header Content-Length 0;
            return 204;
        }
    }
    
    # Well-known endpoints
    location /.well-known/ {
        proxy_pass http://localhost:3000/oid4vc/.well-known/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Logs
    access_log /var/log/nginx/utnpf.site.access.log;
    error_log /var/log/nginx/utnpf.site.error.log;
    
    # Tamaño máximo de upload
    client_max_body_size 10M;
}

# Configuración global Nginx
server_tokens off;
EOF

# Verificar nueva configuración
echo "🔍 Verificando nueva configuración SSL..."
if sudo nginx -t; then
    echo "✅ Configuración SSL válida"
    sudo systemctl reload nginx
else
    echo "❌ Error en configuración SSL"
    exit 1
fi

# ==================== CONFIGURAR RENOVACIÓN AUTOMÁTICA ====================
echo "⏰ Configurando renovación automática de certificados..."

# Crear hook para recargar nginx después de renovar
sudo mkdir -p /etc/letsencrypt/renewal-hooks/deploy
sudo tee /etc/letsencrypt/renewal-hooks/deploy/nginx-reload.sh > /dev/null << 'EOF'
#!/bin/bash
systemctl reload nginx
EOF

sudo chmod +x /etc/letsencrypt/renewal-hooks/deploy/nginx-reload.sh

# Probar renovación
echo "🔄 Probando renovación de certificados..."
sudo certbot renew --dry-run

if [ $? -eq 0 ]; then
    echo "✅ Renovación automática configurada correctamente"
else
    echo "⚠️  Advertencia: Problema con renovación automática"
fi

# ==================== VERIFICACIONES FINALES ====================
echo "🔍 Ejecutando verificaciones finales..."

# Verificar que SSL funciona
echo "🌐 Verificando SSL..."
if curl -s -I https://$DOMAIN/ | grep -q "HTTP/"; then
    echo "✅ HTTPS funcionando correctamente"
else
    echo "❌ Error: HTTPS no responde"
    exit 1
fi

# Verificar endpoints OpenID4VC
echo "🔍 Verificando endpoints OpenID4VC..."
if curl -s https://$DOMAIN/oid4vc/.well-known/openid-credential-issuer | grep -q "issuer"; then
    echo "✅ Endpoint OpenID4VC funcionando"
else
    echo "⚠️  Advertencia: Endpoint OpenID4VC no responde (normal si el contenedor no está ejecutándose)"
fi

# Verificar certificado SSL
echo "🔒 Verificando certificado SSL..."
SSL_EXPIRY=$(echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | openssl x509 -noout -dates | grep notAfter | cut -d= -f2)
echo "📅 Certificado expira: $SSL_EXPIRY"

# Verificar configuración para Android
echo "📱 Verificando compatibilidad con Android..."
if echo | openssl s_client -servername $DOMAIN -connect $DOMAIN:443 2>/dev/null | grep -q "TLSv1.2\|TLSv1.3"; then
    echo "✅ TLS 1.2/1.3 habilitado (compatible con Android)"
else
    echo "⚠️  Advertencia: Verificar configuración TLS"
fi

# ==================== RESUMEN FINAL ====================
echo ""
echo "🎉 ¡Configuración SSL completada exitosamente!"
echo ""
echo "📋 RESUMEN:"
echo "   🌐 Dominio: $DOMAIN"
echo "   🔒 SSL: Let's Encrypt (renovación automática)"
echo "   📱 Compatible: Android/Lissi Wallet"
echo "   🔧 Nginx: Configurado con optimizaciones SSL"
echo ""
echo "🔗 URLs de prueba:"
echo "   • Página principal: https://$DOMAIN/"
echo "   • Metadata OpenID4VC: https://$DOMAIN/oid4vc/.well-known/openid-credential-issuer"
echo "   • Test SSL: https://$DOMAIN/oid4vc/ssl-test"
echo "   • Health Check: https://$DOMAIN/oid4vc/health"
echo ""
echo "📝 PRÓXIMOS PASOS:"
echo "   1. Ejecutar: docker-compose up -d"
echo "   2. Probar con Lissi Wallet escaneando QR"
echo "   3. Verificar logs: sudo tail -f /var/log/nginx/utnpf.site.error.log"
echo ""
echo "✅ ¡Sistema listo para uso en producción!"
