from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def match(products, threshold=0.7):
    names = [p["name_norm"] for p in products]

    tfidf = TfidfVectorizer().fit_transform(names)
    sim = cosine_similarity(tfidf)

    groups = []
    used = set()

    for i in range(len(products)):
        if i in used:
            continue
        group = [products[i]]
        for j in range(i+1, len(products)):
            if sim[i][j] > threshold:
                group.append(products[j])
                used.add(j)
        groups.append(group)

    return groups
