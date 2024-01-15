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
    "localhost:5173"
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

# if __name__ == "__main__":
#     port = int(os.environ.get('PORT', 8000))
#     uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)