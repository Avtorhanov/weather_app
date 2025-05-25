import aiosqlite

DB_PATH = "data/weather.db"  

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city TEXT NOT NULL,
                count INTEGER DEFAULT 1
            )
        """)
        await db.commit()

async def record_search(city: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT count FROM searches WHERE city = ?", (city,))
        row = await cursor.fetchone()
        if row:
            await db.execute("UPDATE searches SET count = count + 1 WHERE city = ?", (city,))
        else:
            await db.execute("INSERT INTO searches (city, count) VALUES (?, ?)", (city, 1))
        await db.commit()

async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT city, count FROM searches ORDER BY count DESC")
        results = await cursor.fetchall()
        return results
