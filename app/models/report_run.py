"""
ReportRun Model - Report execution history

Tracks each execution of a saved report with results and timing.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.database import Base


class ReportRun(Base):
    """
    ReportRun - Execution history for SavedReport
    
    One record per report execution, storing parameters, results, and metadata.
    """
    __tablename__ = "report_runs"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    report_id = Column(Integer, ForeignKey("saved_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    executed_by = Column(Integer, ForeignKey("tenant_users.id", ondelete="SET NULL"), nullable=True)
    
    # Execution details
    executed_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    status = Column(String(50), nullable=False)  # "success", "failed", "timeout"
    
    # Results
    row_count = Column(Integer, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    output_file_path = Column(String(500), nullable=True)  # Path to generated CSV/Excel
    
    # Relationships
    report = relationship("SavedReport", back_populates="report_runs")
    tenant = relationship("Tenant", back_populates="report_runs")
    executor = relationship("TenantUser", foreign_keys=[executed_by])
    
    def __repr__(self):
        return f"<ReportRun {self.id} Report:{self.report_id} Status:{self.status}>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": self.id,
            "report_id": self.report_id,
            "tenant_id": self.tenant_id,
            "executed_by": self.executed_by,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "status": self.status,
            "row_count": self.row_count,
            "execution_time_ms": self.execution_time_ms,
            "error_message": self.error_message,
            "output_file_path": self.output_file_path,
        }
