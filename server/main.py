from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
import secrets
from datetime import datetime

from models import Base, User, CheckInLog
from mining import can_checkin, calculate_reward, get_current_rate

engine = create_engine(
    "sqlite:///ice_sim.db",
    connect_args={"check_same_thread": False}
)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


app = FastAPI(title="Ice Mining Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class RegisterInput(BaseModel):
    username: str
    referred_by: str | None = None


@app.get("/")
def root():
    return {"status": "ok", "message": "Ice Mining Server is running"}


@app.post("/register")
def register(data: RegisterInput, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(400, "این نام کاربری قبلاً ثبت شده")

    if data.referred_by:
        referrer = db.query(User).filter(
            User.referral_code == data.referred_by
        ).first()
        if not referrer:
            raise HTTPException(404, "کد معرف نامعتبر است")

    code = secrets.token_urlsafe(6)
    user = User(
        username=data.username,
        referral_code=code,
        referred_by=data.referred_by,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"message": "ثبت‌نام موفق", "your_code": code, "username": user.username}


@app.post("/kyc/{username}")
def verify_kyc(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(404, "کاربر یافت نشد")
    user.kyc_verified = True
    db.commit()
    return {"message": "احراز هویت تایید شد"}


@app.post("/checkin/{username}")
def checkin(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(404, "کاربر یافت نشد")
    if not user.kyc_verified:
        raise HTTPException(403, "ابتدا KYC را انجام دهید")

    ok, remaining = can_checkin(user.last_checkin)
    if not ok:
        hours = remaining.total_seconds() // 3600
        minutes = (remaining.total_seconds() % 3600) // 60
        raise HTTPException(
            429,
            f"هنوز زمان نرسیده. {int(hours)} ساعت و {int(minutes)} دقیقه مانده"
        )

    team_size = db.query(User).filter(
        User.referred_by == user.referral_code
    ).count()
    total_checkins = db.query(CheckInLog).count()

    reward = calculate_reward(team_size, total_checkins)

    user.balance += reward
    user.last_checkin = datetime.utcnow()
    db.add(CheckInLog(user_id=user.id, amount=reward))
    db.commit()

    return {
        "message": "چک‌این موفق",
        "earned": reward,
        "balance": round(user.balance, 4),
        "team_size": team_size,
    }


@app.get("/user/{username}")
def get_user(username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(404, "کاربر یافت نشد")

    team = db.query(User).filter(
        User.referred_by == user.referral_code
    ).count()

    can_do = True
    remaining_text = "آماده"
    ok, remaining = can_checkin(user.last_checkin)
    if not ok:
        can_do = False
        h = int(remaining.total_seconds() // 3600)
        m = int((remaining.total_seconds() % 3600) // 60)
        remaining_text = f"{h} ساعت و {m} دقیقه"

    return {
        "username": user.username,
        "balance": round(user.balance, 4),
        "referral_code": user.referral_code,
        "team_size": team,
        "last_checkin": user.last_checkin.isoformat() if user.last_checkin else None,
        "kyc_verified": user.kyc_verified,
        "can_checkin": can_do,
        "remaining": remaining_text,
    }


@app.get("/stats")
def stats(db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    total_checkins = db.query(CheckInLog).count()
    return {
        "total_users": total_users,
        "total_checkins": total_checkins,
        "current_rate": get_current_rate(total_checkins),
    }