"""Semantic theme mapping for stock screening (KIK-581).

Uses TEI embeddings to match natural language themes to stock 
business summaries.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from src.data.embedding_client import get_embedding, is_available


def calculate_cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    a = np.array(v1)
    b = np.array(v2)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def rank_stocks_by_theme(
    theme_query: str,
    stocks_data: List[dict],
    top_n: int = 10
) -> List[Tuple[dict, float]]:
    """Rank stocks by their relevance to a semantic theme.

    Parameters
    ----------
    theme_query : str
        The theme to search for (e.g. "Artificial Intelligence").
    stocks_data : list[dict]
        List of stock detail dicts containing 'business_summary'.
    top_n : int
        Number of top results to return.

    Returns
    -------
    list[tuple[dict, float]]
        List of (stock_dict, similarity_score) sorted by score.
    """
    if not is_available():
        return []
        
    query_emb = get_embedding(theme_query)
    if not query_emb:
        return []
        
    results = []
    for stock in stocks_data:
        summary = stock.get("business_summary") or stock.get("name") or ""
        if not summary:
            continue
            
        stock_emb = get_embedding(summary)
        if not stock_emb:
            continue
            
        similarity = calculate_cosine_similarity(query_emb, stock_emb)
        results.append((stock, similarity))
        
    # Sort by similarity descending
    results.sort(key=lambda x: x[1], reverse=True)
    return results[:top_n]
