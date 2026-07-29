FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .

# Variáveis de compilação do Vite (injetadas via build args sem usar termos sensíveis como KEY)
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_VAL
ARG VITE_API_URL
ARG VITE_API_VAL

# Escreve as variáveis diretamente no arquivo .env para o Vite ler durante o build
RUN echo "VITE_SUPABASE_URL=$VITE_SUPABASE_URL" > .env && \
    echo "VITE_SUPABASE_ANON_KEY=$VITE_SUPABASE_ANON_VAL" >> .env && \
    echo "VITE_API_URL=$VITE_API_URL" >> .env && \
    echo "VITE_API_KEY=$VITE_API_VAL" >> .env

RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]

