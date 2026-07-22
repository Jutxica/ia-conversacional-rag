FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json .
RUN npm ci

COPY . .

ARG VITE_SUPABASE_URL="https://tmblzshfpiltzxkdamdq.supabase.co"
ARG VITE_SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYmx6c2hmcGlsdHp4a2RhbWRxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzczMzI2ODIsImV4cCI6MjA5MjkwODY4Mn0.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InRtYmx6c2hmcGlsdHp4a2RhbWRxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzczMzI2ODIsImV4cCI6MjA5MjkwODY4Mn0"
ARG VITE_API_URL="https://api.147.15.29.242.sslip.io/api/chat"
ARG VITE_API_KEY="e94c9ba1ba74aee889b5c5fe3e0a6521"

ENV VITE_SUPABASE_URL=$VITE_SUPABASE_URL
ENV VITE_SUPABASE_ANON_KEY=$VITE_SUPABASE_ANON_KEY
ENV VITE_API_URL=$VITE_API_URL
ENV VITE_API_KEY=$VITE_API_KEY

RUN npm run build

FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
