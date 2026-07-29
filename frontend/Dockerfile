FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Variáveis de compilação do Vite (suporta tanto chaves diretas quanto valores alternativos)
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_KEY
ARG VITE_SUPABASE_ANON_VAL
ARG VITE_API_URL
ARG VITE_API_KEY
ARG VITE_API_VAL

# Resolve as variáveis usando fallback e escreve diretamente no arquivo .env
RUN SUPABASE_ANON="${VITE_SUPABASE_ANON_VAL:-$VITE_SUPABASE_ANON_KEY}" && \
    API_KEY="${VITE_API_VAL:-$VITE_API_KEY}" && \
    echo "VITE_SUPABASE_URL=$VITE_SUPABASE_URL" > .env && \
    echo "VITE_SUPABASE_ANON_KEY=$SUPABASE_ANON" >> .env && \
    echo "VITE_API_URL=$VITE_API_URL" >> .env && \
    echo "VITE_API_KEY=$API_KEY" >> .env

RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

