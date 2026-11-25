# Rossmann Store Sales Forecasting: Preprocessing & Feature Ablation Study

Implementasi end-to-end metodologi penelitian dari artikel:

> **Albassam, S., Alqahtani, A., & Alazba, A. (2026).** *Retail Sales Forecasting Using Tree-Based Machine Learning Models: An Empirical Study of Preprocessing Configurations and Feature Ablation.* Applied Sciences, 16(15), 7556. https://doi.org/10.3390/app16157556

Artikel lengkap tersedia di: [docs/Albassam_2026_Retail_Sales_Forecasting_Tree_Based_ML.pdf](./docs/Albassam_2026_Retail_Sales_Forecasting_Tree_Based_ML.pdf)

---

## Ringkasan Metodologi

Pipeline eksperimen mengevaluasi 7 model *tree-based* dan 3 baseline klasik pada dataset **Rossmann Store Sales** (1.115 toko, 1.017.209 baris mentah; 844.338 baris hari operasional `Open == 1` dan `Sales > 0`) dengan validasi kronologis ketat untuk mencegah *temporal data leakage*.

### 1. Konfigurasi Preprocessing (C1 sampai C5)
Seluruh transformasi dipasang di dalam `sklearn.pipeline.Pipeline` sehingga statistik imputasi dan skema encoding hanya dipelajari dari data latih:

| Konfigurasi | Deskripsi |
| :--- | :--- |
| **C1: Baseline** | Preprocessing minimal: *one-hot encoding* variabel kategorikal saja, tanpa imputasi statistik dan tanpa penghapusan fitur *zero-variance*. |
| **C2: Preprocessed** | Pipeline penuh: imputasi median (numerik), imputasi modus + *one-hot encoding* (kategorikal). |
| **C3: Preprocessed + Selected** | Sama seperti C2 ditambah `VarianceThreshold(threshold=0.0)` untuk menghapus fitur bernilai konstan. |
| **C4: Preprocessed, No Seasonality** | Sama seperti C2, tetapi menghapus fitur musiman dan promosi menggunakan regex `holiday|weather|temp|season|weekend|quarter|weekday|promo`. |
| **C5: Preprocessed + Selected, No Seasonality** | Gabungan C3 dengan penghapusan fitur musiman/promosi seperti C4. |

### 2. Skenario Ablasi `Customers`
Seluruh konfigurasi `C1` sampai `C5` dijalankan paralel pada dua kondisi:
- **Without Customers (Realistis):** Jumlah pengunjung (`Customers`) dihapus karena tidak tersedia sebelum periode peramalan pada operasional nyata.
- **With Customers (Batas Atas / Ablasi):** `Customers` disertakan untuk mengukur kontribusi independennya terhadap akurasi prediksi.

### 3. Model, Validasi, dan Uji Statistik
- **7 Model Tree-Based** (`random_state=42`, `100` estimator, tanpa tuning hiperparameter): `AdaBoost`, `DecisionTree` (`max_depth=10`), `ExtraTrees`, `GradientBoosting` (early stopping patience 10), `HistGradientBoosting`, `RandomForest`, dan `XGBoost`.
- **3 Baseline Klasik** (pada C3 tanpa `Customers`): `Ridge Regression` (`alpha=1.0`), `Seasonal-Naive` (lag-7 dengan backoff), dan `ETS` per toko (Holt-Winters *additive damped trend* + *additive weekly seasonality*).
- **Strategi Validasi:** Split kronologis tetap **80/20** untuk metrik utama (`RMSE`, `RMSE%` terhadap rata-rata `y_train`, `MAE`, `R²`) dan **5-fold `TimeSeriesSplit`** (`CV R²` dan standar deviasi `σ`).
- **Uji Signifikansi:** Diebold-Mariano test pada error harian (MAE & MSE, `T = 183` hari validasi) dengan Newey-West HAC variance (`lag = 7`) dan koreksi Holm-Bonferroni.
- **Interpretabilitas:** Tree feature importance dan `shap.TreeExplainer` pada 500 sampel validasi (`random_state=42`) dengan agregasi ke 5 kategori (`Promotional`, `Competition`, `Store`, `Calendar/Temporal`, `Customer`).

---

## Ringkasan Hasil Penelitian (Albassam et al., 2026)

### 1. Performa Terbaik per Skenario (C3: Preprocessed + Selected)

#### A. Rossmann Without Customers (Tabel 4, Kondisi Realistis)
| Model | RMSE | RMSE% | MAE | R² | CV R² |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **RandomForest** | **1044.25** | **15.01%** | **701.01** | **0.8838** | **0.8319** |
| ExtraTrees | 1095.94 | 15.76% | 737.62 | 0.8720 | 0.8217 |
| XGBoost | 1274.18 | 18.32% | 902.35 | 0.8270 | 0.7873 |
| HistGradientBoosting | 1825.77 | 26.25% | 1333.61 | 0.6448 | 0.6267 |
| DecisionTree | 2295.82 | 33.01% | 1658.25 | 0.4384 | 0.4389 |
| GradientBoosting | 2420.96 | 34.81% | 1736.54 | 0.3755 | 0.3773 |
| AdaBoost | 3899.48 | 56.06% | 3241.38 | -0.6201 | -1.0091 |

#### B. Rossmann With Customers (Tabel 5, Batas Atas Ablasi)
| Model | RMSE | RMSE% | MAE | R² | CV R² |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **ExtraTrees** | **572.18** | **8.23%** | **389.13** | **0.9651** | 0.9598 |
| **RandomForest** | 574.62 | 8.26% | 391.28 | 0.9648 | **0.9609** |
| XGBoost | 641.62 | 9.22% | 448.20 | 0.9561 | 0.9543 |
| HistGradientBoosting | 868.99 | 12.49% | 625.09 | 0.9195 | 0.9243 |
| DecisionTree | 1101.01 | 15.83% | 798.52 | 0.8708 | 0.8775 |
| GradientBoosting | 1116.97 | 16.06% | 800.09 | 0.8671 | 0.8783 |
| AdaBoost | 2267.38 | 32.60% | 1904.98 | 0.4523 | 0.4208 |

### 2. Dampak Ablasi Fitur (Tabel 6 & Tabel 7)
- **Penambahan `Customers` (C3):** Meningkatkan seluruh model secara konsisten. Model terbaik naik dari `R² = 0.8838` (`RMSE% = 15.01%`) menjadi `R² = 0.9651` (`RMSE% = 8.23%`). Model yang sebelumnya lemah mengalami lonjakan terbesar (`GradientBoosting` +0.4916 `R²`, `AdaBoost` +1.0724 `R²`).
- **Penghapusan Fitur Musiman & Promosi (C3 -> C4):**
  - *Without Customers:* Penurunan tajam di semua model kuat (`RandomForest` turun dari `R² = 0.884` ke `0.607` / delta `-0.277`, `RMSE%` hampir dua kali lipat dari `15.01%` ke `27.63%`; `ExtraTrees` `-0.266`; `XGBoost` `-0.235`).
  - *With Customers:* Dampak jauh lebih kecil (`RandomForest` `-0.028`, `ExtraTrees` `-0.035`), menandakan bahwa `Customers` secara tidak langsung sudah menangkap sebagian efek promosi dan hari libur.
- **Efek Preprocessing:** Transisi `C1 -> C2` memberi peningkatan signifikan pada model bagging & XGBoost (`RandomForest` +0.028 `R²`, p < 0.001), sedangkan penghapusan *zero-variance* (`C2 -> C3`) berdampak sangat kecil (delta `R² <= 0.001`, p > 0.05).

### 3. Perbandingan dengan Baseline Klasik (Tabel 8, C3 Without Customers)
| Model | RMSE | RMSE% | MAE | R² | CV R² |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Ridge Regression | 2695.51 | 38.75% | 1958.88 | 0.2259 | 0.1891 |
| Seasonal-Naive (lag-7) | 1956.36 | 28.13% | 1466.33 | 0.5922 | 0.4884 |
| ETS (per-store) | 1823.27 | 26.21% | 1347.27 | 0.6458 | 0.4887 |
| **RandomForest (C3)** | **1044.25** | **15.01%** | **701.01** | **0.8838** | **0.8319** |

`RandomForest` menurunkan RMSE sekitar **43%** dibanding baseline klasik terbaik (`ETS`) dan unggul signifikan secara statistik terhadap seluruh baseline (Diebold-Mariano Holm-corrected `p < 0.001`, Tabel 10).

### 4. Sensitivity Analysis & Interpretabilitas SHAP (Tabel 12 & Bagian 4.6)
- **Sensitivitas (Tabel 12):** Mengubah `n_estimators` (`50`, `100`, `200`) hampir tidak mengubah peringkat (`RandomForest` stabil di `R² = 0.8828` sampai `0.8840`). Membatasi kedalaman pohon secara agresif (`max_depth = 15`) menjatuhkan performa kedua model secara drastis (`R²` turun ~0.18 sampai 0.20 menjadi `0.6829` untuk RF dan `0.6917` untuk ET).
- **Agregasi Atribusi SHAP:**
  - *Without Customers (`RandomForest`, C3):* Promotional **39.7%**, Store **23.4%**, Competition **18.7%**, Calendar/Temporal **18.2%** (gabungan Promotional + Temporal ~58%).
  - *With Customers (`ExtraTrees`, C3):* Customer **43.8%**, Promotional **22.6%**, Store **19.3%**, Competition **7.6%**, Calendar/Temporal **6.8%**.

---

## Verifikasi Pipeline Lokal

Benchmark cepat pada dataset penuh (844.338 baris, C3, Without Customers, held-out 80/20) di Apple Silicon M3 (16 GB RAM) menunjukkan kecocokan tinggi dengan Tabel 4 paper:

| Model | Waktu 1x Fit | R² (Implementasi Ini) | R² (Paper Tabel 4) |
| :--- | :---: | :---: | :---: |
| `DecisionTree` | 2,58 dtk | `0.4339` | `0.4384` |
| `HistGradientBoosting` | 6,10 dtk | `0.6660` | `0.6448` |
| `XGBoost` | 2,46 dtk | `0.8284` | `0.8270` |

---

## Struktur Direktori

```text
Rossmann Sales Forecasting/
├── docs/
│   └── Albassam_2026_Retail_Sales_Forecasting_Tree_Based_ML.pdf
├── src/
│   ├── config.py             # Konstanta eksperimen, regex C4/C5, path output
│   ├── data_loader.py        # Merge train + store, sorting kronologis, split 80/20
│   ├── preprocessing.py      # Pipeline fold-safe C1-C5
│   ├── models.py             # 7 model tree-based dengan konfigurasi paper
│   ├── baselines.py          # Ridge Regression, Seasonal-Naive, per-store ETS
│   ├── metrics.py            # MAE, RMSE, RMSE%, R²
│   ├── evaluation.py         # Engine benchmark + auto-checkpoint/resume
│   ├── statistics.py         # Diebold-Mariano (Newey-West HAC lag=7) + Holm
│   ├── sensitivity.py        # Sensitivity analysis (Tabel 12)
│   └── interpretability.py   # Actual vs Predicted, Feature Importance, SHAP
├── run_experiments.py        # Orchestrator CLI utama
├── requirements.txt
└── README.md
```

---

## Cara Menjalankan

### 1. Persiapan Dataset & Dependensi
Unduh dataset [Rossmann Store Sales (Kaggle)](https://www.kaggle.com/c/rossmann-store-sales) lalu ekstrak `train.csv` dan `store.csv` ke folder `data/`.

```bash
pip install -r requirements.txt
```

### 2. Mode Eksekusi (Dengan Auto-Checkpoint & Resume)
Pipeline otomatis menyimpan hasil dan prediksi setiap selesai 1 kombinasi `(Skenario, Konfigurasi, Model)` ke `outputs/checkpoints/`. Jika proses dihentikan (`Ctrl + C`), jalankan ulang perintah yang sama dan model yang sudah selesai akan dilewati otomatis (`RESUMED`).

```bash
# 1. Uji cepat (smoke test 25 toko, ~20 detik)
python3 run_experiments.py --sample-stores 25 --n-estimators 20 --force-rerun

# 2. Eksekusi bertahap di full dataset (disarankan untuk laptop 16 GB RAM)
# Tahap A: model cepat dulu (~2 menit)
python3 run_experiments.py --models DecisionTree HistGradientBoosting XGBoost --skip-baselines --skip-stats --skip-sensitivity

# Tahap B: lanjut model berat (otomatis resume hasil Tahap A)
python3 run_experiments.py --n-jobs 4

# 3. Full run tanpa 5-fold CV (hemat ~5x waktu, tetap dapat hasil held-out 80/20)
python3 run_experiments.py --skip-cv --n-jobs 4
```

Opsi CLI utama:
- `--models`: pilih subset model (contoh: `--models RandomForest ExtraTrees`).
- `--configs`: pilih subset konfigurasi (`C1` sampai `C5`).
- `--scenarios`: `without`, `with`, atau `both` (default).
- `--n-jobs`: jumlah thread CPU paralel (default `4` untuk mencegah swap RAM).
- `--force-rerun`: abaikan checkpoint dan hitung ulang dari awal.
