import re
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import sent_tokenize, word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('punkt_tab', quiet=True)

STOP_WORDS = set(stopwords.words('english'))


def clean_text(text: str) -> str:
    """
    Lowercase, remove special characters, remove stopwords.
    """
    text = text.lower()
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    tokens = word_tokenize(text)
    tokens = [t for t in tokens if t not in STOP_WORDS and len(t) > 2]
    return ' '.join(tokens)


def extract_keywords(text: str, num: int = 8) -> str:
    """
    Extract top keywords from text using TF-IDF.
    Used to build a Google search query.
    """
    try:
        vectorizer = TfidfVectorizer(max_features=num, stop_words='english')
        vectorizer.fit_transform([text])
        keywords = vectorizer.get_feature_names_out()
        return ' '.join(keywords)
    except Exception:
        # Fallback: just take first 8 words
        words = text.split()[:8]
        return ' '.join(words)


def compute_similarity(text1: str, text2: str) -> dict:
    """
    Compare two texts and return:
    - overall similarity percentage
    - matched sentence pairs
    - plagiarism verdict
    """
    if not text1.strip() or not text2.strip():
        return {
            'similarity_percentage': 0.0,
            'matched_sentences': [],
            'plagiarism_detected': False,
            'verdict': 'clean',
        }

    # Overall similarity using TF-IDF + cosine
    cleaned1 = clean_text(text1)
    cleaned2 = clean_text(text2)

    vectorizer = TfidfVectorizer()
    try:
        tfidf_matrix = vectorizer.fit_transform([cleaned1, cleaned2])
        score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        percentage = round(float(score) * 100, 2)
    except Exception:
        percentage = 0.0

    # Sentence-level matching
    sentences1 = sent_tokenize(text1)
    sentences2 = sent_tokenize(text2)
    matched_sentences = []

    if sentences1 and sentences2:
        sent_vectorizer = TfidfVectorizer()
        try:
            all_sentences = sentences1 + sentences2
            sent_vectorizer.fit(all_sentences)

            for s1 in sentences1:
                for s2 in sentences2:
                    pair_matrix = sent_vectorizer.transform([s1, s2])
                    sim = cosine_similarity(
                        pair_matrix[0:1], pair_matrix[1:2]
                    )[0][0]

                    if sim >= 0.6:  # 60% threshold
                        matched_sentences.append({
                            'original_sentence': s1,
                            'matched_sentence': s2,
                            'similarity': round(float(sim) * 100, 1),
                        })
        except Exception:
            pass

    # Remove duplicate matches
    seen = set()
    unique_matches = []
    for m in matched_sentences:
        key = m['original_sentence'][:50]
        if key not in seen:
            seen.add(key)
            unique_matches.append(m)

    # Verdict
    if percentage >= 70:
        verdict = 'high'
    elif percentage >= 40:
        verdict = 'medium'
    elif percentage >= 15:
        verdict = 'low'
    else:
        verdict = 'clean'

    return {
        'similarity_percentage': percentage,
        'matched_sentences': unique_matches,
        'plagiarism_detected': percentage >= 15,
        'verdict': verdict,
    }


def compare_against_sources(user_text: str, sources: list) -> dict:
    """
    Compare user text against multiple scraped web sources.
    Returns the best match and all results combined.

    sources = [{'url': '...', 'text': '...'}, ...]
    """
    all_matches = []
    source_results = []
    highest_similarity = 0.0
    highest_source = None

    for source in sources:
        if not source.get('text', '').strip():
            continue

        result = compute_similarity(user_text, source['text'])
        result['url'] = source['url']
        result['title'] = source.get('title', source['url'])
        source_results.append(result)

        # Collect all matched sentences
        for match in result['matched_sentences']:
            match['source_url'] = source['url']
            match['source_title'] = source.get('title', source['url'])
            all_matches.append(match)

        # Track highest match
        if result['similarity_percentage'] > highest_similarity:
            highest_similarity = result['similarity_percentage']
            highest_source = source['url']

    # Sort by similarity descending
    source_results.sort(key=lambda x: x['similarity_percentage'], reverse=True)

    # Deduplicate matched sentences
    seen = set()
    unique_all_matches = []
    for m in all_matches:
        key = m['original_sentence'][:50]
        if key not in seen:
            seen.add(key)
            unique_all_matches.append(m)

    # Overall verdict based on highest match
    if highest_similarity >= 70:
        verdict = 'high'
    elif highest_similarity >= 40:
        verdict = 'medium'
    elif highest_similarity >= 15:
        verdict = 'low'
    else:
        verdict = 'clean'

    return {
        'overall_similarity': round(highest_similarity, 2),
        'verdict': verdict,
        'plagiarism_detected': highest_similarity >= 15,
        'highest_source': highest_source,
        'source_results': source_results,
        'all_matched_sentences': unique_all_matches[:30],  # limit to 30
    }