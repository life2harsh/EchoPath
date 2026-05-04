from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.feature_selection import VarianceThreshold
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report, f1_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold, train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import LinearSVC, SVC

from ..audio_features import feature_columns
from ..config import load_config


def _arg(args: Any, name: str, default: Any) -> Any:
    return getattr(args, name, default)


def _load_table(features_path: str | None, manifest_path: str | None) -> pd.DataFrame:
    if features_path:
        return pd.read_csv(Path(features_path).expanduser())

    config = load_config(None)
    manifest = Path(manifest_path).expanduser() if manifest_path else config.manifest_path
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    return pd.DataFrame(payload)


def _ensure_label(frame: pd.DataFrame, label_column: str) -> pd.Series:
    if label_column in frame.columns:
        return frame[label_column].astype(str)

    if label_column == "preference_proxy":
        energy = pd.to_numeric(frame.get("energy", 0.0), errors="coerce").fillna(0.0)
        valence = pd.to_numeric(frame.get("valence", 0.0), errors="coerce").fillna(0.0)
        tempo = pd.to_numeric(frame.get("tempo", 0.0), errors="coerce").fillna(0.0)
        score = 0.45 * energy + 0.35 * valence + 0.20 * (tempo / max(float(tempo.max()), 1.0))
        threshold = float(score.median())
        return pd.Series(np.where(score >= threshold, "like", "skip"))

    raise SystemExit(f"Label column '{label_column}' not found. Try --label-column genre_label or cluster_id.")


def _filter_and_balance(
    frame: pd.DataFrame,
    labels: pd.Series,
    min_per_class: int,
    top_classes: int | None,
    balance_classes: bool,
    max_per_class: int | None,
) -> tuple[pd.DataFrame, pd.Series]:
    labels = labels.astype(str).str.strip()
    invalid = {"", "nan", "none", "unknown", "NaN", "None", "Unknown"}
    usable = labels.notna() & ~labels.isin(invalid)

    frame = frame.loc[usable].copy().reset_index(drop=True)
    labels = labels.loc[usable].copy().reset_index(drop=True)

    counts = labels.value_counts()
    keep = counts[counts >= min_per_class].index
    frame = frame.loc[labels.isin(keep)].copy().reset_index(drop=True)
    labels = labels.loc[labels.isin(keep)].copy().reset_index(drop=True)

    if top_classes and top_classes > 0:
        top = labels.value_counts().head(top_classes).index
        frame = frame.loc[labels.isin(top)].copy().reset_index(drop=True)
        labels = labels.loc[labels.isin(top)].copy().reset_index(drop=True)

    if balance_classes:
        pieces = []
        label_name = "_echopath_label"
        temp = frame.copy()
        temp[label_name] = labels.values

        counts = temp[label_name].value_counts()
        if counts.empty:
            raise SystemExit("No usable classes after filtering.")

        target_count = int(counts.min())
        if max_per_class:
            target_count = min(target_count, int(max_per_class))

        for _, group in temp.groupby(label_name):
            pieces.append(group.sample(n=target_count, random_state=42))

        balanced = pd.concat(pieces, axis=0).sample(frac=1.0, random_state=42).reset_index(drop=True)
        labels = balanced.pop(label_name).astype(str)
        frame = balanced.reset_index(drop=True)

    return frame, labels


def _numeric_matrix(frame: pd.DataFrame, cols: list[str]) -> np.ndarray:
    numeric = frame[cols].apply(pd.to_numeric, errors="coerce")
    numeric = numeric.replace([np.inf, -np.inf], np.nan)
    return numeric.to_numpy(dtype=float)


def _base_pipeline(estimator: Any, scale: bool = True) -> Pipeline:
    steps: list[tuple[str, Any]] = [
        ("imputer", SimpleImputer(strategy="median")),
        ("variance", VarianceThreshold()),
    ]
    if scale:
        steps.append(("scaler", StandardScaler()))
    steps.append(("model", estimator))
    return Pipeline(steps)


def _fit_model(name: str, pipeline: Pipeline, param_grid: dict[str, list[Any]], x_train: np.ndarray, y_train: np.ndarray, tune: bool):
    if not tune or not param_grid:
        pipeline.fit(x_train, y_train)
        return pipeline, {}

    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    search = GridSearchCV(
        estimator=pipeline,
        param_grid=param_grid,
        scoring="f1_macro",
        cv=cv,
        n_jobs=-1,
        refit=True,
        verbose=0,
    )
    search.fit(x_train, y_train)
    return search.best_estimator_, search.best_params_


def run_train_classical(args) -> None:
    frame = _load_table(_arg(args, "features", None), _arg(args, "manifest", None))
    if frame.empty:
        raise SystemExit("No rows found for training.")

    cols = feature_columns(frame.iloc[0].to_dict())
    if not cols:
        raise SystemExit("No numeric feature columns found. Run echopath ingest first.")

    y_raw = _ensure_label(frame, _arg(args, "label_column", "genre_label"))

    frame, y_raw = _filter_and_balance(
        frame=frame,
        labels=pd.Series(y_raw),
        min_per_class=int(_arg(args, "min_per_class", 20)),
        top_classes=_arg(args, "top_classes", None),
        balance_classes=bool(_arg(args, "balance_classes", False)),
        max_per_class=_arg(args, "max_per_class", None),
    )

    if y_raw.nunique() < 2:
        raise SystemExit("Need at least two usable classes after filtering.")

    class_counts = y_raw.value_counts().sort_values(ascending=False)
    print("Training rows:", len(frame))
    print("Classes:", y_raw.nunique())
    print("Class distribution:")
    print(class_counts.to_string())
    print("")

    x = _numeric_matrix(frame, cols)
    encoder = LabelEncoder()
    y = encoder.fit_transform(y_raw.astype(str))

    stratify = y if min(np.bincount(y)) >= 2 else None
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=float(_arg(args, "test_size", 0.25)),
        random_state=42,
        stratify=stratify,
    )

    tune = bool(_arg(args, "tune", False))

    models: dict[str, tuple[Pipeline, dict[str, list[Any]]]] = {
        "logistic_regression": (
            _base_pipeline(LogisticRegression(max_iter=4000, class_weight="balanced")),
            {
                "model__C": [0.1, 1.0, 3.0, 10.0],
            },
        ),
        "linear_svm": (
            _base_pipeline(LinearSVC(class_weight="balanced", max_iter=8000)),
            {
                "model__C": [0.1, 0.5, 1.0, 3.0],
            },
        ),
        "svm_rbf": (
            _base_pipeline(SVC(kernel="rbf", class_weight="balanced")),
            {
                "model__C": [1.0, 3.0, 10.0],
                "model__gamma": ["scale", 0.03, 0.1],
            },
        ),
        "random_forest": (
            _base_pipeline(
                RandomForestClassifier(
                    n_estimators=500,
                    random_state=42,
                    class_weight="balanced_subsample",
                    n_jobs=-1,
                ),
                scale=False,
            ),
            {
                "model__max_features": ["sqrt", 0.5],
                "model__min_samples_leaf": [1, 2, 4],
            },
        ),
        "extra_trees": (
            _base_pipeline(
                ExtraTreesClassifier(
                    n_estimators=700,
                    random_state=42,
                    class_weight="balanced",
                    n_jobs=-1,
                ),
                scale=False,
            ),
            {
                "model__max_features": ["sqrt", 0.5],
                "model__min_samples_leaf": [1, 2, 4],
            },
        ),
        "mlp": (
            _base_pipeline(
                MLPClassifier(
                    hidden_layer_sizes=(256, 128),
                    alpha=1e-3,
                    learning_rate_init=1e-3,
                    early_stopping=True,
                    validation_fraction=0.15,
                    max_iter=700,
                    random_state=42,
                )
            ),
            {
                "model__hidden_layer_sizes": [(128, 64), (256, 128)],
                "model__alpha": [1e-4, 1e-3],
            },
        ),
    }

    output_dir = Path(_arg(args, "output_dir", "artifacts/models/classical")).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    best_name = None
    best_f1 = -1.0
    best_pipeline = None
    best_params = {}

    for name, (pipeline, grid) in models.items():
        print(f"Training {name}...")
        estimator, params = _fit_model(name, pipeline, grid, x_train, y_train, tune=tune)
        predictions = estimator.predict(x_test)

        accuracy = accuracy_score(y_test, predictions)
        balanced_accuracy = balanced_accuracy_score(y_test, predictions)
        macro_f1 = f1_score(y_test, predictions, average="macro", zero_division=0)
        weighted_f1 = f1_score(y_test, predictions, average="weighted", zero_division=0)

        rows.append(
            {
                "model": name,
                "accuracy": accuracy,
                "balanced_accuracy": balanced_accuracy,
                "macro_f1": macro_f1,
                "weighted_f1": weighted_f1,
                "best_params": json.dumps(params),
            }
        )

        report = classification_report(
            y_test,
            predictions,
            labels=list(range(len(encoder.classes_))),
            target_names=encoder.classes_,
            zero_division=0,
        )
        (output_dir / f"{name}_classification_report.txt").write_text(report, encoding="utf-8")

        if macro_f1 > best_f1:
            best_name = name
            best_f1 = macro_f1
            best_pipeline = estimator
            best_params = params

    metrics = pd.DataFrame(rows).sort_values("macro_f1", ascending=False)
    metrics.to_csv(output_dir / "classical_metrics.csv", index=False)
    class_counts.to_csv(output_dir / "class_distribution.csv", header=["count"])

    joblib.dump(
        {
            "model": best_pipeline,
            "label_encoder": encoder,
            "feature_columns": cols,
            "label_column": _arg(args, "label_column", "genre_label"),
            "class_counts": class_counts.to_dict(),
            "best_model_name": best_name,
            "best_params": best_params,
        },
        output_dir / "best_classical_model.joblib",
    )

    print("")
    print("Classical training complete")
    print(metrics[["model", "accuracy", "balanced_accuracy", "macro_f1", "weighted_f1"]].to_string(index=False))
    print(f"Best model: {best_name}")
    if best_params:
        print(f"Best params: {best_params}")
    print(f"Artifacts: {output_dir}")
