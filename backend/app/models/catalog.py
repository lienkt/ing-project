from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.database.session import Base

class Bank(Base):
    __tablename__ = "banks"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    normalized_name: Mapped[str] = mapped_column(String(120), unique=True)

class ProjectOption(Base):
    __tablename__ = "projects"
    key: Mapped[str] = mapped_column(String(40), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
