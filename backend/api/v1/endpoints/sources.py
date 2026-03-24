from fastapi import APIRouter

router = APIRouter()

@router.get("/{source_id}")
async def get_source(source_id: str):
    return {"source_id": source_id, "content": "Kaynak içeriği buraya gelecek."}
