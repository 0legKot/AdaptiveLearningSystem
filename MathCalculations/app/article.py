import pandas as pd
import numpy as np
import re
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.optimize import curve_fit
import warnings

warnings.filterwarnings('ignore', category=RuntimeWarning)

def sigmoid(x: float) -> float:
    x = max(-10.0, min(10.0, x))
    return 1.0 / (1.0 + np.exp(-x))

def sigmoid_fit(x, L, x0, k, b):
    return L / (1 + np.exp(-k * (x - x0))) + b

def entropy_bernoulli(p: float) -> float:
    p = float(np.clip(p, 1e-9, 1 - 1e-9))
    return -(p * np.log(p) + (1 - p) * np.log(1 - p))

def logit(p: float) -> float:
    p = float(np.clip(p, 1e-9, 1 - 1e-9))
    return np.log(p / (1 - p))

def topic_from_tag(tag_str: str) -> str:
    if "HTML" in tag_str:
        return "HTML"
    if "SQL" in tag_str or "Database" in tag_str:
        return "SQL"
    if "Python" in tag_str:
        return "Python"
    if "PHP" in tag_str:
        return "PHP"
    return "General"

def parse_metadata(columns):
    questions_meta = []
    for col in columns:
        tag_match = re.search(r'\[Tag:(.*?)\]', col)
        opts_match = re.search(r'\[Opts:(\d+)\]', col)

        if not (tag_match and opts_match):
            continue

        tag_str = tag_match.group(1).strip()
        opts = int(opts_match.group(1))
        topic = topic_from_tag(tag_str)

        questions_meta.append({
            'col_name': col,
            'topic': topic,
            'opts': opts
        })
    return questions_meta

def calc_guess_slip(difficulty: float, total_options: int):
    base_guess = 1.0 / max(total_options, 2)
    guess_adjustment = 0.10 * sigmoid(-difficulty)
    p_guess = min(base_guess + 0.10, base_guess + guess_adjustment)

    p_slip = 0.10 + 0.20 * sigmoid(difficulty)
    return float(np.clip(p_guess, 0.01, 0.60)), float(np.clip(p_slip, 0.01, 0.60))

def calculate_bkt(p_known: float, is_correct: bool, difficulty: float, total_options: int, attempt_num: int) -> float:
    p_guess, p_slip = calc_guess_slip(difficulty, total_options)

    if is_correct:
        base_learn = 0.01
        diff_factor = max(0.05, 1.0 - (difficulty * 0.15))
        fatigue_factor = np.exp(-0.15 * attempt_num)
        p_learn = base_learn * diff_factor * fatigue_factor
    else:
        p_learn = 0.0

    prior = float(p_known)

    if is_correct:
        likelihood = prior * (1 - p_slip)
        marginal = likelihood + (1 - prior) * p_guess
    else:
        likelihood = prior * p_slip
        marginal = likelihood + (1 - prior) * (1 - p_guess)

    posterior = prior if marginal == 0 else (likelihood / marginal)
    p_next = posterior + (1 - posterior) * p_learn

    return float(np.clip(p_next, 0.01, 0.99))

def calibrate_difficulty_smoothed(df: pd.DataFrame, questions_meta, alpha=1.0, beta=1.0):
    for q in questions_meta:
        col = q['col_name']
        s = df[col].sum(skipna=True)
        n = df[col].count()
        if n <= 0:
            q['diff'] = 0.0
            q['p_hat'] = np.nan
            q['n'] = 0
            continue

        p_hat = (s + alpha) / (n + alpha + beta)
        q['p_hat'] = float(p_hat)
        q['n'] = int(n)
        q['diff'] = float(-logit(p_hat))
    return questions_meta

def expected_information_gain(p: float, q_diff: float, q_opts: int, attempt_num: int) -> float:
    p = float(np.clip(p, 0.01, 0.99))
    p_guess, p_slip = calc_guess_slip(q_diff, q_opts)

    p_r1 = p * (1 - p_slip) + (1 - p) * p_guess
    p_r0 = 1 - p_r1

    p_next_if_1 = calculate_bkt(p, True,  q_diff, q_opts, attempt_num)
    p_next_if_0 = calculate_bkt(p, False, q_diff, q_opts, attempt_num)

    H_now = entropy_bernoulli(p)
    H_exp = p_r1 * entropy_bernoulli(p_next_if_1) + p_r0 * entropy_bernoulli(p_next_if_0)
    return float(H_now - H_exp)

def analyze_results(file_path: str,
                    sep=';',
                    alpha=1.0, beta=1.0,
                    prior_p=0.15,
                    mastery_threshold=0.95,
                    fail_threshold=0.10,
                    min_items=5,
                    max_items=12):

    df_raw = pd.read_csv(file_path, sep=sep)

    questions_meta = parse_metadata(df_raw.columns)

    q_cols = [q['col_name'] for q in questions_meta]
    df = df_raw[q_cols].copy()

    for c in q_cols:
        df[c] = pd.to_numeric(df[c], errors='coerce')
        df.loc[~df[c].isin([0, 1]), c] = np.nan

    questions_meta = calibrate_difficulty_smoothed(df, questions_meta, alpha=alpha, beta=beta)

    unique_topics = sorted(set(q['topic'] for q in questions_meta))
    results = []

    for idx, row in df.iterrows():
        student_data = {'Student_ID': idx + 1}

        for topic in unique_topics:
            topic_questions = [q for q in questions_meta if q['topic'] == topic]
            if not topic_questions:
                continue

            vals = row[[q['col_name'] for q in topic_questions]]
            actual_score = int(np.nansum(vals.values))
            total_answered = int(np.sum(~np.isnan(vals.values)))
            denom = len(topic_questions)
            actual_pct = round((actual_score / denom) * 100, 2) if denom else 0.0

            p_known = float(prior_p)
            questions_to_mastery = 0
            mastery_achieved = False

            available = topic_questions.copy()
            attempt = 0

            while available:
                attempt += 1

                target_diff = (p_known - 0.5) * 6.0
                lam = 0.10

                def score(q):
                    ig = expected_information_gain(p_known, q['diff'], q['opts'], attempt_num=attempt + 1)
                    proximity_penalty = lam * abs(q['diff'] - target_diff)
                    return ig - proximity_penalty

                best_q_idx = max(range(len(available)), key=lambda i: score(available[i]))
                q = available.pop(best_q_idx)

                val = row[q['col_name']]
                is_correct = bool(val == 1)

                p_known = calculate_bkt(
                    p_known=p_known,
                    is_correct=is_correct,
                    difficulty=q['diff'],
                    total_options=q['opts'],
                    attempt_num=attempt
                )

                questions_to_mastery += 1

                if attempt >= min_items and p_known >= mastery_threshold:
                    mastery_achieved = True
                    break

                if attempt >= min_items and p_known <= fail_threshold:
                    mastery_achieved = False
                    break

                if attempt >= max_items and 0.20 <= p_known <= 0.80:
                    mastery_achieved = False
                    break

            student_data[f'{topic}_Actual_Score'] = actual_score
            student_data[f'{topic}_Actual_Percentage'] = actual_pct
            student_data[f'{topic}_Final_P'] = round(p_known, 4)
            student_data[f'{topic}_Mastery'] = mastery_achieved
            student_data[f'{topic}_Questions_Needed'] = questions_to_mastery
            student_data[f'{topic}_Answered'] = total_answered

        results.append(student_data)

    results_df = pd.DataFrame(results)
    return results_df, questions_meta, unique_topics

def generate_research_plot(df_results, unique_topics):
    sns.set_theme(style="whitegrid", palette="muted")

    plot_df = pd.DataFrame()
    for topic in unique_topics:
        cols = [f'{topic}_Actual_Percentage', f'{topic}_Questions_Needed', f'{topic}_Final_P']
        if not all(c in df_results.columns for c in cols):
            continue
        temp = df_results[cols].copy()
        temp.columns = ['Actual_Percentage', 'Questions_Needed', 'Final_P']
        temp['Topic'] = topic
        plot_df = pd.concat([plot_df, temp], ignore_index=True)

    fig = plt.figure(figsize=(22, 12))
    gs = fig.add_gridspec(2, 3, height_ratios=[1, 1.2])

    ax1 = fig.add_subplot(gs[0, 0])
    sns.histplot(data=plot_df, x='Actual_Percentage', bins=15, kde=True, color='teal', ax=ax1)
    ax1.set_title('Distribution of Actual Knowledge (n=250)', pad=15, fontsize=14)
    ax1.set_xlabel('Actual Correct Answers (%)')
    ax1.set_ylabel('Number of Students')

    ax2 = fig.add_subplot(gs[0, 1:3])
    avg_questions = plot_df.groupby('Topic', as_index=False)['Questions_Needed'].mean()
    avg_questions['Type'] = 'Adaptive (IG + BKT)'

    static_data = pd.DataFrame({'Topic': unique_topics, 'Questions_Needed': [25] * len(unique_topics)})
    static_data['Type'] = 'Static Test'

    bar_data = pd.concat([static_data, avg_questions], ignore_index=True)

    sns.barplot(data=bar_data, x='Topic', y='Questions_Needed', hue='Type', palette='viridis', ax=ax2)
    ax2.set_title('Algorithm Efficiency: Test Length Reduction', pad=15, fontsize=14)
    ax2.set_xlabel('Topic')
    ax2.set_ylabel('Average Questions Administered')

    for p in ax2.patches:
        ax2.annotate(f"{p.get_height():.1f}",
                     (p.get_x() + p.get_width() / 2., p.get_height()),
                     ha='center', va='bottom', fontsize=11,
                     xytext=(0, 5), textcoords='offset points')

    axes_bottom = [fig.add_subplot(gs[1, i]) for i in range(3)]
    topics_for_scatter = unique_topics[:3]
    palette = sns.color_palette("Set2", len(unique_topics))

    for idx, topic in enumerate(topics_for_scatter):
        ax = axes_bottom[idx]
        topic_data = plot_df[plot_df['Topic'] == topic].dropna()

        sns.scatterplot(
            data=topic_data,
            x='Actual_Percentage',
            y='Final_P',
            color=palette[idx],
            s=60,
            alpha=0.7,
            ax=ax,
            label=f'{topic} Data'
        )

        x_data = topic_data['Actual_Percentage'].values
        y_data = topic_data['Final_P'].values

        if len(x_data) >= 6:
            try:
                p0 = [max(y_data), np.median(x_data), 0.1, min(y_data)]
                popt, _ = curve_fit(sigmoid_fit, x_data, y_data, p0, maxfev=10000)
                x_fit = np.linspace(min(x_data), max(x_data), 100)
                y_fit = sigmoid_fit(x_fit, *popt)
                ax.plot(x_fit, y_fit, color='crimson', linestyle='--', linewidth=2.5, label='Logistic Fit')
            except RuntimeError:
                pass

        ax.set_title(f'BKT Assessment Consistency: {topic}', pad=10, fontsize=12)
        ax.set_xlabel('Actual Score (%)')
        ax.set_ylabel('Probability P(L)')
        ax.axhline(y=0.95, color='green', linestyle=':', alpha=0.8, label='Mastery Threshold')
        ax.legend(loc='lower right', fontsize=9)

    plt.tight_layout()
    plt.savefig('BKT_Comprehensive_Analysis.png', dpi=300)
    plt.close()

def run_threshold_sensitivity(file_path: str, sep=';'):
    settings = [
        {
            'Setting': 'Baseline',
            'mastery_threshold': 0.95,
            'fail_threshold': 0.10,
            'min_items': 7,
            'max_items': 12
        },
        {
            'Setting': 'Lower mastery',
            'mastery_threshold': 0.90,
            'fail_threshold': 0.10,
            'min_items': 7,
            'max_items': 12
        },
        {
            'Setting': 'Higher mastery',
            'mastery_threshold': 0.97,
            'fail_threshold': 0.10,
            'min_items': 7,
            'max_items': 12
        },
        {
            'Setting': 'Earlier stop',
            'mastery_threshold': 0.95,
            'fail_threshold': 0.10,
            'min_items': 5,
            'max_items': 10
        },
        {
            'Setting': 'More conservative',
            'mastery_threshold': 0.95,
            'fail_threshold': 0.10,
            'min_items': 8,
            'max_items': 14
        }
    ]

    all_rows = []

    for cfg in settings:
        df_analysis, meta, topics = analyze_results(
            file_path=file_path,
            sep=sep,
            alpha=1.0,
            beta=1.0,
            prior_p=0.15,
            mastery_threshold=cfg['mastery_threshold'],
            fail_threshold=cfg['fail_threshold'],
            min_items=cfg['min_items'],
            max_items=cfg['max_items']
        )

        question_cols = [f'{topic}_Questions_Needed' for topic in topics if f'{topic}_Questions_Needed' in df_analysis.columns]
        prob_cols = [f'{topic}_Final_P' for topic in topics if f'{topic}_Final_P' in df_analysis.columns]
        mastery_cols = [f'{topic}_Mastery' for topic in topics if f'{topic}_Mastery' in df_analysis.columns]

        questions_values = df_analysis[question_cols].values.flatten()
        prob_values = df_analysis[prob_cols].values.flatten()
        mastery_values = df_analysis[mastery_cols].values.flatten()

        questions_values = questions_values[~pd.isna(questions_values)]
        prob_values = prob_values[~pd.isna(prob_values)]

        early_fail_share = np.mean(prob_values <= cfg['fail_threshold']) * 100
        mastery_share = np.mean(mastery_values.astype(float)) * 100

        all_rows.append({
            'Setting': cfg['Setting'],
            'Mastery_Threshold': cfg['mastery_threshold'],
            'Fail_Threshold': cfg['fail_threshold'],
            'Min_Items': cfg['min_items'],
            'Max_Items': cfg['max_items'],
            'Avg_Questions': round(float(np.mean(questions_values)), 2),
            'Median_Questions': round(float(np.median(questions_values)), 2),
            'Mean_Final_P': round(float(np.mean(prob_values)), 4),
            'Mastery_Share_%': round(float(mastery_share), 2),
            'Early_Fail_Share_%': round(float(early_fail_share), 2)
        })

    sensitivity_df = pd.DataFrame(all_rows)
    sensitivity_df.to_csv('BKT_Threshold_Sensitivity.csv', index=False)

    plt.figure(figsize=(10, 6))
    ax = sns.barplot(data=sensitivity_df, x='Setting', y='Avg_Questions', palette='crest')
    ax.set_title('Sensitivity of stopping thresholds: average test length', fontsize=13, pad=12)
    ax.set_xlabel('Threshold setting')
    ax.set_ylabel('Average administered questions')

    for container in ax.containers:
        ax.bar_label(container, fmt='%.2f', padding=3)

    plt.xticks(rotation=15)
    plt.tight_layout()
    plt.savefig('BKT_Threshold_Sensitivity.png', dpi=300)
    plt.close()

    return sensitivity_df

if __name__ == "__main__":
    df_analysis, meta, topics = analyze_results(
        file_path="TestResults.csv",
        sep=';',
        alpha=1.0, beta=1.0,
        prior_p=0.15,
        mastery_threshold=0.95,
        fail_threshold=0.10,
        min_items=7,
        max_items=12
    )
    generate_research_plot(df_analysis, topics)
    df_analysis.to_csv('BKT_Predictions.csv', index=False)

    sensitivity_df = run_threshold_sensitivity(
        file_path="TestResults.csv",
        sep=';'
    )
    print(sensitivity_df)