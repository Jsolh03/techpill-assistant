"""Gestion de documentos (PDFs) adjuntos a una conversacion."""
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from .. import models, pdf_service, schemas
from ..database import get_db

router = APIRouter(prefix="/api", tags=["documentos"])

# Limite de tamano del PDF (10 MB) para no aceptar archivos enormes.
MAX_PDF_BYTES = 10 * 1024 * 1024


@router.post(
    "/conversations/{conversation_id}/documents",
    response_model=schemas.DocumentOut,
    status_code=201,
)
async def upload_document(
    conversation_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Sube un PDF, extrae su texto y lo asocia a la conversacion."""
    conv = db.get(models.Conversation, conversation_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")

    if not (file.filename or "").lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Solo se aceptan archivos PDF")

    data = await file.read()
    if len(data) > MAX_PDF_BYTES:
        raise HTTPException(status_code=413, detail="El PDF supera el limite de 10 MB")

    try:
        text = pdf_service.extract_text(data)
    except pdf_service.PdfError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    doc = models.Document(
        conversation_id=conv.id,
        filename=file.filename,
        char_count=len(text),
        content=text,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return doc


@router.get(
    "/conversations/{conversation_id}/documents",
    response_model=list[schemas.DocumentOut],
)
def list_documents(conversation_id: int, db: Session = Depends(get_db)):
    """Lista los documentos adjuntos a una conversacion."""
    conv = db.get(models.Conversation, conversation_id)
    if conv is None:
        raise HTTPException(status_code=404, detail="Conversacion no encontrada")
    return conv.documents


@router.delete("/documents/{document_id}", status_code=204)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Borra un documento adjunto."""
    doc = db.get(models.Document, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Documento no encontrado")
    db.delete(doc)
    db.commit()
