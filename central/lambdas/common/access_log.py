def log_event(cur, event, user_id, team_id=None, file_id=None, transfer_id=None, outcome=None):
    """Append an access-log row inside the caller's transaction. Ids only: never
    pass request bodies, team names, queries or file content. `outcome` is a short code."""
    if transfer_id is None and outcome is None:
        cur.execute(
            "INSERT INTO access_log (event, user_id, team_id, file_id) VALUES (%s, %s, %s, %s)",
            (event, user_id, str(team_id) if team_id else None, file_id),
        )
        return
    cur.execute(
        "INSERT INTO access_log (event, user_id, team_id, file_id, transfer_id, outcome) "
        "VALUES (%s, %s, %s, %s, %s, %s)",
        (event, user_id, str(team_id) if team_id else None, file_id,
         str(transfer_id) if transfer_id else None, outcome),
    )
