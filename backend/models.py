"""
SQLAlchemy ORM models for the Healing Agent database.
Three tables: runs, fixes, timeline_events.
"""
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from database import Base


class Run(Base):
    """A single healing agent run (job)."""
    __tablename__ = "runs"

    id = Column(String, primary_key=True, index=True)  # UUID job_id
    repo_url = Column(String, nullable=False)
    team_name = Column(String, nullable=False)
    leader_name = Column(String, nullable=False)
    branch_name = Column(String, nullable=False)

    # Status tracking
    status = Column(String, default="queued")  # queued|cloning|testing|analyzing|fixing|pushing|done|failed
    progress = Column(Integer, default=0)
    current_agent = Column(String, default="Initializing")
    error_message = Column(Text, default="")

    # Metrics
    errors_found = Column(Integer, default=0)
    errors_fixed = Column(Integer, default=0)
    commit_count = Column(Integer, default=0)
    retry_count = Column(Integer, default=0)
    retry_limit = Column(Integer, default=5)

    # Results
    verify_passed = Column(Boolean, default=False)
    repo_language = Column(String, default="unknown")
    push_success = Column(Boolean, default=False)
    ci_status = Column(String, default="PENDING")  # PENDING|PASSED|FAILED

    # Scoring
    score_total = Column(Integer, default=0)
    score_base = Column(Integer, default=100)
    score_speed_bonus = Column(Integer, default=0)
    score_efficiency_penalty = Column(Integer, default=0)
    elapsed_seconds = Column(Float, default=0.0)

    # Timestamps
    start_time = Column(Float)  # epoch
    timestamp = Column(String)  # ISO 8601
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    # Raw output (can be large)
    raw_test_output = Column(Text, default="")

    # Relationships
    fixes = relationship("Fix", back_populates="run", cascade="all, delete-orphan",
                         lazy="joined")
    timeline_events = relationship("TimelineEvent", back_populates="run",
                                   cascade="all, delete-orphan", lazy="joined",
                                   order_by="TimelineEvent.id")

    def to_dict(self):
        """Convert to dictionary matching the existing API response format."""
        return {
            "job_id": self.id,
            "repo_url": self.repo_url,
            "repo": self.repo_url.split("github.com/")[-1].replace(".git", "") if "github.com/" in self.repo_url else self.repo_url,
            "team_name": self.team_name,
            "leader_name": self.leader_name,
            "branch_name": self.branch_name,
            "status": self.status,
            "progress": self.progress,
            "current_agent": self.current_agent,
            "error_message": self.error_message,
            "errors_found": self.errors_found,
            "errors_fixed": self.errors_fixed,
            "commit_count": self.commit_count,
            "retry_count": self.retry_count,
            "retry_limit": self.retry_limit,
            "verify_passed": self.verify_passed,
            "repo_language": self.repo_language,
            "push_success": self.push_success,
            "ci_status": self.ci_status,
            "start_time": self.start_time,
            "timestamp": self.timestamp,
            "fixes": [f.to_dict() for f in self.fixes],
            "timeline": [t.to_dict() for t in self.timeline_events],
            "score": {
                "total": self.score_total,
                "base": self.score_base,
                "speed_bonus": self.score_speed_bonus,
                "efficiency_penalty": self.score_efficiency_penalty,
                "elapsed_seconds": self.elapsed_seconds,
            },
        }


class Fix(Base):
    """A single fix applied during a run."""
    __tablename__ = "fixes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True)

    fix_id = Column(String)  # e.g. "LINTING_src_utils_py_15"
    type = Column(String, nullable=False)  # LINTING|SYNTAX|LOGIC|TYPE_ERROR|IMPORT|INDENTATION
    file = Column(String, nullable=False)
    line = Column(Integer, default=0)
    message = Column(Text, default="")
    formatted = Column(Text, default="")  # Full output string for dashboard
    fix_description = Column(Text, default="")
    commit_message = Column(String, default="")
    status = Column(String, default="pending")  # pending|fixed|failed

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship
    run = relationship("Run", back_populates="fixes")

    def to_dict(self):
        """Convert to dictionary matching the existing fix format."""
        return {
            "id": self.fix_id,
            "type": self.type,
            "file": self.file,
            "line": self.line,
            "message": self.message,
            "formatted": self.formatted,
            "fix_description": self.fix_description,
            "commit_message": self.commit_message,
            "status": self.status,
        }


class TimelineEvent(Base):
    """A CI/CD timeline event during a run."""
    __tablename__ = "timeline_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey("runs.id", ondelete="CASCADE"), nullable=False, index=True)

    agent = Column(String, nullable=False)  # Clone Agent, Test Agent, etc.
    msg = Column(Text, default="")
    timestamp = Column(String)  # ISO 8601
    iteration = Column(Integer, default=0)
    passed = Column(Boolean, default=False)

    # Relationship
    run = relationship("Run", back_populates="timeline_events")

    def to_dict(self):
        """Convert to dictionary matching the existing timeline format."""
        return {
            "agent": self.agent,
            "msg": self.msg,
            "timestamp": self.timestamp,
            "iteration": self.iteration,
            "passed": self.passed,
        }
