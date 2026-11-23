import os
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from src.preprocessing import preprocessor

try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import docx
except ImportError:
    docx = None

class DocumentQAEngine:
    """
    Document Question Answering & Information Retrieval Engine.
    Supports PDF, DOCX, and TXT parsing, paragraph chunking, TF-IDF vectorization,
    Cosine Similarity matching, and source citation.
    """
    def __init__(self):
        self._indexes = {}

    @staticmethod
    def _scope(user_id=None):
        return str(user_id) if user_id is not None else "guest"

    def _index(self, user_id=None):
        scope = self._scope(user_id)
        if scope not in self._indexes:
            self._indexes[scope] = {"chunks": [], "vectorizer": None, "vectors": None}
        return self._indexes[scope]

    @property
    def indexed_chunks(self):
        """Compatibility view for anonymous/demo callers."""
        return self._index()["chunks"]

    def has_documents(self, user_id=None):
        return bool(self._index(user_id)["chunks"])

    def list_documents(self, user_id=None):
        sources = {}
        for chunk in self._index(user_id)["chunks"]:
            sources[chunk["source"]] = sources.get(chunk["source"], 0) + 1
        return sources

    def read_txt(self, file_path: str) -> str:
        """Extract text from TXT file."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def read_pdf(self, file_path: str) -> list:
        """Extract text page-by-page from PDF file."""
        pages_content = []
        if pypdf:
            try:
                reader = pypdf.PdfReader(file_path)
                for idx, page in enumerate(reader.pages):
                    text = page.extract_text() or ""
                    if text.strip():
                        pages_content.append({"page": idx + 1, "text": text})
            except Exception as e:
                print(f"Error reading PDF {file_path}: {e}")
        return pages_content

    def read_docx(self, file_path: str) -> str:
        """Extract text from DOCX file."""
        if docx:
            try:
                doc = docx.Document(file_path)
                return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            except Exception as e:
                print(f"Error reading DOCX {file_path}: {e}")
        return ""

    def chunk_text(self, text: str, source_name: str, page_num: int = 1) -> list:
        """Split text into paragraph/section chunks for embedding and vector search."""
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if len(p.strip()) > 30]
        if not paragraphs:
            # Fallback to sentence chunking if no clear double newline
            sentences = preprocessor.tokenize_sentences(text)
            chunk_size = 3
            paragraphs = [" ".join(sentences[i:i+chunk_size]) for i in range(0, len(sentences), chunk_size)]

        chunks = []
        for idx, p in enumerate(paragraphs):
            processed_p = preprocessor.preprocess_for_vectorizer(p)
            if processed_p:
                chunks.append({
                    "chunk_id": f"{source_name}_p{page_num}_c{idx+1}",
                    "source": source_name,
                    "page": page_num,
                    "raw_text": p,
                    "processed_text": processed_p
                })
        return chunks

    def process_document(self, file_path: str, source_name: str = None, user_id=None) -> list:
        """
        Process a document file (PDF, DOCX, TXT), build chunks, and update index.
        """
        if not source_name:
            source_name = os.path.basename(file_path)

        ext = os.path.splitext(file_path)[1].lower()
        chunks = []

        if ext == '.pdf':
            pages = self.read_pdf(file_path)
            for p in pages:
                chunks.extend(self.chunk_text(p["text"], source_name, page_num=p["page"]))
        elif ext == '.docx':
            text = self.read_docx(file_path)
            chunks.extend(self.chunk_text(text, source_name))
        else:  # default txt
            text = self.read_txt(file_path)
            chunks.extend(self.chunk_text(text, source_name))

        self._index(user_id)["chunks"].extend(chunks)
        self._rebuild_vector_index(user_id)
        return chunks

    def process_raw_text(self, text: str, source_name: str = "Uploaded Document", user_id=None) -> list:
        """Process direct raw text string uploaded by user."""
        chunks = self.chunk_text(text, source_name)
        self._index(user_id)["chunks"].extend(chunks)
        self._rebuild_vector_index(user_id)
        return chunks

    def clear_index(self, user_id=None):
        """Reset index."""
        self._indexes.pop(self._scope(user_id), None)

    def _rebuild_vector_index(self, user_id=None):
        """Fit TfidfVectorizer on all indexed document chunks."""
        index = self._index(user_id)
        if not index["chunks"]:
            index["vectorizer"] = None
            index["vectors"] = None
            return

        corpus = [c["processed_text"] for c in index["chunks"]]
        index["vectorizer"] = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
        index["vectors"] = index["vectorizer"].fit_transform(corpus)

    def search_document(self, query: str, top_k: int = 3, score_threshold: float = 0.1,
                        user_id=None) -> list:
        """
        Query the indexed document chunks using Cosine Similarity.
        Returns top k matched chunks with relevance scores and citation details.
        """
        index = self._index(user_id)
        if not index["chunks"] or not index["vectorizer"] or not query.strip():
            return []

        processed_query = preprocessor.preprocess_for_vectorizer(query)
        if not processed_query:
            return []

        query_vec = index["vectorizer"].transform([processed_query])
        similarities = cosine_similarity(query_vec, index["vectors"])[0]

        top_indices = similarities.argsort()[::-1][:top_k]

        results = []
        for idx in top_indices:
            score = float(similarities[idx])
            if score >= score_threshold:
                chunk = index["chunks"][idx].copy()
                chunk["score"] = round(score, 4)
                results.append(chunk)

        return results

document_qa = DocumentQAEngine()
