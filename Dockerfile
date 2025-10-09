# Dockerfile
FROM node:18-alpine as frontend-build
WORKDIR /Company/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

FROM python:3.11-slim
WORKDIR /Company
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
COPY --from=frontend-build /Company/frontend/build ./frontend/build
EXPOSE 5000
CMD ["python", "run.py"]
