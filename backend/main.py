from fastapi import FastAPI, Body, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import SessionLocal, engine, Base
from models_items import Item
from models_slots import Slot
from models_slot_allowed import SlotAllowedItem

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="db4tarkov CN API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)


# ---------------------------------------------------
# Database
# ---------------------------------------------------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ---------------------------------------------------
# Weapons
# ---------------------------------------------------

@app.get("/guns")
def get_guns(db: Session = Depends(get_db)):
    guns = db.query(Item).filter(Item.is_weapon == True).all()

    return [
        {
            "id": gun.id,
            "name": gun.name,
            "base_ergo": gun.base_ergonomics,
            "weight": gun.weight,
        }
        for gun in guns
    ]


# ---------------------------------------------------
# Slots
# ---------------------------------------------------

@app.get("/items/{item_id}/slots")
def get_item_slots(item_id: str, db: Session = Depends(get_db)):
    return db.query(Slot).filter(Slot.parent_item_id == item_id).all()


# ---------------------------------------------------
# Allowed Items
# ---------------------------------------------------

@app.get("/slots/{slot_id}/allowed-items")
def get_allowed_items(slot_id: str, db: Session = Depends(get_db)):
    allowed = db.query(SlotAllowedItem).filter(
        SlotAllowedItem.slot_id == slot_id
    ).all()

    ids = [a.allowed_item_id for a in allowed]

    items = db.query(Item).filter(Item.id.in_(ids)).all()

    return [
        {
            "id": item.id,
            "name": item.name,
            "weight": item.weight,
            "ergonomics_modifier": item.ergonomics_modifier,
        }
        for item in items
    ]


# ---------------------------------------------------
# Evo Ergo Calculation (TRUE DB4TARKOV MODEL)
# ---------------------------------------------------

@app.post("/build/calculate")
def calculate_build(
    base_item_id: str = Body(...),
    attachment_ids: List[str] | None = Body(default=None),
    db: Session = Depends(get_db),
):

    base_item = db.query(Item).filter(Item.id == base_item_id).first()

    if not base_item:
        raise HTTPException(status_code=404, detail="Base item not found")

    # -------------------------
    # Base values
    # -------------------------

    base_ergo = base_item.base_ergonomics or 0
    base_weight = base_item.weight or 0

    total_ergo = base_ergo
    total_weight = base_weight

    # -------------------------
    # Apply attachments
    # -------------------------

    if attachment_ids:
        attachments = db.query(Item).filter(
            Item.id.in_(attachment_ids)
        ).all()

        for att in attachments:
            total_ergo += att.ergonomics_modifier or 0
            total_weight += att.weight or 0

    # -------------------------
    # Gear modifier (currently 0)
    # -------------------------

    b = 0  # equipment modifier (future expansion)

    # -------------------------
    # Effective Ergo
    # -------------------------

    E = total_ergo * (1 + b)

    # -------------------------
    # Sweetspot curve (KG)
    # -------------------------

    KG = (
        0.0007556 * (E ** 2)
        + 0.02736 * E
        + 2.9159
    )

    # -------------------------
    # EvoWeight
    # -------------------------

    evo_weight = total_weight - KG

    # -------------------------
    # Overswing
    # -------------------------

    overswing = evo_weight > 0

    # -------------------------
    # EvoErgoDelta (EED)
    # -------------------------

    eed = -15 * evo_weight

    return {
        "base_ergo": round(base_ergo, 2),
        "base_weight": round(base_weight, 3),
        "total_weight": round(total_weight, 3),
        "overswing": overswing,
        "evo_ergo_delta": round(eed, 2),
    }