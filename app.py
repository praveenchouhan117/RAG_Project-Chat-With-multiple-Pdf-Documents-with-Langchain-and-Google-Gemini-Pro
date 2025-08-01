import streamlit as st 
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()
os.getenv("GOOGLE_API_KEY")
genai.configure(api_key =  os.getenv("GOOGLE_API_KEY"))


def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_text_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=500)
    chuncks = text_splitter.split_text(text)
    return chuncks

def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model = "models/embedding-001")
    vector_store = FAISS.from_texts(text_chunks, embeddings)
    vector_store.save_local("Faiss_index")
    
    
def get_qa_chain():
    prompt_template = """
    You are a helpful assistant. Use the following pieces of context to answer the question at the end.
    \n\n
    Context:\n {context} ?\n
    Question:\n {question}\n
    \n
    Answer:"""
    
    model = ChatGoogleGenerativeAI(model="gemini-2.5-pro",
                                   temperature=0.3)
    
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model,chain_type="stuff", prompt=prompt)
    return chain

def user_input(user_question):
    embeddings = GoogleGenerativeAIEmbeddings(model = "models/embedding-001")
    new_db = FAISS.load_local("Faiss_index", embeddings, allow_dangerous_deserialization=True)
    # Perform similarity search
    docs = new_db.similarity_search(user_question)
    
    chain = get_qa_chain()
    
    response = chain(
        {"input_documents": docs, "question": user_question}
        , return_only_outputs=True)
    
    print(response)
    st.write("Replay: ", response['output_text'])
    
    
def main():
    st.set_page_config(page_title="Chat with PDF", page_icon=":books:")
    st.header("Chat with PDF Documents")
    
    user_question = st.text_input("Ask a question about the PDF documents:")
    
    if user_question:
        user_input(user_question)
        
    with st.sidebar:
        st.title("Menu: ")
        pdf_docs = st.file_uploader("Upload PDF documents", type=["pdf"], accept_multiple_files=True)
        if st.button("Submit & Process"):
            with st.spinner("Processing..."):
                raw_text = get_pdf_text(pdf_docs)
                text_chunks = get_text_chunks(raw_text)
                get_vector_store(text_chunks)
                st.success("PDF documents processed and vector store created successfully!")


if __name__ == "__main__":
    main()