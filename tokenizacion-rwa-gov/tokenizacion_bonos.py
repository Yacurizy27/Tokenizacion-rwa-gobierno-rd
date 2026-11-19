from datetime import datetime
from pathlib import Path
import sqlite3

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "tokenized_assets.db"


def get_connection(row_factory=False):
    conn = sqlite3.connect(DB_PATH)
    if row_factory:
        conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def reset_db_for_clean_test():
    """Elimina la base de datos local para dejar un entorno de pruebas limpio."""
    if DB_PATH.exists():
        DB_PATH.unlink()
        print(f"[🗑] Base de datos anterior eliminada: {DB_PATH}")


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

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
    print(f"[✔] Base de datos inicializada correctamente en: {DB_PATH}")


def issue_tokens(tx_hash, token_id, to_wallet, amount):
    """Emite tokens respetando el tope total_supply configurado en la tabla tokens."""
    if amount <= 0:
        print("[✘] EMISIÓN RECHAZADA: El monto debe ser mayor que cero.")
        return

    conn = get_connection()
    cursor = conn.cursor()

    try:
        token_row = cursor.execute(
            "SELECT total_supply FROM tokens WHERE token_id = ?",
            (token_id,)
        ).fetchone()

        if not token_row:
            print(f"[✘] EMISIÓN RECHAZADA: El token '{token_id}' no existe.")
            return

        total_supply = float(token_row[0])
        already_issued = float(cursor.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE token_id = ? AND tx_type = 'ISSUE'",
            (token_id,)
        ).fetchone()[0])

        if already_issued + amount > total_supply + 1e-9:
            disponible_emitir = max(0.0, total_supply - already_issued)
            print(
                f"[✘] EMISIÓN RECHAZADA: Excede el supply de {token_id} "
                f"(Máximo: {total_supply:,.2f} | Ya emitido: {already_issued:,.2f} | Disponible: {disponible_emitir:,.2f})."
            )
            return

        now = datetime.now().isoformat()
        cursor.execute("""
            INSERT INTO transactions (tx_hash, token_id, from_wallet, to_wallet, amount, tx_type, timestamp)
            VALUES (?, ?, NULL, ?, ?, 'ISSUE', ?)
        """, (tx_hash, token_id, to_wallet, amount, now))

        conn.commit()
        print(f"[✔] Emisión exitosa: {amount:,.2f} de {token_id} -> {to_wallet} (Tx: {tx_hash})")

    except sqlite3.IntegrityError as e:
        conn.rollback()
        print(f"[ℹ] Aviso de integridad en emisión: {e}")
    finally:
        conn.close()


def seed_simulation_data():
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()

    cursor.execute("""
    INSERT OR IGNORE INTO assets VALUES (?, ?, ?, ?, ?)
    """, ("ASSET-BOND-001", "Bono Verde Municipal Fase I", "Financiamiento para panel solar comunitario", 500000.00, now))

    wallets = [
        ("0xAyuntamientoGov", "Ayuntamiento Municipal", "Issuer"),
        ("0xInversionistaA", "Fondo de Inversión S.A.", "Investor"),
        ("0xAuditorFiscal", "Auditoría Externa Independiente", "Auditor")
    ]
    cursor.executemany("INSERT OR IGNORE INTO wallets VALUES (?, ?, ?)", wallets)

    cursor.execute("""
    INSERT OR IGNORE INTO tokens VALUES (?, ?, ?, ?, ?)
    """, ("TOKEN-GBOND-1", "ASSET-BOND-001", "GBOND", 10000.00, 2))

    conn.commit()
    conn.close()

    issue_tokens("tx_hash_001", "TOKEN-GBOND-1", "0xAyuntamientoGov", 10000.00)
    print("[✔] Datos iniciales de simulación verificados.")


def seed_mass_data():
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()

    print("[⏳] Generando 50 registros masivos...")

    for i in range(1, 51):
        asset_id = f"ASSET-BOND-{i:03d}"
        name = f"Bono Municipal Masivo Fase {i}"
        description = f"Financiamiento para proyecto de infraestructura comunitaria #{i}"
        valuation = 100000.0 + (i * 5000)

        token_id = f"TOKEN-MBOND-{i:03d}"
        symbol = f"MBND{i}"
        total_supply = 50000.00

        wallet_addr = f"0xWalletGov{i}"
        wallet_name = f"Institución Pública Regional {i}"

        cursor.execute("INSERT OR IGNORE INTO wallets VALUES (?, ?, ?)", (wallet_addr, wallet_name, "Issuer"))
        cursor.execute("INSERT OR IGNORE INTO assets VALUES (?, ?, ?, ?, ?)", (asset_id, name, description, valuation, now))
        cursor.execute("INSERT OR IGNORE INTO tokens VALUES (?, ?, ?, ?, ?)", (token_id, asset_id, symbol, total_supply, 2))

    conn.commit()
    conn.close()

    for i in range(1, 51):
        token_id = f"TOKEN-MBOND-{i:03d}"
        wallet_addr = f"0xWalletGov{i}"
        tx_hash = f"tx_mass_mbond_issue_{i:03d}"
        issue_tokens(tx_hash, token_id, wallet_addr, 50000.00)

    print("[✔] ¡50 registros masivos verificados exitosamente!")


def get_balance(token_id, wallet_address):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT
            (SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE token_id = ? AND to_wallet = ?) -
            (SELECT COALESCE(SUM(amount), 0) FROM transactions WHERE token_id = ? AND from_wallet = ?)
    """, (token_id, wallet_address, token_id, wallet_address))
    balance = cursor.fetchone()[0]
    conn.close()
    return float(balance or 0.0)


def transfer_tokens(tx_hash, token_id, from_wallet, to_wallet, amount):
    if amount <= 0:
        print("[✘] TRANSFERENCIA RECHAZADA: El monto debe ser mayor que cero.")
        return

    conn = get_connection()
    cursor = conn.cursor()

    try:
        current_balance = get_balance(token_id, from_wallet)
        print(f"[ℹ] Validando saldo para [{from_wallet}] -> Disponible: {current_balance:,.2f} | Solicitado: {amount:,.2f}")

        if current_balance < amount:
            print(f"[✘] TRANSFERENCIA RECHAZADA: Fondos insuficientes en la wallet {from_wallet}.")
            return

        now = datetime.now().isoformat()
        cursor.execute("""
        INSERT INTO transactions (tx_hash, token_id, from_wallet, to_wallet, amount, tx_type, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (tx_hash, token_id, from_wallet, to_wallet, amount, "TRANSFER", now))

        conn.commit()
        print(f"[✔] Transferencia exitosa: {amount:,.2f} tokens de {from_wallet} -> {to_wallet} (Tx: {tx_hash})")

    except sqlite3.IntegrityError as e:
        conn.rollback()
        print(f"[ℹ] Aviso de integridad (posible Tx duplicada o wallet/token inexistente): {e}")
    finally:
        conn.close()


def mostrar_resumen_activos():
    with get_connection(row_factory=True) as conn:
        rows = conn.execute("""
            SELECT
                a.asset_id,
                a.name,
                a.total_valuation,
                t.token_id,
                t.symbol,
                t.total_supply,
                t.decimals,
                COUNT(tx.tx_hash) AS total_tx
            FROM assets a
            LEFT JOIN tokens t ON a.asset_id = t.asset_id
            LEFT JOIN transactions tx ON t.token_id = tx.token_id
            GROUP BY a.asset_id, t.token_id
            ORDER BY a.asset_id ASC;
        """).fetchall()

    print("\n" + "=" * 105)
    print("RESUMEN DE ACTIVOS SUBYACENTES (RWA) Y TOKENS EMITIDOS")
    print("=" * 105)
    print(f"{'ASSET ID':<16} | {'TOKEN ID':<16} | {'SÍMBOLO':<8} | {'VALORACIÓN':>14} | {'SUPPLY':>12} | {'TXS':>4}")
    print("-" * 105)

    for r in rows:
        asset_id = r["asset_id"] or "-"
        token_id = r["token_id"] or "SIN TOKEN"
        symbol = r["symbol"] or "-"
        valuation = f"{r['total_valuation']:,.2f}" if r["total_valuation"] is not None else "0.00"
        supply = f"{r['total_supply']:,.2f}" if r["total_supply"] is not None else "0.00"
        txs = r["total_tx"]
        print(f"{asset_id:<16} | {token_id:<16} | {symbol:<8} | {valuation:>14} | {supply:>12} | {txs:>4}")


def mostrar_saldos_por_wallet(token_id=None):
    with get_connection(row_factory=True) as conn:
        base_query = """
            WITH movimientos AS (
                SELECT
                    token_id,
                    to_wallet AS wallet_address,
                    amount AS delta
                FROM transactions
                WHERE to_wallet IS NOT NULL

                UNION ALL

                SELECT
                    token_id,
                    from_wallet AS wallet_address,
                    -amount AS delta
                FROM transactions
                WHERE from_wallet IS NOT NULL
            )
            SELECT
                m.token_id,
                t.symbol,
                m.wallet_address,
                w.owner_name,
                w.role,
                ROUND(SUM(m.delta), 4) AS balance
            FROM movimientos m
            JOIN wallets w ON m.wallet_address = w.wallet_address
            JOIN tokens t ON m.token_id = t.token_id
        """
        params = []
        if token_id:
            base_query += " WHERE m.token_id = ?"
            params.append(token_id)

        base_query += """
            GROUP BY m.token_id, m.wallet_address
            HAVING ABS(balance) > 1e-9
            ORDER BY m.token_id ASC, balance DESC;
        """
        rows = conn.execute(base_query, params).fetchall()

    print("\n" + "=" * 105)
    titulo = f"POSICIONES / SALDOS ACTUALES ({token_id})" if token_id else "POSICIONES / SALDOS ACTUALES (TODOS LOS TOKENS)"
    print(titulo)
    print("=" * 105)
    print(f"{'TOKEN ID':<16} | {'WALLET':<20} | {'TITULAR':<30} | {'ROL':<10} | {'SALDO':>14}")
    print("-" * 105)

    if not rows:
        print("No hay saldos activos registrados para el filtro seleccionado.")
        return

    for r in rows:
        print(f"{r['token_id']:<16} | {r['wallet_address']:<20} | {r['owner_name']:<30} | {r['role']:<10} | {r['balance']:>14,.2f}")


def reconciliar_token(token_id):
    with get_connection(row_factory=True) as conn:
        token_info = conn.execute(
            "SELECT token_id, symbol, total_supply FROM tokens WHERE token_id = ?",
            (token_id,)
        ).fetchone()

        if not token_info:
            print(f"\n[✘] El token '{token_id}' no existe.")
            return

        emitido = conn.execute("""
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM transactions
            WHERE token_id = ? AND tx_type = 'ISSUE'
        """, (token_id,)).fetchone()["total"]

        circulacion = conn.execute("""
            WITH movimientos AS (
                SELECT to_wallet AS wallet_address, amount AS delta
                FROM transactions
                WHERE token_id = ? AND to_wallet IS NOT NULL
                UNION ALL
                SELECT from_wallet AS wallet_address, -amount AS delta
                FROM transactions
                WHERE token_id = ? AND from_wallet IS NOT NULL
            )
            SELECT COALESCE(SUM(delta), 0) AS total
            FROM movimientos
        """, (token_id, token_id)).fetchone()["total"]

    print("\n" + "-" * 70)
    print(f"RECONCILIACIÓN CONTABLE — {token_info['token_id']} ({token_info['symbol']})")
    print("-" * 70)
    print(f"Supply configurado en tabla 'tokens' : {token_info['total_supply']:>14,.2f}")
    print(f"Total emitido en ledger ('ISSUE')   : {emitido:>14,.2f}")
    print(f"Suma de saldos en circulación        : {circulacion:>14,.2f}")
    diferencia = abs(emitido - circulacion)
    estado = "CUADRADO [✔]" if diferencia < 1e-9 else f"DESCUADRE ({diferencia:,.4f}) [✘]"
    print(f"Estado de integridad                 : {estado}")


def mostrar_trazabilidad(token_id, limite=15):
    with get_connection(row_factory=True) as conn:
        rows = conn.execute("""
            SELECT
                t.timestamp,
                t.tx_type,
                t.tx_hash,
                COALESCE(w1.owner_name, 'SISTEMA (Emisión)') AS emisor,
                w2.owner_name AS receptor,
                t.amount
            FROM transactions t
            LEFT JOIN wallets w1 ON t.from_wallet = w1.wallet_address
            JOIN wallets w2 ON t.to_wallet = w2.wallet_address
            WHERE t.token_id = ?
            ORDER BY t.timestamp ASC, t.rowid ASC
            LIMIT ?;
        """, (token_id, limite)).fetchall()

    print("\n" + "=" * 110)
    print(f"TRAZABILIDAD / LEDGER — {token_id} (mostrando hasta {limite} registros)")
    print("=" * 110)
    print(f"{'FECHA/HORA':<19} | {'TIPO':<8} | {'TX HASH':<20} | {'EMISOR':<24} | {'RECEPTOR':<24} | {'MONTO':>12}")
    print("-" * 110)

    for r in rows:
        fecha = (r["timestamp"] or "")[:19]
        print(f"{fecha:<19} | {r['tx_type']:<8} | {r['tx_hash']:<20} | {r['emisor']:<24} | {r['receptor']:<24} | {r['amount']:>12,.2f}")


if __name__ == "__main__":
    print("[▶] Iniciando ejecución de tokenizacion_bonos.py...")
    # reset_db_for_clean_test()  # Descomenta solo si deseas reiniciar la BD de pruebas desde cero
    init_db()
    seed_simulation_data()
    seed_mass_data()

    transfer_tokens(
        tx_hash="tx_hash_002",
        token_id="TOKEN-GBOND-1",
        from_wallet="0xAyuntamientoGov",
        to_wallet="0xInversionistaA",
        amount=2500.00
    )

    mostrar_resumen_activos()
    reconciliar_token("TOKEN-GBOND-1")
    mostrar_saldos_por_wallet("TOKEN-GBOND-1")
    mostrar_trazabilidad("TOKEN-GBOND-1", limite=10)
    print("\n[✔] Ejecución finalizada.")
