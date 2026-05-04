from __future__ import annotations


def run_train_classical(args) -> None:
    print("EchoPath classical training scaffold")
    print(f"Feature table: {args.features or 'data/features.parquet'}")
    print(f"Label column: {args.label_column}")
    print("")
    print("Planned models: Logistic Regression, SVM, Random Forest, MLPClassifier")
    print("This command will own split creation, metrics, artifact saving, and report tables.")
