from typing import Dict, List, Any, Optional
from app.schemas.indicators import (
    RSIData, MACDData, StochData, BollingerBandsData, 
    MarketCondition, TechnicalAnalysisSummary
)
import logging

logger = logging.getLogger(__name__)

class TechnicalAnalyzer:
    @staticmethod
    def parse_rsi_data(data: Dict[str, Any]) -> List[RSIData]:
        """Parse RSI indicator data."""
        try:
            results = []
            technical_analysis = data.get("Technical Analysis: RSI", {})
            
            for timestamp, values in technical_analysis.items():
                result = RSIData(
                    timestamp=timestamp,
                    rsi=float(values.get("RSI", 0))
                )
                results.append(result)
            
            # Sort by timestamp (most recent first)
            results.sort(key=lambda x: x.timestamp, reverse=True)
            return results
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing RSI data: {e}")
            raise ValueError("Invalid RSI data format")

    @staticmethod
    def parse_macd_data(data: Dict[str, Any]) -> List[MACDData]:
        """Parse MACD indicator data."""
        try:
            results = []
            technical_analysis = data.get("Technical Analysis: MACD", {})
            
            for timestamp, values in technical_analysis.items():
                result = MACDData(
                    timestamp=timestamp,
                    macd=float(values.get("MACD", 0)),
                    macd_hist=float(values.get("MACD_Hist", 0)),
                    macd_signal=float(values.get("MACD_Signal", 0))
                )
                results.append(result)
            
            # Sort by timestamp (most recent first)
            results.sort(key=lambda x: x.timestamp, reverse=True)
            return results
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing MACD data: {e}")
            raise ValueError("Invalid MACD data format")

    @staticmethod
    def parse_stoch_data(data: Dict[str, Any]) -> List[StochData]:
        """Parse Stochastic indicator data."""
        try:
            results = []
            technical_analysis = data.get("Technical Analysis: STOCH", {})
            
            for timestamp, values in technical_analysis.items():
                result = StochData(
                    timestamp=timestamp,
                    slowk=float(values.get("SlowK", 0)),
                    slowd=float(values.get("SlowD", 0))
                )
                results.append(result)
            
            # Sort by timestamp (most recent first)
            results.sort(key=lambda x: x.timestamp, reverse=True)
            return results
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing Stochastic data: {e}")
            raise ValueError("Invalid Stochastic data format")

    @staticmethod
    def parse_bbands_data(data: Dict[str, Any]) -> List[BollingerBandsData]:
        """Parse Bollinger Bands indicator data."""
        try:
            results = []
            technical_analysis = data.get("Technical Analysis: BBANDS", {})
            
            for timestamp, values in technical_analysis.items():
                result = BollingerBandsData(
                    timestamp=timestamp,
                    real_upper_band=float(values.get("Real Upper Band", 0)),
                    real_middle_band=float(values.get("Real Middle Band", 0)),
                    real_lower_band=float(values.get("Real Lower Band", 0))
                )
                results.append(result)
            
            # Sort by timestamp (most recent first)
            results.sort(key=lambda x: x.timestamp, reverse=True)
            return results
        except (KeyError, ValueError, TypeError) as e:
            logger.error(f"Error parsing Bollinger Bands data: {e}")
            raise ValueError("Invalid Bollinger Bands data format")

    @staticmethod
    def analyze_rsi(rsi_data: List[RSIData]) -> tuple[MarketCondition, str]:
        """Analyze RSI for market condition."""
        if not rsi_data:
            return MarketCondition.NEUTRAL, "No RSI data available"
        
        current_rsi = rsi_data[0].rsi
        
        if current_rsi >= 70:
            return MarketCondition.OVERBOUGHT, f"RSI at {current_rsi:.2f} indicates overbought conditions"
        elif current_rsi <= 30:
            return MarketCondition.OVERSOLD, f"RSI at {current_rsi:.2f} indicates oversold conditions"
        else:
            return MarketCondition.NEUTRAL, f"RSI at {current_rsi:.2f} indicates neutral conditions"

    @staticmethod
    def analyze_macd(macd_data: List[MACDData]) -> tuple[MarketCondition, str]:
        """Analyze MACD for market condition."""
        if len(macd_data) < 2:
            return MarketCondition.NEUTRAL, "Insufficient MACD data for analysis"
        
        current = macd_data[0]
        previous = macd_data[1]
        
        # MACD bullish/bearish signals
        if current.macd > current.macd_signal and previous.macd <= previous.macd_signal:
            return MarketCondition.OVERSOLD, "MACD bullish crossover - potential buy signal"
        elif current.macd < current.macd_signal and previous.macd >= previous.macd_signal:
            return MarketCondition.OVERBOUGHT, "MACD bearish crossover - potential sell signal"
        elif current.macd > current.macd_signal:
            return MarketCondition.NEUTRAL, "MACD above signal line - bullish momentum"
        else:
            return MarketCondition.NEUTRAL, "MACD below signal line - bearish momentum"

    @staticmethod
    def analyze_stoch(stoch_data: List[StochData]) -> tuple[MarketCondition, str]:
        """Analyze Stochastic for market condition."""
        if not stoch_data:
            return MarketCondition.NEUTRAL, "No Stochastic data available"
        
        current = stoch_data[0]
        
        if current.slowk >= 80 and current.slowd >= 80:
            return MarketCondition.OVERBOUGHT, f"Stochastic K={current.slowk:.2f}, D={current.slowd:.2f} indicates overbought"
        elif current.slowk <= 20 and current.slowd <= 20:
            return MarketCondition.OVERSOLD, f"Stochastic K={current.slowk:.2f}, D={current.slowd:.2f} indicates oversold"
        else:
            return MarketCondition.NEUTRAL, f"Stochastic K={current.slowk:.2f}, D={current.slowd:.2f} indicates neutral"

    @staticmethod
    def analyze_bbands(bbands_data: List[BollingerBandsData], current_price: Optional[float] = None) -> tuple[MarketCondition, str]:
        """Analyze Bollinger Bands for market condition."""
        if not bbands_data:
            return MarketCondition.NEUTRAL, "No Bollinger Bands data available"
        
        current = bbands_data[0]
        
        if current_price:
            if current_price >= current.real_upper_band:
                return MarketCondition.OVERBOUGHT, f"Price {current_price:.2f} at upper band {current.real_upper_band:.2f} - overbought"
            elif current_price <= current.real_lower_band:
                return MarketCondition.OVERSOLD, f"Price {current_price:.2f} at lower band {current.real_lower_band:.2f} - oversold"
            else:
                return MarketCondition.NEUTRAL, f"Price {current_price:.2f} within bands - neutral"
        else:
            return MarketCondition.NEUTRAL, "Bollinger Bands available but no current price for comparison"

    @staticmethod
    def get_indicator_metadata(data: Dict[str, Any]) -> Dict[str, str]:
        """Extract metadata from technical indicator response."""
        metadata = data.get("Meta Data", {})
        return {
            "symbol": metadata.get("1: Symbol", ""),
            "indicator": metadata.get("2: Indicator", ""),
            "last_refreshed": metadata.get("3: Last Refreshed", ""),
            "interval": metadata.get("4: Interval", ""),
            "time_period": metadata.get("5: Time Period", ""),
            "series_type": metadata.get("6: Series Type", "")
        }
