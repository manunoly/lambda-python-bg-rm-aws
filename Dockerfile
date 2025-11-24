# ==========================================
# ETAPA 1: BUILDER (Compilación y Limpieza)
# ==========================================
FROM public.ecr.aws/lambda/python:3.12 as builder

# 1. Instalar herramientas de compilación
# Necesarias para construir algunas dependencias de Python si no hay wheels disponibles
RUN dnf update -y && \
    dnf install -y gcc-c++ tar gzip && \
    dnf clean all

# 2. Copiar y preparar dependencias
COPY requirements.txt .

# 3. Instalar librerías en carpeta temporal /asset
# Usamos --no-cache-dir para mantener la imagen ligera
RUN pip install \
    --target /asset \
    --no-cache-dir \
    -r requirements.txt

# 4. LIMPIEZA PROFUNDA (Optimización de tamaño)
# Eliminamos tests, cachés y carpetas de documentación que no sirven en producción
RUN find /asset -type d -name "tests" -exec rm -rf {} + && \
    find /asset -type d -name "__pycache__" -exec rm -rf {} + && \
    find /asset -type d -name "doc" -exec rm -rf {} +

# ==========================================
# ETAPA 2: FINAL (Imagen de Producción)
# ==========================================
FROM public.ecr.aws/lambda/python:3.12

# 1. Instalar librerías del sistema para gráficos
# mesa-libGL es OBLIGATORIO para que OpenCV/Pillow funcionen dentro de rembg
RUN dnf install -y mesa-libGL shadow-utils && dnf clean all

# 2. Variables de Entorno Críticas
# U2NET_HOME: Obliga a rembg a buscar los modelos LOCALMENTE (en .u2net)
# NUMBA_CACHE_DIR: Redirige el caché a /tmp (único lugar escribible en Lambda)
# MODEL_NAME: Valor por defecto (se puede sobrescribir desde la consola AWS)
ENV U2NET_HOME=${LAMBDA_TASK_ROOT}/.u2net
ENV NUMBA_CACHE_DIR=/tmp
ENV MODEL_NAME=u2net

# 3. Copiar las librerías limpias desde la etapa Builder
COPY --from=builder /asset ${LAMBDA_TASK_ROOT}

# 4. PREPARAR MODELOS OFFLINE ("Bake-in")
# Creamos la carpeta oculta que usa rembg
RUN mkdir -p ${LAMBDA_TASK_ROOT}/.u2net

# Copiamos TODOS los archivos .onnx que tengas en tu carpeta local 'models/'
# Esto incluye u2net.onnx, u2netp.onnx e isnet-general-use.onnx
COPY models/ ${LAMBDA_TASK_ROOT}/.u2net/

# 5. Copiar el código de la función
COPY app.py ${LAMBDA_TASK_ROOT}

# 6. Definir el comando de arranque
CMD [ "app.lambda_handler" ]