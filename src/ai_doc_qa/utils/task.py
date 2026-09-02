from fastapi import BackgroundTasks

from ai_doc_qa.db import AsyncSessionLocal
from ai_doc_qa.services.ingestion import IngestionService


async def run_ingestion(
    document_id: int,
    file_path: str,
    user_id: int,
) -> None:

    async with AsyncSessionLocal() as db:
        ingestion_service = IngestionService(db)

        await ingestion_service.process_document(
            file_path=file_path,
            document_id=document_id,
            user_id=user_id,
        )


def run_ingestion_service(
    background_tasks: BackgroundTasks,
    document_id: int,
    file_path: str,
    user_id: int,
) -> None:

    background_tasks.add_task(
        run_ingestion,
        document_id=document_id,
        file_path=file_path,
        user_id=user_id,
    )
