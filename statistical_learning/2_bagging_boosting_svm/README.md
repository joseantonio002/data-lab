# Assignment 02 – Bagging, Boosting & SVM

## Summary & Goals
- Predict the binary `Diabetes_binary` flag from the CDC BRFSS 2015 dataset (`diabetes _ binary _ 5050split _ health _ indicators _ BRFSS2015.csv`) by fitting ensemble models and SVM, documenting preprocessing, grid-search/one-standard-error tuning, and hold-out performance.
- Compare how Random Forest, gradient boosting (HistGradientBoostingClassifier), and SVM behave on the same training/validation/test splits, quantify their test error, and comment on model simplicity versus efficacy.

## Runtime environment
- Execute the notebook under Python 3 with `scikit-learn`, `pandas`, `numpy`, and visualization libraries (`matplotlib`, `seaborn`).
- Grid searches rely on `sklearn.model_selection.GridSearchCV` and `cv_results_` metadata to implement the one-standard-error rule.
- Training uses the full dataset (≈70k rows) for the final fit after the two-phase hyperparameter campaign, so the environment only needs enough memory for pandas DataFrames and sklearn estimators.

## Models used
- **Random Forest Classifier (`sklearn.ensemble.RandomForestClassifier`)** – Benefits: bagging across trees reduces variance; insensitive to feature scaling; minimal preprocessing required. Trade-offs: still prone to overfitting if trees are too deep, so we tune `max_depth`, `min_samples_split`, `min_samples_leaf`, and `n_estimators` in two phases and pick the simplest candidate via one-standard-error. Result: test error ≈ 25.10% (accuracy 74.90%) with the selected model (`max_depth=20, min_samples_leaf=40, min_samples_split=80, n_estimators=300`). Use Random Forest when you need a robust baseline that tolerates correlated inputs.
- **HistGradientBoostingClassifier (`sklearn.ensemble.HistGradientBoostingClassifier`)** – Benefits: sequential boosting with histogram binning accelerates training on large datasets, accepts missing values, and lowers variance through learning-rate control. Trade-offs: more sensitive to learning rate and early stopping than RF. With `learning_rate=0.1`, `max_iter=50`, `max_leaf_nodes=31`, and `early_stopping=True` we achieved the best accuracy (75.37%) and lowest test error (24.63%). Prefer it when you want the most predictive power from tree ensembles and can spend the extra tuning time.
- **Support Vector Machine (`sklearn.svm.SVC` with `kernel='rbf'`)** – Benefits: strong theoretical margin maximization and flexible kernels to capture nonlinear boundaries. Trade-offs: expensive to train (especially with large `C`/small `gamma`), so we experimented with subsets (50%/10%) and applied the one-standard-error rule to pick `C=0.1`, `gamma='scale'`. Final test accuracy 73.76% (error 26.24%), showing that the flexible decision boundary still lags slightly behind the tree-based methods when training cost is considered. Use SVM when you need a strong margin-based classifier and can restrict model size or training data.

## Results snapshot
| Model | Accuracy (test) | Error (test) | Notes |
|---|---|---|---|
| Random Forest | 0.7490 | 0.2510 | `max_depth=20`, `min_samples_leaf=40`, `n_estimators=300` (one-standard-error simple candidate) |
| Gradient Boosting (HGB) | **0.7537** | **0.2463** | `learning_rate=0.1`, `max_iter=50`, `max_leaf_nodes=31`, `early_stopping=True`; best average accuracy and lowest error |
| SVM | 0.7376 | 0.2624 | `C=0.1`, `gamma='scale'`, `kernel='rbf'`; tuned with 10% subset, same test precision as using all data |

## Lessons learned
One-standard-error tuning forces us to prefer the simplest grid candidate that is statistically indistinguishable from the best, which guards against overfitting especially for RF and boosting. Gradient boosting edges out the other models in this dataset, but Random Forest and SVM stay within a few percentage points—an observation that confirms the BRFSS features limit predictive power around 75% accuracy. Running a fast subset for SVM grid search demonstrates we can keep the same final hyperparameters with less compute, which is useful when models are expensive.
