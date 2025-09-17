from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime
from app.core.database import get_db
from app.core.auth import get_current_active_user
from app.models.user import User
from app.models.favorite import AssetType
from app.schemas.analysis import (
    MarketAnalysisResult, AnalysisThresholds, BulkAnalysisRequest,
    BulkAnalysisResponse, WatchlistAnalysis, MarketScreenerRequest,
    ScreenerResult, MarketCondition
)
from app.services.market_analysis import MarketAnalysisService
from app.services.favorites import FavoritesService
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analysis", tags=["Market Analysis"])

@router.get("/symbol/{symbol}", response_model=MarketAnalysisResult)
async def analyze_symbol(
    symbol: str,
    asset_type: Optional[str] = Query("stock", description="stock or crypto"),
    rsi_overbought: Optional[float] = Query(70.0, description="RSI overbought threshold"),
    rsi_oversold: Optional[float] = Query(30.0, description="RSI oversold threshold"),
    stoch_overbought: Optional[float] = Query(80.0, description="Stochastic overbought threshold"),
    stoch_oversold: Optional[float] = Query(20.0, description="Stochastic oversold threshold"),
    current_user: User = Depends(get_current_active_user)
):
    """Analyze a single symbol with configurable thresholds."""
    try:
        # Validate asset type
        if asset_type not in ["stock", "crypto"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Asset type must be 'stock' or 'crypto'"
            )
        
        # Create custom thresholds
        thresholds = AnalysisThresholds(
            rsi_overbought=rsi_overbought,
            rsi_oversold=rsi_oversold,
            stoch_overbought=stoch_overbought,
            stoch_oversold=stoch_oversold
        )
        
        analysis_service = MarketAnalysisService()
        result = await analysis_service.analyze_symbol(symbol.upper(), asset_type, thresholds)
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing symbol {symbol}: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze symbol: {str(e)}"
        )

@router.post("/bulk", response_model=BulkAnalysisResponse)
async def bulk_analysis(
    request: BulkAnalysisRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Analyze multiple symbols at once."""
    try:
        if len(request.symbols) > 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 20 symbols allowed for bulk analysis"
            )
        
        analysis_service = MarketAnalysisService()
        results = []
        
        for symbol in request.symbols:
            try:
                result = await analysis_service.analyze_symbol(
                    symbol.upper(), 
                    request.asset_type, 
                    request.thresholds
                )
                results.append(result)
            except Exception as e:
                logger.warning(f"Failed to analyze {symbol}: {e}")
                # Continue with other symbols
        
        # Calculate summary
        summary = {
            "overbought": sum(1 for r in results if r.overall_condition == MarketCondition.OVERBOUGHT),
            "oversold": sum(1 for r in results if r.overall_condition == MarketCondition.OVERSOLD),
            "neutral": sum(1 for r in results if r.overall_condition == MarketCondition.NEUTRAL)
        }
        
        return BulkAnalysisResponse(
            results=results,
            summary=summary,
            analysis_timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Error in bulk analysis: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk analysis: {str(e)}"
        )

@router.get("/watchlist", response_model=WatchlistAnalysis)
async def analyze_watchlist(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Analyze user's favorite symbols (watchlist)."""
    try:
        favorites_service = FavoritesService(db)
        analysis_service = MarketAnalysisService()
        
        # Get user's favorites
        favorites = favorites_service.get_user_favorites(current_user.id)
        
        if not favorites:
            return WatchlistAnalysis(
                user_id=current_user.id,
                total_favorites=0,
                overbought_count=0,
                oversold_count=0,
                neutral_count=0,
                top_opportunities=[],
                top_risks=[]
            )
        
        # Analyze each favorite
        analysis_results = []
        for favorite in favorites:
            try:
                asset_type = "stock" if favorite.asset_type == AssetType.STOCK else "crypto"
                result = await analysis_service.analyze_symbol(favorite.symbol, asset_type)
                analysis_results.append(result)
            except Exception as e:
                logger.warning(f"Failed to analyze favorite {favorite.symbol}: {e}")
        
        # Calculate counts
        overbought_count = sum(1 for r in analysis_results if r.overall_condition == MarketCondition.OVERBOUGHT)
        oversold_count = sum(1 for r in analysis_results if r.overall_condition == MarketCondition.OVERSOLD)
        neutral_count = sum(1 for r in analysis_results if r.overall_condition == MarketCondition.NEUTRAL)
        
        # Get top opportunities (oversold with high confidence)
        opportunities = [r for r in analysis_results if r.overall_condition == MarketCondition.OVERSOLD]
        opportunities.sort(key=lambda x: x.confidence_score, reverse=True)
        top_opportunities = opportunities[:5]
        
        # Get top risks (overbought with high confidence)
        risks = [r for r in analysis_results if r.overall_condition == MarketCondition.OVERBOUGHT]
        risks.sort(key=lambda x: x.confidence_score, reverse=True)
        top_risks = risks[:5]
        
        return WatchlistAnalysis(
            user_id=current_user.id,
            total_favorites=len(favorites),
            overbought_count=overbought_count,
            oversold_count=oversold_count,
            neutral_count=neutral_count,
            top_opportunities=top_opportunities,
            top_risks=top_risks
        )
        
    except Exception as e:
        logger.error(f"Error analyzing watchlist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze watchlist: {str(e)}"
        )

@router.get("/screener", response_model=List[ScreenerResult])
async def market_screener(
    condition: MarketCondition = Query(..., description="overbought, oversold, or neutral"),
    min_confidence: Optional[float] = Query(0.6, description="Minimum confidence score"),
    asset_type: Optional[str] = Query("stock", description="stock or crypto"),
    limit: Optional[int] = Query(20, description="Maximum number of results"),
    current_user: User = Depends(get_current_active_user)
):
    """Screen the market for symbols matching specific conditions."""
    try:
        # For demo purposes, we'll use a predefined list of popular symbols
        # In production, you might want to screen a larger universe of symbols
        
        if asset_type == "stock":
            symbols = [
                "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA", "NFLX",
                "AMD", "INTC", "CRM", "ORCL", "ADBE", "PYPL", "UBER", "SPOT",
                "ZOOM", "SQ", "TWTR", "SNAP"
            ]
        else:
            symbols = [
                "BTC", "ETH", "BNB", "XRP", "ADA", "SOL", "DOGE", "DOT",
                "AVAX", "SHIB", "MATIC", "LTC", "UNI", "LINK", "ATOM"
            ]
        
        analysis_service = MarketAnalysisService()
        screener_results = []
        
        for symbol in symbols[:limit * 2]:  # Analyze more than needed to filter
            try:
                result = await analysis_service.analyze_symbol(symbol, asset_type)
                
                # Filter by condition and confidence
                if (result.overall_condition == condition and 
                    result.confidence_score >= min_confidence):
                    
                    # Extract key signals
                    key_signals = [
                        f"{signal.indicator}: {signal.description}"
                        for signal in result.signals
                        if signal.signal_strength > 0.5
                    ]
                    
                    screener_results.append(ScreenerResult(
                        symbol=symbol,
                        condition=result.overall_condition,
                        confidence_score=result.confidence_score,
                        current_price=result.current_price,
                        key_signals=key_signals[:3]  # Top 3 signals
                    ))
                    
                    if len(screener_results) >= limit:
                        break
                        
            except Exception as e:
                logger.warning(f"Failed to screen {symbol}: {e}")
                continue
        
        # Sort by confidence score
        screener_results.sort(key=lambda x: x.confidence_score, reverse=True)
        
        return screener_results[:limit]
        
    except Exception as e:
        logger.error(f"Error in market screener: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to screen market: {str(e)}"
        )
