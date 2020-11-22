import sqlite3

with sqlite3.connect("db.sqlite3") as conn:
    # ------- setup tables -------
    statement = """CREATE TABLE lol_accounts (
        discord_name text,
        league_name text,
        server_name text,
        PRIMARY KEY (league_name, server_name)
        )"""
    conn.execute(statement)

    # -------- inserting many values (SQL injection proof) --------
    lolaccounts = [
        ("Rose#6264", "JeanSuper", "euw"),
        ("Rose#6264", "Fortniter", "euw"),
    ]
    conn.executemany("INSERT INTO lol_accounts VALUES (?,?,?)", lolaccounts)

    # retrieving data (chaining conn events)
    results = conn.execute("SELECT * from lol_accounts").fetchall()
    print(results)