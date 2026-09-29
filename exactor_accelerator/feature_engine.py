"""
Domain Feature Engine for Exactor Accelerator v2.0

Provides automated, robust feature extraction and enrichment across
specialized operational domains: fraud, medical, forex, manufacturing, security,
as well as generic tabular data.
"""

from typing import Dict, Any, List, Optional, Callable
import pandas as pd
import numpy as np


class DomainFeatureEngine:
    """
    Base feature engine providing domain-agnostic feature enrichment utilities.
    """

    def __init__(self, domain: str = "general"):
        self.domain = domain.lower()

    def extract_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich dataframe with domain-specific features without mutating in-place.

        Args:
            df: Input pandas DataFrame

        Returns:
            Enriched pandas DataFrame copy
        """
        result = df.copy()
        return self._extract_domain_features(result)

    def _extract_domain_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fallback generic feature enrichment."""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if not col.endswith(("_zscore", "_trend", "_score")):
                std = df[col].std()
                mean = df[col].mean()
                if std and not np.isnan(std) and std > 1e-9:
                    df[f"{col}_zscore"] = (df[col] - mean) / std
        return df


class FraudFeatureEngine(DomainFeatureEngine):
    """
    Specialized feature engine for real-time transaction fraud detection.
    """

    def __init__(self):
        super().__init__(domain="fraud")

    def _extract_domain_features(self, df: pd.DataFrame) -> pd.DataFrame:
        # Amount z-score
        if "amount" in df.columns:
            mean = df["amount"].mean()
            std = df["amount"].std()
            df["amount_zscore"] = (df["amount"] - mean) / (std if std > 1e-9 else 1.0)
        elif "amount_zscore" not in df.columns:
            df["amount_zscore"] = 0.0

        # Velocity features (1h, 1m)
        if "velocity_1h" in df.columns:
            df["velocity_1m"] = df["velocity_1h"] / 60.0
        elif "velocity" in df.columns:
            df["velocity_1h"] = df["velocity"]
            df["velocity_1m"] = df["velocity"] / 60.0
        else:
            df["velocity_1h"] = 1.0
            df["velocity_1m"] = 1.0 / 60.0

        # Device trust trend
        if "device_trust" in df.columns:
            # Device trust delta / rolling trend
            df["device_trust_trend"] = df["device_trust"].diff().fillna(0.0)
        else:
            df["device_trust_trend"] = 0.0

        # IP reputation score (0.0 = clean, 1.0 = malicious / high risk)
        if "ip_reputation" in df.columns:
            if df["ip_reputation"].dtype == object:
                mapping = {"CLEAN": 0.05, "SUSPICIOUS": 0.60, "MALICIOUS": 0.95}
                df["ip_reputation_score"] = (
                    df["ip_reputation"].astype(str).str.upper().map(mapping).fillna(0.5)
                )
            else:
                df["ip_reputation_score"] = df["ip_reputation"].astype(float)
        elif "ip_reputation_score" not in df.columns:
            df["ip_reputation_score"] = 0.1

        # Geolocation risk score (0.0 = low risk, 1.0 = high risk)
        if "country_risk" in df.columns:
            if df["country_risk"].dtype == object:
                mapping = {"LOW": 0.10, "MEDIUM": 0.50, "HIGH": 0.90}
                df["geolocation_risk_score"] = (
                    df["country_risk"].astype(str).str.upper().map(mapping).fillna(0.5)
                )
            else:
                df["geolocation_risk_score"] = df["country_risk"].astype(float)
        elif "geolocation_risk_score" not in df.columns:
            df["geolocation_risk_score"] = 0.1

        return df


class MedicalFeatureEngine(DomainFeatureEngine):
    """
    Specialized feature engine for emergency clinical and medical triage.
    """

    def __init__(self):
        super().__init__(domain="medical")

    def _extract_domain_features(self, df: pd.DataFrame) -> pd.DataFrame:
        # Vitals z-scores based on physiological reference values or sample statistics
        vitals_specs = {
            "heart_rate": (75.0, 15.0),
            "blood_pressure_systolic": (120.0, 20.0),
            "blood_pressure_diastolic": (80.0, 12.0),
            "oxygen_saturation": (98.0, 3.0),
            "temperature": (37.0, 0.8),
            "respiratory_rate": (16.0, 4.0),
        }

        for vital, (ref_mean, ref_std) in vitals_specs.items():
            if vital in df.columns:
                std = df[vital].std()
                mean = df[vital].mean()
                use_mean = mean if (not np.isnan(mean) and len(df) > 10) else ref_mean
                use_std = std if (std and not np.isnan(std) and std > 1e-5) else ref_std
                df[f"{vital}_zscore"] = (df[vital] - use_mean) / use_std
                df[f"{vital}_trend"] = df[vital].diff().fillna(0.0)

        # Age risk factor (0.0 to 1.0)
        if "age" in df.columns:
            df["age_risk_factor"] = np.clip(
                (df["age"].astype(float) - 18.0) / 70.0, 0.0, 1.0
            )
        else:
            df["age_risk_factor"] = 0.3

        # Comorbidity score (0.0 to 1.0)
        comorbidity_cols = [c for c in ["diabetes", "hypertension", "heart_disease"] if c in df.columns]
        if comorbidity_cols:
            weights = {"diabetes": 0.3, "hypertension": 0.3, "heart_disease": 0.4}
            score = pd.Series(0.0, index=df.index)
            for c in comorbidity_cols:
                w = weights.get(c, 0.33)
                score += df[c].astype(float) * w
            df["comorbidity_score"] = np.clip(score, 0.0, 1.0)
        else:
            df["comorbidity_score"] = 0.0

        return df


class ForexFeatureEngine(DomainFeatureEngine):
    """
    Specialized feature engine for high-frequency technical Forex/trading.
    """

    def __init__(self):
        super().__init__(domain="forex")

    def _extract_domain_features(self, df: pd.DataFrame) -> pd.DataFrame:
        has_ohlc = all(c in df.columns for c in ["open", "high", "low", "close"])

        if has_ohlc:
            close = df["close"].astype(float)
            high = df["high"].astype(float)
            low = df["low"].astype(float)
            open_ = df["open"].astype(float)

            # Candle body and range
            df["candle_body"] = (close - open_).abs()
            candle_range = (high - low).replace(0, 1e-9)
            df["candle_range"] = candle_range

            # Wick ratios
            upper_wick = high - np.maximum(open_, close)
            lower_wick = np.minimum(open_, close) - low
            df["wick_balance_ratio"] = (upper_wick - lower_wick) / candle_range

            # ATR (14-period Average True Range approximation)
            prev_close = close.shift(1).fillna(open_)
            tr1 = high - low
            tr2 = (high - prev_close).abs()
            tr3 = (low - prev_close).abs()
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr_14 = tr.rolling(window=14, min_periods=1).mean()
            df["atr"] = atr_14
            df["atr_norm_pct"] = (atr_14 / close.replace(0, 1e-9)).fillna(0.0)

            # RSI (14-period Relative Strength Index)
            delta = close.diff().fillna(0.0)
            gain = delta.clip(lower=0)
            loss = -delta.clip(upper=0)
            avg_gain = gain.rolling(window=14, min_periods=1).mean()
            avg_loss = loss.rolling(window=14, min_periods=1).mean().replace(0, 1e-9)
            rs = avg_gain / avg_loss
            df["rsi"] = 100.0 - (100.0 / (1.0 + rs))

            # EMA Spread (Fast 9 vs Slow 21)
            ema_9 = close.ewm(span=9, adjust=False).mean()
            ema_21 = close.ewm(span=21, adjust=False).mean()
            df["ema_spread"] = ema_9 - ema_21

            # MACD (12, 26, 9)
            ema_12 = close.ewm(span=12, adjust=False).mean()
            ema_26 = close.ewm(span=26, adjust=False).mean()
            macd_line = ema_12 - ema_26
            macd_signal = macd_line.ewm(span=9, adjust=False).mean()
            df["macd_hist"] = macd_line - macd_signal

            # ADX approximation (14 periods)
            up_move = high.diff().fillna(0.0)
            down_move = -low.diff().fillna(0.0)
            plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
            minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
            tr_smooth = tr.rolling(window=14, min_periods=1).mean().replace(0, 1e-9)
            plus_di = 100.0 * pd.Series(plus_dm, index=df.index).rolling(window=14, min_periods=1).mean() / tr_smooth
            minus_di = 100.0 * pd.Series(minus_dm, index=df.index).rolling(window=14, min_periods=1).mean() / tr_smooth
            di_sum = (plus_di + minus_di).replace(0, 1e-9)
            dx = 100.0 * (plus_di - minus_di).abs() / di_sum
            df["adx"] = dx.rolling(window=14, min_periods=1).mean().fillna(20.0)

            # Bollinger Bands Bandwidth
            mid_band = close.rolling(window=20, min_periods=1).mean()
            std_band = close.rolling(window=20, min_periods=1).std().fillna(1e-9)
            df["bb_bandwidth"] = (4.0 * std_band) / mid_band.replace(0, 1e-9)
        else:
            # Fallback defaults for missing OHLC
            for col in ["atr", "rsi", "ema_spread", "macd_hist", "adx"]:
                if col not in df.columns:
                    df[col] = 0.0

        return df


class ManufacturingFeatureEngine(DomainFeatureEngine):
    """
    Specialized feature engine for industrial sensor quality and predictive maintenance.
    """

    def __init__(self):
        super().__init__(domain="manufacturing")

    def _extract_domain_features(self, df: pd.DataFrame) -> pd.DataFrame:
        # Detect sensor columns
        sensor_cols = [c for c in df.columns if c.startswith("sensor_") and not c.endswith(("_zscore", "_trend"))]
        if not sensor_cols:
            sensor_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c not in ["defect", "hours_since_maintenance"]]

        zscore_cols = []
        for c in sensor_cols:
            mean = df[c].mean()
            std = df[c].std()
            z_col = f"{c}_zscore"
            trend_col = f"{c}_trend"
            df[z_col] = (df[c] - mean) / (std if std and not np.isnan(std) and std > 1e-9 else 1.0)
            df[trend_col] = df[c].diff().fillna(0.0)
            zscore_cols.append(z_col)

        # Anomaly score: maximum absolute z-score across all sensors
        if zscore_cols:
            df["anomaly_score"] = df[zscore_cols].abs().max(axis=1)
        else:
            df["anomaly_score"] = 0.0

        # Maintenance risk: normalized degradation by hours since maintenance
        if "hours_since_maintenance" in df.columns:
            df["maintenance_risk"] = np.clip(
                df["hours_since_maintenance"].astype(float) / 2000.0, 0.0, 1.0
            )
        else:
            df["maintenance_risk"] = 0.1

        return df


class SecurityFeatureEngine(DomainFeatureEngine):
    """
    Specialized feature engine for real-time security log and threat detection.
    """

    def __init__(self):
        super().__init__(domain="security")

    def _extract_domain_features(self, df: pd.DataFrame) -> pd.DataFrame:
        # IP reputation score (0.0 clean -> 1.0 malicious)
        if "ip_reputation" in df.columns:
            if df["ip_reputation"].dtype == object:
                mapping = {"CLEAN": 0.05, "SUSPICIOUS": 0.60, "MALICIOUS": 0.95}
                df["ip_reputation_score"] = (
                    df["ip_reputation"].astype(str).str.upper().map(mapping).fillna(0.5)
                )
            else:
                df["ip_reputation_score"] = df["ip_reputation"].astype(float)
        elif "ip_reputation_score" not in df.columns:
            df["ip_reputation_score"] = 0.1

        # Request velocities (1m, 1s)
        if "request_velocity_1m" in df.columns:
            df["request_velocity_1s"] = df["request_velocity_1m"] / 60.0
        elif "request_velocity" in df.columns:
            df["request_velocity_1m"] = df["request_velocity"]
            df["request_velocity_1s"] = df["request_velocity"] / 60.0
        else:
            df["request_velocity_1m"] = 1.0
            df["request_velocity_1s"] = 1.0 / 60.0

        # Payload anomaly score
        if "payload_size" in df.columns:
            mean = df["payload_size"].mean()
            std = df["payload_size"].std()
            df["payload_anomaly_score"] = (df["payload_size"] - mean) / (std if std and not np.isnan(std) and std > 1e-9 else 1.0)
        else:
            df["payload_anomaly_score"] = 0.0

        # User behavior risk (0.0 to 1.0)
        risk_components = []
        if "failed_logins" in df.columns:
            risk_components.append(np.clip(df["failed_logins"].astype(float) / 5.0, 0.0, 1.0))
        if "password_resets" in df.columns:
            risk_components.append(np.clip(df["password_resets"].astype(float) / 2.0, 0.0, 1.0))
        if "unusual_access" in df.columns:
            risk_components.append(df["unusual_access"].astype(float))
        if "off_hours_access" in df.columns:
            risk_components.append(df["off_hours_access"].astype(float) * 0.5)

        if risk_components:
            df["user_behavior_risk"] = pd.concat(risk_components, axis=1).mean(axis=1)
        else:
            df["user_behavior_risk"] = 0.1

        return df


# Configuration and factory
ConfigurableFeatureEngine = DomainFeatureEngine


def get_feature_engine(domain: str = "general") -> DomainFeatureEngine:
    """
    Factory function to obtain a domain-specific feature engine.

    Args:
        domain: Domain name ("fraud", "medical", "forex", "manufacturing", "security", "general")

    Returns:
        Instance of domain-specific DomainFeatureEngine
    """
    domain_map = {
        "fraud": FraudFeatureEngine,
        "medical": MedicalFeatureEngine,
        "forex": ForexFeatureEngine,
        "manufacturing": ManufacturingFeatureEngine,
        "security": SecurityFeatureEngine,
        "general": DomainFeatureEngine,
        "generic": DomainFeatureEngine,
    }

    engine_cls = domain_map.get(domain.lower().strip(), DomainFeatureEngine)
    return engine_cls()


__all__ = [
    "DomainFeatureEngine",
    "ConfigurableFeatureEngine",
    "FraudFeatureEngine",
    "MedicalFeatureEngine",
    "ForexFeatureEngine",
    "ManufacturingFeatureEngine",
    "SecurityFeatureEngine",
    "get_feature_engine",
]
