import os
import psycopg2
url = os.environ.get('DATABASE_URL') or 'postgresql://neondb_owner:npg_3HlMFYN6esBt@ep-jolly-rain-ayh8jbn6-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require'
conn = psycopg2.connect(url)
cur = conn.cursor()
cur.execute("SELECT count(*) FROM core_resident;")
print("Residents in Postgres:", cur.fetchone()[0])
conn.close()
