<p align="center">
  <img src="banner.png" alt="PDF RAG Question Answering Bot" width="100%">
</p>

# 📄 PDF RAG Question Answering Bot

A Retrieval-Augmented Generation (RAG) based PDF Question Answering application built with Python and Streamlit.

This project allows users to upload a PDF document and ask questions about its content. The application extracts the PDF text, splits it into smaller chunks, converts the chunks into vector embeddings, and uses similarity search to retrieve the most relevant information.

## 🚀 Features

- 📤 Upload PDF documents
- 📖 Extract text from PDF files
- ✂️ Split documents into smaller chunks
- 🧠 Generate semantic embeddings using Sentence Transformers
- 🔎 Perform semantic similarity search using FAISS
- 📑 Display relevant information from the uploaded PDF
- 📄 Show source page numbers
- 📊 Display similarity scores
- 🖥️ Simple and interactive Streamlit interface

## 🛠️ Technologies Used

- Python
- Streamlit
- PyPDF
- Sentence Transformers
- FAISS
- NumPy
- LangChain Text Splitters

## 🔄 How It Works

```text
        PDF Upload
             ↓
      Extract PDF Text
             ↓
       Text Chunking
             ↓
     Generate Embeddings
             ↓
       FAISS Vector DB
             ↓
       User Question
             ↓
      Similarity Search
             ↓
     Relevant PDF Content
