# Assignment 03 – Deep Learning for Diabetes

## Summary & Goals
- Standardize the BRFSS diabetes dataset, build multiple feedforward neural networks (from a simple baseline to deep architectures with dropout, BatchNorm, and L1/L2 penalties), and use early stopping with AUC monitoring to keep training stable.
- Compare the neural nets against the classical models from Assignment 2, explain when ANN complexity is justified, and comment on the limits imposed by the tabular features.

## Runtime environment
- Run the notebook with Python 3 on a machine that has `tensorflow`/`keras`, `scikit-learn`, `pandas`, `matplotlib`, and `seaborn` installed; GPU acceleration is optional but speeds up the 90–100 second training sessions for deep nets.
- Input data is the same `diabetes _ binary _ 5050split _ health _ indicators _ BRFSS2015.csv` file used in Assignment 2, ensuring the experiments remain comparable across methodologies.
- Early stopping (with `restore_best_weights=True`) and standard scaling are implemented inside Keras training helpers to keep architecture experiments reproducible.

## Models used
- **Feature preprocessing & standardization** – Ordinal categorical variables are z-score normalized rather than one-hot encoded because their ordering matters for the target, while continuous features are scaled jointly to keep gradient magnitudes stable during training. This simple scaling eliminates the need for embedding layers or complicated encodings.
- **Simple baseline ANN (2 layers: 64, 32)** – Benefits: light (~3k parameters), trains in ~31 seconds, reaches 75.12% accuracy and 0.8305 AUC with no regularization. Trade-offs: limited capacity means it might underfit more complex relationships, but the results match the boosted trees, which shows the dataset is the bottleneck.
- **Complex ANN without regularization (5 layers)** – Benefits: tests overfitting risk; drawback: early stopping triggers early (val_acc plateaus at ≈0.752) and training patterns indicate memorization. The architecture uses ~600k parameters and still underperforms the simple net, proving depth alone is insufficient without constraint.
- **Complex architectures with regularization (L2, L1, Dropout, BatchNorm)** – L2 + Dropout + BatchNorm stabilizes training and keeps test accuracy ≈ 75.18%/AUC ≈ 0.8302 with 100k parameters; L1 + aggressive dropout slows learning and yields slightly worse accuracy (~74.90%) while increasing runtime (~100 s); deeper L2 + Dropout + BatchNorm (5 layers) achieves the highest AUC (0.8306) but still needs 92 s. These experiments show regularization enables deeper nets without divergence but returns diminishing gains compared to the simple baseline.
- **Comparison with classical ML (Random Forest, Gradient Boosting, SVM)** – The final table highlights that ANNs converge to the same ~75% accuracy and ~0.83 AUC achieved by the ensembles in Assignment 2. Neural nets are more sensitive to architecture/regularization choices and take longer to train, so they are justified only if the dataset grows in size or complexity.

## Results snapshot
| Model | architecture | Regularization | Acc (test) | AUC (test) | Precision | Recall | Time (s) | Batch | LR |
|--------|--------------|----------------|------------|------------|-----------|--------|------------|-------|----|
| Simple baseline | 2 layers (64, 32) | No | 0.7512 | 0.8305 | 0.7219 | 0.8172 | 31.2 | 64 | 1e-4 |
| complex no reg. | 5 layers (512, 256, 128, 64, 32) | No | 0.7486 | 0.8290 | 0.7162 | 0.8236 | ~40 | 64 | 1e-4 |
| complex L2 | 4 layers (256, 128, 64, 32) | L2(1e-5) + Dropout(0.2) + BatchNorm | 0.7518 | 0.8302 | 0.7288 | 0.8018 | 37.9 | 256 | 1e-4 |
| complex L1 | 5 layers (512, 256, 128, 64, 32) | L1(1e-3) + Dropout(0.4) + BatchNorm | 0.7490 | 0.8292 | 0.7323 | 0.7848 | 100.0 | 512 | 1e-4 |
| complex L2 deep | 5 layers (512, 256, 128, 64, 32) | L2(1e-5) + Dropout(0.3) + BatchNorm | 0.7522 | 0.8306 | 0.7341 | 0.7909 | 92.0 | 512 | 1e-4 |

## Lessons learned
Deep learning models reach the same 75% accuracy ceiling as the classical ensembles because the tabular BRFSS features already encode almost all the learnable signal; adding layers or heavier regularization only increases runtime without improving the score. Early stopping, BatchNorm, and dropout are still valuable for keeping training stable, but the lesson is to pick the simplest ANN that matches the ensemble performance and reserve more complex designs for datasets with richer structure (e.g., temporal sequences where RNNs would finally pay off).
