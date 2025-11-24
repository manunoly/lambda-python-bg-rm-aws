import boto3
import io
import os
from rembg import new_session, remove
from PIL import Image

s3 = boto3.client('s3')

# OPTIMIZACIÓN GLOBAL:
# Inicializamos la sesión fuera del handler.
# Esto carga el modelo en RAM una sola vez durante el arranque (Cold Start)
# y lo reutiliza en ejecuciones subsiguientes (Warm Start).
model_name = "u2net"
session = new_session(model_name)

def lambda_handler(event, context):
    print("Iniciando procesamiento de imagen...")
    
    try:
        # 1. Parsear el evento de S3
        record = event['Records'][0]
        bucket_name = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        
        # Seguridad: Evitar bucles infinitos si el trigger está mal configurado
        if "-no-bg.png" in key:
            return {"statusCode": 200, "body": "Archivo ya procesado."}

        print(f"Descargando: {key} desde {bucket_name}")
        
        # 2. Descargar imagen desde S3 a memoria
        response = s3.get_object(Bucket=bucket_name, Key=key)
        image_content = response['Body'].read()
        
        # 3. Procesar imagen (Eliminar fondo)
        input_image = Image.open(io.BytesIO(image_content))
        
        # Usamos la sesión pre-cargada para máxima velocidad
        output_image = remove(input_image, session=session)
        
        # 4. Guardar resultado en buffer
        out_img_bytes = io.BytesIO()
        output_image.save(out_img_bytes, format='PNG')
        out_img_bytes.seek(0)
        
        # 5. Subir imagen procesada a S3
        # Agregamos sufijo para diferenciar
        new_key = os.path.splitext(key)[0] + "-no-bg.png"
        
        s3.put_object(
            Bucket=bucket_name,
            Key=new_key,
            Body=out_img_bytes,
            ContentType='image/png'
        )
        
        print(f"Éxito. Guardado en: {new_key}")
        return {"statusCode": 200, "body": "Fondo eliminado correctamente"}

    except Exception as e:
        print(f"Error crítico: {str(e)}")
        # Lanzar error para que Lambda pueda reintentar si es necesario
        raise e