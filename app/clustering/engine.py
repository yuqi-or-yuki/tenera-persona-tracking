"""Clustering engine — transforms persona entities into clusters.

Implements three algorithms based on recent research:
- K-Means: Fast, good for clean numerical data (default)
- HDBSCAN: Auto-discovers K, handles noise, density-aware
- K-Prototypes: Handles mixed numerical + categorical data natively

References:
- Frontiers 2024: "Comprehensive investigation of clustering algorithms for UEBA"
- IEEE/ACM CHASE 2024: "Data-driven Persona with B2B Software"
- Pipedrive: "Identifying behavioral personas with cluster analysis"
"""

import json
import logging
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.preprocessing import LabelEncoder, StandardScaler

logger = logging.getLogger(__name__)


def _build_feature_matrix(
    personas: List[Dict],
) -> Tuple[pd.DataFrame, List[str], List[str]]:
    """Convert persona entities into a feature matrix.

    Returns (dataframe, persona_ids, feature_names).
    Each row is a persona, each column is an entity key.
    """
    rows = []
    persona_ids = []

    for p in personas:
        row = {}
        for entity in p.get("entities", []):
            row[entity["key"]] = entity["value"]
        rows.append(row)
        persona_ids.append(p["id"])

    df = pd.DataFrame(rows, index=persona_ids)
    # Drop columns where all values are NaN (no persona has this entity)
    df = df.dropna(axis=1, how="all")
    return df, persona_ids, list(df.columns)


def _classify_columns(df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    """Classify columns as numerical or categorical."""
    numerical = []
    categorical = []

    for col in df.columns:
        # Try to convert to numeric
        converted = pd.to_numeric(df[col], errors="coerce")
        non_null_ratio = converted.notna().sum() / max(len(df), 1)
        if non_null_ratio > 0.5:
            numerical.append(col)
        else:
            categorical.append(col)

    return numerical, categorical


def _preprocess_for_kmeans(
    df: pd.DataFrame,
) -> Tuple[np.ndarray, List[str], List[str]]:
    """Preprocess for K-Means: encode categoricals, standardize numericals."""
    numerical, categorical = _classify_columns(df)
    parts = []

    # Numerical columns: fill NaN with median, standardize
    if numerical:
        num_df = df[numerical].apply(pd.to_numeric, errors="coerce")
        num_df = num_df.fillna(num_df.median())
        scaler = StandardScaler()
        parts.append(pd.DataFrame(scaler.fit_transform(num_df), index=df.index, columns=numerical))

    # Categorical columns: label encode then one-hot
    if categorical:
        cat_df = df[categorical].fillna("_unknown_")
        cat_encoded = pd.get_dummies(cat_df, prefix_sep="=")
        parts.append(cat_encoded)

    if not parts:
        raise ValueError("No features available for clustering")

    result = pd.concat(parts, axis=1)
    return result.values, numerical, categorical


def _to_native(obj):
    """Convert numpy types to native Python types for JSON serialization."""
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, dict):
        return {_to_native(k): _to_native(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_native(i) for i in obj]
    return obj


def _generate_cluster_names(
    df: pd.DataFrame, labels: np.ndarray, numerical: List[str], categorical: List[str]
) -> Dict[int, str]:
    """Auto-generate cluster names from dominant entity values."""
    names = {}
    unique_labels = sorted(set(labels))

    for label in unique_labels:
        if label == -1:  # HDBSCAN noise
            names[label] = "Outliers"
            continue

        mask = labels == label
        cluster_df = df[mask]

        # Find the most distinctive feature for this cluster
        descriptors = []

        # Check categorical columns first (more descriptive names)
        for col in categorical:
            if col in cluster_df.columns:
                values = cluster_df[col].dropna()
                if len(values) > 0:
                    most_common = values.mode()
                    if len(most_common) > 0:
                        val = most_common.iloc[0]
                        # Check if this value is distinctive to this cluster
                        overall_ratio = (df[col] == val).mean()
                        cluster_ratio = (cluster_df[col] == val).mean()
                        if cluster_ratio > overall_ratio * 1.3:
                            descriptors.append(f"{col}={val}")

        # Check numerical columns
        for col in numerical:
            if col in cluster_df.columns:
                col_numeric = pd.to_numeric(cluster_df[col], errors="coerce")
                overall_numeric = pd.to_numeric(df[col], errors="coerce")
                if col_numeric.notna().any() and overall_numeric.notna().any():
                    cluster_mean = col_numeric.mean()
                    overall_mean = overall_numeric.mean()
                    overall_std = overall_numeric.std()
                    if overall_std > 0 and abs(cluster_mean - overall_mean) > overall_std * 0.5:
                        direction = "high" if cluster_mean > overall_mean else "low"
                        descriptors.append(f"{direction}_{col}")

        if descriptors:
            names[label] = "Cluster: " + ", ".join(descriptors[:3])
        else:
            names[label] = f"Cluster {label}"

    return names


def run_kmeans(
    personas: List[Dict], n_clusters: int = 3, max_iter: int = 300
) -> Dict[str, Any]:
    """Run K-Means clustering on persona entities."""
    df, persona_ids, features = _build_feature_matrix(personas)
    if len(df) < n_clusters:
        raise ValueError(f"Need at least {n_clusters} personas, got {len(df)}")

    X, numerical, categorical = _preprocess_for_kmeans(df)

    model = KMeans(n_clusters=n_clusters, max_iter=max_iter, n_init=10, random_state=42)
    labels = model.fit_predict(X)

    metrics = _compute_metrics(X, labels)
    cluster_names = _generate_cluster_names(df, labels, numerical, categorical)

    return _to_native({
        "algorithm": "kmeans",
        "params": {"n_clusters": n_clusters, "max_iter": max_iter},
        "labels": labels.tolist(),
        "persona_ids": persona_ids,
        "cluster_names": cluster_names,
        "metrics": metrics,
        "num_clusters": n_clusters,
    })


def run_hdbscan(
    personas: List[Dict], min_cluster_size: int = 3, min_samples: int = 2
) -> Dict[str, Any]:
    """Run HDBSCAN clustering — auto-discovers number of clusters."""
    import hdbscan

    df, persona_ids, features = _build_feature_matrix(personas)
    X, numerical, categorical = _preprocess_for_kmeans(df)

    model = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size, min_samples=min_samples)
    labels = model.fit_predict(X)

    # Count real clusters (excluding noise label -1)
    real_labels = labels[labels != -1]
    n_clusters = len(set(real_labels)) if len(real_labels) > 0 else 0

    metrics = _compute_metrics(X, labels) if n_clusters >= 2 else {}
    cluster_names = _generate_cluster_names(df, labels, numerical, categorical)

    return _to_native({
        "algorithm": "hdbscan",
        "params": {"min_cluster_size": min_cluster_size, "min_samples": min_samples},
        "labels": labels.tolist(),
        "persona_ids": persona_ids,
        "cluster_names": cluster_names,
        "metrics": metrics,
        "num_clusters": n_clusters,
    })


def run_kprototypes(
    personas: List[Dict], n_clusters: int = 3
) -> Dict[str, Any]:
    """Run K-Prototypes — handles mixed numerical + categorical data natively."""
    from kmodes.kprototypes import KPrototypes

    df, persona_ids, features = _build_feature_matrix(personas)
    if len(df) < n_clusters:
        raise ValueError(f"Need at least {n_clusters} personas, got {len(df)}")

    numerical, categorical = _classify_columns(df)

    # Prepare data: numerical stays numeric, categorical stays as strings
    processed = df.copy()
    for col in numerical:
        processed[col] = pd.to_numeric(processed[col], errors="coerce").fillna(0)
    for col in categorical:
        processed[col] = processed[col].fillna("_unknown_")

    # Identify categorical column indices
    cat_indices = [list(processed.columns).index(c) for c in categorical]

    if not cat_indices:
        # Fall back to K-Means if no categorical columns
        return run_kmeans(personas, n_clusters=n_clusters)

    model = KPrototypes(n_clusters=n_clusters, init="Cao", random_state=42)
    labels = model.fit_predict(processed.values, categorical=cat_indices)

    # For metrics, we need a numerical representation
    X, _, _ = _preprocess_for_kmeans(df)
    metrics = _compute_metrics(X, labels)
    cluster_names = _generate_cluster_names(df, labels, numerical, categorical)

    return _to_native({
        "algorithm": "kprototypes",
        "params": {"n_clusters": n_clusters},
        "labels": labels.tolist(),
        "persona_ids": persona_ids,
        "cluster_names": cluster_names,
        "metrics": metrics,
        "num_clusters": n_clusters,
    })


def find_optimal_k(personas: List[Dict], max_k: int = 7) -> Dict[str, Any]:
    """Find optimal K using silhouette score (capped at 7 for actionability)."""
    df, persona_ids, features = _build_feature_matrix(personas)
    X, _, _ = _preprocess_for_kmeans(df)

    max_k = min(max_k, len(df) - 1)
    if max_k < 2:
        return {"optimal_k": 2, "scores": {}}

    scores = {}
    for k in range(2, max_k + 1):
        model = KMeans(n_clusters=k, n_init=10, random_state=42)
        labels = model.fit_predict(X)
        scores[k] = round(silhouette_score(X, labels), 4)

    optimal_k = max(scores, key=scores.get)
    return {"optimal_k": optimal_k, "scores": scores}


def _compute_metrics(X: np.ndarray, labels: np.ndarray) -> Dict[str, float]:
    """Compute clustering quality metrics."""
    # Filter out noise points (label == -1) for metrics
    mask = labels != -1
    if mask.sum() < 2 or len(set(labels[mask])) < 2:
        return {}

    X_clean = X[mask]
    labels_clean = labels[mask]

    return {
        "silhouette_score": round(float(silhouette_score(X_clean, labels_clean)), 4),
        "calinski_harabasz": round(float(calinski_harabasz_score(X_clean, labels_clean)), 4),
        "davies_bouldin": round(float(davies_bouldin_score(X_clean, labels_clean)), 4),
    }
