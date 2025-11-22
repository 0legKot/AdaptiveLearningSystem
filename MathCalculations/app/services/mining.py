import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from typing import List, Dict


def mine_rules(history: List[Dict]) -> List[Dict]:
    # 1. Підготовка даних (One-Hot Encoding)
    dataset = []
    for h in history:
        # h['failed_topics'] може бути пустим, це ок
        row = {topic: True for topic in h['failed_topics']}
        dataset.append(row)

    df = pd.DataFrame(dataset).fillna(False)

    # Якщо даних мало або вони одноманітні - виходимо
    if df.empty or df.shape[1] < 2:
        return []

    # 2. Пошук частих наборів (Frequent Itemsets)
    # min_support = 0.05 (5%) - тема має зустрічатися хоча б у 5% двієчників
    frequent_itemsets = apriori(df, min_support=0.05, use_colnames=True)

    if frequent_itemsets.empty:
        return []

    # 3. Генерація правил
    # metric="lift" - це стандарт для пошуку цікавих залежностей
    rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1.1)

    results = []
    for _, row in rules.iterrows():
        # antecedents (Якщо) та consequents (То) - це frozenset, їх може бути декілька
        ant = list(row['antecedents'])
        con = list(row['consequents'])

        # Формуємо красиві рядки для складних правил: "SQL, C#"
        ant_str = " + ".join(ant)
        con_str = " + ".join(con)

        results.append({
            "rule": f"{ant_str} -> {con_str}",
            "antecedents": ant,
            "consequents": con,
            "confidence": round(row['confidence'], 2),  # Наскільки правило точне (0-1)
            "lift": round(row['lift'], 2),  # Наскільки зв'язок сильніший за випадковий (>1)
            "support": round(row['support'], 2)  # Як часто це трапляється (0-1)
        })

    # Сортуємо: спочатку ті, де зв'язок найсильніший (Lift), потім по точності (Confidence)
    results.sort(key=lambda x: (x['lift'], x['confidence']), reverse=True)

    return results