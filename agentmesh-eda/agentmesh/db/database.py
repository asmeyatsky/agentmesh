from sqlalchemy import create_engine, Column, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://user:password@postgres/agentmesh_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)


class Message(Base):
    __tablename__ = "messages"

    id = Column(String, primary_key=True, index=True)
    tenant_id = Column(String, index=True)
    payload = Column(Text)
    # Add other fields as needed, e.g., timestamp, routing info


def init_db():
    Base.metadata.create_all(bind=engine)
