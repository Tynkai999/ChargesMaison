import os
import psycopg2
from dotenv import load_dotenv

def reset_db():
    # Force le chargement du .env
    load_dotenv()
    url = os.environ.get("DATABASE_URL")
    
    if not url:
        print("Erreur: DATABASE_URL n'est pas défini dans l'environnement ou le .env.")
        return

    print("Connexion à la base PostgreSQL pour réinitialisation...")
    try:
        conn = psycopg2.connect(url)
        conn.autocommit = True
        cur = conn.cursor()
        
        # Supprime et recrée le schéma public (supprime toutes les tables)
        print("Suppression des anciennes tables...")
        cur.execute("DROP SCHEMA public CASCADE;")
        cur.execute("CREATE SCHEMA public;")
        # Restaure les permissions par défaut
        cur.execute("GRANT ALL ON SCHEMA public TO public;")
        
        print("✅ Base de données réinitialisée avec succès !")
        conn.close()
    except Exception as e:
        print(f"Erreur lors de la réinitialisation : {e}")

if __name__ == "__main__":
    reset_db()

