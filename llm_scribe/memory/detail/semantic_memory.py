import json
from typing import List, Dict
from ...storage.database.connection import get_connection


class SemanticMemory:
    """语义记忆"""

    @staticmethod
    def add_concept(
            group_id: int,
            concepts: List[str]
    ):
        if not concepts:
            return
        conn = get_connection()
        cur = conn.cursor()

        sql = """
              INSERT IGNORE INTO semantic_concepts (group_id, concept)
              VALUES (%s, %s) \
              """

        for concept in concepts:
            cur.execute(sql, (group_id, concept))

        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def add_event(
            group_id: int,
            event: str,
            participants: List[str],
            timestamp: int
    ):
        conn = get_connection()
        cur = conn.cursor()

        sql = """
              INSERT INTO semantic_events (group_id, event, participants_json, timestamp)
              VALUES (%s, %s, %s, %s) \
              """

        participants_json = json.dumps(participants, ensure_ascii=False) \
            if participants else None

        cur.execute(sql, (group_id, event, participants_json, timestamp))
        conn.commit()
        cur.close()
        conn.close()

    @staticmethod
    def get_concepts(
            group_id: int
    ) -> List[Dict]:
        conn = get_connection()
        cur = conn.cursor()

        sql = """
              SELECT DISTINCT concept
              FROM semantic_concepts
              WHERE group_id = %s
              ORDER BY created_at DESC \
              """

        cur.execute(sql, (group_id,))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        return [rows[0] for rows in rows]

    @staticmethod
    def get_events(
            group_id: int,
            limit: int = 10
    ) -> List[Dict]:
        conn = get_connection()
        cur = conn.cursor()

        sql = """
              SELECT group_id, event, participants_json, timestamp, created_at
              FROM semantic_events
              WHERE group_id = %s
              ORDER BY timestamp DESC
              LIMIT %s \
              """
        cur.execute(sql, (group_id, limit))
        rows = cur.fetchall()
        cur.close()
        conn.close()

        events = []
        for row in rows:
            participants = json.loads(row["participants_json"]) \
                if row["participants_json"] else []
            events.append({
                "group_id": row["group_id"],
                "event": row["event"],
                "participants": participants,
                "created_at": row["created_at"].isoformat()
                    if row["created_at"] else None
            })

        return events