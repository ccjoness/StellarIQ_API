import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.schemas.analysis import (
    AnalysisThresholds,
    IndicatorSignal,
    MarketAnalysisResult,
    MarketCondition,
)
from app.schemas.indicators import BollingerBandsData, MACDData, RSIData, StochData
from app.services.market_data import MarketDataService
from app.utils.data_parser import DataParser
from app.utils.technical_analysis import TechnicalAnalyzer

logger = logging.getLogger(__name__)


class MarketAnalysisService:
    def __init__(self):
        self.market_service = MarketDataService()
        self.default_thresholds = AnalysisThresholds()

    async def analyze_symbol(
        self,
        symbol: str,
        asset_type: str = "stock",
        thresholds: Optional[AnalysisThresholds] = None,
    ) -> MarketAnalysisResult:
        """Perform comprehensive market analysis for a single symbol."""
        if thresholds is None:
            thresholds = self.default_thresholds

        try:
            # Get current price
            current_price = None
            if asset_type == "stock":
                quote_data = await self.market_service.get_stock_quote(symbol)
                quote = DataParser.parse_stock_quote(quote_data)
                current_price = quote.price
            elif asset_type == "crypto":
                rate_data = await self.market_service.get_crypto_exchange_rate(
                    symbol, "USD"
                )
                rate = DataParser.parse_crypto_exchange_rate(rate_data)
                current_price = rate.exchange_rate

            # Get technical indicators
            signals = []

            # RSI Analysis
            try:
                rsi_data_raw = await self.market_service.get_rsi(symbol, "daily")
                rsi_data = TechnicalAnalyzer.parse_rsi_data(rsi_data_raw)
                rsi_signal = self._analyze_rsi(rsi_data, thresholds)
                if rsi_signal:
                    signals.append(rsi_signal)
            except Exception as e:
                logger.warning(f"Failed to get RSI for {symbol}: {e}")

            # MACD Analysis
            try:
                macd_data_raw = await self.market_service.get_macd(symbol, "daily")
                macd_data = TechnicalAnalyzer.parse_macd_data(macd_data_raw)
                macd_signal = self._analyze_macd(macd_data)
                if macd_signal:
                    signals.append(macd_signal)
            except Exception as e:
                logger.warning(f"Failed to get MACD for {symbol}: {e}")

            # Stochastic Analysis
            try:
                stoch_data_raw = await self.market_service.get_stoch(symbol, "daily")
                stoch_data = TechnicalAnalyzer.parse_stoch_data(stoch_data_raw)
                stoch_signal = self._analyze_stochastic(stoch_data, thresholds)
                if stoch_signal:
                    signals.append(stoch_signal)
            except Exception as e:
                logger.warning(f"Failed to get Stochastic for {symbol}: {e}")

            # Bollinger Bands Analysis
            try:
                bbands_data_raw = await self.market_service.get_bbands(symbol, "daily")
                bbands_data = TechnicalAnalyzer.parse_bbands_data(bbands_data_raw)
                bbands_signal = self._analyze_bollinger_bands(
                    bbands_data, current_price
                )
                if bbands_signal:
                    signals.append(bbands_signal)
            except Exception as e:
                logger.warning(f"Failed to get Bollinger Bands for {symbol}: {e}")

            # Calculate overall condition and confidence
            (
                overall_condition,
                confidence_score,
                recommendation,
                risk_level,
            ) = self._calculate_overall_analysis(signals)

            return MarketAnalysisResult(
                symbol=symbol,
                asset_type=asset_type,
                analysis_timestamp=datetime.utcnow(),
                current_price=current_price,
                signals=signals,
                overall_condition=overall_condition,
                confidence_score=confidence_score,
                recommendation=recommendation,
                risk_level=risk_level,
                thresholds_used=thresholds,
            )

        except Exception as e:
            logger.error(f"Error analyzing {symbol}: {e}")
            # Return a basic result with error info
            return MarketAnalysisResult(
                symbol=symbol,
                asset_type=asset_type,
                analysis_timestamp=datetime.utcnow(),
                signals=[],
                overall_condition=MarketCondition.NEUTRAL,
                confidence_score=0.0,
                recommendation=f"Analysis failed: {str(e)}",
                risk_level="unknown",
                thresholds_used=thresholds,
            )

    def _analyze_rsi(
        self, rsi_data: List[RSIData], thresholds: AnalysisThresholds
    ) -> Optional[IndicatorSignal]:
        """Analyze RSI indicator."""
        if not rsi_data:
            return None

        current_rsi = rsi_data[0].rsi

        if current_rsi >= thresholds.rsi_overbought:
            strength = min(
                (current_rsi - thresholds.rsi_overbought)
                / (100 - thresholds.rsi_overbought),
                1.0,
            )
            return IndicatorSignal(
                indicator="RSI",
                condition=MarketCondition.OVERBOUGHT,
                value=current_rsi,
                signal_strength=strength,
                description=f"RSI at {current_rsi:.2f} indicates overbought conditions",
            )
        elif current_rsi <= thresholds.rsi_oversold:
            strength = min(
                (thresholds.rsi_oversold - current_rsi) / thresholds.rsi_oversold, 1.0
            )
            return IndicatorSignal(
                indicator="RSI",
                condition=MarketCondition.OVERSOLD,
                value=current_rsi,
                signal_strength=strength,
                description=f"RSI at {current_rsi:.2f} indicates oversold conditions",
            )
        else:
            return IndicatorSignal(
                indicator="RSI",
                condition=MarketCondition.NEUTRAL,
                value=current_rsi,
                signal_strength=0.5,
                description=f"RSI at {current_rsi:.2f} indicates neutral conditions",
            )

    def _analyze_macd(self, macd_data: List[MACDData]) -> Optional[IndicatorSignal]:
        """Analyze MACD indicator."""
        if len(macd_data) < 2:
            return None

        current = macd_data[0]
        previous = macd_data[1]

        # Check for crossovers
        if current.macd > current.macd_signal and previous.macd <= previous.macd_signal:
            # Bullish crossover
            strength = min(
                abs(current.macd - current.macd_signal) / abs(current.macd), 1.0
            )
            return IndicatorSignal(
                indicator="MACD",
                condition=MarketCondition.OVERSOLD,  # Bullish signal suggests buying opportunity
                value=current.macd,
                signal_strength=strength,
                description="MACD bullish crossover - potential buy signal",
            )
        elif (
            current.macd < current.macd_signal and previous.macd >= previous.macd_signal
        ):
            # Bearish crossover
            strength = min(
                abs(current.macd_signal - current.macd) / abs(current.macd), 1.0
            )
            return IndicatorSignal(
                indicator="MACD",
                condition=MarketCondition.OVERBOUGHT,  # Bearish signal suggests selling opportunity
                value=current.macd,
                signal_strength=strength,
                description="MACD bearish crossover - potential sell signal",
            )
        else:
            # No crossover, check current position
            condition = MarketCondition.NEUTRAL
            description = "MACD no significant crossover"

            if current.macd > current.macd_signal:
                description = "MACD above signal line - bullish momentum"
            else:
                description = "MACD below signal line - bearish momentum"

            return IndicatorSignal(
                indicator="MACD",
                condition=condition,
                value=current.macd,
                signal_strength=0.3,
                description=description,
            )

    def _analyze_stochastic(
        self, stoch_data: List[StochData], thresholds: AnalysisThresholds
    ) -> Optional[IndicatorSignal]:
        """Analyze Stochastic indicator."""
        if not stoch_data:
            return None

        current = stoch_data[0]
        avg_stoch = (current.slowk + current.slowd) / 2

        if avg_stoch >= thresholds.stoch_overbought:
            strength = min(
                (avg_stoch - thresholds.stoch_overbought)
                / (100 - thresholds.stoch_overbought),
                1.0,
            )
            return IndicatorSignal(
                indicator="Stochastic",
                condition=MarketCondition.OVERBOUGHT,
                value=avg_stoch,
                signal_strength=strength,
                description=f"Stochastic at {avg_stoch:.2f} indicates overbought conditions",
            )
        elif avg_stoch <= thresholds.stoch_oversold:
            strength = min(
                (thresholds.stoch_oversold - avg_stoch) / thresholds.stoch_oversold, 1.0
            )
            return IndicatorSignal(
                indicator="Stochastic",
                condition=MarketCondition.OVERSOLD,
                value=avg_stoch,
                signal_strength=strength,
                description=f"Stochastic at {avg_stoch:.2f} indicates oversold conditions",
            )
        else:
            return IndicatorSignal(
                indicator="Stochastic",
                condition=MarketCondition.NEUTRAL,
                value=avg_stoch,
                signal_strength=0.5,
                description=f"Stochastic at {avg_stoch:.2f} indicates neutral conditions",
            )

    def _analyze_bollinger_bands(
        self, bbands_data: List[BollingerBandsData], current_price: Optional[float]
    ) -> Optional[IndicatorSignal]:
        """Analyze Bollinger Bands indicator."""
        if not bbands_data or current_price is None:
            return None

        current = bbands_data[0]
        band_width = current.real_upper_band - current.real_lower_band

        if current_price >= current.real_upper_band:
            # Price at or above upper band
            distance_ratio = (current_price - current.real_upper_band) / band_width
            strength = min(distance_ratio, 1.0)
            return IndicatorSignal(
                indicator="Bollinger Bands",
                condition=MarketCondition.OVERBOUGHT,
                value=current_price,
                signal_strength=strength,
                description=f"Price {current_price:.2f} at upper band - overbought",
            )
        elif current_price <= current.real_lower_band:
            # Price at or below lower band
            distance_ratio = (current.real_lower_band - current_price) / band_width
            strength = min(distance_ratio, 1.0)
            return IndicatorSignal(
                indicator="Bollinger Bands",
                condition=MarketCondition.OVERSOLD,
                value=current_price,
                signal_strength=strength,
                description=f"Price {current_price:.2f} at lower band - oversold",
            )
        else:
            return IndicatorSignal(
                indicator="Bollinger Bands",
                condition=MarketCondition.NEUTRAL,
                value=current_price,
                signal_strength=0.5,
                description=f"Price {current_price:.2f} within bands - neutral",
            )

    def _calculate_overall_analysis(
        self, signals: List[IndicatorSignal]
    ) -> tuple[MarketCondition, float, str, str]:
        """Calculate overall market condition from individual signals."""
        if not signals:
            return MarketCondition.NEUTRAL, 0.0, "No signals available", "unknown"

        # Weight signals by their strength
        weighted_scores = {"overbought": 0.0, "oversold": 0.0, "neutral": 0.0}
        total_weight = 0.0

        for signal in signals:
            weight = signal.signal_strength
            total_weight += weight

            if signal.condition == MarketCondition.OVERBOUGHT:
                weighted_scores["overbought"] += weight
            elif signal.condition == MarketCondition.OVERSOLD:
                weighted_scores["oversold"] += weight
            else:
                weighted_scores["neutral"] += weight

        if total_weight == 0:
            return MarketCondition.NEUTRAL, 0.0, "No valid signals", "unknown"

        # Normalize scores
        for key in weighted_scores:
            weighted_scores[key] /= total_weight

        # Determine overall condition
        max_score = max(weighted_scores.values())
        confidence_score = max_score

        if weighted_scores["overbought"] == max_score:
            overall_condition = MarketCondition.OVERBOUGHT
            recommendation = (
                "Consider selling - multiple indicators suggest overbought conditions"
            )
            risk_level = "high" if confidence_score > 0.7 else "medium"
        elif weighted_scores["oversold"] == max_score:
            overall_condition = MarketCondition.OVERSOLD
            recommendation = (
                "Consider buying - multiple indicators suggest oversold conditions"
            )
            risk_level = "low" if confidence_score > 0.7 else "medium"
        else:
            overall_condition = MarketCondition.NEUTRAL
            recommendation = "Hold - mixed or neutral signals from technical indicators"
            risk_level = "medium"

        return overall_condition, confidence_score, recommendation, risk_level
