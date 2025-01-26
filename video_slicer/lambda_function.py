import boto3
import cv2
import zipfile
import os
import json

sqs = boto3.client('sqs')
s3 = boto3.client('s3')

TO_PROCESS_QUEUE_URL = os.getenv('TO_PROCESS_QUEUE_URL')
STATUS_QUEUE_URL = os.getenv('STATUS_QUEUE_URL')
BUCKET_NAME = os.getenv('LAMBDA_BUCKET_NAME')

def lambda_handler(event, context):
    if 'Records' not in event or not event['Records']:
        return respond(400, "Payload inválido.")

    message = event['Records'][0]
    body = json.loads(message['body'])
    video_name = body['videoName']
    receipt_handle = message['receiptHandle']

    print(f"Processando vídeo: {video_name}")

    update_status(video_name, "PROCESSANDO")

    source_s3_key = f"videos/{video_name}.zip"
    print(f"Chave do arquivo fonte no S3: {source_s3_key}")
    output_s3_key = f"zip/{video_name}_thumbnails.zip"
    print(f"Chave do arquivo de saída no S3: {output_s3_key}")
    download_path = "/tmp/video.zip"
    print(f"Caminho do arquivo baixado: {download_path}")
    output_zip = "/tmp/thumbnails.zip"
    print(f"Caminho do arquivo de saída: {output_zip}")


    try:
        if not check_file_exists_in_s3(BUCKET_NAME, source_s3_key):
            print(f"Arquivo não encontrado no S3: {source_s3_key}")
            raise FileNotFoundError(f"Arquivo não encontrado no S3.")

        print(f"Baixando arquivo do S3: {BUCKET_NAME}, {source_s3_key}, {download_path}")
        download_video_from_s3(BUCKET_NAME, source_s3_key, download_path)
        extract_zip(download_path, "/tmp")
        print(f"Arquivo extraído: {download_path}")
        video_file = find_video_file("/tmp")
        print(f"Arquivo de vídeo encontrado: {video_file}")

        if not video_file:
            print("Arquivo de vídeo .mp4 não encontrado após extração.")
            raise FileNotFoundError("Arquivo de vídeo .mp4 não encontrado após extração.")

        print(f"Gerando thumbnails do vídeo: {video_file}")
        create_thumbnails(f"/tmp/{video_file}", interval=20, output_zip=output_zip)
        print(f"Thumbnails criados e salvos: {output_zip}")
        upload_file_to_s3(BUCKET_NAME, output_s3_key, output_zip)
        print(f"Thumbnails enviados para o S3: {output_s3_key}")
        update_status(video_name, "PROCESSADO")
        print(f"Status atualizado para PROCESSADO: {video_name}")
        delete_message_from_sqs(TO_PROCESS_QUEUE_URL, receipt_handle)

        return respond(200, "Thumbnails criados e enviados com sucesso.")
    except Exception as e:
        update_status(video_name, "ERRO")
        return respond(500, f"Erro durante o processamento: {str(e)}")

def delete_message_from_sqs(queue_url, receipt_handle):
    print(f"Deletando mensagem da fila SQS.")
    sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)

def update_status(video_name, status):
    print(f"Atualizando status para {status} do vídeo: {video_name}")
    message = {
        "videoName": video_name,
        "processingStatus": status
    }
    sqs.send_message(QueueUrl=STATUS_QUEUE_URL, MessageBody=json.dumps(message))

def respond(status_code, message):
    return {"statusCode": status_code, "body": message}

def check_file_exists_in_s3(bucket_name, s3_key):
    try:
        print(f"Verificando se o arquivo existe no S3: {bucket_name}, {s3_key}")
        s3.head_object(Bucket=bucket_name, Key=s3_key)
        return True

    except s3.exceptions.ClientError as e:
        if e.response['Error']['Code'] == '404':

            print("Erro - Arquivo não encontrado no bucket.")
            return False
        raise

def download_video_from_s3(bucket_name, s3_key, download_path):
    print("Baixando arquivo do S3.")
    s3.download_file(bucket_name, s3_key, download_path)

def extract_zip(zip_path, extract_to):
    print("Extraindo arquivo ZIP.")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def find_video_file(directory):
    print("Procurando arquivo .mp4 no diretório.")
    for file in os.listdir(directory):
        if file.endswith('.mp4'):
            print("Arquivo de vídeo encontrado")
            return file
    print("Nenhum arquivo de vídeo encontrado.")
    return None

def create_thumbnails(video_path, interval, output_zip):
    print("Gerando thumbnails do vídeo.")
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError("Erro ao abrir o vídeo.")

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps

    with zipfile.ZipFile(output_zip, 'w') as zipf:
        for t in range(0, int(duration), interval):
            cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
            ret, frame = cap.read()
            if not ret:
                break
            thumbnail_path = f"/tmp/thumbnail_{t}.png"
            cv2.imwrite(thumbnail_path, frame)
            zipf.write(thumbnail_path, os.path.basename(thumbnail_path))
            os.remove(thumbnail_path)

    cap.release()
    print("Thumbnails criados e salvos.")

def upload_file_to_s3(bucket_name, s3_key, file_path):
    print("Enviando arquivo para o bucket.")
    s3.upload_file(file_path, bucket_name, s3_key)