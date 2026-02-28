from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()

# Association table for many-to-many relationship between users and skills
user_skills = Table(
    'user_skills',
    Base.metadata,
    Column('user_id', UUID(as_uuid=True), ForeignKey('app_users.id'), primary_key=True),
    Column('skill_id', UUID(as_uuid=True), ForeignKey('skills.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "app_users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    title = Column(String)
    company = Column(String)
    hashed_password = Column(String, nullable=False)
    helped_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    skills = relationship("Skill", secondary=user_skills, back_populates="users")
    help_requests_created = relationship("HelpRequest", foreign_keys="HelpRequest.requester_id", back_populates="requester")
    help_requests_helping = relationship("HelpRequest", foreign_keys="HelpRequest.helper_id", back_populates="helper")

class Skill(Base):
    __tablename__ = "skills"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    users = relationship("User", secondary=user_skills, back_populates="skills")

class HelpRequest(Base):
    __tablename__ = "help_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    skill_id = Column(UUID(as_uuid=True), ForeignKey('skills.id'), nullable=False)
    description = Column(Text)
    status = Column(String, default="open")  # open, in_progress, completed, cancelled
    requester_id = Column(UUID(as_uuid=True), ForeignKey('app_users.id'), nullable=False)
    helper_id = Column(UUID(as_uuid=True), ForeignKey('app_users.id'), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    requester = relationship("User", foreign_keys=[requester_id], back_populates="help_requests_created")
    helper = relationship("User", foreign_keys=[helper_id], back_populates="help_requests_helping")
    skill = relationship("Skill")