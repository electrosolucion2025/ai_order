from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker
from sqlalchemy import event
from datetime import datetime, timedelta
from app.models.base import Base
from app.core.dependencies import engine


class ProcessedMessage(Base):
    __tablename__ = "processed_messages"

    message_id = Column(String, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False)  # Relación con el tenant
    created_at = Column(DateTime(timezone=True), server_default=func.now())



# Function to delete old records
def delete_old_records(session, *args, **kwargs):
    expiration_date = datetime.now() - timedelta(
        days=1
    )  # Adjust the timedelta as needed
    session.query(ProcessedMessage).filter(
        ProcessedMessage.created_at < expiration_date
    ).delete()
    session.commit()


# Set up event listener for automatic deletion
Session = sessionmaker(bind=engine)
event.listen(Session, "before_flush", delete_old_records)
