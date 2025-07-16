"""
1. Carga y preprocesa el dataset.
2. Divide en train / validation / test.
3. RandomizedSearchCV para optimizar hiperparámetros (excluyendo n_estimators).
4. Guarda cv_results_ en 'randomForest/rf_cv_results.csv'.
5. Entrenamiento incremental (warm_start) con los mejores parámetros:
   - Añade árboles en bloques y registra MSE en train/val.
6. Guarda métricas de curva de aprendizaje en 'randomForest/rf_warmup_metrics.csv' 
   y curva en 'randomForest/rf_learning_curve.png'.
7. Guarda los mejores parámetros en 'randomForest/rf_best_params.json'.
8. Evalúa en test, imprime métricas y guarda modelo final en 'randomForest/rf_final_model.joblib'.
"""

import os
import json
import joblib
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np

def main():
    # 0. Crear carpeta de resultados
    output_dir = "randomForest3"
    os.makedirs(output_dir, exist_ok=True)

    # 1. Carga y filtrado de outliers
    df = pd.read_csv("../dataset/blackjack_dataset.csv")
    df = df[df["recompensa_normalizada"].between(-2.0, 2.0)].reset_index(drop=True)

    # 2. Preparo X e y
    X = df[[
        "mano_valor", "dealer_valor_carta", "conteo_cartas",
        "mano_es_blanda", "mano_es_par_divisible"
    ]].copy()
    X["mano_es_blanda"] = X["mano_es_blanda"].astype(int)
    X["mano_es_par_divisible"] = X["mano_es_par_divisible"].astype(int)
    # one-hot encoding de la acción
    X = pd.concat([X, pd.get_dummies(df["accion_tomada"], prefix="acc")], axis=1)

    y = df["recompensa_normalizada"]

    # 3. Split: train (60%), val (20%), test (20%)
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_val, y_train_val, test_size=0.25, random_state=42
    )

    # 4. Búsqueda aleatoria de hiperparámetros
    param_dist = {
        "max_depth":         [None, 10, 20, 30, 50],
        "max_features":      ["sqrt", "log2", 0.5, None],
        "min_samples_split": [2, 5, 10, 20],
        "min_samples_leaf":  [1, 2, 4, 8],
        "bootstrap":         [True, False]
    }

    base_rf = RandomForestRegressor(
        n_estimators=100,    # número fijo de árboles durante CV
        n_jobs=-1,
        random_state=42
    )

    rand_search = RandomizedSearchCV(
        estimator=base_rf,
        param_distributions=param_dist,
        n_iter=50,           # probamos 50 combinaciones
        scoring="r2",        # métrica a maximizar
        cv=4,
        verbose=2,
        random_state=42,
        return_train_score=True,
        n_jobs=-1
    )
    rand_search.fit(X_train, y_train)

    # 5. Guardar resultados de CV
    cv_df = pd.DataFrame(rand_search.cv_results_)
    cv_df.to_csv(f"{output_dir}/rf_cv_results.csv", index=False)
    print(f"CV results saved to '{output_dir}/rf_cv_results.csv'")

    best_params = rand_search.best_params_
    print("Mejores parámetros:", best_params)
    print(f"Mejor R² en validación (CV): {rand_search.best_score_:.4f}")

    # guardo parámetros en JSON
    with open(f"{output_dir}/rf_best_params.json", "w") as f:
        json.dump(best_params, f, indent=4)

    # 6. Entrenamiento incremental (warm_start)
    metrics = []
    rf = RandomForestRegressor(
        warm_start=True,
        n_estimators=0,
        n_jobs=-1,
        random_state=42,
        **best_params
    )
    max_trees = 200
    step = 10

    for n in range(step, max_trees + 1, step):
        rf.n_estimators = n
        rf.fit(X_train, y_train)

        mse_tr = mean_squared_error(y_train, rf.predict(X_train))
        mse_val = mean_squared_error(y_val,   rf.predict(X_val))
        metrics.append((n, mse_tr, mse_val))
        print(f"{n} árboles → MSE train: {mse_tr:.2f}, MSE val: {mse_val:.2f}")

    warm_df = pd.DataFrame(metrics, columns=["n_trees", "mse_train", "mse_val"])
    warm_df.to_csv(f"{output_dir}/rf_warmup_metrics.csv", index=False)
    print(f"Learning curve data saved to '{output_dir}/rf_warmup_metrics.csv'")

    # 7. Gráfica de curva de aprendizaje
    plt.figure(figsize=(8, 5))
    plt.plot(warm_df["n_trees"], warm_df["mse_train"], label="MSE Train")
    plt.plot(warm_df["n_trees"], warm_df["mse_val"], label="MSE Validation")
    plt.xlabel("Número de árboles")
    plt.ylabel("MSE")
    plt.title("Curva de Aprendizaje - Random Forest(normalizada)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(f"{output_dir}/rf_learning_curve.png")
    plt.close()
    print(f"Learning curve plot saved to '{output_dir}/rf_learning_curve.png'")

    # 8. Entrenar y evaluar modelo final
    best_n = int(warm_df.loc[warm_df.mse_val.idxmin(), "n_trees"])
    print(f"Número óptimo de árboles: {best_n}")

    final_rf = RandomForestRegressor(
        n_estimators=best_n,
        n_jobs=-1,
        random_state=42,
        **best_params
    )
    final_rf.fit(X_train_val, y_train_val)

    mse_test = mean_squared_error(y_test, final_rf.predict(X_test))
    r2_test  = r2_score(y_test, final_rf.predict(X_test))
    print(f"Test MSE: {mse_test:.2f}, Test R²: {r2_test:.4f}")

    # 9. Guardar modelo final
    joblib.dump(final_rf, f"{output_dir}/rf_final_model.joblib")
    print(f"Modelo final guardado en '{output_dir}/rf_final_model.joblib'")

if __name__ == "__main__":
    main()
