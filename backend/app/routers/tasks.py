"""CRUD de tareas / recordatorios personales."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/tasks", tags=["tareas"])

# Orden de prioridad para listar (alta primero).
_PRIORIDAD_ORDEN = {"alta": 0, "media": 1, "baja": 2}


def _get_or_404(db: Session, task_id: int) -> models.Task:
    task = db.get(models.Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    return task


@router.get("", response_model=list[schemas.TaskOut])
def list_tasks(db: Session = Depends(get_db)):
    """Lista las tareas: pendientes primero, luego por fecha y prioridad."""
    tasks = list(db.scalars(select(models.Task)).all())
    # Orden: no hechas antes que hechas; con fecha antes que sin fecha;
    # por fecha ascendente; y por prioridad (alta -> baja).
    tasks.sort(
        key=lambda t: (
            t.done,
            t.due_date is None,
            t.due_date or date.max,
            _PRIORIDAD_ORDEN.get(t.priority, 1),
        )
    )
    return tasks


@router.post("", response_model=schemas.TaskOut, status_code=201)
def create_task(payload: schemas.TaskCreate, db: Session = Depends(get_db)):
    task = models.Task(
        title=payload.title, due_date=payload.due_date, priority=payload.priority
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=schemas.TaskOut)
def update_task(task_id: int, payload: schemas.TaskUpdate, db: Session = Depends(get_db)):
    """Actualiza solo los campos enviados (marcar como hecha, cambiar fecha, etc.)."""
    task = _get_or_404(db, task_id)
    cambios = payload.model_dump(exclude_unset=True)
    for campo, valor in cambios.items():
        setattr(task, campo, valor)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = _get_or_404(db, task_id)
    db.delete(task)
    db.commit()
