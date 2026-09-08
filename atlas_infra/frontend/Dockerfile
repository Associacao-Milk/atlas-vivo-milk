FROM nginx:1.27-alpine

# Frontend estático servido por nginx interno (proxy do nginx principal)
COPY . /usr/share/nginx/html

RUN cat > /etc/nginx/conf.d/default.conf <<'EOF'
server {
  listen 80 default_server;
  root /usr/share/nginx/html;
  index index.html;
  location / { try_files $uri $uri/ /index.html; }
}
EOF

EXPOSE 80
