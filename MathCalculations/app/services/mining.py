import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from typing import List, Dict


def mine_rules(history: List[Dict]) -> List[Dict]:
    dataset = []
    for h in history:
        row = {topic: True for topic in h['failed_topics']}
        dataset.append(row)

    df = pd.DataFrame(dataset).fillna(False)

    # Зменшили поріг з 5 до 1 запису, бо даних мало
    if df.empty:
        return []

        # FIX: Зменшили min_support з 0.2 до 0.01 (1%), щоб гарантовано знайти правила
    frequent_itemsets = apriori(df, min_support=0.01, use_colnames=True)

    if frequent_itemsets.empty:
        return []

    # FIX: Зменшили min_threshold з 0.5 до 0.1
    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.1)

    results = []
    for _, row in rules.iterrows():
        ant = list(row['antecedents'])[0]
        con = list(row['consequents'])[0]
        results.append({
            "rule": f"Якщо слабкий {ant} -> Слабкий {con}",
            "confidence": round(row['confidence'], 2)
        })

    # Сортуємо, щоб зверху були найсильніші
    results.sort(key=lambda x: x['confidence'], reverse=True)
    return results