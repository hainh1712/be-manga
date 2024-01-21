import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi_sqlalchemy import DBSessionMiddleware, db
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import joinedload
from fastapi import HTTPException
import os
from dotenv import load_dotenv
import boto3
from typing import List

load_dotenv('.env')

app = FastAPI()

# app.add_middleware(DBSessionMiddleware, db_url=os.environ['DATABASE_URL'])
origins = [
    "http://localhost:5173",
    "localhost:5173",
    "https://hai-doctruyen.vercel.app/"
]
s3 = boto3.client("s3", aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'], aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'], region_name=os.environ['AWS_REGION'])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
async def root():
    return {"message": "hello world"}
@app.get('/length_folder')
def get_folder_length(bucket_name, folder_prefix):
    response = s3.list_objects(Bucket=bucket_name, Prefix=folder_prefix)
    object_count = len(response.get("Contents", []))
    
    return object_count

@app.post("/upload")
async def upload_files(files: List[UploadFile], prefix: str):
    try:
        uploaded_urls = []

        for file in files:
            object_key = prefix + file.filename
            s3.upload_fileobj(file.file, os.environ['AWS_BUCKET_NAME'], object_key, ExtraArgs={
                'ContentType': file.content_type,
            })
            uploaded_url = f"https://{os.environ['AWS_BUCKET_NAME']}.s3.{os.environ['AWS_REGION']}.amazonaws.com/{object_key}"
            uploaded_urls.append(uploaded_url)

        return {"message": "Upload successful", "urls": uploaded_urls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.get("/images/{folder_name}")
async def get_images_from_folder(folder_name: str):
    try:
        bucket_name = os.environ['AWS_BUCKET_NAME']
        folder_prefix = f"{folder_name}/"

        s3 = boto3.client("s3", aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'], aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'], region_name=os.environ['AWS_REGION'])

        response = s3.list_objects(Bucket=bucket_name, Prefix=folder_prefix)
        object_keys = [obj['Key'] for obj in response.get("Contents", [])]

        images = []
        for key in object_keys:
            image_url = f"https://{bucket_name}.s3.{os.environ['AWS_REGION']}.amazonaws.com/{key}"
            alt = os.path.splitext(key.split("/")[-1])[0]
            images.append({'url': image_url, 'alt': key, 'name': alt})

        return images
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# if __name__ == "__main__":
#     port = int(os.environ.get('PORT', 8000))
#     uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)