import sqlite3
from datetime import datetime

DB_PATH = "tokenized_assets.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON;")
    
    # 1. Tabla de Activos Subyacentes (RWA)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS assets (
        asset_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        total_valuation REAL NOT NULL,
        created_at TEXT NOT NULL
    );
    """)
    
    # 2. Tabla de Wallets / Participantes
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS wallets (
        wallet_address TEXT PRIMARY KEY,
        owner_name TEXT NOT NULL,
        role TEXT NOT NULL
    );
    """)
    
    # 3. Tabla de Tokens Emitidos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tokens (
        token_id TEXT PRIMARY KEY,
        asset_id TEXT NOT NULL,
        symbol TEXT NOT NULL,
        total_supply REAL NOT NULL,
        decimals INTEGER DEFAULT 2,
        FOREIGN KEY (asset_id) REFERENCES assets(asset_id)
    );
    """)
    
    # 4. Tabla de Transacciones / Trazabilidad (Ledger)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS transactions (
        tx_hash TEXT PRIMARY KEY,
        token_id TEXT NOT NULL,
        from_wallet TEXT,
        to_wallet TEXT NOT NULL,
        amount REAL NOT NULL,
        tx_type TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (token_id) REFERENCES tokens(token_id),
        FOREIGN KEY (from_wallet) REFERENCES wallets(wallet_address),
        FOREIGN KEY (to_wallet) REFERENCES wallets(wallet_address)
    );
    """)
    
    conn.commit()
    conn.close()
    print("[✔] Base de datos inicializada correctamente.")

def seed_mass_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    print("[⏳] Generando 50 registros masivos...")
    
    # Bucle para crear 50 activos y sus respectivos tokens y wallets
    for i in range(1, 51):
        asset_id = f"ASSET-BOND-{i:03d}"
        name = f"Bono Municipal Masivo Fase {i}"
        description = f"Financiamiento para proyecto de infraestructura comunitaria #{i}"
        valuation = 100000.0 + (i * 5000)
        
        token_id = f"TOKEN-GBOND-{i}"
        symbol = f"GBND{i}"
        total_supply = 50000.00
        
        wallet_addr = f"0xWalletGov{i}"
        wallet_name = f"Institución Pública Regional {i}"
        
        # 1. Insertar Wallet
        cursor.execute("INSERT OR IGNORE INTO wallets VALUES (?, ?, ?)", (wallet_addr, wallet_name, "Issuer"))
        
        # 2. Insertar Activo RWA
        cursor.execute("INSERT OR IGNORE INTO assets VALUES (?, ?, ?, ?, ?)", (asset_id, name, description, valuation, now))
        
        # 3. Insertar Token
        cursor.execute("INSERT OR IGNORE INTO tokens VALUES (?, ?, ?, ?, ?)", (token_id, asset_id, symbol, total_supply, 2))
        
        # 4. Transacción de emisión inicial
        tx_hash = f"tx_mass_issue_{i:03d}"
        cursor.execute("INSERT OR IGNORE INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?)", 
                       (tx_hash, token_id, None, wallet_addr, total_supply, "ISSUE", now))

    conn.commit()
    conn.close()
    print("[✔] ¡50 registros masivos agregados exitosamente!")

if __name__ == "__main__":
    init_db()
    seed_mass_data()