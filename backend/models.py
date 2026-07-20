from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, DECIMAL, ForeignKey, Enum
from sqlalchemy.orm import relationship
from database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100))

    interviews = relationship("Interview", back_populates="user")


class Interview(Base):
    __tablename__ = "interviews"

    interview_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    interview_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    overall_score = Column(DECIMAL(4, 2))
    status = Column(Enum("in_progress", "completed"), default="in_progress")
    questions_json = Column(Text)
    user = relationship("User", back_populates="interviews")
    answers = relationship("Answer", back_populates="interview")


class Question(Base):
    __tablename__ = "questions"

    question_id = Column(Integer, primary_key=True, autoincrement=True)
    question_text = Column(Text)
    topic = Column(String(50))
    difficulty = Column(Enum("Easy", "Medium", "Hard"))

    answers = relationship("Answer", back_populates="question")


class Answer(Base):
    __tablename__ = "answers"

    answer_id = Column(Integer, primary_key=True, autoincrement=True)
    interview_id = Column(Integer, ForeignKey("interviews.interview_id"))
    question_id = Column(Integer, ForeignKey("questions.question_id"))
    answer_text = Column(Text)
    score = Column(DECIMAL(4, 2))
    feedback = Column(Text)

    interview = relationship("Interview", back_populates="answers")
    question = relationship("Question", back_populates="answers")