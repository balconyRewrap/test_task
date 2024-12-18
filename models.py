from sqlalchemy import BigInteger, Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, relationship

MAXIMUM_NUMBER_LENGTH = 15

class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(MAXIMUM_NUMBER_LENGTH), nullable=False)
    tasks = relationship('Task', back_populates='user')
    
    def __repr__(self):
        return f"User(id={self.id}, name={self.name}, phone={self.phone})"



class Task(Base):
    __tablename__ = 'tasks'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    is_completed = Column(Boolean, default=False)
    user_id = Column(BigInteger, ForeignKey('users.id'))
    user = relationship('User', back_populates='tasks')
    tags = relationship('Tag', secondary='task_tags', back_populates='tasks')




class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    tasks = relationship('Task', secondary='task_tags', back_populates='tags')

    def __str__(self) -> str:
        return str(self.name)

    def __repr__(self):
        return f"Tag(id={self.id}, name={self.name})"



class TaskTag(Base):
    __tablename__ = 'task_tags'

    task_id = Column(Integer, ForeignKey('tasks.id', ondelete='CASCADE'), primary_key=True)
    tag_id = Column(Integer, ForeignKey('tags.id', ondelete='CASCADE'), primary_key=True)
