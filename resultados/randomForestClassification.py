#!/usr/bin/env python3
"""
train_rf_action_clf.py

1. Carga el dataset y filtra por recompensa_normalizada en [–2,2].
2. Filtra al AgenteAleatorio.
3. Crea indicador usa_conteo y rellena conteo_cartas.
4. Prepara X (features de estado) e y (acción tomada).
5. Divide en train (60%), val (20%), test (20%).
6. RandomizedSearchCV en train para optimizar hiperparámetros.
7. Entrenamiento incremental (warm_start) para trazar accuracy train vs val.
8. Evalúa en test con classification_report y matriz de confusión.
9. Guarda CSV y gráfica de learning curve, modelo y encoder.
"""

import os
import json
import joblib
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.ensemble        import RandomForestClassifier
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.preprocessing   import LabelEncoder
from sklearn.metrics         import classification_report, confusion_matrix, accuracy_score, log_loss

def main():
    output_dir = "randomForestClass3"
    os.makedirs(output_dir, exist_ok=True)

    # 1. Carga y filtrado por recompensa_normalizada
    df = pd.read_csv("../dataset/blackjack_dataset.csv")
    df = df[df["recompensa_normalizada"].between(-2.0, 2.0)].reset_index(drop=True)

    # 2. Filtrar el AgenteAleatorio
    df = df[df["agente_nombre"] != "AgenteAleatorio"].reset_index(drop=True)

    # 3. Indicador de uso de conteo y reemplazo de None
    df["usa_conteo"] = df["conteo_cartas"].notna().astype(int)
    df["conteo_cartas"] = df["conteo_cartas"].fillna(0)

    # 4. Preparación de X e y
    X = df[[
        "mano_valor",
        "dealer_valor_carta",
        "conteo_cartas",
        "usa_conteo",
        "mano_es_blanda",
        "mano_es_par_divisible",
        "mano_apuesta"
    ]].copy()
    X[["mano_es_blanda", "mano_es_par_divisible"]] = \
        X[["mano_es_blanda", "mano_es_par_divisible"]].astype(int)

    le = LabelEncoder()
    y = le.fit_transform(df["accion_tomada"])

    # 5. División train (60%), val (20%), test (20%)
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y,
        test_size=0.20,
        random_state=42,
        stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val,
        test_size=0.25,
        random_state=42,
        stratify=y_train_val
    )

    # 6. RandomizedSearchCV para optimizar hiperparámetros
    param_dist = {
        "n_estimators":      [50, 100, 200],
        "max_depth":         [None, 10, 20, 30, 50, 70],   # profundidades mayores
        "max_features":      ["sqrt", "log2", 0.5, None],
        "min_samples_split": [2, 3, 5, 10],               # splits más finos
        "min_samples_leaf":  [1, 2, 4],                   # hojas más puras
        "bootstrap":         [True, False]
    }

    base_clf = RandomForestClassifier(
        random_state=42,
        class_weight="balanced",
        n_jobs=-1
    )

    rand_search = RandomizedSearchCV(
        estimator=base_clf,
        param_distributions=param_dist,
        n_iter=40,               # ampliamos a 40 combinaciones
        scoring="f1_macro",
        cv=4,
        verbose=2,
        random_state=42,
        return_train_score=True,
        n_jobs=-1
    )
    rand_search.fit(X_train, y_train)
    
    best_params = rand_search.best_params_
    print("Mejores parámetros (CV):", best_params)
    print(f"Mejor F1-macro (CV): {rand_search.best_score_:.4f}")

    with open(f"{output_dir}/rf_best_params.json", "w") as f:
        json.dump(best_params, f, indent=4)

    # 7. Entrenamiento incremental (warm_start)
    metrics = []
    clf = RandomForestClassifier(
        warm_start=True,
        random_state=42,
        n_jobs=-1,
        **best_params
    )
    max_trees = 500
    step = 10

    for n in range(step, max_trees+1, step):
        clf.n_estimators = n
        clf.fit(X_train, y_train)

        # 1) Accuracy
        train_acc = accuracy_score(y_train, clf.predict(X_train))
        val_acc   = accuracy_score(y_val, clf.predict(X_val))

        # 2) Log‐loss (cross‐entropy)
        train_loss = log_loss(y_train, clf.predict_proba(X_train))
        val_loss   = log_loss(y_val, clf.predict_proba(X_val))

        metrics.append((n, train_acc, val_acc, train_loss, val_loss))
        print(f"{n} trees → acc train: {train_acc:.3f}, acc val: {val_acc:.3f}"
          f"  |  logloss train: {train_loss:.3f}, val: {val_loss:.3f}")

# Convertir a DataFrame
    cols = ["n_trees", "train_acc", "val_acc", "train_loss", "val_loss"]
    lc = pd.DataFrame(metrics, columns=cols)

    # Guardar CSV
    lc.to_csv(f"{output_dir}/learning_curve.csv", index=False)

    # Graficar
    plt.figure(figsize=(12,5))

    # Subplot 1: accuracy
    plt.subplot(1,2,1)
    plt.plot(lc["n_trees"], lc["train_acc"], label="Train Acc")
    plt.plot(lc["n_trees"], lc["val_acc"],   label="Val Acc")
    plt.xlabel("Nº árboles"); plt.ylabel("Accuracy")
    plt.legend(); plt.grid(True)

    # Subplot 2: log‐loss
    plt.subplot(1,2,2)
    plt.plot(lc["n_trees"], lc["train_loss"], label="Train LogLoss")
    plt.plot(lc["n_trees"], lc["val_loss"],   label="Val LogLoss")
    plt.xlabel("Nº árboles"); plt.ylabel("Log‐loss")
    plt.legend(); plt.grid(True)

    plt.tight_layout()
    plt.savefig(f"{output_dir}/learning_curve.png")
    plt.close()

    # 8. Entrenar modelo final y evaluar en test
    best_n = int(lc.loc[lc.val_acc.idxmax(), "n_trees"])
    print(f"Número óptimo de árboles: {best_n}")
    
    # tras calcular best_n
    best_params_final = best_params.copy()
    best_params_final.pop("n_estimators", None)  # quita n_estimators

    final_clf = RandomForestClassifier(
        n_estimators=best_n,
        random_state=42,
        n_jobs=-1,
        **best_params_final
    )

    final_clf.fit(X_train_val, y_train_val)

    y_pred = final_clf.predict(X_test)
    print("\n=== Classification Report (test) ===")
    print(classification_report(y_test, y_pred, target_names=le.classes_))
    print("=== Matriz de Confusión (test) ===")
    print(confusion_matrix(y_test, y_pred))

    # 9. Guardar modelo y encoder
    joblib.dump(final_clf, f"{output_dir}/rf_action_clf.joblib")
    joblib.dump(le,        f"{output_dir}/label_encoder.joblib")
    print(f"Modelos guardados en '{output_dir}/'")

if __name__ == "__main__":
    main()
