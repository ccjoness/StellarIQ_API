"""
Crypto portfolio model for tracking user's cryptocurrency holdings
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, String, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CryptoPortfolio(Base):
    """User crypto portfolio model"""
    
    __tablename__ = "crypto_portfolio"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # User identification
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    
    # Crypto identification
    symbol: Mapped[str] = mapped_column(String(10), index=True)
    name: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Portfolio data
    amount: Mapped[float] = mapped_column(Float)  # Amount of crypto owned
    average_buy_price: Mapped[Optional[float]] = mapped_column(Float)  # Average purchase price in USD
    
    # Calculated fields (updated periodically)
    current_price: Mapped[Optional[float]] = mapped_column(Float)  # Current market price
    total_value: Mapped[Optional[float]] = mapped_column(Float)  # amount * current_price
    profit_loss: Mapped[Optional[float]] = mapped_column(Float)  # total_value - (amount * average_buy_price)
    profit_loss_percentage: Mapped[Optional[float]] = mapped_column(Float)  # (profit_loss / investment) * 100
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    last_price_update: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    
    # Relationships
    # user: Mapped["User"] = relationship("User", back_populates="crypto_portfolio")
    
    # Ensure unique combination of user and symbol
    __table_args__ = (
        UniqueConstraint('user_id', 'symbol', name='_user_symbol_uc'),
    )
    
    def __repr__(self) -> str:
        return f"<CryptoPortfolio(user_id={self.user_id}, symbol='{self.symbol}', amount={self.amount})>"
