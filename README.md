# AWS Lambda - Removedor de Fondos de Imagen (Python)

Este proyecto implementa una función **AWS Lambda** basada en contenedor (Docker) que elimina automáticamente el fondo de las imágenes subidas a un bucket de **Amazon S3**.

Utiliza la librería **rembg** (basada en el modelo U^2-Net) y está optimizada con una arquitectura "Zero-Latency" para evitar descargas en tiempo de ejecución.

## 📋 Características

* **Stack:** Python 3.12 + Docker.
* **IA:** `rembg` (U^2-Net) con `onnxruntime`.
* **Optimización:** Modelo "horneado" (baked-in) en la imagen Docker para eliminar el tiempo de descarga en arranques en frío (Cold Starts).
* **Desarrollo:** Configuración con `docker compose watch` para Hot Reload local.
* **Build:** Dockerfile Multi-stage para reducir el tamaño final de la imagen.

## 📂 Estructura del Proyecto

```text
.
├── app.py                 # Lógica de la Lambda (Handler)
├── Dockerfile             # Construcción Multi-stage optimizada
├── docker-compose.yaml    # Entorno local con Hot Reload
├── requirements.txt       # Dependencias (rembg[cpu], boto3, etc.)
├── event.json             # Evento de prueba simulado de S3
├── .env                   # Variables de entorno (NO subir al repo)
└── models/
    └── u2net.onnx         # Modelo de IA (Debe descargarse manualmente)
