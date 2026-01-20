from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Discount, Coupon, PriceRule, TaxRule
from app.schemas.pricing import CouponCreate, DiscountCreate, PriceRuleCreate, TaxRuleCreate

router = APIRouter(prefix="/pricing", tags=["Pricing & Promotions"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------
# Discounts
# -------------------------
@router.post("/discounts")
def create_discount(data: DiscountCreate, db: Session = Depends(get_db)):
    discount = Discount(**data.dict())
    db.add(discount)
    db.commit()
    db.refresh(discount)
    return discount

@router.get("/discounts")
def list_discounts(db: Session = Depends(get_db)):
    return db.query(Discount).all()

# -------------------------
# Coupons
# -------------------------
@router.post("/coupons")
def create_coupon(data: CouponCreate, db: Session = Depends(get_db)):
    coupon = Coupon(**data.dict())
    db.add(coupon)
    db.commit()
    db.refresh(coupon)
    return coupon

@router.get("/coupons")
def list_coupons(db: Session = Depends(get_db)):
    return db.query(Coupon).all()

# -------------------------
# Price Rules
# -------------------------
@router.post("/price-rules")
def create_price_rule(data: PriceRuleCreate, db: Session = Depends(get_db)):
    rule = PriceRule(**data.dict())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule

@router.get("/price-rules")
def list_price_rules(db: Session = Depends(get_db)):
    return db.query(PriceRule).all()

# -------------------------
# Tax Rules
# -------------------------
@router.post("/tax-rules")
def create_tax_rule(data: TaxRuleCreate, db: Session = Depends(get_db)):
    rule = TaxRule(**data.dict())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule

@router.get("/tax-rules")
def list_tax_rules(db: Session = Depends(get_db)):
    return db.query(TaxRule).all()
