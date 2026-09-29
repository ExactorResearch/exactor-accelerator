"""
Domain Regime Detector for ExactorAccelerator v2.0

Detects regime changes in structured domains (fraud, medical, forex, manufacturing, security)
to enable adaptive thresholds and concept drift detection.
"""

from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from collections import Counter
from scipy import stats


class DomainRegimeDetector:
    """
    Generalized regime detector for structured domains.
    
    Automatically detects: STABLE_PATTERN, DRIFTING_PATTERN, HIGH_ENTROPY, CONCEPT_DRIFT
    and dynamically adjusts thresholds based on detected regime.
    """
    
    REGIMES = ["STABLE_PATTERN", "DRIFTING_PATTERN", "HIGH_ENTROPY", "CONCEPT_DRIFT"]
    
    def __init__(self, domain: str = "general", window_size: int = 50, drift_threshold: float = 0.3):
        """
        Initializes the regime detector.
        
        Args:
            domain: Specific domain (fraud, medical, forex, manufacturing, security)
            window_size: Window size for historical analysis
            drift_threshold: Threshold para detectar concept drift
        """
        self.domain = domain
        self.window_size = window_size
        self.drift_threshold = drift_threshold
        self.regime_history = []
        
    def analyze_regime(
        self, 
        features: Dict[str, Any], 
        history_df: Optional[pd.DataFrame] = None
    ) -> Dict[str, Any]:
        """
        Detects regime based on stability, entropy, and concept drift.
        
        Args:
            features: Features actuales del estado
            history_df: Historical DataFrame of features and predictions
            
        Returns:
            Dict with detected regime details
        """
        if history_df is None or len(history_df) < 10:
            return self._default_regime()
        
        # Calculate regime metrics
        feature_stability = self._calculate_feature_stability(features, history_df)
        class_entropy = self._calculate_class_entropy(history_df)
        drift_score = self._detect_concept_drift(history_df)
        
        # Calculate regime probabilities
        regime_probs = {
            "STABLE_PATTERN": feature_stability * 0.4,
            "DRIFTING_PATTERN": drift_score * 0.3,
            "HIGH_ENTROPY": class_entropy * 0.3,
            "CONCEPT_DRIFT": drift_score * 0.3,
        }
        
        # Normalizar probabilidades
        total = sum(regime_probs.values())
        if total > 0:
            regime_probs = {k: v / total for k, v in regime_probs.items()}
        
        # Determine dominant regime
        dominant_regime = max(regime_probs, key=regime_probs.get)
        
        # Determinar gate de accionabilidad
        actionability_gate = self._determine_gate(regime_probs)
        
        # Guardar en historial
        self.regime_history.append({
            "regime": dominant_regime,
            "probabilities": regime_probs,
            "stability_index": feature_stability,
            "entropy_index": class_entropy,
            "drift_score": drift_score,
            "actionability_gate": actionability_gate,
        })
        
        return {
            "regime": dominant_regime,
            "dominant_regime": dominant_regime,
            "regime_distribution": regime_probs,
            "stability_index": feature_stability,
            "entropy_index": class_entropy,
            "drift_score": drift_score,
            "actionability_gate": actionability_gate,
            "recommendation": self._get_regime_recommendation(dominant_regime),
        }
    
    def _default_regime(self) -> Dict[str, Any]:
        """Returns default regime when insufficient history is available."""
        return {
            "regime": "STABLE_PATTERN",
            "dominant_regime": "STABLE_PATTERN",
            "regime_distribution": {"STABLE_PATTERN": 1.0},
            "stability_index": 1.0,
            "entropy_index": 0.0,
            "drift_score": 0.0,
            "actionability_gate": "PROCEED",
            "recommendation": "Insufficient historical data - using default stable regime",
        }
    
    def _calculate_feature_stability(self, features: Dict[str, Any], history_df: pd.DataFrame) -> float:
        """
        Calculates feature stability based on historical variance.
        
        Returns:
            float: Stability index (0-1, where 1 is very stable)
        """
        if len(history_df) < 10:
            return 1.0
        
        # Calculate numerical feature variance
        numeric_features = history_df.select_dtypes(include=[np.number])
        
        if numeric_features.empty:
            return 1.0
        
        # Calculate coefficient of variation
        cv = numeric_features.std() / (numeric_features.mean() + 1e-6)
        
        # Invert: lower variation = higher stability
        stability = 1.0 - cv.mean()
        
        return max(0.0, min(1.0, stability))
    
    def _calculate_class_entropy(self, history_df: pd.DataFrame) -> float:
        """
        Calculates class distribution entropy.
        
        Returns:
            float: Entropy index (0-1, where 1 is high entropy)
        """
        # Search for prediction/target column
        target_col = None
        for col in history_df.columns:
            if col in ["target", "prediction", "label", "class"]:
                target_col = col
                break
        
        if target_col is None:
            return 0.0
        
        # Calculate class distribution
        class_counts = Counter(history_df[target_col])
        total = len(history_df)
        
        if total == 0:
            return 0.0
        
        # Calculate Shannon entropy
        probabilities = [count / total for count in class_counts.values()]
        entropy = -sum(p * np.log2(p) for p in probabilities if p > 0)
        
        # Normalizar a 0-1
        max_entropy = np.log2(len(class_counts)) if len(class_counts) > 1 else 1.0
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.0
        
        return normalized_entropy
    
    def _detect_concept_drift(self, history_df: pd.DataFrame) -> float:
        """
        Detects concept drift by comparing recent vs historical distributions.
        
        Returns:
            float: Score de drift (0-1, donde 1 es drift severo)
        """
        if len(history_df) < 20:
            return 0.0
        
        # Split into recent vs historical
        split_point = len(history_df) // 2
        recent_df = history_df.iloc[split_point:]
        historical_df = history_df.iloc[:split_point]
        
        # Compare numerical feature distributions
        numeric_features = history_df.select_dtypes(include=[np.number])
        
        if numeric_features.empty:
            return 0.0
        
        drift_scores = []
        for col in numeric_features.columns:
            recent_values = recent_df[col].dropna()
            historical_values = historical_df[col].dropna()
            
            if len(recent_values) < 5 or len(historical_values) < 5:
                continue
            
            # Kolmogorov-Smirnov test to detect distribution shift
            try:
                ks_statistic, p_value = stats.ks_2samp(recent_values, historical_values)
                drift_scores.append(ks_statistic)
            except:
                continue
        
        if not drift_scores:
            return 0.0
        
        # Promedio de scores de drift
        avg_drift = np.mean(drift_scores)
        
        return min(1.0, avg_drift)
    
    def _determine_gate(self, regime_probs: Dict[str, float]) -> str:
        """
        Determines actionability gate based on regime distribution.
        
        Returns:
            str: Gate (PROCEED, CAUTION, HALT)
        """
        drift_prob = regime_probs.get("DRIFTING_PATTERN", 0) + regime_probs.get("CONCEPT_DRIFT", 0)
        entropy_prob = regime_probs.get("HIGH_ENTROPY", 0)
        
        if drift_prob > 0.6:
            return "HALT"
        elif drift_prob > 0.3 or entropy_prob > 0.7:
            return "CAUTION"
        else:
            return "PROCEED"
    
    def _get_regime_recommendation(self, regime: str) -> str:
        """
        Returns regime-specific recommendation.
        
        Args:
            regime: Detected regime
            
        Returns:
            str: Action recommendation
        """
        recommendations = {
            "STABLE_PATTERN": "Continue with current thresholds - system is stable",
            "DRIFTING_PATTERN": "Monitor closely - consider adaptive threshold adjustment",
            "HIGH_ENTROPY": "High uncertainty - increase threshold for fast-path, use Jev for ambiguous cases",
            "CONCEPT_DRIFT": "Significant drift detected - trigger retraining or model update",
        }
        
        return recommendations.get(regime, "Unknown regime")
    
    def get_regime_history(self, n: int = 10) -> List[Dict[str, Any]]:
        """
        Returns history of detected regimes.
        
        Args:
            n: Number of entries to return
            
        Returns:
            List of dicts with regime history
        """
        return self.regime_history[-n:]
    
    def reset_history(self):
        """Resets regime history."""
        self.regime_history = []


# Domain-specific regime detectors

class FraudRegimeDetector(DomainRegimeDetector):
    """Regime detector specialized for fraud detection."""
    
    def __init__(self):
        super().__init__(domain="fraud", window_size=100, drift_threshold=0.25)
    
    def _calculate_feature_stability(self, features: Dict[str, Any], history_df: pd.DataFrame) -> float:
        """Calculates fraud-specific stability."""
        base_stability = super()._calculate_feature_stability(features, history_df)
        
        # Adjust for fraud-specific characteristics
        if "amount" in history_df.columns:
            amount_cv = history_df["amount"].std() / (history_df["amount"].mean() + 1e-6)
            base_stability *= (1.0 - min(0.5, amount_cv))
        
        return max(0.0, min(1.0, base_stability))


class MedicalRegimeDetector(DomainRegimeDetector):
    """Regime detector specialized for clinical triage."""
    
    def __init__(self):
        super().__init__(domain="medical", window_size=50, drift_threshold=0.2)
    
    def _determine_gate(self, regime_probs: Dict[str, float]) -> str:
        """More conservative gate for medical domain."""
        drift_prob = regime_probs.get("DRIFTING_PATTERN", 0) + regime_probs.get("CONCEPT_DRIFT", 0)
        
        if drift_prob > 0.4:  # More sensitive for medical
            return "HALT"
        elif drift_prob > 0.2 or regime_probs.get("HIGH_ENTROPY", 0) > 0.6:
            return "CAUTION"
        else:
            return "PROCEED"


class ForexRegimeDetector(DomainRegimeDetector):
    """Regime detector specialized for technical forex."""
    
    def __init__(self):
        super().__init__(domain="forex", window_size=200, drift_threshold=0.35)
    
    def _calculate_feature_stability(self, features: Dict[str, Any], history_df: pd.DataFrame) -> float:
        """Calculates forex-specific stability."""
        base_stability = super()._calculate_feature_stability(features, history_df)
        
        # Forex is inherently volatile, adjust expectations
        return max(0.0, min(1.0, base_stability * 1.2))


class ManufacturingRegimeDetector(DomainRegimeDetector):
    """Regime detector specialized for quality monitoring."""
    
    def __init__(self):
        super().__init__(domain="manufacturing", window_size=100, drift_threshold=0.3)
    
    def _detect_concept_drift(self, history_df: pd.DataFrame) -> float:
        """Detects manufacturing sensor drift."""
        base_drift = super()._detect_concept_drift(history_df)
        
        # Adjust for sensor anomalies
        if "sensor_zscore" in history_df.columns:
            anomaly_rate = (history_df["sensor_zscore"] > 3).mean()
            base_drift += anomaly_rate * 0.5
        
        return min(1.0, base_drift)


class SecurityRegimeDetector(DomainRegimeDetector):
    """Regime detector specialized for security logs."""
    
    def __init__(self):
        super().__init__(domain="security", window_size=150, drift_threshold=0.25)
    
    def _determine_gate(self, regime_probs: Dict[str, float]) -> str:
        """Gate muy conservador para seguridad."""
        drift_prob = regime_probs.get("DRIFTING_PATTERN", 0) + regime_probs.get("CONCEPT_DRIFT", 0)
        
        if drift_prob > 0.3:  # Muy sensible para seguridad
            return "HALT"
        elif drift_prob > 0.15 or regime_probs.get("HIGH_ENTROPY", 0) > 0.5:
            return "CAUTION"
        else:
            return "PROCEED"


def get_regime_detector(domain: str) -> DomainRegimeDetector:
    """
    Factory to obtain domain-specific regime detector.
    
    Args:
        domain: Dominio (fraud, medical, forex, manufacturing, security, general)
        
    Returns:
        Domain-specific DomainRegimeDetector instance
    """
    detectors = {
        "fraud": FraudRegimeDetector,
        "medical": MedicalRegimeDetector,
        "forex": ForexRegimeDetector,
        "manufacturing": ManufacturingRegimeDetector,
        "security": SecurityRegimeDetector,
        "general": DomainRegimeDetector,
    }
    
    detector_class = detectors.get(domain.lower(), DomainRegimeDetector)
    return detector_class()
