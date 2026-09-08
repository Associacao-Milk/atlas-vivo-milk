FROM node:20-alpine

WORKDIR /app

# Dependências
COPY package.json package-lock.json* ./
RUN npm install --omit=dev

# Código
COPY src ./src

# Diretório de uploads
RUN mkdir -p /data/uploads
VOLUME ["/data/uploads"]

ENV NODE_ENV=production
EXPOSE 3000

CMD ["node", "src/server.js"]
