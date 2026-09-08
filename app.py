import re
import streamlit as st
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np


# ---------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------

st.set_page_config(
    page_title="PDF RAG Question Answering",
    page_icon="📄",
    layout="wide"
)


# ---------------------------------------------------------
# TITLE
# ---------------------------------------------------------

st.title("📄 PDF RAG Question Answering")


# ---------------------------------------------------------
# LOAD EMBEDDING MODEL
# ---------------------------------------------------------

@st.cache_resource
def load_embedding_model():
    return SentenceTransformer("all-MiniLM-L6-v2")


model = load_embedding_model()


# ---------------------------------------------------------
# PDF UPLOAD
# ---------------------------------------------------------

uploaded_file = st.file_uploader(
    "Upload your PDF",
    type=["pdf"]
)


if uploaded_file is not None:

    # -----------------------------------------------------
    # READ PDF
    # -----------------------------------------------------

    reader = PdfReader(uploaded_file)

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):

        page_text = page.extract_text()

        if page_text:
            pages.append({
                "page": page_number,
                "text": page_text
            })


    # -----------------------------------------------------
    # COMBINE TEXT
    # -----------------------------------------------------

    full_text = "\n".join(
        page["text"] for page in pages
    )


    st.success("PDF uploaded successfully! ✅")

    st.write(f"Number of pages: {len(reader.pages)}")


    # -----------------------------------------------------
    # TEXT CHUNKING
    # -----------------------------------------------------

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150
    )


    chunks = []

    for page in pages:

        page_chunks = text_splitter.split_text(
            page["text"]
        )

        for chunk in page_chunks:

            chunks.append({
                "text": chunk,
                "page": page["page"]
            })


    st.write(f"Number of chunks: {len(chunks)}")


    # -----------------------------------------------------
    # CREATE EMBEDDINGS
    # -----------------------------------------------------

    chunk_texts = [
        chunk["text"] for chunk in chunks
    ]


    embeddings = model.encode(
        chunk_texts,
        normalize_embeddings=True
    )


    embeddings = np.array(
        embeddings,
        dtype="float32"
    )


    # -----------------------------------------------------
    # CREATE FAISS DATABASE
    # -----------------------------------------------------

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatIP(dimension)

    index.add(embeddings)


    st.success(
        "FAISS vector database created successfully! 🎉"
    )


    # -----------------------------------------------------
    # DISPLAY EXTRACTED TEXT
    # -----------------------------------------------------

    with st.expander("View extracted text"):

        st.write(full_text)


    # -----------------------------------------------------
    # DISPLAY CHUNKS
    # -----------------------------------------------------

    with st.expander("View text chunks"):

        for i, chunk in enumerate(chunks):

            st.write(
                f"### Chunk {i + 1} — Page {chunk['page']}"
            )

            st.write(chunk["text"])


    # -----------------------------------------------------
    # QUESTION INPUT
    # -----------------------------------------------------

    question = st.text_input(
        "Ask a question about your PDF:"
    )


    if question:

        question_lower = question.lower()


        # =================================================
        # SPECIAL CASE:
        # QUESTIONS ABOUT EXPERIMENT NUMBER
        # =================================================

        experiment_match = re.search(
            r"(?:experiment|ex\.?\s*no\.?)\s*(?:no\.?\s*)?(\d+)",
            question_lower
        )


        if experiment_match:

            experiment_number = int(
                experiment_match.group(1)
            )


            # ---------------------------------------------
            # FIND EXPERIMENT START
            # ---------------------------------------------

            experiment_start = None

            experiment_header_pattern = re.compile(
                r"(?:experiment|ex\.?\s*no\.?)\s*(?:no\.?\s*)?[:.\-]?\s*(\d+)",
                re.IGNORECASE
            )


            for i, page in enumerate(pages):

                matches = experiment_header_pattern.findall(
                    page["text"]
                )

                for number in matches:

                    if int(number) == experiment_number:

                        experiment_start = i
                        break

                if experiment_start is not None:
                    break


            # ---------------------------------------------
            # IF EXPERIMENT FOUND
            # ---------------------------------------------

            if experiment_start is not None:

                experiment_pages = []

                for i in range(
                    experiment_start,
                    len(pages)
                ):

                    # Stop when next experiment starts
                    if i > experiment_start:

                        next_matches = (
                            experiment_header_pattern.findall(
                                pages[i]["text"]
                            )
                        )

                        if next_matches:

                            break


                    experiment_pages.append(
                        pages[i]
                    )


                experiment_text = "\n".join(
                    page["text"]
                    for page in experiment_pages
                )


                # -----------------------------------------
                # LOOK FOR AIM
                # -----------------------------------------

                aim_match = re.search(
                    r"\bAIM\b\s*[:\-]?\s*(.*?)(?=\n\s*(?:PROCEDURE|PROGRAM|ALGORITHM|THEORY|OUTPUT|RESULT|EXPERIMENT|$))",
                    experiment_text,
                    re.IGNORECASE | re.DOTALL
                )


                if aim_match:

                    answer = aim_match.group(1).strip()


                    # Clean unnecessary spaces
                    answer = re.sub(
                        r"\s+",
                        " ",
                        answer
                    )


                    st.subheader("🎯 Answer")

                    st.success(answer)


                    st.subheader(
                        "📚 Source"
                    )

                    start_page = experiment_pages[0]["page"]

                    end_page = experiment_pages[-1]["page"]


                    if start_page == end_page:

                        st.write(
                            f"Page {start_page}"
                        )

                    else:

                        st.write(
                            f"Pages {start_page}–{end_page}"
                        )


                else:

                    st.warning(
                        f"Experiment {experiment_number} was found, "
                        "but an AIM section could not be detected."
                    )


                    st.subheader(
                        "Experiment content"
                    )

                    st.write(experiment_text)


            else:

                st.warning(
                    f"Experiment {experiment_number} "
                    "could not be found in the PDF."
                )


        # =================================================
        # NORMAL RAG QUESTION
        # =================================================

        else:

            st.subheader(
                "🔎 Relevant information"
            )


            # ---------------------------------------------
            # EMBED QUESTION
            # ---------------------------------------------

            question_embedding = model.encode(
                [question],
                normalize_embeddings=True
            )


            question_embedding = np.array(
                question_embedding,
                dtype="float32"
            )


            # ---------------------------------------------
            # SEARCH FAISS
            # ---------------------------------------------

            k = min(5, len(chunks))

            scores, indices = index.search(
                question_embedding,
                k
            )


            # ---------------------------------------------
            # DISPLAY RESULTS
            # ---------------------------------------------

            for result_number, chunk_index in enumerate(
                indices[0],
                start=1
            ):

                if chunk_index == -1:
                    continue


                result_chunk = chunks[chunk_index]

                score = scores[0][result_number - 1]


                st.write(
                    f"### Result {result_number}"
                )


                st.caption(
                    f"Page {result_chunk['page']} | "
                    f"Similarity: {score:.3f}"
                )


                st.write(
                    result_chunk["text"]
                )


                st.divider()