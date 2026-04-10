from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.position import Position, PositionStatus
from app.schemas.position import PositionCreate, PositionUpdate, PositionResponse

router = APIRouter(prefix="/api/positions", tags=["positions"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=PositionResponse)
def create_position(body: PositionCreate, db: Session = Depends(get_db)):
    if not body.title.strip():
        raise HTTPException(status_code=422, detail="Title cannot be empty")
    position = Position(**body.model_dump())
    db.add(position)
    db.commit()
    db.refresh(position)
    return _to_response(position)


@router.get("", response_model=list[PositionResponse])
def list_positions(db: Session = Depends(get_db)):
    positions = db.query(Position).order_by(Position.updated_at.desc()).all()
    return [_to_response(p) for p in positions]


@router.get("/{position_id}", response_model=PositionResponse)
def get_position(position_id: int, db: Session = Depends(get_db)):
    position = db.get(Position, position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    return _to_response(position)


@router.patch("/{position_id}", response_model=PositionResponse)
def update_position(
    position_id: int, body: PositionUpdate, db: Session = Depends(get_db)
):
    position = db.get(Position, position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    update_data = body.model_dump(exclude_unset=True)
    if "status" in update_data:
        update_data["status"] = PositionStatus(update_data["status"])
    for key, value in update_data.items():
        setattr(position, key, value)
    db.commit()
    db.refresh(position)
    return _to_response(position)


@router.delete("/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_position(position_id: int, db: Session = Depends(get_db)):
    position = db.get(Position, position_id)
    if not position:
        raise HTTPException(status_code=404, detail="Position not found")
    db.delete(position)
    db.commit()


def _to_response(position: Position) -> dict:
    return {
        "id": position.id,
        "title": position.title,
        "department": position.department,
        "jd_text": position.jd_text,
        "core_competencies": position.core_competencies,
        "preferences": position.preferences,
        "status": position.status.value,
        "created_at": position.created_at,
        "updated_at": position.updated_at,
        "candidate_count": len(position.candidates) if position.candidates else 0,
    }
