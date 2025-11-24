# --------------------------------------------------
# ETAPA 1: BUILDER (Descarga y Compilación)
# --------------------------------------------------
FROM public.ecr.aws/lambda/python:3.12 as builder

# Instalamos herramientas de sistema necesarias para compilar dependencias
RUN dnf update -y && \
    dnf install -y gcc-c++ tar gzip && \
    dnf clean all

COPY requirements.txt .

# Instalamos dependencias en carpeta temporal /asset
RUN pip install \
    --target /asset \
    --no-cache-dir \
    rembg[cpu] pillow boto3 onnxruntime

# Limpieza profunda de archivos basura (__pycache__, tests)
RUN find /asset -type d -name "tests" -exec rm -rf {} + && \
    find /asset -type d -name "__pycache__" -exec rm -rf {} +

# --------------------------------------------------
# ETAPA 2: FINAL (Producción)
# --------------------------------------------------
FROM public.ecr.aws/lambda/python:3.12

# Instalar librería gráfica GL (necesaria para OpenCV/Pillow interno de rembg)
RUN dnf install -y mesa-libGL shadow-utils && dnf clean all

# Variables de Entorno Críticas
# U2NET_HOME: Obliga a rembg a usar el modelo local
# NUMBA_CACHE_DIR: Evita errores de permisos de escritura
ENV U2NET_HOME=${LAMBDA_TASK_ROOT}/.u2net
ENV NUMBA_CACHE_DIR=/tmp

# 1. Copiar librerías de Python desde el builder
COPY --from=builder /asset ${LAMBDA_TASK_ROOT}

# 2. Copiar el modelo descargado ("Bake-in")
RUN mkdir -p ${LAMBDA_TASK_ROOT}/.u2net
COPY models/u2net.onnx ${LAMBDA_TASK_ROOT}/.u2net/u2net.onnx

# 3. Copiar el código de la función
COPY app.py ${LAMBDA_TASK_ROOT}

CMD [ "app.lambda_handler" ]