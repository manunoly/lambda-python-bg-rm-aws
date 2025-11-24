import boto3
import io
import os
from rembg import new_session, remove
from PIL import Image

s3 = boto3.client('s3')

# ------------------------------------------------------------------
# CONFIGURACIÓN E INICIALIZACIÓN GLOBAL (WARM START)
# ------------------------------------------------------------------
# 1. Leemos la variable de entorno configurada en AWS Lambda.
#    Si no existe, usa 'u2net' por defecto.
MODEL_NAME = os.environ.get('MODEL_NAME', 'u2net')

print(f"⚙️ Configuración detectada: Modelo '{MODEL_NAME}'")
print("⏳ Cargando modelo en memoria RAM...")

# 2. Creamos la sesión UNA SOLA VEZ al iniciar el contenedor.
#    Esto ocurre durante el "Cold Start". Las ejecuciones siguientes son instantáneas.
try:
    session = new_session(MODEL_NAME)
    print("✅ Modelo cargado exitosamente.")
except Exception as e:
    print(f"❌ Error fatal cargando el modelo {MODEL_NAME}: {e}")
    # Si falla la carga del modelo, rompemos la ejecución inicial para que salga en los logs
    raise e

def lambda_handler(event, context):
    try:
        # 1. Obtener datos de S3
        record = event['Records'][0]
        bucket_name = record['s3']['bucket']['name']
        key = record['s3']['object']['key']

        # Evitar bucles infinitos (si el trigger está mal configurado)
        if "-no-bg.png" in key:
            print("Archivo ya procesado. Omitiendo.")
            return {"statusCode": 200, "body": "Skipped"}

        print(f"🚀 Procesando: {key} con modelo '{MODEL_NAME}'")
        
        # 2. Descargar imagen
        response = s3.get_object(Bucket=bucket_name, Key=key)
        image_data = response['Body'].read()
        
        # 3. Procesar Imagen
        # Convertimos bytes a objeto PIL
        input_image = Image.open(io.BytesIO(image_data))
        
        # EL PASO MÁGICO: Usamos la 'session' global ya cargada
        output_image = remove(input_image, session=session)
        
        # 4. Guardar resultado en buffer
        out_img_bytes = io.BytesIO()
        output_image.save(out_img_bytes, format='PNG')
        out_img_bytes.seek(0)
        
        # 5. Subir a S3
        # Agregamos el nombre del modelo al archivo para saber con cuál se hizo
        # Ej: foto-u2net-no-bg.png
        new_key = os.path.splitext(key)[0] + f"-{MODEL_NAME}-no-bg.png"
        
        s3.put_object(
            Bucket=bucket_name,
            Key=new_key,
            Body=out_img_bytes,
            ContentType='image/png'
        )
        
        print(f"💾 Guardado en: {new_key}")
        return {"statusCode": 200, "body": f"Success with {MODEL_NAME}"}

    except Exception as e:
        print(f"🔥 Error procesando imagen: {str(e)}")
        # Importante: Lanzar el error permite que AWS marque la ejecución como fallida
        raise e