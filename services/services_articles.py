from database.db import get_connection
from datetime import datetime
import uuid


# ---------------------------------------------------
# CREATE ARTICLE
# ---------------------------------------------------

def create_trust_article(
    title,
    content,
    category=None,
    article_type=None,
    is_required=0
):
    conn = get_connection()
    cur = conn.cursor()

    article_id = f"ART-{uuid.uuid4().hex[:8].upper()}"

    cur.execute("""
        INSERT INTO trust_articles (
            article_id,
            title,
            category,
            article_type,
            content,
            is_required
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        article_id,
        title,
        category,
        article_type,
        content,
        is_required
    ))

    conn.commit()
    conn.close()

    return article_id


# ---------------------------------------------------
# GET ALL ARTICLES
# ---------------------------------------------------

def get_all_trust_articles():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM trust_articles
        WHERE is_active = 1
        ORDER BY category, title
    """)

    rows = cur.fetchall()

    conn.close()

    return rows


# ---------------------------------------------------
# GET ARTICLE BY ID
# ---------------------------------------------------

def get_trust_article(article_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM trust_articles
        WHERE article_id = ?
    """, (article_id,))

    row = cur.fetchone()

    conn.close()

    return row


# ---------------------------------------------------
# ASSIGN ARTICLE TO TRUST
# ---------------------------------------------------

def assign_article_to_trust(
    trust_id,
    article_id,
    sort_order=0
):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO trust_article_assignments (
            trust_id,
            article_id,
            sort_order
        )
        VALUES (?, ?, ?)
    """, (
        trust_id,
        article_id,
        sort_order
    ))

    conn.commit()
    conn.close()


# ---------------------------------------------------
# GET TRUST ARTICLES
# ---------------------------------------------------

def get_articles_for_trust(trust_id):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT
            ta.*,
            taa.sort_order
        FROM trust_article_assignments taa
        JOIN trust_articles ta
            ON ta.article_id = taa.article_id
        WHERE taa.trust_id = ?
        AND taa.is_enabled = 1
        ORDER BY taa.sort_order ASC
    """, (trust_id,))

    rows = cur.fetchall()

    conn.close()

    return rows
