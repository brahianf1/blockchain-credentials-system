#!/bin/bash

# ==================== SCRIPT DE CORRECCIÓN NGINX SSL ====================
# Corrige los errores específicos detectados en la configuración SSL

echo "🔧 Aplicando corrección a configuración Nginx SSL..."

# Variables
NGINX_CONFIG="/etc/nginx/sites-available/openid4vc"

# Backup de la configuración actual
if [ -f "$NGINX_CONFIG" ]; then
    sudo cp "$NGINX_CONFIG" "$NGINX_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
    echo "✅ Backup creado: $NGINX_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Crear configuración corregida
echo "📝 Creando configuración Nginx corregida..."

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
EOF

# Añadir configuración global al archivo principal de Nginx
echo "🔧 Configurando directivas globales de Nginx..."

# Verificar si server_tokens ya existe en nginx.conf
if ! grep -q "server_tokens off" /etc/nginx/nginx.conf; then
    # Añadir server_tokens al bloque http
    sudo sed -i '/http {/a\\tserver_tokens off;' /etc/nginx/nginx.conf
    echo "✅ server_tokens añadido a nginx.conf"
else
    echo "✅ server_tokens ya configurado en nginx.conf"
fi

# Verificar configuración
echo "🔍 Verificando configuración corregida..."
if sudo nginx -t; then
    echo "✅ ¡Configuración Nginx corregida exitosamente!"
    
    # Recargar Nginx
    echo "🔄 Recargando Nginx..."
    sudo systemctl reload nginx
    echo "✅ Nginx recargado"
    
    # Verificar que SSL funciona
    echo "🌐 Verificando SSL..."
    if curl -s -I https://utnpf.site/ | grep -q "HTTP/"; then
        echo "✅ ¡HTTPS funcionando correctamente!"
    else
        echo "⚠️  HTTPS no responde aún - puede tardar unos segundos"
    fi
    
else
    echo "❌ Error en configuración - revisar logs:"
    sudo nginx -t
    exit 1
fi

echo ""
echo "🎉 ¡Configuración SSL corregida y aplicada!"
echo ""
echo "🔗 URLs de prueba:"
echo "   • HTTPS: https://utnpf.site/"
echo "   • OpenID4VC: https://utnpf.site/oid4vc/.well-known/openid-credential-issuer"
echo "   • SSL Test: https://utnpf.site/oid4vc/ssl-test"
echo ""
echo "📝 Próximo paso: Probar con Lissi Wallet"
