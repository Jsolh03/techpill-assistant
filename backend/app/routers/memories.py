"""CRUD de la memoria global (datos que el usuario pide recordar)."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/memories", tags=["memoria"])


@router.get("", response_model=list[schemas.MemoryOut])
def list_memories(db: Session = Depends(get_db)):
    """Lista los datos recordados, del mas reciente al mas antiguo."""
    stmt = select(models.Memory).order_by(models.Memory.created_at.desc())
    return db.scalars(stmt).all()


@router.post("", response_model=schemas.MemoryOut, status_code=201)
def create_memory(payload: schemas.MemoryCreate, db: Session = Depends(get_db)):
    mem = models.Memory(content=payload.content.strip())
    db.add(mem)
    db.commit()
    db.refresh(mem)
    return mem


@router.delete("/{memory_id}", status_code=204)
def delete_memory(memory_id: int, db: Session = Depends(get_db)):
    mem = db.get(models.Memory, memory_id)
    if mem is None:
        raise HTTPException(status_code=404, detail="Recuerdo no encontrado")
    db.delete(mem)
    db.commit()
