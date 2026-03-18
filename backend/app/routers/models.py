from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db.database import get_db

router = APIRouter()


@router.get("/api/models")
def get_all_models(db: Session = Depends(get_db)):
    query = text("""
        SELECT b.name as brand, vm.name as model,
               vm.body_type, vm.segment
        FROM vehicle_models vm
        JOIN brands b ON b.id = vm.brand_id
        ORDER BY b.name, vm.name
    """)
    results = db.execute(query).fetchall()

    return [
        {
            "brand": row.brand,
            "model": row.model,
            "body_type": row.body_type,
            "segment": row.segment,
        }
        for row in results
    ]
