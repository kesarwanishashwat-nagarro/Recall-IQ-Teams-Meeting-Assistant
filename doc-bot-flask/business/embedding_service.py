from langchain.schema import Document
from langchain_community.vectorstores.faiss import FAISS
from flask import current_app
from langchain_openai import OpenAIEmbeddings
from langchain_core.prompts import PromptTemplate
from langchain.chains import ConversationalRetrievalChain
from langchain_openai import OpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from azure.storage.blob import BlobServiceClient
import faiss

class EmbeddingService:
    blob_service_client = None
    def __init__(self, app):
        self.__class__.blob_service_client = BlobServiceClient.from_connection_string(app.config['CONNECTION_STRING'])
    
    def process_transcript(self, transcript, user_id, meeting_id, documents):
        document = documents or [Document(page_content=transcript, metadata={"user_id": user_id, "meeting_id": meeting_id})]
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=200, chunk_overlap=30)
        documents = text_splitter.split_documents(document)
        embedding_model = OpenAIEmbeddings()
        faiss_store = self.__load_index(embedding_model) #FAISS.load_local(current_app.config['FAISS_INDEX'], embedding_model, allow_dangerous_deserialization=True)
        if faiss_store is not None and  'faiss_store' in locals():
            faiss_store.add_documents(document)
        else:
            faiss_store = FAISS.from_documents(document, embedding_model)
        self.__save_index(faiss_store)
    
    def __load_index(self, embedding_model):
        try: 
            if current_app.config['ENVIRONMENT'] == "production":
                    blob_client = self.__class__.blob_service_client.get_blob_client(container=current_app.config['CONTAINER_NAME'], blob=current_app.config['BLOB_NAME'])
                    with open(current_app.config['FAISS_INDEX'] + '/index.faiss', "wb") as download_file:
                        download_file.write(blob_client.download_blob().readall())
            return FAISS.load_local(current_app.config['FAISS_INDEX'], embedding_model, allow_dangerous_deserialization=True)
        except Exception as e:
            print("Failed to load blob:", e)
            return None
        
    def __save_index(self, faiss_store):
        faiss_store.save_local(current_app.config['FAISS_INDEX'])
        if current_app.config['ENVIRONMENT'] == "production":
            try: 
                if self.__class__.blob_service_client:  #current_app.config['ENVIRONMENT'] == 'production':
                    blob_client = self.__class__.blob_service_client.get_blob_client(container=current_app.config['CONTAINER_NAME'], blob=current_app.config['BLOB_NAME'])
                    with open(current_app.config['FAISS_INDEX'] + '/index.faiss', "rb") as data:
                        blob_client.upload_blob(data, overwrite=True)
            except:
                print("Failed to save blob production:", e)
        
    def process_query(self, chat_query, chat_history, user_id):
        prompt = self.__get_prompt_template()
        embedding_model = OpenAIEmbeddings()
        faiss_store = self.__load_index(embedding_model) #FAISS.load_local(current_app.config['FAISS_INDEX'], embedding_model, allow_dangerous_deserialization=True)
        user_embeddings_retriever = faiss_store.as_retriever(search_kwargs={"filter": {"user_id": user_id}, 'k': 6})
        qa_chain = ConversationalRetrievalChain.from_llm(
            llm=OpenAI(),
            retriever= user_embeddings_retriever,
            chain_type='stuff',
            verbose=True,
            combine_docs_chain_kwargs={"prompt": prompt},
            return_source_documents=False
        )
        result = qa_chain({'question': chat_query, 'chat_history': chat_history})
        return result['answer']
        
    def __get_prompt_template(self):
        custom_template = """Use following pieces of context to answer the question at the end.
        Do not use your own knowledge base, just say that you don't know if it is not in the following context.

        {context}

        Question: {question}
        Helpful Answer:"""

        prompt = PromptTemplate(
            input_variables=["question", "context"],
            template=custom_template
        )
        return prompt
    