# Configuración SSL para OpenID4VC

## Opción A: Nginx con Let's Encrypt (Recomendada)

### 1. Instalar Nginx y Certbot
```bash
# En el VPS
sudo apt update
sudo apt install nginx certbot python3-certbot-nginx -y
```

### 2. Configurar dominio (necesario para SSL)
- Apuntar un dominio/subdominio a 209.38.151.153
- Ejemplo: credentials.tudominio.com

### 3. Configurar Nginx
```nginx
# /etc/nginx/sites-available/openid4vc
server {
    listen 80;
    server_name credentials.tudominio.com;
    
    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 4. Obtener certificado SSL
```bash
sudo certbot --nginx -d credentials.tudominio.com
```

## Opción B: Traefik con Docker (Alternativa)

### docker-compose.ssl.yml
```yaml
version: '3.8'
services:
  traefik:
    image: traefik:v2.10
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./traefik.yml:/traefik.yml
      - ./acme.json:/acme.json
    
  python-controller:
    # ... configuración existente
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`credentials.tudominio.com`)"
      - "traefik.http.routers.api.tls.certresolver=letsencrypt"
```
