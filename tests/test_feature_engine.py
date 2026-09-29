"""
Tests for Domain Feature Engine in Exactor Accelerator v2.0
"""

import pytest
import pandas as pd
import numpy as np

from exactor_accelerator.feature_engine import (
    get_feature_engine,
    DomainFeatureEngine,
    FraudFeatureEngine,
    MedicalFeatureEngine,
    ForexFeatureEngine,
    ManufacturingFeatureEngine,
    SecurityFeatureEngine,
)
from exactor_accelerator import (
    get_feature_engine as root_get_feature_engine,
    DomainFeatureEngine as RootDomainFeatureEngine,
)


def test_factory_instances():
    """Verify that get_feature_engine returns correct subclasses."""
    assert isinstance(get_feature_engine("fraud"), FraudFeatureEngine)
    assert isinstance(get_feature_engine("medical"), MedicalFeatureEngine)
    assert isinstance(get_feature_engine("forex"), ForexFeatureEngine)
    assert isinstance(get_feature_engine("manufacturing"), ManufacturingFeatureEngine)
    assert isinstance(get_feature_engine("security"), SecurityFeatureEngine)
    assert isinstance(get_feature_engine("general"), DomainFeatureEngine)
    assert isinstance(get_feature_engine("unknown_domain"), DomainFeatureEngine)
    assert root_get_feature_engine is get_feature_engine
    assert RootDomainFeatureEngine is DomainFeatureEngine


def test_immutability():
    """Verify extract_all does not modify input DataFrame in-place."""
    df = pd.DataFrame({"amount": [10.0, 20.0, 30.0]})
    cols_before = list(df.columns)
    engine = get_feature_engine("fraud")
    enriched = engine.extract_all(df)
    assert list(df.columns) == cols_before
    assert "amount_zscore" in enriched.columns


def test_fraud_feature_engine():
    """Verify fraud feature extraction."""
    engine = get_feature_engine("fraud")
    df = pd.DataFrame({
        "amount": [100.0, 200.0, 300.0, 400.0],
        "velocity_1h": [1.0, 5.0, 10.0, 20.0],
        "device_trust": [0.9, 0.8, 0.5, 0.1],
        "ip_reputation": ["CLEAN", "CLEAN", "SUSPICIOUS", "MALICIOUS"],
        "country_risk": ["LOW", "MEDIUM", "HIGH", "HIGH"],
    })
    enriched = engine.extract_all(df)
    assert "amount_zscore" in enriched.columns
    assert "velocity_1m" in enriched.columns
    assert "device_trust_trend" in enriched.columns
    assert "ip_reputation_score" in enriched.columns
    assert "geolocation_risk_score" in enriched.columns

    # Verify score mappings
    assert enriched["ip_reputation_score"].iloc[0] < enriched["ip_reputation_score"].iloc[-1]
    assert enriched["geolocation_risk_score"].iloc[0] < enriched["geolocation_risk_score"].iloc[-1]


def test_medical_feature_engine():
    """Verify medical triage feature extraction."""
    engine = get_feature_engine("medical")
    df = pd.DataFrame({
        "heart_rate": [70, 85, 120, 160],
        "blood_pressure_systolic": [115, 130, 160, 190],
        "oxygen_saturation": [99, 96, 92, 85],
        "age": [25, 45, 68, 82],
        "diabetes": [0, 0, 1, 1],
        "hypertension": [0, 1, 1, 1],
        "heart_disease": [0, 0, 0, 1],
    })
    enriched = engine.extract_all(df)
    assert "heart_rate_zscore" in enriched.columns
    assert "blood_pressure_systolic_zscore" in enriched.columns
    assert "oxygen_saturation_zscore" in enriched.columns
    assert "age_risk_factor" in enriched.columns
    assert "comorbidity_score" in enriched.columns

    assert enriched["comorbidity_score"].iloc[0] == 0.0
    assert enriched["comorbidity_score"].iloc[-1] == 1.0


def test_forex_feature_engine():
    """Verify technical forex indicator calculation."""
    engine = get_feature_engine("forex")
    np.random.seed(42)
    closes = np.cumsum(np.random.randn(30)) + 100.0
    df = pd.DataFrame({
        "open": closes - 0.2,
        "high": closes + 0.5,
        "low": closes - 0.5,
        "close": closes,
        "volume": [1000] * 30,
    })
    enriched = engine.extract_all(df)
    expected_cols = [
        "candle_body",
        "candle_range",
        "wick_balance_ratio",
        "atr",
        "rsi",
        "ema_spread",
        "macd_hist",
        "adx",
        "bb_bandwidth",
    ]
    for col in expected_cols:
        assert col in enriched.columns
        assert not enriched[col].isna().all()


def test_manufacturing_feature_engine():
    """Verify manufacturing sensor anomaly score calculation."""
    engine = get_feature_engine("manufacturing")
    df = pd.DataFrame({
        "sensor_1": [100.0, 102.0, 99.0, 150.0],
        "sensor_2": [50.0, 49.0, 51.0, 85.0],
        "hours_since_maintenance": [100, 300, 800, 2200],
    })
    enriched = engine.extract_all(df)
    assert "sensor_1_zscore" in enriched.columns
    assert "sensor_1_trend" in enriched.columns
    assert "anomaly_score" in enriched.columns
    assert "maintenance_risk" in enriched.columns

    # The outlier on row 3 should produce the highest anomaly score
    assert enriched["anomaly_score"].iloc[3] > enriched["anomaly_score"].iloc[0]
    assert enriched["maintenance_risk"].iloc[3] == 1.0


def test_security_feature_engine():
    """Verify security log feature extraction."""
    engine = get_feature_engine("security")
    df = pd.DataFrame({
        "ip_reputation": ["CLEAN", "SUSPICIOUS", "MALICIOUS"],
        "request_velocity_1m": [10, 60, 600],
        "payload_size": [200, 450, 5000],
        "failed_logins": [0, 2, 8],
        "password_resets": [0, 1, 3],
        "unusual_access": [0, 1, 1],
        "off_hours_access": [0, 0, 1],
    })
    enriched = engine.extract_all(df)
    assert "ip_reputation_score" in enriched.columns
    assert "request_velocity_1s" in enriched.columns
    assert "payload_anomaly_score" in enriched.columns
    assert "user_behavior_risk" in enriched.columns

    assert enriched["user_behavior_risk"].iloc[-1] > enriched["user_behavior_risk"].iloc[0]


def test_graceful_missing_columns():
    """Verify that feature engines don't crash when optional columns are missing."""
    empty_df = pd.DataFrame({"random_col": [1, 2, 3]})
    for domain in ["fraud", "medical", "forex", "manufacturing", "security", "general"]:
        engine = get_feature_engine(domain)
        enriched = engine.extract_all(empty_df)
        assert isinstance(enriched, pd.DataFrame)
        assert len(enriched) == 3
