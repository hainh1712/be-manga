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
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
load_dotenv('.env')

app = FastAPI()

# app.add_middleware(DBSessionMiddleware, db_url=os.environ['DATABASE_URL'])
origins = [
    "http://localhost:5173",
    "localhost:5173",
    "localhost:8000",
    "https://hai-doctruyen.vercel.app/",
    "http://localhost:3000",
    "https://onepage-next14.vercel.app/",
    "https://onepage-next13.vercel.app/",
    "http://tachayfood.vn/"
]
s3 = boto3.client("s3", aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'], aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'], region_name=os.environ['AWS_REGION'])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    # allow_origins=["*"],
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
    
@app.get("/length_manga/{manga_name}")
def get_subfolder_count(manga_name: str):
    try:
        bucket_name = os.environ['AWS_BUCKET_NAME']
        folder_prefix = f"{manga_name}/"

        s3 = boto3.client("s3", aws_access_key_id=os.environ['AWS_ACCESS_KEY_ID'], aws_secret_access_key=os.environ['AWS_SECRET_ACCESS_KEY'], region_name=os.environ['AWS_REGION'])

        response = s3.list_objects(Bucket=bucket_name, Prefix=folder_prefix, Delimiter='/')
        
        subfolder_count = len(response.get("CommonPrefixes", []))

        return {"manga_name": manga_name, "subfolder_count": subfolder_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/send-email")
def send_email_with_custom_template(customer_name: str, customer_phone: str, customer_address: str, order_details: str):
    try:
        order_details_str = "\n".join([f"<li>{item}</li>" for item in order_details])
        content = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    background-color: #f9f9f9;
                    padding: 20px;
                }}
                .email-content {{
                    background-color: #ffffff;
                    border: 1px solid #ddd;
                    padding: 20px;
                    border-radius: 8px;
                }}
                h2 {{
                    color: #333;
                }}
                .order-details {{
                    background-color: #f3f3f3;
                    padding: 10px;
                    border-radius: 5px;
                    margin-top: 10px;
                }}
                ul {{
                    padding-left: 20px;
                }}
                li {{
                    color: #555;
                    margin-bottom: 5px;
                }}
            </style>
        </head>
        <body>
            <div class="email-content">
                <h2>Hello Tachay Food Team,</h2>
                <p>You got a new order from <strong>{customer_name}</strong>:</p>
                <ul>
                    <li><strong>Name:</strong> {customer_name}</li>
                    <li><strong>Phone:</strong> {customer_phone}</li>
                    <li><strong>Address:</strong> {customer_address}</li>
                </ul>

                <div class="order-details">
                    <p><strong>Order Details:</strong></p>
                    <ul>
                        {order_details_str}
                    </ul>
                </div>

                <p>Thank you for using our service!</p>
                <p>Best regards,<br>Tachay Food Team</p>
            </div>
        </body>
        </html>
        """
        message = Mail(
            from_email='sendgrid@gmail.com',
            to_emails=os.environ.get('TO_EMAILS'),
            subject="New Order Notification",
            html_content=content
        )
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        return {"status_code": response.status_code, "message": "Email sent successfully"}
    except Exception as e:
        return {"error": str(e)}
    
if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    # uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
    uvicorn.run("main:app", host="localhost", port=port, reload=True)