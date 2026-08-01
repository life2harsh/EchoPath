from __future__ import annotations

import json
import os
import platform
from pathlib import Path
import sys
from typing import Any

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.base import clone
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.feature_selection import VarianceThreshold
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, classification_report, confusion_matrix, f1_score
from sklearn.model_selection import GridSearchCV, StratifiedGroupKFold
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.svm import LinearSVC, SVC

from ..audio_features import feature_columns
from ..config import load_config
from ..splits import load_or_create_splits, track_identity


def _arg(args: Any, name: str, default: Any) -> Any:
    return getattr(args, name, default)


def _load_table(features_path: str | None, manifest_path: str | None) -> pd.DataFrame:
    if features_path:
        return pd.read_csv(Path(features_path).expanduser(), dtype={"track_id": str})

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
    classes: list[str] | None,
    balance_classes: bool,
    max_per_class: int | None,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.Series]:
    labels = labels.astype(str).str.strip()
    invalid = {"", "nan", "none", "unknown", "NaN", "None", "Unknown"}
    usable = labels.notna() & ~labels.isin(invalid)

    frame = frame.loc[usable].copy().reset_index(drop=True)
    labels = labels.loc[usable].copy().reset_index(drop=True)

    if classes:
        allowed = {str(label) for label in classes}
        frame = frame.loc[labels.isin(allowed)].copy().reset_index(drop=True)
        labels = labels.loc[labels.isin(allowed)].copy().reset_index(drop=True)

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
            pieces.append(group.sample(n=target_count, random_state=seed))

        balanced = pd.concat(pieces, axis=0).sample(frac=1.0, random_state=seed).reset_index(drop=True)
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


def _fit_model(
    pipeline: Pipeline,
    param_grid: dict[str, list[Any]],
    x_train: np.ndarray,
    y_train: np.ndarray,
    groups: np.ndarray,
    tune: bool,
    seed: int,
):
    if not tune or not param_grid:
        pipeline.fit(x_train, y_train)
        return pipeline, {}

    minimum_group_count = min(len(set(groups[y_train == label])) for label in np.unique(y_train))
    if minimum_group_count < 2:
        pipeline.fit(x_train, y_train)
        return pipeline, {}
    cv = StratifiedGroupKFold(n_splits=min(3, minimum_group_count), shuffle=True, random_state=seed)
    search = GridSearchCV(
        estimator=pipeline,
        param_grid=param_grid,
        scoring="f1_macro",
        cv=cv,
        n_jobs=-1,
        refit=True,
        verbose=0,
    )
    search.fit(x_train, y_train, groups=groups)
    return search.best_estimator_, search.best_params_


def _training_indices(
    labels: pd.Series,
    indices: np.ndarray,
    balance: bool,
    max_per_class: int | None,
    seed: int,
) -> np.ndarray:
    if not balance:
        return indices
    selected: list[int] = []
    available = labels.iloc[indices]
    target_count = int(available.value_counts().min())
    if max_per_class:
        target_count = min(target_count, int(max_per_class))
    for label in sorted(available.unique()):
        candidates = indices[available.to_numpy() == label]
        rng = np.random.default_rng(seed + len(selected))
        selected.extend(int(index) for index in rng.choice(candidates, size=target_count, replace=False))
    return np.array(sorted(selected), dtype=int)


def _training_groups(records: list[dict[str, Any]], indices: np.ndarray, group_column: str | None) -> np.ndarray:
    values = []
    for index in indices:
        record = records[int(index)]
        value = record.get(group_column) if group_column else None
        normalized = str(value).strip().casefold() if value is not None else ""
        values.append(normalized if normalized not in {"", "nan", "none", "unknown", "unknown artist"} else track_identity(record, int(index)))
    return np.asarray(values, dtype=object)


def _confidence(estimator: Pipeline, x: np.ndarray) -> np.ndarray:
    if hasattr(estimator, "predict_proba"):
        return np.max(estimator.predict_proba(x), axis=1)
    scores = np.asarray(estimator.decision_function(x))
    if scores.ndim == 1:
        return 1.0 / (1.0 + np.exp(-np.abs(scores)))
    scores = scores - scores.max(axis=1, keepdims=True)
    probabilities = np.exp(scores) / np.exp(scores).sum(axis=1, keepdims=True)
    return probabilities.max(axis=1)


def run_train_classical(args) -> None:
    formal_evaluation = bool(_arg(args, "formal_evaluation", False))
    requested_classes = _arg(args, "classes", None)
    if formal_evaluation and not requested_classes:
        raise SystemExit("Formal evaluation requires an explicit --classes cohort.")
    if formal_evaluation and _arg(args, "label_column", "genre_label") == "preference_proxy":
        raise SystemExit("Formal evaluation does not support globally derived preference_proxy labels.")
    frame = _load_table(_arg(args, "features", None), _arg(args, "manifest", None))
    if frame.empty:
        raise SystemExit("No rows found for training.")

    cols = feature_columns(frame.iloc[0].to_dict())
    if not cols:
        raise SystemExit("No numeric feature columns found. Run echopath ingest first.")

    y_raw = _ensure_label(frame, _arg(args, "label_column", "genre_label"))

    seed = int(_arg(args, "seed", 42))
    balance_classes = bool(_arg(args, "balance_classes", False))
    frame, y_raw = _filter_and_balance(
        frame=frame,
        labels=pd.Series(y_raw),
        min_per_class=int(_arg(args, "min_per_class", 20)),
        top_classes=_arg(args, "top_classes", None),
        classes=_arg(args, "classes", None),
        balance_classes=False,
        max_per_class=_arg(args, "max_per_class", None),
        seed=seed,
    )
    if formal_evaluation and set(y_raw.astype(str)) != {str(label) for label in requested_classes}:
        missing = sorted({str(label) for label in requested_classes} - set(y_raw.astype(str)))
        raise SystemExit(f"Formal evaluation cohort is incomplete after filtering: {missing}")

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

    output_dir = Path(_arg(args, "output_dir", "artifacts/models/classical")).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    split_path = Path(_arg(args, "splits", None) or output_dir / "splits.csv")
    records = frame.to_dict("records")
    splits = load_or_create_splits(
        records,
        y_raw.astype(str).tolist(),
        split_path,
        validation_size=float(_arg(args, "validation_size", 0.15)),
        test_size=float(_arg(args, "test_size", 0.15)),
        seed=seed,
        group_column=_arg(args, "group_column", "artist"),
        regenerate=bool(_arg(args, "regenerate_splits", False)),
    )
    train_mask = splits == "train"
    validation_mask = splits == "validation"
    test_mask = splits == "test"
    train_indices = _training_indices(
        y_raw,
        np.flatnonzero(train_mask),
        balance_classes,
        _arg(args, "max_per_class", None),
        seed,
    )
    x_train, y_train = x[train_indices], y[train_indices]
    x_validation, y_validation = x[validation_mask], y[validation_mask]
    x_test, y_test = x[test_mask], y[test_mask]
    if set(np.unique(y_train)) != set(np.unique(y)):
        raise SystemExit("Training split must contain every class; adjust split sizes or grouping.")

    tune = bool(_arg(args, "tune", False))
    group_column = _arg(args, "group_column", "artist")
    train_groups = _training_groups(records, train_indices, group_column)

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
                    random_state=seed,
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
                    random_state=seed,
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
                    random_state=seed,
                )
            ),
            {
                "model__hidden_layer_sizes": [(128, 64), (256, 128)],
                "model__alpha": [1e-4, 1e-3],
            },
        ),
    }

    rows = []
    validation_prediction_rows: list[dict[str, Any]] = []
    best_name = None
    best_f1 = -1.0
    best_pipeline = None
    best_params = {}

    for name, (pipeline, grid) in models.items():
        print(f"Training {name}...")
        estimator, params = _fit_model(
            pipeline,
            grid,
            x_train,
            y_train,
            groups=train_groups,
            tune=tune,
            seed=seed,
        )
        predictions = estimator.predict(x_validation)

        accuracy = accuracy_score(y_validation, predictions)
        balanced_accuracy = balanced_accuracy_score(y_validation, predictions)
        macro_f1 = f1_score(y_validation, predictions, average="macro", zero_division=0)
        weighted_f1 = f1_score(y_validation, predictions, average="weighted", zero_division=0)

        rows.append(
            {
                "model": name,
                "split": "validation",
                "accuracy": accuracy,
                "balanced_accuracy": balanced_accuracy,
                "macro_f1": macro_f1,
                "weighted_f1": weighted_f1,
                "best_params": json.dumps(params),
            }
        )

        report = classification_report(
            y_validation,
            predictions,
            labels=list(range(len(encoder.classes_))),
            target_names=encoder.classes_,
            zero_division=0,
        )
        (output_dir / f"{name}_validation_classification_report.txt").write_text(report, encoding="utf-8")
        confidence = _confidence(estimator, x_validation)
        validation_indices = np.flatnonzero(validation_mask)
        for index, predicted, score in zip(validation_indices, predictions, confidence):
            validation_prediction_rows.append(
                {
                    "model": name,
                    "track_id": track_identity(records[int(index)], int(index)),
                    "split": "validation",
                    "true_label": encoder.inverse_transform([y[int(index)]])[0],
                    "prediction": encoder.inverse_transform([int(predicted)])[0],
                    "confidence": float(score),
                }
            )

        if macro_f1 > best_f1:
            best_name = name
            best_f1 = macro_f1
            best_pipeline = estimator
            best_params = params

    metrics = pd.DataFrame(rows).sort_values("macro_f1", ascending=False)
    metrics.to_csv(output_dir / "validation_metrics.csv", index=False)
    pd.DataFrame(validation_prediction_rows).to_csv(output_dir / "validation_predictions.csv", index=False)
    class_counts.to_csv(output_dir / "class_distribution.csv", header=["count"])

    if best_pipeline is None or best_name is None:
        raise RuntimeError("No classical model was trained")
    final_pipeline = clone(best_pipeline)
    train_validation_mask = train_mask | validation_mask
    final_pipeline.fit(x[train_validation_mask], y[train_validation_mask])
    test_predictions = final_pipeline.predict(x_test)
    test_confidence = _confidence(final_pipeline, x_test)
    test_metrics = {
        "model": best_name,
        "accuracy": float(accuracy_score(y_test, test_predictions)),
        "balanced_accuracy": float(balanced_accuracy_score(y_test, test_predictions)),
        "macro_f1": float(f1_score(y_test, test_predictions, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_test, test_predictions, average="weighted", zero_division=0)),
        "selected_validation_macro_f1": float(best_f1),
        "test_rows": int(test_mask.sum()),
    }
    (output_dir / "final_test_metrics.json").write_text(json.dumps(test_metrics, indent=2), encoding="utf-8")
    test_report = classification_report(
        y_test,
        test_predictions,
        labels=list(range(len(encoder.classes_))),
        target_names=encoder.classes_,
        zero_division=0,
    )
    (output_dir / "final_test_classification_report.txt").write_text(test_report, encoding="utf-8")
    pd.DataFrame(
        confusion_matrix(y_test, test_predictions, labels=list(range(len(encoder.classes_)))),
        index=encoder.classes_,
        columns=encoder.classes_,
    ).to_csv(output_dir / "final_test_confusion_matrix.csv", index_label="true_label")
    test_indices = np.flatnonzero(test_mask)
    pd.DataFrame(
        {
            "track_id": [track_identity(records[int(index)], int(index)) for index in test_indices],
            "split": "test",
            "true_label": encoder.inverse_transform(y_test),
            "prediction": encoder.inverse_transform(test_predictions),
            "confidence": test_confidence,
        }
    ).to_csv(output_dir / "test_predictions.csv", index=False)

    config_metadata = {
        "command": "train-classical",
        "features": os.path.relpath(Path(_arg(args, "features", "")).expanduser().resolve(), output_dir) if _arg(args, "features", None) else None,
        "manifest": os.path.relpath(Path(_arg(args, "manifest", "")).expanduser().resolve(), output_dir) if _arg(args, "manifest", None) else None,
        "label_column": _arg(args, "label_column", "genre_label"),
        "feature_columns": cols,
        "seed": seed,
        "validation_size": float(_arg(args, "validation_size", 0.15)),
        "test_size": float(_arg(args, "test_size", 0.15)),
        "group_column": group_column,
        "split_path": os.path.relpath(split_path.expanduser().resolve(), output_dir),
        "tune": tune,
        "min_per_class": int(_arg(args, "min_per_class", 20)),
        "top_classes": _arg(args, "top_classes", None),
        "classes": _arg(args, "classes", None),
        "balance_classes": balance_classes,
        "max_per_class": _arg(args, "max_per_class", None),
        "selected_model": best_name,
        "formal_evaluation": formal_evaluation,
        "best_params": best_params,
        "rows": {name: int((splits == name).sum()) for name in ("train", "validation", "test")},
        "training_rows_after_balance": int(len(train_indices)),
        "python_version": platform.python_version(),
        "numpy_version": np.__version__,
        "pandas_version": pd.__version__,
        "scikit_learn_version": sklearn.__version__,
        "platform": sys.platform,
    }
    (output_dir / "training_config.json").write_text(json.dumps(config_metadata, indent=2), encoding="utf-8")

    joblib.dump(
        {
            "model": final_pipeline,
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
    print(f"Final test macro F1: {test_metrics['macro_f1']:.4f}")
    if best_params:
        print(f"Best params: {best_params}")
    print(f"Artifacts: {output_dir}")
