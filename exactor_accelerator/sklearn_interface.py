"""
Scikit-Learn Compatible Interface for ExactorAccelerator (Neuro-Symbolic Exact Inference).
Provides standard Estimator & Classifier wrappers:
 - ExactorAcceleratorClassifier: Supports Binary (C = 2) and Multi-Class (C > 2 via One-vs-Rest Hypercubes).
 - ExactorAcceleratorMultiLabelClassifier: Supports Multi-Label (K simultaneous binary targets).

Compatible with Pipeline, GridSearchCV, cross_val_score, and classification_report.
"""

from typing import Union, List, Dict, Any, Optional
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin

from .engine.runtime import HybridRuntime


class ExactorAcceleratorClassifier(BaseEstimator, ClassifierMixin):
    """
    Scikit-Learn Compatible Classifier powered by ExactorAccelerator.
    Combines exact Boolean Hypercube induction (Exactor) with LLM/RLCD semantic reasoning (JEV).
    Supports both Binary (C=2) and Native Multi-Class (C>2) classification.
    """

    def __init__(
        self,
        max_variables: int = 12,
        default_threshold: float = 0.80,
        use_cloud_exactor: bool = False,
        exactor_token: Optional[str] = None,
        jev_token: Optional[str] = None,
        deepseek_api_key: Optional[str] = None,
        db_path: str = ":memory:",
        fast_path: bool = True,
        domain: str = "general",
        fast_path_threshold: Optional[float] = None,
        anchor_critical_rules: bool = False,
        **kwargs: Any,
    ):
        self.max_variables = max_variables
        self.default_threshold = fast_path_threshold if fast_path_threshold is not None else default_threshold
        self.use_cloud_exactor = use_cloud_exactor
        self.exactor_token = exactor_token
        self.jev_token = jev_token
        self.deepseek_api_key = deepseek_api_key
        self.db_path = db_path
        self.fast_path = fast_path
        self.domain = domain
        self.fast_path_threshold = fast_path_threshold if fast_path_threshold is not None else default_threshold
        self.anchor_critical_rules = anchor_critical_rules
        self.extra_kwargs = kwargs

        self._runtime: Optional[HybridRuntime] = None
        self._class_runtimes: Dict[Any, HybridRuntime] = {}
        self.classes_: Optional[np.ndarray] = None
        self.is_multiclass_: bool = False
        self.feature_names_in_: Optional[List[str]] = None
        self.formula_expr_: Optional[str] = None
        self.formulas_: Dict[Any, str] = {}
        self.propositions_: Optional[List[str]] = None
        self.propositions_by_class_: Dict[Any, List[str]] = {}
        self.is_fitted_: bool = False

    def _create_runtime(self) -> HybridRuntime:
        return HybridRuntime(
            db_path=self.db_path,
            default_threshold=self.default_threshold,
            jev_api_key=self.jev_token,
            use_cloud_exactor=self.use_cloud_exactor,
            exactor_api_key=self.exactor_token,
            deepseek_api_key=self.deepseek_api_key,
        )

    # -------------------------------------------------------------------------
    # 1. SCIKIT-LEARN: FIT
    # -------------------------------------------------------------------------
    def fit(self, X: Union[pd.DataFrame, np.ndarray, List[Dict[str, Any]]], y: Union[pd.Series, np.ndarray, List[Any]]):
        """
        Ajusta el motor causal EXACTOR en el hipercubo booleano B^k.
        Supports binary and multi-class classification (C > 2).
        """
        if isinstance(X, np.ndarray):
            feature_names = [f"feature_{i}" for i in range(X.shape[1])]
            df_X = pd.DataFrame(X, columns=feature_names)
        elif isinstance(X, list):
            df_X = pd.DataFrame(X)
            feature_names = list(df_X.columns)
        elif isinstance(X, pd.DataFrame):
            df_X = X.copy()
            feature_names = list(df_X.columns)
        else:
            raise TypeError("X debe ser DataFrame de pandas, array de numpy o lista de dicts.")

        self.feature_names_in_ = feature_names

        # Convertir etiquetas y
        y_arr = np.array(y)
        self.classes_ = np.unique(y_arr)
        n_classes = len(self.classes_)

        if n_classes < 2:
            raise ValueError("Se requieren al menos 2 clases distintas en y.")

        self.is_multiclass_ = (n_classes > 2)

        if not self.is_multiclass_:
            # -------------------------------------------------------------
            # MODO BINARIO (C = 2)
            # -------------------------------------------------------------
            self._runtime = self._create_runtime()
            target_col = "__target_label__"
            df_train = df_X.copy()
            df_train[target_col] = (y_arr == self.classes_[-1]).astype(int)

            res = self._runtime.phase_a_onboard(
                df=df_train,
                target_col=target_col,
                max_variables=self.max_variables,
                trigger_reason="SKLEARN_FIT_BINARY",
            )
            self.formula_expr_ = res.get("formula_expr")
            self.propositions_ = [p.name for p in self._runtime.binarizer.propositions]
        else:
            # -------------------------------------------------------------
            # MODO MULTI-CLASE (C > 2): One-vs-Rest Hypercube Ensemble
            # -------------------------------------------------------------
            self._class_runtimes = {}
            self.formulas_ = {}
            self.propositions_by_class_ = {}

            for c in self.classes_:
                c_runtime = self._create_runtime()
                target_col = f"__target_{str(c).replace(' ', '_')}__"
                df_train = df_X.copy()
                df_train[target_col] = (y_arr == c).astype(int)

                res = c_runtime.phase_a_onboard(
                    df=df_train,
                    target_col=target_col,
                    max_variables=self.max_variables,
                    trigger_reason=f"SKLEARN_FIT_MULTICLASS_{c}",
                )
                self._class_runtimes[c] = c_runtime
                self.formulas_[c] = res.get("formula_expr")
                self.propositions_by_class_[c] = [p.name for p in c_runtime.binarizer.propositions]

            self.formula_expr_ = f"MULTI_CLASS_ENSEMBLE({n_classes} classes: {', '.join(map(str, self.classes_))})"
            self.propositions_ = list({p for plist in self.propositions_by_class_.values() for p in plist})

        self.is_fitted_ = True
        return self

    # -------------------------------------------------------------------------
    # 2. SCIKIT-LEARN: PREDICT
    # -------------------------------------------------------------------------
    def predict(self, X: Union[pd.DataFrame, np.ndarray, List[Dict[str, Any]]]) -> np.ndarray:
        """
        Predice las clases de las muestras en X.
        """
        if not self.is_fitted_:
            raise RuntimeError("Este estimador no ha sido entrenado. Llama a fit() primero.")

        if not self.is_multiclass_:
            records = self._convert_x_to_records(X)
            predictions = []
            for row in records:
                res = self._runtime.phase_b_query(row, fast_path=self.fast_path)
                pred_idx = 1 if res.decision_status == "CRITICAL" or res.exact_boolean_evaluation == 1 else 0
                predictions.append(self.classes_[pred_idx])
            return np.array(predictions)
        else:
            probas = self.predict_proba(X)
            best_indices = np.argmax(probas, axis=1)
            return np.array([self.classes_[idx] for idx in best_indices])

    # -------------------------------------------------------------------------
    # 3. SCIKIT-LEARN: PREDICT_PROBA
    # -------------------------------------------------------------------------
    def predict_proba(self, X: Union[pd.DataFrame, np.ndarray, List[Dict[str, Any]]]) -> np.ndarray:
        """
        Calcula las probabilidades calibradas para cada clase.
        """
        if not self.is_fitted_:
            raise RuntimeError("Este estimador no ha sido entrenado. Llama a fit() primero.")

        records = self._convert_x_to_records(X)

        if not self.is_multiclass_:
            probas = []
            for row in records:
                res = self._runtime.phase_b_query(row, fast_path=self.fast_path)
                p1 = float(res.criterio_logico_prob)
                p0 = 1.0 - p1
                probas.append([p0, p1])
            return np.array(probas)
        else:
            # Multi-Class One-vs-Rest Probability Matrix
            all_sample_probas = []
            for row in records:
                raw_scores = []
                for c in self.classes_:
                    rt = self._class_runtimes[c]
                    res = rt.phase_b_query(row, fast_path=self.fast_path)
                    
                    score = float(res.criterio_logico_prob)
                    # If the exact boolean rule is satisfied, add formal weight
                    if res.exact_boolean_evaluation == 1 or res.decision_status == "CRITICAL":
                        score += 1.0
                    raw_scores.append(max(0.01, score))

                # Softmax / Sum Normalization
                exp_scores = np.exp(np.array(raw_scores) - np.max(raw_scores))
                normalized_p = exp_scores / np.sum(exp_scores)
                all_sample_probas.append(normalized_p)

            return np.array(all_sample_probas)

    # -------------------------------------------------------------------------
    # 4. SCIKIT-LEARN: SCORE
    # -------------------------------------------------------------------------
    def score(self, X: Union[pd.DataFrame, np.ndarray, List[Dict[str, Any]]], y: Union[pd.Series, np.ndarray, List[Any]]) -> float:
        """Calcula el Mean Accuracy en el conjunto de prueba."""
        y_pred = self.predict(X)
        y_true = np.array(y)
        return float(np.mean(y_pred == y_true))

    # -------------------------------------------------------------------------
    # 5. SCIKIT-LEARN: GET_PARAMS / SET_PARAMS
    # -------------------------------------------------------------------------
    def get_params(self, deep: bool = True) -> Dict[str, Any]:
        return {
            "max_variables": self.max_variables,
            "default_threshold": self.default_threshold,
            "use_cloud_exactor": self.use_cloud_exactor,
            "exactor_token": self.exactor_token,
            "jev_token": self.jev_token,
            "deepseek_api_key": self.deepseek_api_key,
            "db_path": self.db_path,
            "fast_path": self.fast_path,
        }

    def set_params(self, **params):
        for key, value in params.items():
            setattr(self, key, value)
        return self

    # -------------------------------------------------------------------------
    # 6. EXPLAINABILITY AND AUDIT
    # -------------------------------------------------------------------------
    def explain(self, sample: Union[Dict[str, Any], pd.DataFrame, pd.Series]) -> str:
        """Generates a causal audit explanation for a specific sample (dict, Series, or DataFrame)."""
        if not self.is_fitted_:
            raise RuntimeError("This estimator is not fitted yet. Call fit() first.")

        if isinstance(sample, pd.DataFrame):
            sample_dict = sample.iloc[0].to_dict()
        elif isinstance(sample, pd.Series):
            sample_dict = sample.to_dict()
        else:
            sample_dict = dict(sample)

        if not self.is_multiclass_:
            eval_res = self._runtime.phase_b_query(raw_state=sample_dict, fast_path=self.fast_path)
            exp = self._runtime.deepseek_explainer.generate_explanation(
                event_state=sample_dict,
                active_propositions=eval_res.propositions_evaluated,
                exact_eval=eval_res.exact_boolean_evaluation,
                criterio_prob=eval_res.criterio_logico_prob,
                chosen_action=eval_res.chosen_action,
                autonomous_executed=eval_res.autonomous_action_executed,
                rule_formula=self.formula_expr_,
            )
            return exp.get("explanation", "")
        else:
            # Multi-Class Explanation
            probas = self.predict_proba([sample_dict])[0]
            winning_idx = np.argmax(probas)
            winning_class = self.classes_[winning_idx]
            winning_rt = self._class_runtimes[winning_class]
            eval_res = winning_rt.phase_b_query(raw_state=sample_dict, fast_path=self.fast_path)

            lines = [
                f"**Multi-Class Result:** Winning Class = `{winning_class}` (Probability: {probas[winning_idx]*100:.1f}%)",
                "**Probability Distribution:** " + ", ".join([f"{c}: {p*100:.1f}%" for c, p in zip(self.classes_, probas)]),
                f"**Active Boolean Formula:** `{self.formulas_.get(winning_class, '')}`",
                f"**Active Propositions:** {list(eval_res.propositions_evaluated.keys())}",
            ]
            return "\n".join(lines)

    explain_decision = explain

    def _convert_x_to_records(self, X: Union[pd.DataFrame, np.ndarray, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
        if isinstance(X, pd.DataFrame):
            return X.to_dict(orient="records")
        elif isinstance(X, np.ndarray):
            df = pd.DataFrame(X, columns=self.feature_names_in_)
            return df.to_dict(orient="records")
        elif isinstance(X, list):
            if len(X) > 0 and isinstance(X[0], dict):
                return X
            df = pd.DataFrame(X, columns=self.feature_names_in_)
            return df.to_dict(orient="records")
        else:
            raise TypeError("Formato de entrada no soportado.")


class ExactorAcceleratorMultiLabelClassifier(BaseEstimator, ClassifierMixin):
    """
    Multi-Label Classifier powered by ExactorAccelerator.
    Trains independent Boolean Hypercubes for multiple simultaneous targets (K binary outputs).
    """

    def __init__(
        self,
        max_variables: int = 12,
        default_threshold: float = 0.80,
        use_cloud_exactor: bool = False,
        fast_path: bool = True,
    ):
        self.max_variables = max_variables
        self.default_threshold = default_threshold
        self.use_cloud_exactor = use_cloud_exactor
        self.fast_path = fast_path

        self.label_names_: List[str] = []
        self._label_classifiers: Dict[str, ExactorAcceleratorClassifier] = {}
        self.is_fitted_: bool = False

    def fit(self, X: Union[pd.DataFrame, np.ndarray], Y: Union[pd.DataFrame, np.ndarray]):
        """
        Entrena clasificadores independientes para cada una de las K etiquetas objetivo.
        """
        if isinstance(Y, pd.DataFrame):
            self.label_names_ = list(Y.columns)
            Y_matrix = Y.values
        else:
            Y_arr = np.array(Y)
            self.label_names_ = [f"label_{i}" for i in range(Y_arr.shape[1])]
            Y_matrix = Y_arr

        self._label_classifiers = {}
        for idx, lbl in enumerate(self.label_names_):
            y_col = Y_matrix[:, idx]
            clf = ExactorAcceleratorClassifier(
                max_variables=self.max_variables,
                default_threshold=self.default_threshold,
                use_cloud_exactor=self.use_cloud_exactor,
                fast_path=self.fast_path,
            )
            clf.fit(X, y_col)
            self._label_classifiers[lbl] = clf

        self.is_fitted_ = True
        return self

    def predict(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Retorna matriz binaria (n_samples, n_labels) con 0/1 para cada etiqueta."""
        if not self.is_fitted_:
            raise RuntimeError("Estimador no entrenado.")
        
        preds = []
        for lbl in self.label_names_:
            preds.append(self._label_classifiers[lbl].predict(X))
        
        return np.column_stack(preds)

    def predict_proba(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        """Retorna matriz de probabilidades (n_samples, n_labels) para cada etiqueta."""
        if not self.is_fitted_:
            raise RuntimeError("Estimador no entrenado.")
        
        probas = []
        for lbl in self.label_names_:
            p = self._label_classifiers[lbl].predict_proba(X)[:, 1]
            probas.append(p)
        
        return np.column_stack(probas)
