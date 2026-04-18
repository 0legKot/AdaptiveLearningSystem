import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import warnings

warnings.filterwarnings('ignore')


# --- BKT CORE ---
def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + np.exp(-max(-10.0, min(10.0, x))))


def logit(p: float) -> float:
    p = float(np.clip(p, 1e-9, 1 - 1e-9))
    return np.log(p / (1 - p))


def entropy_bernoulli(p: float) -> float:
    p = float(np.clip(p, 1e-9, 1 - 1e-9))
    return -(p * np.log(p) + (1 - p) * np.log(1 - p))


def topic_from_tag(tag_str: str) -> str:
    if "HTML" in tag_str:
        return "HTML/Frontend"
    if "SQL" in tag_str or "Database" in tag_str:
        return "SQL/Database"
    if "Python" in tag_str:
        return "Python/Backend"
    if "PHP" in tag_str:
        return "PHP/Backend"
    return "General"


def parse_metadata(columns):
    questions_meta = []
    for col in columns:
        tag_match = re.search(r'\[Tag:(.*?)\]', col)
        opts_match = re.search(r'\[Opts:(\d+)\]', col)
        if not (tag_match and opts_match):
            continue
        questions_meta.append({
            'col_name': col,
            'topic': topic_from_tag(tag_match.group(1).strip()),
            'opts': int(opts_match.group(1))
        })
    return questions_meta


def calc_guess_slip(difficulty: float, total_options: int):
    base_guess = 1.0 / max(total_options, 2)
    p_guess = min(base_guess + 0.10, base_guess + 0.10 * sigmoid(-difficulty))
    p_slip = 0.10 + 0.20 * sigmoid(difficulty)
    return float(np.clip(p_guess, 0.01, 0.60)), float(np.clip(p_slip, 0.01, 0.60))


def calculate_bkt(p_known: float, is_correct: bool, difficulty: float, total_options: int, attempt_num: int) -> float:
    p_guess, p_slip = calc_guess_slip(difficulty, total_options)
    p_learn = 0.01 * max(0.05, 1.0 - (difficulty * 0.15)) * np.exp(-0.15 * attempt_num) if is_correct else 0.0

    prior = float(p_known)
    likelihood = prior * (1 - p_slip) if is_correct else prior * p_slip
    marginal = likelihood + (1 - prior) * (p_guess if is_correct else (1 - p_guess))
    posterior = prior if marginal == 0 else (likelihood / marginal)

    return float(np.clip(posterior + (1 - posterior) * p_learn, 0.01, 0.99))


def calibrate_difficulty_smoothed(df: pd.DataFrame, questions_meta, alpha=1.0, beta=1.0):
    for q in questions_meta:
        s = df[q['col_name']].sum(skipna=True)
        n = df[q['col_name']].count()
        if n <= 0:
            q['diff'] = 0.0
            continue
        p_hat = (s + alpha) / (n + alpha + beta)
        q['diff'] = float(-logit(p_hat))
    return questions_meta


def expected_information_gain(p: float, q_diff: float, q_opts: int, attempt_num: int) -> float:
    p_guess, p_slip = calc_guess_slip(q_diff, q_opts)
    p_r1 = p * (1 - p_slip) + (1 - p) * p_guess
    h_now = entropy_bernoulli(p)
    h_exp = (
        p_r1 * entropy_bernoulli(calculate_bkt(p, True, q_diff, q_opts, attempt_num)) +
        (1 - p_r1) * entropy_bernoulli(calculate_bkt(p, False, q_diff, q_opts, attempt_num))
    )
    return float(h_now - h_exp)


def analyze_results(file_path: str):
    df_raw = pd.read_csv(file_path, sep='\t') if '\t' in open(file_path, encoding='utf-8').readline() else pd.read_csv(file_path, sep=';')
    questions_meta = parse_metadata(df_raw.columns)
    q_cols = [q['col_name'] for q in questions_meta]
    df = df_raw[q_cols].copy()

    for c in q_cols:
        df[c] = pd.to_numeric(df[c], errors='coerce')
        df.loc[~df[c].isin([0, 1]), c] = np.nan

    questions_meta = calibrate_difficulty_smoothed(df, questions_meta)
    unique_topics = sorted(set(q['topic'] for q in questions_meta))
    results = []

    for idx, row in df.iterrows():
        student_data = {'Developer_ID': idx + 1}
        for topic in unique_topics:
            topic_questions = [q for q in questions_meta if q['topic'] == topic]
            if not topic_questions:
                continue

            p_known = 0.15
            available = topic_questions.copy()
            attempt = 0

            while available:
                attempt += 1
                target_diff = (p_known - 0.5) * 6.0

                best_q_idx = max(
                    range(len(available)),
                    key=lambda i: expected_information_gain(
                        p_known,
                        available[i]['diff'],
                        available[i]['opts'],
                        attempt + 1
                    ) - 0.10 * abs(available[i]['diff'] - target_diff)
                )

                q = available.pop(best_q_idx)
                val = row[q['col_name']]
                p_known = calculate_bkt(p_known, bool(val == 1), q['diff'], q['opts'], attempt)

                if attempt >= 7 and (p_known >= 0.95 or p_known <= 0.10):
                    break
                if attempt >= 12 and 0.20 <= p_known <= 0.80:
                    break

            student_data[topic] = round(p_known, 4)
        results.append(student_data)

    return pd.DataFrame(results), unique_topics


def generate_clustering_plots(df_results: pd.DataFrame, unique_topics):
    sns.set_theme(style="whitegrid")

    # --- clustering ---
    x = df_results[unique_topics].fillna(0)
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=20)
    df_results['Cluster'] = kmeans.fit_predict(x)

    cluster_centers = pd.DataFrame(kmeans.cluster_centers_, columns=unique_topics)
    cluster_means = cluster_centers.mean(axis=1)
    sorted_idx = cluster_means.sort_values().index

    role_map = {
        sorted_idx[0]: "Junior / Novice",
        sorted_idx[1]: "I-Shaped (Specialists)",
        sorted_idx[2]: "T-Shaped (Balanced)"
    }

    df_results['Role'] = df_results['Cluster'].map(role_map)

    cluster_centers['Cluster'] = cluster_centers.index
    cluster_centers['Role'] = cluster_centers['Cluster'].map(role_map)
    cluster_centers = cluster_centers.set_index('Role')[unique_topics]

    role_order = ["Junior / Novice", "I-Shaped (Specialists)", "T-Shaped (Balanced)"]
    cluster_centers = cluster_centers.loc[role_order]

    # --- PCA for 2D visualization ---
    pca = PCA(n_components=2, random_state=42)
    coords = pca.fit_transform(x)
    df_results['PC1'] = coords[:, 0]
    df_results['PC2'] = coords[:, 1]

    explained_var = pca.explained_variance_ratio_

    # centers in PCA space
    centers_2d = pca.transform(cluster_centers[unique_topics].values)
    centers_df = pd.DataFrame(centers_2d, columns=['PC1', 'PC2'], index=cluster_centers.index)

    # --- figure 1: heatmap ---
    plt.figure(figsize=(8, 5))
    ax = sns.heatmap(
        cluster_centers.T,
        annot=True,
        cmap="YlGnBu",
        fmt=".2f",
        linewidths=.5,
        cbar_kws={'label': 'Ймовірність володіння навичкою P(L)'}
    )
    ax.set_title('Теплова матриця центроїдів кластерів', fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel('Тип профілю')
    ax.set_ylabel('Технологічний домен')
    plt.tight_layout()
    plt.savefig('Fig1_Cluster_Heatmap.png', dpi=300, bbox_inches='tight')
    plt.close()

    # --- figure 2: PCA scatter ---
    plt.figure(figsize=(9, 6))
    ax = sns.scatterplot(
        data=df_results,
        x='PC1',
        y='PC2',
        hue='Role',
        style='Role',
        s=80
    )

    plt.scatter(
        centers_df['PC1'],
        centers_df['PC2'],
        marker='X',
        s=250,
        linewidths=1.5,
        edgecolor='black',
        label='Центроїди'
    )

    for idx, row in centers_df.iterrows():
        plt.text(row['PC1'] + 0.01, row['PC2'] + 0.01, idx, fontsize=10)

    plt.title(
        f'Просторова візуалізація профілів респондентів у просторі PCA '
        f'(PC1={explained_var[0]:.1%}, PC2={explained_var[1]:.1%})',
        fontsize=12,
        fontweight='bold',
        pad=10
    )
    plt.xlabel('Головна компонента 1')
    plt.ylabel('Головна компонента 2')
    plt.tight_layout()
    plt.savefig('Fig2_PCA_Clusters.png', dpi=300, bbox_inches='tight')
    plt.close()

    # --- figure 3: cluster size barplot ---
    role_counts = (
        df_results['Role']
        .value_counts()
        .reindex(role_order)
        .reset_index()
    )
    role_counts.columns = ['Role', 'Count']

    plt.figure(figsize=(8, 5))
    ax = sns.barplot(data=role_counts, x='Role', y='Count')
    ax.set_title('Розподіл респондентів за типами компетентнісних профілів', fontsize=13, fontweight='bold', pad=12)
    ax.set_xlabel('Тип профілю')
    ax.set_ylabel('Кількість респондентів')

    for container in ax.containers:
        ax.bar_label(container, fmt='%d', padding=3)

    plt.xticks(rotation=10)
    plt.tight_layout()
    plt.savefig('Fig3_Cluster_Sizes.png', dpi=300, bbox_inches='tight')
    plt.close()

    # --- summary table for article text ---
    summary = cluster_centers.copy()
    summary['Cluster_Size'] = role_counts.set_index('Role')['Count']
    summary.to_csv('Cluster_Profile_Summary.csv', encoding='utf-8-sig')

    print("Аналіз завершено.")
    print("Збережено:")
    print("- Fig1_Cluster_Heatmap.png")
    print("- Fig2_PCA_Clusters.png")
    print("- Fig3_Cluster_Sizes.png")
    print("- Cluster_Profile_Summary.csv")


if __name__ == "__main__":
    df_analysis, topics = analyze_results("TestResults.csv")
    generate_clustering_plots(df_analysis, topics)