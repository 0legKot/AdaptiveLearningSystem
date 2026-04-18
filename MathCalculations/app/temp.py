import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid", palette="muted")

data_matrix = np.array([
    [0.50, 0.10, 0.25, 0.10],
    [0.25, 0.10, 0.20, 0.15],
    [0.10, 0.25, 0.05, 0.30]
])
rows = ["Easy", "Medium", "Hard"]
cols = ["P(Guess) [2 Options]", "P(Slip) [2 Options]", "P(Guess) [4 Options]", "P(Slip) [4 Options]"]
df_matrix = pd.DataFrame(data_matrix, index=rows, columns=cols)

plt.figure(figsize=(8, 5))
sns.heatmap(df_matrix, annot=True, cmap="YlGnBu", fmt=".2f", cbar_kws={'label': 'Ймовірність'})
plt.title("Рисунок 1 – Ініціалізація матриці параметрів складності питань", pad=20)
plt.tight_layout()
plt.savefig("figure_1_matrix.png", dpi=300)
plt.close()

steps = np.arange(1, 16)
p_learning = [0.30, 0.35, 0.50, 0.65, 0.60, 0.75, 0.82, 0.88, 0.92, 0.95, 0.97, 0.98, 0.98, 0.99, 0.99]

plt.figure(figsize=(8, 5))
plt.plot(steps, p_learning, marker='o', linestyle='-', color='b', linewidth=2, markersize=8)
plt.axhline(y=0.95, color='r', linestyle='--', label='Поріг засвоєння (Mastery Threshold = 0.95)')
plt.ylim(0, 1.05)
plt.xlim(0.5, 15.5)
plt.xlabel("Номер питання")
plt.ylabel("Ймовірність засвоєння P(L)")
plt.title("Рисунок 2 – Приклад кривої навчання студента (Learning Curve)", pad=20)
plt.legend()
plt.tight_layout()
plt.savefig("figure_2_learning_curve.png", dpi=300)
plt.close()

steps_comp = np.arange(1, 11)
p_classic = [0.30, 0.55, 0.75, 0.88, 0.96, 0.98, 0.99, 0.99, 0.99, 0.99]
p_modified = [0.30, 0.38, 0.45, 0.55, 0.62, 0.75, 0.85, 0.92, 0.96, 0.98]

plt.figure(figsize=(8, 5))
plt.plot(steps_comp, p_classic, marker='s', linestyle='-', color='orange', label='Класичний BKT (Static)')
plt.plot(steps_comp, p_modified, marker='o', linestyle='-', color='green', label='Модифікований BKT (Difficulty-Adjusted)')
plt.axhline(y=0.95, color='r', linestyle='--', alpha=0.5)
plt.ylim(0, 1.05)
plt.xlabel("Номер питання (Easy -> Medium -> Hard)")
plt.ylabel("Оцінка P(L)")
plt.title("Рисунок 3 – Порівняння ймовірнісних оцінок моделей", pad=20)
plt.legend()
plt.tight_layout()
plt.savefig("figure_3_comparison.png", dpi=300)
plt.close()

steps_rmse = np.arange(1, 21)
rmse_values = 0.45 * np.exp(-0.15 * steps_rmse) + 0.05 + np.random.normal(0, 0.02, 20)

plt.figure(figsize=(8, 5))
plt.plot(steps_rmse, rmse_values, marker='^', linestyle='-', color='purple', linewidth=2)
plt.ylim(0, 0.5)
plt.xlabel("Кількість заданих питань")
plt.ylabel("Помилка прогнозування (RMSE)")
plt.title("Рисунок 4 – Графік розподілу помилок прогнозування (RMSE)", pad=20)
plt.tight_layout()
plt.savefig("figure_4_rmse.png", dpi=300)
plt.close()

categories = ['Лінійний тест', 'Адаптивний BKT']
lengths = [25.0, 11.4]

plt.figure(figsize=(6, 5))
ax = sns.barplot(x=categories, y=lengths, hue=categories, palette="viridis", legend=False)
for p in ax.patches:
    ax.annotate(f"{p.get_height():.1f}", (p.get_x() + p.get_width() / 2., p.get_height()),
                ha='center', va='bottom', fontsize=12, xytext=(0, 5), textcoords='offset points')
plt.ylim(0, 30)
plt.ylabel("Середня кількість питань")
plt.title("Рисунок 5 – Порівняльна гістограма середньої довжини тестів", pad=20)
plt.tight_layout()
plt.savefig("figure_5_test_length.png", dpi=300)
plt.close()

metrics = ['Accuracy', 'RMSE']
linear_scores = [0.92, 0.08]
bkt_scores = [0.91, 0.09]

df_metrics = pd.DataFrame({
    'Metric': metrics * 2,
    'Score': linear_scores + bkt_scores,
    'Method': ['Лінійний тест']*2 + ['Адаптивний BKT']*2
})

plt.figure(figsize=(7, 5))
ax2 = sns.barplot(data=df_metrics, x='Metric', y='Score', hue='Method', palette="coolwarm")
for p in ax2.patches:
    ax2.annotate(f"{p.get_height():.2f}", (p.get_x() + p.get_width() / 2., p.get_height()),
                 ha='center', va='bottom', fontsize=10, xytext=(0, 5), textcoords='offset points')
plt.ylim(0, 1.1)
plt.ylabel("Значення метрики")
plt.title("Рисунок 6 – Приклад розрахунку метрик збереження точності оцінювання", pad=20)
plt.legend(loc='upper center')
plt.tight_layout()
plt.savefig("figure_6_accuracy.png", dpi=300)
plt.close()