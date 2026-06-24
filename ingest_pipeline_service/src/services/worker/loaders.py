from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    PyMuPDFLoader,
    Docx2txtLoader,
    BSHTMLLoader,
)
from typing import List
from pathlib import Path

from schemas import FileRecordInfo



def load_documents(
    file_path: Path,
    file_record: FileRecordInfo,
) -> List[Document]:
    """Загружает документы в зависимости от типа файла"""

    match file_record.ext:
        case "pdf":
            # loader = PyPDFLoader(file_path=file_path)
            loader = PyMuPDFLoader(file_path)
            return list(loader.lazy_load())

        case "txt" | "md":
            try:
                text = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                text = file_path.read_text(encoding="latin-1")

            return [
                Document(
                    page_content=text,
                    metadata={
                        "file_id": file_record.id,
                        "filename": file_record.filename,
                        "ext": file_record.ext,
                    },
                )
            ]

        case "docx":
            loader = Docx2txtLoader(file_path)
            documents = loader.load()
            for doc in documents:
                doc.metadata.update(
                    {
                    "file_id": file_record.id,
                    "filename": file_record.filename,
                    "ext": file_record.ext,
                    }
                )
            return documents

        case "html":
            loader = BSHTMLLoader(file_path)
            documents = loader.load()
            for doc in documents:
                doc.metadata.update(
                {
                    "file_id": file_record.id,
                    "filename": file_record.filename,
                    "ext": file_record.ext,
                }
                )
            return documents

        case _:
            raise ValueError(f"Неподдерживаемый тип файла: {file_record.ext}")