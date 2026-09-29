"""
Batch Processor for ExactorAccelerator v2.0

Provides batch processing capabilities for high-throughput scenarios.
"""

from typing import Dict, Any, Iterator
import pandas as pd


class BatchProcessor:
    """Batch processor for sensor monitoring and high-volume workloads."""
    
    def __init__(self, clf, batch_size: int = 1000):
        """
        Inicializa procesador por lotes.
        
        Args:
            clf: ExactorAccelerator classifier
            batch_size: Batch size
        """
        self.clf = clf
        self.batch_size = batch_size
    
    def predict_batch(self, df: pd.DataFrame) -> pd.Series:
        """
        Predicts in batches for high throughput.
        
        Args:
            df: DataFrame with input data
            
        Returns:
            Series of predictions
        """
        predictions = []
        
        for i in range(0, len(df), self.batch_size):
            batch = df.iloc[i:i + self.batch_size]
            batch_pred = self.clf.predict(batch)
            predictions.extend(batch_pred)
        
        return pd.Series(predictions)
    
    def predict_stream(self, stream: Iterator[Dict[str, Any]]) -> Iterator[str]:
        """
        Predicts in streaming for real-time evaluation.
        
        Args:
            stream: Iterator of state dictionaries
            
        Yields:
            Predictions
        """
        for state in stream:
            yield self.clf.predict(pd.DataFrame([state]))[0]
