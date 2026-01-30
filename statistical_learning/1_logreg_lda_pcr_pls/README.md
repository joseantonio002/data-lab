# Assignment 01 – LogReg, LDA, PCR & PLS

## Summary & Goals
- Understand the relationship between tuition variables and private/public status in the `College` dataset using Logistic Regression and LDA; report coefficients, pseudo R², confusion, class imbalance issues, and recommend the most trustworthy classifier.
- Contrast ordinary least squares with Ridge, Lasso, PCR and PLS to predict `Apps`, capture the impact of multicollinearity, and identify the model with the best test mean squared error.
- Deliver a narrative that interprets coefficients, explains modeling trade-offs, and documents why logistic + targeted regularization best handles this dataset.

## Runtime environment
- Run the notebook inside a local Python 3 kernel (Jupyter Notebook) with `pandas`, `statsmodels`, `matplotlib`, `seaborn`, and `scikit-learn` installed via `pip`/`conda`.
- `statsmodels` is used for logistic regression to expose interpretable coefficients and p-values; `scikit-learn` supplies LDA/PCR/PLS implementations and cross-validation helpers.

## Models used
- **Logistic Regression (`statsmodels.discrete.discrete_model.Logit`)** – Benefits: interpretable coefficients (converted to odds ratios) and deterministic fits for binary classification; handles class imbalance reasonably when paired with validation splits. Trade-offs: assumes linearity of log-odds and is sensitive to multicollinearity, but the model trained on `Outstate` + `F.Undergrad` achieved pseudo R² = 0.6737, CV accuracy ≈ 94%, and test accuracy ≈ 94.9%. Use it when you need explainability with a well-specified link function.
- **Linear Discriminant Analysis (`sklearn.discriminant_analysis.LinearDiscriminantAnalysis`)** – Benefits: explicit Gaussian assumptions and closed-form discriminants; useful for problems with similar class covariances. Trade-offs: violated homogeneity of covariance and skewed predictors in this dataset (notably `F.Undergrad`), so LDA underperforms (TN ≈ 67% vs logistic’s 83.7% for the minority class). Only prefer LDA when the predictors are roughly normal and the covariance matrices are comparable.
- **Ordinary Least Squares Regression** – Benefits: interpretable slope estimates and diagnostic tools (VIF). Trade-offs: multicollinearity (high VIF for `Enroll`, `F.Undergrad`) inflates variance, so OLS alone leaves high MSE on `Apps` predictions.
- **Ridge Regression (`sklearn.linear_model.RidgeCV`)** – Benefits: shrinks coefficients uniformly to tame multicollinearity without discarding variables; test MSE increased slightly because the data already fit well but training remained stable. Use Ridge when every predictor carries signal and you want to keep them in the model.
- **Lasso Regression (`sklearn.linear_model.LassoCV`)** – Benefits: variable selection via L1 regularization; Trade-offs: aggressive shrinkage led to worse MSE for this problem, suggesting the informative predictors cannot be zeroed out without underfitting.
- **PCR (Principal Component Regression)** – Benefits: orthogonal components mitigate multicollinearity and reduce dimensionality. Trade-offs: components ignore `y`, so predictive utility suffers (PCR produced the same test MSE as OLS because all predictors retained signal); use PCR when you need a drastic dimensionality reduction and the main aim is variance capture.
- **PLS (Partial Least Squares Regression)** – Benefits: components maximize covariance with `y`, so PLS squeezed slightly better generalization (lowest test error ~26.65%) while still handling correlated predictors. Trade-offs: components are linear combinations of predictors, reducing interpretability compared to raw coefficients, but PLS proved to be the best regularized choice.

## Lessons learned
Logistic regression with `Outstate` and `F.Undergrad` balances interpretability and predictive power, outperforming LDA when the Gaussian/covariance assumptions break. Regularization is essential when multicollinearity is present: Ridge keeps the model stable, Lasso over-regularizes, and PLS offers the best trade-off between bias and variance for `Apps` predictions, delivering the lowest MSE without dropping informative features.
