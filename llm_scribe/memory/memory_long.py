from llm_scribe.DB.connection import get_connection

def save_memory_long(group_id, summary_text):
    conn = get_connection()
    cur = conn.cursor()

    sql1 = """
        SELECT IFNULL(MAX(ver), 0) + 1
        FROM memory_long
        WHERE group_id=%s
        FOR UPDATE
    """
    cur.execute(sql1, (group_id,))
    version = cur.fetchone()[0]

    sql2 = """
        INSERT INTO memory_long(group_id, ver, summary_text, created_at)
        VALUES (%s, %s, %s, NOW())
    """
    cur.execute(sql2, (group_id, version, summary_text))

    conn.commit()
    cur.close()
    conn.close()
    return version
