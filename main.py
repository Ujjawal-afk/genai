# This is the main chatbot file

import os
import ollama
import streamlit as st
from dotenv import load_dotenv
import pandas as pd
# from langchain.retrievers import HybridSearchRetriever
# from langchain.retrievers import BaseRetriever
# from langchain.retrievers import VectorStoreRetriever

from langchain.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings

import re
from nltk.corpus import stopwords
import nltk

load_dotenv()


try:
    if "stopwords" not in st.session_state.keys():
        nltk.download("stopwords")



    st.header("GenAI Chatbot")



    def chat_completion(user_query, context):
        client = ollama.Client(
            host="https://ollama.com",
            headers={'Authorization': 'Bearer ' + os.getenv('ollama_api_key')}
        )

        prompt = " You are a very good question asnwering bot, You can easily find the answers to the questions asked \
                        You will be given a CONTEXT and USER QUERY you need to find answer from the given context and finally respond"
        

        master_prompt = "<USERY QUERY>" + user_query + '</USER QUERY>\n\n<CONTEXT>' + str(context) + '</CONTEXT>'

        message = [
            {
                "role":'system', 'content': prompt
            },
            {
                "role":"user", "content": master_prompt
            }
        ]
        response = client.chat('gpt-oss:120b', messages=message)['message'].content
        return response

        
    if "embedding_model" not in st.session_state.keys():
        with st.spinner("loading embedding model.."):
            embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    if "vector_store" not in st.session_state.keys():
        with st.spinner("Loading FAISS vector store"):
            vectorstore = FAISS.load_local("genai_embedding_store_new", embedding_model, allow_dangerous_deserialization=True)


    def extract_keywords(query):
        # Lowercase and remove non-alphanumeric
        query = re.sub(r'[^a-zA-Z0-9\s]', '', query.lower())
        words = query.split()
        
        # Remove stopwords
        keywords = [w for w in words if w not in stopwords.words('english')]
        return keywords


    # class KeywordRetriever(BaseRetriever):
    #     def __init__(self, docs, keywords):
    #         self.docs = docs
    #         self.keywords = keywords
    #     def get_relevant_documents(self, query):
    #         return [doc for doc in self.docs if any(kw.lower() in doc.page_content.lower() for kw in self.keywords)]







    if "k" not in st.session_state.keys():
        st.session_state.k = 50



    if "messsage_data" not in st.session_state.keys():
        st.session_state.message_data = [{
            "role": "assistant",
            "message":"Hey! how can I help you?"
        }]

    if user_query := st.chat_input("Your message"):
        with st.spinner("Please wait while we generate the response"):
            st.session_state.user_query = user_query
            message = {
                'role':'user',
                'message':user_query,
                'context': []
            }
            st.session_state.message_data.append(message)
            # keywords = extract_keywords(st.session_state.user_query)
            # keyword_retriever = KeywordRetriever(st.session_state.vectorstore.get_all_documents(), keywords)

            # vector_retriever = VectorStoreRetriever(
            # vectorstore=vectorstore,
            # search_kwargs={"k": 5} 
            # )

            # hybrid_retriever = HybridSearchRetriever(
            # vectorstore_retriever=vector_retriever,
            # keyword_retriever=keyword_retriever,
            # alpha=0.5
            # )
            # vector_results = vector_retriever.get_relevant_documents(st.session_state.user_query)

            # received_context = hybrid_retriever.get_relevant_documents("AI in industry")
            # retriever = vectorstore.as_retriever(search_kwargs = {"k":5})
            # vector_results = retriever.get_relevant_documents(st.session_state.user_query)

            retriever = vectorstore.as_retriever(search_kwargs = {"k":st.session_state.k})
            vector_results = retriever.get_relevant_documents(st.session_state.user_query)
            vector_results = [value.page_content for value in vector_results]
            st.session_state.received_response = chat_completion(st.session_state.user_query, vector_results)
            st.session_state.message_data[-1]['context'] = vector_results
            message = {
                'role':'assistant',
                'message':st.session_state.received_response,
                'context': []
            }
            st.session_state.message_data.append(message)

    if len(st.session_state.message_data) > 0:
        for message_data in st.session_state.message_data:
            with st.chat_message(message_data['role']):
                st.write(message_data['message'])


    with st.sidebar:
        st.session_state.k = st.slider("Please input the hyperparameter value for k", min_value= 4, max_value = vectorstore.index.ntotal , help="The higher the value the more the context provided and the model might hallucinate or give a good result")

        if st.button("Download chat data"):
            df = pd.DataFrame(st.sesssion_state.message_data, columns = ['Role', 'Message', 'Context'])
            df.to_excel("Chat history data.xlsx")
except Exception as err:
    st.error("Oops you had an error!")
    with st.expander("Full Error:"):
        st.write(str(err))        