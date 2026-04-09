FROM node:20-alpine AS frontend-build

WORKDIR /workspace/apps/service-frontend

COPY apps/service-frontend/package.json apps/service-frontend/package-lock.json ./
RUN npm ci

COPY apps/service-frontend/ ./

ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ARG VITE_HUB_LOGIN_URL=
ENV VITE_HUB_LOGIN_URL=$VITE_HUB_LOGIN_URL
ARG VITE_HUB_API_BASE_URL=
ENV VITE_HUB_API_BASE_URL=$VITE_HUB_API_BASE_URL

RUN npm run build

FROM nginx:1.29-alpine

COPY infra/nginx/nginx.conf /etc/nginx/nginx.conf
COPY infra/nginx/templates/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=frontend-build /workspace/apps/service-frontend/dist /usr/share/nginx/html

EXPOSE 80 443
