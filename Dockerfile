FROM node:20-alpine AS frontend-build
WORKDIR /ui
RUN corepack enable && corepack prepare pnpm@11.25.0 --activate
COPY frontend/package.json frontend/pnpm-lock.yaml frontend/pnpm-workspace.yaml ./
RUN pnpm install --frozen-lockfile
COPY frontend ./
RUN pnpm run build

FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY --from=frontend-build /ui/dist ./frontend/dist
ENV STATIC_DIR=/app/frontend/dist PORT=8000
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]

