"""
Backward-compatibility shim for exactor_jev.
Aliases all classes to exactor_accelerator so legacy code and coldstart v2 run seamlessly.
"""

import sys
import os

from exactor_accelerator import (
    ExactorAccelerator,
    ExactorAcceleratorClassifier,
    ExactorAcceleratorMultiLabelClassifier,
    AdaptiveBinarizer,
    DataLoader,
    Proposition,
    BinarizationResult,
    SemanticPropositionDiscovery,
    ExactorBridge,
    ExactorHypercubeReducer,
    ExactorSimplificationResult,
    ExactorToJevTranslator,
    JevPayload,
    NoulQuestion,
    ChoiceQuestion,
    ScoreQuestion,
    MemoryLedger,
    JevClient,
    HybridRuntime,
    save_model,
    load_model,
    log_to_mlflow,
    log_to_wandb,
)
from exactor_accelerator.engine.runtime import QueryResult

# Backward-compatible class names
ExactorJev = ExactorAccelerator
ExactorJevClassifier = ExactorAcceleratorClassifier
ExactorJevMultiLabelClassifier = ExactorAcceleratorMultiLabelClassifier

__all__ = [
    "ExactorJev",
    "ExactorJevClassifier",
    "ExactorJevMultiLabelClassifier",
    "ExactorAccelerator",
    "ExactorAcceleratorClassifier",
    "ExactorAcceleratorMultiLabelClassifier",
    "save_model",
    "load_model",
    "log_to_mlflow",
    "log_to_wandb",
    "SemanticPropositionDiscovery",
    "AdaptiveBinarizer",
    "DataLoader",
    "Proposition",
    "BinarizationResult",
    "ExactorBridge",
    "ExactorHypercubeReducer",
    "ExactorSimplificationResult",
    "ExactorToJevTranslator",
    "JevPayload",
    "NoulQuestion",
    "ChoiceQuestion",
    "ScoreQuestion",
    "MemoryLedger",
    "JevClient",
    "HybridRuntime",
    "QueryResult",
]
