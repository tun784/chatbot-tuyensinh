from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def load_chunks(filepath="data.txt"):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    chunks = content.split("\n\n")  # Tách đoạn
    return [chunk.strip() for chunk in chunks if len(chunk.strip()) > 50]

def build_vectorizer(chunks):
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(chunks)
    return vectorizer, vectors

def search_best_chunk(query, vectorizer, vectors, chunks):
    query_vec = vectorizer.transform([query])
    sim = cosine_similarity(query_vec, vectors)
    idx = sim.argmax()
    if sim[0, idx] < 0.2:
        return None
    return chunks[idx]