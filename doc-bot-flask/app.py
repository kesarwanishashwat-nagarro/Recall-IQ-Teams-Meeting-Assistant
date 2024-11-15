from flask import Flask #, jsonify, redirect
from flask import request
from dotenv import load_dotenv
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.schema import Document
import os
from werkzeug.utils import secure_filename
import PyPDF2
from flask_cors import CORS
from business.graph_service import GraphService
from business.embedding_service import EmbeddingService

load_dotenv()
app = Flask(__name__)
CORS(app)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# app.config['REDIRECT_URI'] = 'http://localhost:5000/callback'

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0"

app.config['CLIENT_ID'] = os.getenv('CLIENT_ID', "ebf953d7-d919-4ccf-b524-f9e51cab8472")
app.config['TENANT_ID'] = os.getenv('TENANT_ID', "3a663c68-f2d9-47f0-a3ec-4fd032bcb334")
app.config['CLIENT_SECRET'] = os.getenv('CLIENT_SECRET', "fsD8Q~nzGtkB64LP7ntA4W85Pk3Pc0l~y9AwtbMb")
app.config['AUTHORITY'] = f"https://login.microsoftonline.com/{app.config['TENANT_ID']}"
app.config['GRAPH_API_ENDPOINT'] = os.getenv('GRAPH_API_ENDPOINT') or GRAPH_API_ENDPOINT
app.config['APP_URL'] = os.getenv('APP_URL')
app.config['FAISS_INDEX'] = os.getenv('FAISS_INDEX')
app.config['ENVIRONMENT'] = os.getenv('FLASK_ENV', 'development')
app.config['CONNECTION_STRING'] = os.getenv('CONNECTION_STRING')
app.config['CONTAINER_NAME'] = os.getenv('CONTAINER_NAME', 'recalliq-container')
app.config['BLOB_NAME'] = os.getenv('BLOB_NAME', 'recalliq-blob')
app.config['LOCAL_FILE_PATH'] = os.getenv('LOCAL_FILE_PATH', "/tmp/faiss.index")

graph_service_instances = {}
embedding_service = EmbeddingService(app)

# Get access token from Azure AD
# def get_access_token():
#     url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
#     headers = {"Content-Type": "application/x-www-form-urlencoded"}
#     data = {
#         "grant_type": "client_credentials",
#         "client_id": CLIENT_ID,
#         "client_secret": CLIENT_SECRET,
#         "scope": "OnlineMeetingTranscript.Read.All"
#     }

#     response = requests.post(url, headers=headers, data=data)
#     response_json = response.json()

#     if 'access_token' in response_json:
#         return response_json['access_token']
#     else:
#         raise Exception(f"Unable to get access token: {response_json}")

    
    
# Create a subscription for meeting transcripts
@app.route('/subscribe', methods=['POST'])
def subscribe_to_transcripts():
    data = request.json
    client_token = data['token']
    user_id = data['userId'] or "1ada3a13-67fa-47e0-928f-af150f8c0e29"
    access_token = GraphService.get_access_token_from_client(client_token)
    join_url = data['JoinWebUrl']
    print(f"subscribe payload data - {data}")
    graph_service = GraphService(access_token)
    meeting_id = graph_service.get_meeting_id(join_url, user_id)
    print(f"meeting id - {meeting_id}")
    graph_service_instances[meeting_id] = graph_service
    return graph_service.subscribe_meeting_transcripts(meeting_id)
    # access_token = get_access_token()
    # data = request.json
    # chat_query = request.args.get('query')
    # global access_token
    # access_token = "eyJ0eXAiOiJKV1QiLCJub25jZSI6IjdEbGRFTzJmSTJGaFZaRl9WNWNzazJwUEhqX0ttUkZlNzFVNGUyajc2SzgiLCJhbGciOiJSUzI1NiIsIng1dCI6Ik1jN2wzSXo5M2c3dXdnTmVFbW13X1dZR1BrbyIsImtpZCI6Ik1jN2wzSXo5M2c3dXdnTmVFbW13X1dZR1BrbyJ9.eyJhdWQiOiIwMDAwMDAwMy0wMDAwLTAwMDAtYzAwMC0wMDAwMDAwMDAwMDAiLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC8zYTY2M2M2OC1mMmQ5LTQ3ZjAtYTNlYy00ZmQwMzJiY2IzMzQvIiwiaWF0IjoxNzI4NTUxMTk5LCJuYmYiOjE3Mjg1NTExOTksImV4cCI6MTcyODU1NjQ2NywiYWNjdCI6MCwiYWNyIjoiMSIsImFpbyI6IkFUUUF5LzhZQUFBQWVvR0FTaTNIcnZuMHZpSUJyNG50dWpsYXBqZEk1djNCQjV2SkVlUGZRSnBpVnJWVjA2VW94bDNpNmF4Q3Myd0kiLCJhbXIiOlsicHdkIl0sImFwcF9kaXNwbGF5bmFtZSI6IlRlYW1zQXNzaXN0YW50IiwiYXBwaWQiOiJlYmY5NTNkNy1kOTE5LTRjY2YtYjUyNC1mOWU1MWNhYjg0NzIiLCJhcHBpZGFjciI6IjEiLCJmYW1pbHlfbmFtZSI6Iktlc2Fyd2FuaSIsImdpdmVuX25hbWUiOiJTaGFzaHdhdCIsImlkdHlwIjoidXNlciIsImlwYWRkciI6IjE1Mi41OC4xNTMuNzYiLCJuYW1lIjoiU2hhc2h3YXQgS2VzYXJ3YW5pIiwib2lkIjoiMWFkYTNhMTMtNjdmYS00N2UwLTkyOGYtYWYxNTBmOGMwZTI5IiwicGxhdGYiOiIxNCIsInB1aWQiOiIxMDAzMjAwM0QwQUI1NUMwIiwicmgiOiIwLkFXTUJhRHhtT3RueThFZWo3RV9RTXJ5ek5BTUFBQUFBQUFBQXdBQUFBQUFBQUFCakFkUS4iLCJzY3AiOiJPbmxpbmVNZWV0aW5nQXJ0aWZhY3QuUmVhZC5BbGwgT25saW5lTWVldGluZ3MuUmVhZCBPbmxpbmVNZWV0aW5ncy5SZWFkV3JpdGUgT25saW5lTWVldGluZ1RyYW5zY3JpcHQuUmVhZC5BbGwgUmVzb3VyY2VTcGVjaWZpY1Blcm1pc3Npb25HcmFudC5SZWFkRm9yQ2hhdCBUZWFtc1RhYi5DcmVhdGUgVGVhbXNUYWIuUmVhZC5BbGwgVGVhbXNUYWIuUmVhZFdyaXRlLkFsbCBUZWFtc1RhYi5SZWFkV3JpdGVGb3JVc2VyIFRlYW1zVGFiLlJlYWRXcml0ZVNlbGZGb3JVc2VyIFVzZXIuUmVhZCBwcm9maWxlIG9wZW5pZCBlbWFpbCIsInN1YiI6IkF0UHFLd2hjOUVIUUtiblkwcTQyWXZ6RUNaUS03bFh5bU43c0VoRmdNZnciLCJ0ZW5hbnRfcmVnaW9uX3Njb3BlIjoiTkEiLCJ0aWQiOiIzYTY2M2M2OC1mMmQ5LTQ3ZjAtYTNlYy00ZmQwMzJiY2IzMzQiLCJ1bmlxdWVfbmFtZSI6InNoYXNod2F0a0B6bmZoci5vbm1pY3Jvc29mdC5jb20iLCJ1cG4iOiJzaGFzaHdhdGtAem5maHIub25taWNyb3NvZnQuY29tIiwidXRpIjoiRllyVWd6RFhfMDI0R1J4XzRaa2JBQSIsInZlciI6IjEuMCIsIndpZHMiOlsiNjJlOTAzOTQtNjlmNS00MjM3LTkxOTAtMDEyMTc3MTQ1ZTEwIiwiYjc5ZmJmNGQtM2VmOS00Njg5LTgxNDMtNzZiMTk0ZTg1NTA5Il0sInhtc19pZHJlbCI6IjI4IDEiLCJ4bXNfc3QiOnsic3ViIjoiMDZPTVFsc2JVMUxLSEd0dU9zX1IzWDZ1SndxRTdrZ1kxZHhsbzg4ZzRHWSJ9LCJ4bXNfdGNkdCI6MTcyNjcxMTE4Mn0.E6H1f1uYP8q6NEf_b1O2cRr3RPAj9M2PclAi52Q9P7_PdoyVJ50E91da034lJUDwyVViincTv0FQAzmxc2Tcu7N6JoAOelfv_1xCF2TQ5cd5wtHSx-aDRfYqMNBGjAQ5HiFiq6bbL4epTetaC1UqdsDjj34-ntXtYptyBxJlNzvtidfeOlKdlSR6Dp8XoVVWYE40HQwRaTmZPZ7PWTZAIvFWOIYeQ8uYFEzI3tbBMkXC-ae2M3iBwtF1b57n8TXz04RhDarVUz6jXppuX0Wz_nVC4cJAchn6ccYaq3iWKj_axhPeDsf1y8fTkJvPH8Lrjf2bsfvH-csyR-6TZ5dPaQ"
    # global meetingId 
    # MCMxOTptZWV0aW5nX1ptTXhPV0U0WW1ZdFpHWTRZeTAwT0RKaUxXRTJPRFF0T1dVeU1EbGtNV1JqTWpJeEB0aHJlYWQudjIjMA==
    # meetingId = "MCMxOTptZWV0aW5nX1ptTXhPV0U0WW1ZdFpHWTRZeTAwT0RKaUxXRTJPRFF0T1dVeU1EbGtNV1JqTWpJeEB0aHJlYWQudjIjMA=="
    # meetingId="MSoxYWRhM2ExMy02N2ZhLTQ3ZTAtOTI4Zi1hZjE1MGY4YzBlMjkqMCoqMTk6bWVldGluZ19abU14T1dFNFltWXRaR1k0WXkwME9ESmlMV0UyT0RRdE9XVXlNRGxrTVdSak1qSXhAdGhyZWFkLnYy"
    # meetingId="MSoxYWRhM2ExMy02N2ZhLTQ3ZTAtOTI4Zi1hZjE1MGY4YzBlMjkqMCoqMTk6bWVldGluZ19OVGMxTVRNNVpUZ3ROVFk0TVMwME1qRTRMVGs1Wm1ZdE5qZGpNRGhtTnpZeE1qVmtAdGhyZWFkLnYy"
    
    # Get current GMT time
    # gmt_time = datetime.datetime.now(pytz.timezone('GMT'))
    # subscription_data = {
    #     "changeType": "created",
    #     "notificationUrl": "https://0448-2409-40e3-1f7-2ce4-3139-3171-a1b6-d5d5.ngrok-free.app/notifications",
    #     "resource": "communications/onlineMeetings/" + meetingId + "/transcripts?useResourceSpecificConsentBasedAuthorization=true",
    #     "expirationDateTime": (gmt_time + datetime.timedelta(minutes=45)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'), #"2024-10-10T08:30:00.000Z",  # Adjust based on requirements
    #     "clientState": secrets.token_hex(16)
    # }
    # print(subscription_data)
    # headers = {
    #     "Authorization": f"Bearer {access_token}",
    #     "Content-Type": "application/json"
    # }

    # response = requests.post(f"{GRAPH_API_ENDPOINT}/subscriptions", headers=headers, json=subscription_data)

    # if response.status_code == 201:
    #     return jsonify({"message": "Subscription created successfully", "data": response.json()}), 201
    # else:
    #     return jsonify({"error": "Failed to create subscription", "details": response.json()}), response.status_code


# Endpoint to receive transcript notifications
@app.route('/notifications', methods=['POST'])
def handle_notifications():
    #VjIjIzExYWRhM2ExMy02N2ZhLTQ3ZTAtOTI4Zi1hZjE1MGY4YzBlMjkzYTY2M2M2OC1mMmQ5LTQ3ZjAtYTNlYy00ZmQwMzJiY2IzMzQwNDAwMDAwMDgyMDBFMDAwNzRDNUI3MTAxQTgyRTAwODAwMDAwMDAwNWUzMmM2OTVlZjFhZGIwMTAwMDAwMDAwMDAwMDAwMDAxMDAwMDAwMDUwNDNkNzQyYTgzOTk2NDZhODI4ZmJiODRiY2JjNDgxIyNmNjMxMjc1MC00MDJiLTRlMjAtODQyOS0yY2M2ZWE2MmExZmQ
    print("notifications webhook called")
    # Check if this is a validation request
    validation_token = request.args.get('validationToken')
    if validation_token:
        # Return the validation token in the response for the subscription to be validated
        return validation_token
    
    # print(request.args)
    data = request.get_json()
    print(f"data: {data}")
    # zip
    if 'value' in data:
        for notification in data['value']:
            # Extract the transcript_id from resourceData
            notificationData = notification.get('resourceData', {})
            print(f"notificationData: {notificationData}")
            transcript_id = notificationData.get('id')
            meeting_id = notificationData.get('meeting_id')
            graph_service = graph_service_instances['meeting_id']
            if graph_service.is_valid():
                transcript = graph_service.download_transcript_content(meeting_id, transcript_id)
                embedding_service.process_transcript(transcript)
    
    # Return a 200 OK response
    return 'Notified' #jsonify({"message": "Notification received"}), 200


@app.post('/process-pdf')
def processDocument():
    filepath = saveFile()
    extractedData = extract_text_from_pdf(filepath)
    documents = extractedData['documents']
    # splitDocuments(documents)
    global db
    try:
        embedding_service.process_transcript('', "1ada3a13-67fa-47e0-928f-af150f8c0e29", "6343079b-f79d-49fb-a158-1b0189f4cadd", documents)
    except Exception as e:
        print("An unexpected error occurred:", e)
    return extractedData['allText']

@app.post('/query')
def getChatResult():
    data = request.json
    # chat_query = request.args.get('query')
    # prompt = getPromptTemplate()
    history = data['history']
    user_id = data['userId'] or "1ada3a13-67fa-47e0-928f-af150f8c0e29"
    chat_history = []
    for f in history:
        chat_history.append((f['query'], f['ans']))
    chat_query = data['question']
    # response = get_chatbot_response(db, chat_query, prompt, chat_history)
    return embedding_service.process_query(chat_query, chat_history, user_id)


def saveFile():
    file = request.files['file']
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    return filepath


def splitDocuments(text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=200, chunk_overlap=30)
    documents = text_splitter.split_documents(text)
    print(len(documents))


def extract_text_from_pdf(filepath):
    documents = []
    allText = ''
    rv = {}
    with open(filepath, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page_num in range(len(reader.pages)):
            page = reader.pages[page_num]
            text = page.extract_text() or ""
            allText += text
            if text.strip():  # Only add pages with text
                documents.append(Document(page_content=text,
                                 metadata={"page": page_num + 1, "user_id": "1ada3a13-67fa-47e0-928f-af150f8c0e29", "meeting_id": "6343079b-f79d-49fb-a158-1b0189f4cadd"}))
    return {"documents": documents, "allText": allText}


# def getPromptTemplate():
#     custom_template = """Use following pieces of context to answer the question at the end.
#     Do not use your own knowledge base, just say that you don't know if it is not in the following context.

#     {context}

#     Question: {question}
#     Helpful Answer:"""

#     prompt = PromptTemplate(
#         input_variables=["question", "context"],
#         template=custom_template
#     )
#     return prompt


# def get_chatbot_response(db, chat_query, prompt, chat_history):
    # qa_chain = ConversationalRetrievalChain.from_llm(
    #     llm=OpenAI(),
    #     retriever= db.as_retriever(search_kwargs={'k': 6}),
    #     chain_type='stuff',
    #     verbose=True,
    #     combine_docs_chain_kwargs={"prompt": prompt},
    #     return_source_documents=False
    # )
    # result = qa_chain({'question': chat_query, 'chat_history': chat_history})
    # if len(chat_history) < 5:
    #     chat_history.append((chat_query, result['answer']))
    # else:
    #     chat_history.clear()
    # return result['answer']
if __name__ == '__main__':
    app.run(debug=True)