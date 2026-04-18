import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from typing import List, Dict


def mine_rules(history: List[Dict]) -> List[Dict]:
    dataset = []
    for h in history:
        row = {topic: True for topic in h['failed_topics']}
        dataset.append(row)

    df = pd.DataFrame(dataset).fillna(False)

    if df.empty or df.shape[1] < 2:
        return []

    frequent_itemsets = apriori(df, min_support=0.05, use_colnames=True)

    if frequent_itemsets.empty:
        return []

    rules = association_rules(frequent_itemsets, metric="lift", min_threshold=1.1)

    results = []
    for _, row in rules.iterrows():
        ant = list(row['antecedents'])
        con = list(row['consequents'])

        ant_str = " + ".join(ant)
        con_str = " + ".join(con)

        results.append({
            "rule": f"{ant_str} -> {con_str}",
            "antecedents": ant,
            "consequents": con,
            "confidence": round(row['confidence'], 2),
            "lift": round(row['lift'], 2),
            "support": round(row['support'], 2)
        })

    results.sort(key=lambda x: (x['lift'], x['confidence']), reverse=True)

    return results