"""
Crypto portfolio service for managing user cryptocurrency holdings
"""

import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.crypto_portfolio import CryptoPortfolio
from app.schemas.crypto import (
    CryptoPortfolioItem, 
    CryptoPortfolioCreate, 
    CryptoPortfolioUpdate,
    CryptoPortfolioResponse
)
from app.services.market_data import MarketDataService
from app.utils.data_parser import DataParser

logger = logging.getLogger(__name__)


class CryptoPortfolioService:
    """Service for managing crypto portfolio operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.market_service = MarketDataService()
    
    async def get_user_portfolio(self, user_id: int) -> CryptoPortfolioResponse:
        """Get user's complete crypto portfolio with current prices."""
        portfolio_items = self.db.query(CryptoPortfolio).filter(
            CryptoPortfolio.user_id == user_id
        ).all()
        
        if not portfolio_items:
            return CryptoPortfolioResponse(
                portfolio=[],
                total_value=0.0,
                total_profit_loss=0.0,
                total_profit_loss_percentage=0.0
            )
        
        # Update current prices for all portfolio items
        portfolio_with_prices = []
        total_value = 0.0
        total_investment = 0.0
        
        for item in portfolio_items:
            try:
                # Get current price
                rate_data = await self.market_service.get_crypto_exchange_rate(item.symbol, "USD")
                current_price = DataParser.parse_crypto_exchange_rate(rate_data).exchange_rate
                
                # Calculate values
                total_value_item = item.amount * current_price
                investment = item.amount * (item.average_buy_price or 0)
                profit_loss = total_value_item - investment if item.average_buy_price else None
                profit_loss_percentage = (profit_loss / investment * 100) if investment > 0 and profit_loss is not None else None
                
                # Update database record
                item.current_price = current_price
                item.total_value = total_value_item
                item.profit_loss = profit_loss
                item.profit_loss_percentage = profit_loss_percentage
                
                portfolio_item = CryptoPortfolioItem(
                    symbol=item.symbol,
                    name=item.name or item.symbol,
                    amount=item.amount,
                    average_buy_price=item.average_buy_price,
                    current_price=current_price,
                    total_value=total_value_item,
                    profit_loss=profit_loss,
                    profit_loss_percentage=profit_loss_percentage
                )
                
                portfolio_with_prices.append(portfolio_item)
                total_value += total_value_item
                total_investment += investment
                
            except Exception as e:
                logger.error(f"Error updating price for {item.symbol}: {e}")
                # Add item with existing data if price update fails
                portfolio_item = CryptoPortfolioItem(
                    symbol=item.symbol,
                    name=item.name or item.symbol,
                    amount=item.amount,
                    average_buy_price=item.average_buy_price,
                    current_price=item.current_price,
                    total_value=item.total_value,
                    profit_loss=item.profit_loss,
                    profit_loss_percentage=item.profit_loss_percentage
                )
                portfolio_with_prices.append(portfolio_item)
                if item.total_value:
                    total_value += item.total_value
                if item.average_buy_price:
                    total_investment += item.amount * item.average_buy_price
        
        # Commit price updates
        self.db.commit()
        
        # Calculate total profit/loss
        total_profit_loss = total_value - total_investment
        total_profit_loss_percentage = (total_profit_loss / total_investment * 100) if total_investment > 0 else 0.0
        
        return CryptoPortfolioResponse(
            portfolio=portfolio_with_prices,
            total_value=total_value,
            total_profit_loss=total_profit_loss,
            total_profit_loss_percentage=total_profit_loss_percentage
        )
    
    def add_portfolio_item(self, user_id: int, item_data: CryptoPortfolioCreate) -> CryptoPortfolio:
        """Add a new crypto to user's portfolio."""
        # Check if item already exists
        existing_item = self.db.query(CryptoPortfolio).filter(
            and_(
                CryptoPortfolio.user_id == user_id,
                CryptoPortfolio.symbol == item_data.symbol.upper()
            )
        ).first()
        
        if existing_item:
            # Update existing item (average the buy prices)
            if item_data.average_buy_price and existing_item.average_buy_price:
                total_amount = existing_item.amount + item_data.amount
                total_investment = (existing_item.amount * existing_item.average_buy_price) + \
                                 (item_data.amount * item_data.average_buy_price)
                new_average_price = total_investment / total_amount
                existing_item.average_buy_price = new_average_price
            
            existing_item.amount += item_data.amount
            self.db.commit()
            return existing_item
        
        # Create new portfolio item
        portfolio_item = CryptoPortfolio(
            user_id=user_id,
            symbol=item_data.symbol.upper(),
            amount=item_data.amount,
            average_buy_price=item_data.average_buy_price
        )
        
        self.db.add(portfolio_item)
        self.db.commit()
        self.db.refresh(portfolio_item)
        
        return portfolio_item
    
    def update_portfolio_item(self, user_id: int, symbol: str, update_data: CryptoPortfolioUpdate) -> Optional[CryptoPortfolio]:
        """Update an existing portfolio item."""
        portfolio_item = self.db.query(CryptoPortfolio).filter(
            and_(
                CryptoPortfolio.user_id == user_id,
                CryptoPortfolio.symbol == symbol.upper()
            )
        ).first()
        
        if not portfolio_item:
            return None
        
        if update_data.amount is not None:
            portfolio_item.amount = update_data.amount
        
        if update_data.average_buy_price is not None:
            portfolio_item.average_buy_price = update_data.average_buy_price
        
        self.db.commit()
        self.db.refresh(portfolio_item)
        
        return portfolio_item
    
    def remove_portfolio_item(self, user_id: int, symbol: str) -> bool:
        """Remove a crypto from user's portfolio."""
        portfolio_item = self.db.query(CryptoPortfolio).filter(
            and_(
                CryptoPortfolio.user_id == user_id,
                CryptoPortfolio.symbol == symbol.upper()
            )
        ).first()
        
        if not portfolio_item:
            return False
        
        self.db.delete(portfolio_item)
        self.db.commit()
        
        return True
    
    def get_portfolio_item(self, user_id: int, symbol: str) -> Optional[CryptoPortfolio]:
        """Get a specific portfolio item."""
        return self.db.query(CryptoPortfolio).filter(
            and_(
                CryptoPortfolio.user_id == user_id,
                CryptoPortfolio.symbol == symbol.upper()
            )
        ).first()
