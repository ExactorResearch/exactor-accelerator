"""
Adaptive Binarization Subsystem for EXACTOR + Jev.
Transforms continuous variables and categorical states into discrete propositions (0 and 1)
projected onto the Boolean Hypercube B^k (k <= 64).
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd


class Proposition:
    """Represents a discrete Boolean proposition derived from an input feature."""

    def __init__(
        self,
        name: str,
        source_col: str,
        op: str,
        threshold: Any,
        description: str,
        var_index: int = 0,
    ):
        self.name = name
        self.source_col = source_col
        self.op = op
        self.threshold = threshold
        self.description = description
        self.var_index = var_index

    def evaluate(self, val: Any) -> int:
        """Evaluates a raw feature value against this proposition's threshold condition."""
        if val is None or pd.isna(val):
            return 0

        try:
            if self.op == ">":
                return 1 if float(val) > float(self.threshold) else 0
            elif self.op == ">=":
                return 1 if float(val) >= float(self.threshold) else 0
            elif self.op == "<":
                return 1 if float(val) < float(self.threshold) else 0
            elif self.op == "<=":
                return 1 if float(val) <= float(self.threshold) else 0
            elif self.op == "==":
                return 1 if str(val).strip().lower() == str(self.threshold).strip().lower() else 0
            elif self.op == "!=":
                return 1 if str(val).strip().lower() != str(self.threshold).strip().lower() else 0
            elif self.op == "in":
                return 1 if str(val).strip().lower() in [s.lower() for s in self.threshold] else 0
            elif self.op == "text_feature":
                from .text_extractor import TextFeatureExtractor
                feats = TextFeatureExtractor.extract_from_conversation(val)
                return feats.get(str(self.threshold), 0)
            elif self.op == "semantic_auto_feature":
                from .semantic_discovery import SemanticPropositionDiscovery
                if isinstance(self.threshold, dict) and "pattern" in self.threshold:
                    import re
                    pat = self.threshold["pattern"]
                    return 1 if re.search(pat, str(val), re.IGNORECASE) else 0
                return 0
            else:
                return 0
        except (ValueError, TypeError):
            return 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "source_col": self.source_col,
            "op": self.op,
            "threshold": self.threshold,
            "description": self.description,
            "var_index": self.var_index,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Proposition":
        return cls(
            name=data["name"],
            source_col=data["source_col"],
            op=data["op"],
            threshold=data["threshold"],
            description=data["description"],
            var_index=data.get("var_index", 0),
        )


class BinarizationResult:
    """Encapsulates the result of projecting a dataset onto the Boolean Hypercube."""

    def __init__(
        self,
        variables: List[str],
        propositions: List[Proposition],
        bit_matrix: np.ndarray,
        minterms_on: List[int],
        minterms_off: List[int],
        minterm_counts: Dict[int, int],
        target_col: Optional[str] = None,
        target_vector: Optional[np.ndarray] = None,
    ):
        self.variables = variables
        self.propositions = propositions
        self.bit_matrix = bit_matrix
        self.minterms_on = sorted(list(set(minterms_on)))
        self.minterms_off = sorted(list(set(minterms_off)))
        self.minterm_counts = minterm_counts
        self.target_col = target_col
        self.target_vector = target_vector

    def get_hypercube_dimension(self) -> int:
        return len(self.variables)

    def summary(self) -> Dict[str, Any]:
        return {
            "hypercube_dimension_k": len(self.variables),
            "variable_names": self.variables,
            "total_records": len(self.bit_matrix),
            "unique_on_minterms": len(self.minterms_on),
            "unique_off_minterms": len(self.minterms_off),
            "target_col": self.target_col,
            "propositions": [p.to_dict() for p in self.propositions],
        }


class AdaptiveBinarizer:
    """
    Adaptive pre-processor that converts tabular records into Boolean hypercube minterms.
    Supports continuous numerical variables (via intelligent quantiles & entropy splitting)
    and discrete categorical states.
    """

    def __init__(self, max_variables: int = 16, quantile_count: int = 2):
        self.max_variables = min(max_variables, 64)  # Exactor 64-bit Gray code limit
        self.quantile_count = quantile_count
        self.propositions: List[Proposition] = []
        self.variables: List[str] = []
        self.target_col: Optional[str] = None
        self.is_fitted: bool = False

    def fit(self, df: pd.DataFrame, target_col: Optional[str] = None) -> "AdaptiveBinarizer":
        """Calculates optimal discretization thresholds across columns."""
        self.target_col = target_col
        self.propositions = []
        self.variables = []

        feature_cols = [c for c in df.columns if c != target_col]
        props_to_add: List[Proposition] = []

        for col in feature_cols:
            if len(props_to_add) >= self.max_variables:
                break

            series = df[col].dropna()
            if series.empty:
                continue

            # Numeric continuous feature
            if pd.api.types.is_numeric_dtype(series):
                unique_vals = series.nunique()
                if unique_vals <= 2:
                    # Binary already
                    thresh = float(series.min() + (series.max() - series.min()) / 2.0)
                    p_name = f"is_{col}"
                    props_to_add.append(
                        Proposition(
                            name=p_name,
                            source_col=col,
                            op=">",
                            threshold=thresh,
                            description=f"{col} > {thresh:.2f}",
                            var_index=len(props_to_add),
                        )
                    )
                else:
                    # If target is available and binary, use target-informed split
                    if target_col and target_col in df.columns and df[target_col].nunique() == 2:
                        target = df[target_col]
                        class_0 = series[target == 0]
                        class_1 = series[target == 1]
                        
                        if len(class_0) > 0 and len(class_1) > 0:
                            m0 = class_0.median()
                            m1 = class_1.median()
                            thresh_mid = float((m0 + m1) / 2.0)
                            p_name = f"{col}_above_target_median"
                            props_to_add.append(
                                Proposition(
                                    name=p_name,
                                    source_col=col,
                                    op=">",
                                    threshold=thresh_mid,
                                    description=f"{col} > {thresh_mid:.2f} (optimal target boundary)",
                                    var_index=len(props_to_add),
                                )
                            )

                    # Standard quantile thresholding (e.g. median or 75th percentile)
                    if len(props_to_add) < self.max_variables:
                        q75 = float(series.quantile(0.75))
                        p_name_high = f"{col}_high"
                        props_to_add.append(
                            Proposition(
                                name=p_name_high,
                                source_col=col,
                                op=">",
                                threshold=q75,
                                description=f"{col} in top quartile (> {q75:.2f})",
                                var_index=len(props_to_add),
                            )
                        )

                    if len(props_to_add) < self.max_variables and self.quantile_count > 1:
                        q25 = float(series.quantile(0.25))
                        p_name_low = f"{col}_low"
                        props_to_add.append(
                            Proposition(
                                name=p_name_low,
                                source_col=col,
                                op="<",
                                threshold=q25,
                                description=f"{col} in bottom quartile (< {q25:.2f})",
                                var_index=len(props_to_add),
                            )
                        )

                    # Higher granularity when max_variables >= 20
                    if len(props_to_add) < self.max_variables and self.max_variables >= 20:
                        q50 = float(series.quantile(0.50))
                        props_to_add.append(
                            Proposition(
                                name=f"{col}_above_median",
                                source_col=col,
                                op=">",
                                threshold=q50,
                                description=f"{col} above median (> {q50:.2f})",
                                var_index=len(props_to_add),
                            )
                        )

                    if len(props_to_add) < self.max_variables and self.max_variables >= 24:
                        q90 = float(series.quantile(0.90))
                        props_to_add.append(
                            Proposition(
                                name=f"{col}_top_decile",
                                source_col=col,
                                op=">",
                                threshold=q90,
                                description=f"{col} top 10% extreme (> {q90:.2f})",
                                var_index=len(props_to_add),
                            )
                        )
                    if len(props_to_add) < self.max_variables and self.max_variables >= 28:
                        q10 = float(series.quantile(0.10))
                        props_to_add.append(
                            Proposition(
                                name=f"{col}_bottom_decile",
                                source_col=col,
                                op="<",
                                threshold=q10,
                                description=f"{col} bottom 10% extreme (< {q10:.2f})",
                                var_index=len(props_to_add),
                            )
                        )

            # Categorical or Unstructured Text feature
            else:
                col_lower = col.lower()
                # Skip identifier / primary key columns
                if col_lower == "id" or col_lower.endswith("_id") or col_lower.endswith("_uuid"):
                    continue

                sample_strs = [str(x) for x in series.head(20)]
                avg_len = sum(len(s) for s in sample_strs) / max(1, len(sample_strs))
                text_indicators = ["text", "transcript", "dialogue", "conversation", "message", "mensaje", "contenido", "chat", "comment", "feedback"]
                is_text_unstructured = any(ind in col_lower for ind in text_indicators) or avg_len > 25

                if is_text_unstructured:
                    # 1. Attempt dynamic semantic proposition auto-discovery (Zero-Regex via LLM/Lexicon)
                    from .semantic_discovery import SemanticPropositionDiscovery
                    discovery = SemanticPropositionDiscovery()
                    labels_list = df[target_col].tolist() if (target_col and target_col in df.columns) else None
                    discovered_map = discovery.discover_from_corpus(
                        series.tolist(),
                        target_labels=labels_list,
                        max_propositions=min(8, self.max_variables - len(props_to_add)),
                        domain_hint=col
                    )

                    for p_key, p_meta in discovered_map.items():
                        if len(props_to_add) >= self.max_variables:
                            break
                        props_to_add.append(
                            Proposition(
                                name=f"{col}_{p_key}",
                                source_col=col,
                                op="semantic_auto_feature",
                                threshold={"pattern": p_meta["pattern"]},
                                description=p_meta["description"],
                                var_index=len(props_to_add),
                            )
                        )

                    # 2. Complement with standard structural features if capacity remains
                    structural_props = [
                        ("has_cancellation", "text_has_cancellation_intent", "Expresses cancellation intent, churn, or refund request"),
                        ("has_billing_issue", "text_has_billing_payment_issue", "Billing issue, invoice dispute, payment or credit card problem"),
                        ("has_urgency", "text_has_urgency_critical", "Critical urgency indicator (asap, immediately)"),
                        ("has_frustration", "text_has_frustration_anger", "Frustration sentiment, severe complaint or anger"),
                        ("has_legal_threat", "text_has_legal_threat", "Legal action mention, lawsuit, or consumer protection"),
                        ("is_long_text", "text_is_long", "Long text message or dialogue (> 25 words)"),
                        ("has_exclamation", "text_has_exclamation", "Exclamation marks or high intensity text"),
                    ]
                    for p_suffix, feat_key, desc in structural_props:
                        if len(props_to_add) >= self.max_variables:
                            break
                        props_to_add.append(
                            Proposition(
                                name=f"{col}_{p_suffix}",
                                source_col=col,
                                op="text_feature",
                                threshold=feat_key,
                                description=desc,
                                var_index=len(props_to_add),
                            )
                        )
                else:
                    cat_limit = 8 if self.max_variables >= 24 else 3
                    top_categories = series.value_counts().head(cat_limit).index.tolist()
                    for cat in top_categories:
                        if len(props_to_add) >= self.max_variables:
                            break
                        p_name = f"{col}_eq_{str(cat).replace(' ', '_').lower()}"
                        props_to_add.append(
                            Proposition(
                                name=p_name,
                                source_col=col,
                                op="==",
                                threshold=str(cat),
                                description=f"{col} == '{cat}'",
                                var_index=len(props_to_add),
                            )
                        )

        # Truncate to max_variables if needed
        self.propositions = props_to_add[: self.max_variables]
        for idx, p in enumerate(self.propositions):
            p.var_index = idx
        self.variables = [p.name for p in self.propositions]
        self.is_fitted = True
        return self

    def transform(self, df: pd.DataFrame) -> BinarizationResult:
        """Transforms a DataFrame into minterms on the Boolean hypercube."""
        if not self.is_fitted:
            raise RuntimeError("AdaptiveBinarizer must be fit before calling transform().")

        num_rows = len(df)
        num_vars = len(self.propositions)
        bit_matrix = np.zeros((num_rows, num_vars), dtype=np.uint8)

        for col_idx, prop in enumerate(self.propositions):
            col_series = df.get(prop.source_col)
            if col_series is not None:
                bit_matrix[:, col_idx] = [prop.evaluate(val) for val in col_series]
            else:
                bit_matrix[:, col_idx] = 0

        # Convert bit rows to integer minterm index
        # bit_matrix[:, 0] is the most significant bit or least significant.
        # Standard convention: v = sum(bit_matrix[:, i] * (1 << (num_vars - 1 - i)))
        powers = 1 << np.arange(num_vars - 1, -1, -1, dtype=np.uint64)
        minterm_values = np.dot(bit_matrix.astype(np.uint64), powers)

        minterms_on: List[int] = []
        minterms_off: List[int] = []
        minterm_counts: Dict[int, int] = {}
        target_vector: Optional[np.ndarray] = None

        for idx, m_val in enumerate(minterm_values):
            int_m = int(m_val)
            minterm_counts[int_m] = minterm_counts.get(int_m, 0) + 1

        if self.target_col and self.target_col in df.columns:
            target_series = df[self.target_col].fillna(0).astype(int).values
            target_vector = target_series
            for idx, m_val in enumerate(minterm_values):
                int_m = int(m_val)
                if target_series[idx] == 1:
                    minterms_on.append(int_m)
                else:
                    minterms_off.append(int_m)
        else:
            minterms_on = list(minterm_counts.keys())

        return BinarizationResult(
            variables=self.variables,
            propositions=self.propositions,
            bit_matrix=bit_matrix,
            minterms_on=minterms_on,
            minterms_off=minterms_off,
            minterm_counts=minterm_counts,
            target_col=self.target_col,
            target_vector=target_vector,
        )

    def transform_single(self, record: Dict[str, Any]) -> Tuple[int, Dict[str, int]]:
        """
        Projects a single real-time event record into a minterm integer and proposition map.
        Used by the Phase B real-time inference loop.
        """
        if not self.is_fitted:
            raise RuntimeError("AdaptiveBinarizer is not fitted yet.")

        num_vars = len(self.propositions)
        minterm_val = 0
        prop_map: Dict[str, int] = {}

        for idx, prop in enumerate(self.propositions):
            val = record.get(prop.source_col)
            if val is None and prop.op == "text_feature":
                for alt_key in ["text", "transcript", "dialogue", "conversation", "message", "mensaje", "chat", "content", "user_message", "texto"]:
                    if alt_key in record:
                        val = record[alt_key]
                        break
            bit = prop.evaluate(val)
            prop_map[prop.name] = bit
            if bit == 1:
                minterm_val |= 1 << (num_vars - 1 - idx)

        return minterm_val, prop_map

    def export_state(self) -> Dict[str, Any]:
        """Serializes binarizer state for persistence."""
        return {
            "max_variables": self.max_variables,
            "quantile_count": self.quantile_count,
            "target_col": self.target_col,
            "is_fitted": self.is_fitted,
            "variables": self.variables,
            "propositions": [p.to_dict() for p in self.propositions],
        }

    @classmethod
    def import_state(cls, state: Dict[str, Any]) -> "AdaptiveBinarizer":
        """Reconstructs binarizer from serialized dictionary."""
        binarizer = cls(
            max_variables=state.get("max_variables", 16),
            quantile_count=state.get("quantile_count", 2),
        )
        binarizer.target_col = state.get("target_col")
        binarizer.is_fitted = state.get("is_fitted", False)
        binarizer.variables = state.get("variables", [])
        binarizer.propositions = [Proposition.from_dict(p) for p in state.get("propositions", [])]
        return binarizer
