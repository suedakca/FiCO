from typing import List, Dict, Any
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, UnstructuredHTMLLoader
import os

class IngestionPipeline:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
            is_separator_regex=False,
        )

    def load_and_split(self, file_path: str) -> List[Dict[str, Any]]:
        """Load document and split into chunks."""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == ".pdf":
            loader = PyPDFLoader(file_path)
        elif ext in [".html", ".htm"]:
            loader = UnstructuredHTMLLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}")

        documents = loader.load()
        chunks = self.text_splitter.split_documents(documents)
        
        return [
            {
                "text": chunk.page_content,
                "metadata": {
                    **chunk.metadata,
                    "source_path": file_path
                }
            }
            for chunk in chunks
        ]

ingestion_pipeline = IngestionPipeline()
