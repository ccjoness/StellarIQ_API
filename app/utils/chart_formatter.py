from typing import List, Dict, Any, Optional
from app.schemas.charts import (
    CandlestickData, LineChartData, TechnicalIndicatorOverlay,
    PriceComparisonData
)
from app.schemas.stock import TimeSeriesData
from app.schemas.indicators import RSIData, MACDData, StochData, BollingerBandsData
import logging

logger = logging.getLogger(__name__)

class ChartFormatter:
    @staticmethod
    def format_candlestick_data(time_series_data: List[TimeSeriesData]) -> List[CandlestickData]:
        """Convert time series data to candlestick format for charts."""
        candlestick_data = []
        
        for data_point in time_series_data:
            candlestick = CandlestickData(
                timestamp=data_point.timestamp,
                open=data_point.open,
                high=data_point.high,
                low=data_point.low,
                close=data_point.close,
                volume=data_point.volume
            )
            candlestick_data.append(candlestick)
        
        return candlestick_data

    @staticmethod
    def format_rsi_overlay(rsi_data: List[RSIData]) -> List[LineChartData]:
        """Format RSI data for chart overlay."""
        return [
            LineChartData(timestamp=data.timestamp, value=data.rsi)
            for data in rsi_data
        ]

    @staticmethod
    def format_macd_overlay(macd_data: List[MACDData]) -> Dict[str, List[LineChartData]]:
        """Format MACD data for chart overlay."""
        return {
            "macd": [LineChartData(timestamp=data.timestamp, value=data.macd) for data in macd_data],
            "macd_signal": [LineChartData(timestamp=data.timestamp, value=data.macd_signal) for data in macd_data],
            "macd_histogram": [LineChartData(timestamp=data.timestamp, value=data.macd_hist) for data in macd_data]
        }

    @staticmethod
    def format_stoch_overlay(stoch_data: List[StochData]) -> Dict[str, List[LineChartData]]:
        """Format Stochastic data for chart overlay."""
        return {
            "stoch_k": [LineChartData(timestamp=data.timestamp, value=data.slowk) for data in stoch_data],
            "stoch_d": [LineChartData(timestamp=data.timestamp, value=data.slowd) for data in stoch_data]
        }

    @staticmethod
    def format_bbands_overlay(bbands_data: List[BollingerBandsData]) -> Dict[str, List[LineChartData]]:
        """Format Bollinger Bands data for chart overlay."""
        return {
            "bb_upper": [LineChartData(timestamp=data.timestamp, value=data.real_upper_band) for data in bbands_data],
            "bb_middle": [LineChartData(timestamp=data.timestamp, value=data.real_middle_band) for data in bbands_data],
            "bb_lower": [LineChartData(timestamp=data.timestamp, value=data.real_lower_band) for data in bbands_data]
        }

    @staticmethod
    def create_technical_overlay(
        rsi_data: Optional[List[RSIData]] = None,
        macd_data: Optional[List[MACDData]] = None,
        stoch_data: Optional[List[StochData]] = None,
        bbands_data: Optional[List[BollingerBandsData]] = None
    ) -> TechnicalIndicatorOverlay:
        """Create technical indicator overlay from various indicator data."""
        overlay = TechnicalIndicatorOverlay()
        
        if rsi_data:
            overlay.rsi = ChartFormatter.format_rsi_overlay(rsi_data)
        
        if macd_data:
            macd_formatted = ChartFormatter.format_macd_overlay(macd_data)
            overlay.macd = macd_formatted["macd"]
            overlay.macd_signal = macd_formatted["macd_signal"]
            overlay.macd_histogram = macd_formatted["macd_histogram"]
        
        if stoch_data:
            stoch_formatted = ChartFormatter.format_stoch_overlay(stoch_data)
            overlay.stoch_k = stoch_formatted["stoch_k"]
            overlay.stoch_d = stoch_formatted["stoch_d"]
        
        if bbands_data:
            bbands_formatted = ChartFormatter.format_bbands_overlay(bbands_data)
            overlay.bb_upper = bbands_formatted["bb_upper"]
            overlay.bb_middle = bbands_formatted["bb_middle"]
            overlay.bb_lower = bbands_formatted["bb_lower"]
        
        return overlay

    @staticmethod
    def align_timestamps(
        candlestick_data: List[CandlestickData],
        indicator_data: List[LineChartData]
    ) -> List[LineChartData]:
        """Align indicator data timestamps with candlestick data."""
        candlestick_timestamps = {data.timestamp for data in candlestick_data}
        
        aligned_data = [
            data for data in indicator_data 
            if data.timestamp in candlestick_timestamps
        ]
        
        return aligned_data

    @staticmethod
    def create_price_comparison_data(
        symbols_data: Dict[str, List[TimeSeriesData]],
        normalize: bool = False
    ) -> List[PriceComparisonData]:
        """Create price comparison data for multiple symbols."""
        if not symbols_data:
            return []
        
        # Get all unique timestamps
        all_timestamps = set()
        for symbol_data in symbols_data.values():
            for data_point in symbol_data:
                all_timestamps.add(data_point.timestamp)
        
        # Sort timestamps
        sorted_timestamps = sorted(all_timestamps, reverse=True)
        
        # Get base prices for normalization if needed
        base_prices = {}
        if normalize:
            for symbol, data in symbols_data.items():
                if data:
                    # Use the oldest price as base (last in the sorted list)
                    base_prices[symbol] = data[-1].close
        
        comparison_data = []
        for timestamp in sorted_timestamps:
            prices = {}
            
            for symbol, data in symbols_data.items():
                # Find price for this timestamp
                price = None
                for data_point in data:
                    if data_point.timestamp == timestamp:
                        price = data_point.close
                        break
                
                if price is not None:
                    if normalize and symbol in base_prices and base_prices[symbol] > 0:
                        # Calculate percentage change from base
                        prices[symbol] = ((price - base_prices[symbol]) / base_prices[symbol]) * 100
                    else:
                        prices[symbol] = price
            
            if prices:  # Only add if we have at least one price
                comparison_data.append(PriceComparisonData(
                    timestamp=timestamp,
                    prices=prices
                ))
        
        return comparison_data

    @staticmethod
    def limit_data_points(data: List[Any], max_points: int = 200) -> List[Any]:
        """Limit the number of data points for mobile app performance."""
        if len(data) <= max_points:
            return data
        
        # Take every nth point to reduce data size
        step = len(data) // max_points
        return data[::step][:max_points]
