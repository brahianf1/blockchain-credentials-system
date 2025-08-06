#!/bin/bash
# Script para configurar SSL en VPS con dominio de Hostinger

echo "🚀 Configurando SSL para OpenID4VC..."

# Variables - CAMBIA ESTOS VALORES
DOMAIN="tudominio.com"  # Cambia por tu dominio real
EMAIL="tu@email.com"    # Cambia por tu email

echo "📍 Dominio: $DOMAIN"
echo "📧 Email: $EMAIL"

# 1. Actualizar sistema
echo "📦 Actualizando sistema..."
sudo apt update && sudo apt upgrade -y

# 2. Instalar Nginx y Certbot
echo "🔧 Instalando Nginx y Certbot..."
sudo apt install nginx certbot python3-certbot-nginx -y

# 3. Configurar Nginx para el dominio
echo "⚙️ Configurando Nginx..."
sudo tee /etc/nginx/sites-available/openid4vc << EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN credentials.$DOMAIN;

    # Redirigir todo el tráfico HTTP a HTTPS (después del SSL)
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-Host \$host;
        proxy_set_header X-Forwarded-Port \$server_port;
        
        # Para WebSockets si es necesario
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

# 4. Habilitar sitio
echo "✅ Habilitando sitio..."
sudo ln -sf /etc/nginx/sites-available/openid4vc /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 5. Verificar configuración
echo "🔍 Verificando configuración de Nginx..."
sudo nginx -t

# 6. Reiniciar Nginx
echo "🔄 Reiniciando Nginx..."
sudo systemctl restart nginx
sudo systemctl enable nginx

# 7. Configurar firewall
echo "🔥 Configurando firewall..."
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw --force enable

echo ""
echo "⏳ Esperando propagación DNS..."
echo "   Verifica que $DOMAIN apunte a $(curl -s ifconfig.me)"
echo ""
echo "🔑 Para obtener SSL, ejecuta:"
echo "   sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN -d credentials.$DOMAIN --email $EMAIL --agree-tos --no-eff-email"
echo ""
echo "🎯 Después actualiza el código con tu dominio real."
