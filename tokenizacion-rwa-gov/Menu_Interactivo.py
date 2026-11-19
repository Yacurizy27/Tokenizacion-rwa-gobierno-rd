import csv
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from tokenizacion_bonos import (  # noqa: E402
    consultar_esquema,
    exportar_reporte_csv,
    get_connection,
    init_db,
    issue_tokens,
    reconciliar_token,
    seed_mass_data,
    seed_simulation_data,
    transfer_tokens,
)


def importar_wallets_csv(ruta_csv):
    """
    Importa carteras desde un CSV con columnas:
    wallet_address, owner_name, role
    """
    archivo = Path(ruta_csv)
    if not archivo.is_absolute():
        archivo = BASE_DIR / archivo

    if not archivo.exists():
        print(f"[✘] No se encontró el archivo CSV: {archivo}")
        return

    init_db()
    insertadas = 0
    omitidas = 0

    with open(archivo, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"wallet_address", "owner_name", "role"}
        if not reader.fieldnames or not required.issubset({c.strip() for c in reader.fieldnames}):
            print("[✘] Encabezados inválidos en CSV de wallets. Se requieren: wallet_address, owner_name, role")
            return

        with get_connection() as conn:
            cursor = conn.cursor()
            for fila in reader:
                wallet = (fila.get("wallet_address") or "").strip()
                owner = (fila.get("owner_name") or "").strip()
                role = (fila.get("role") or "").strip()
                if not wallet or not owner or not role:
                    omitidas += 1
                    continue
                cursor.execute(
                    "INSERT OR IGNORE INTO wallets (wallet_address, owner_name, role) VALUES (?, ?, ?)",
                    (wallet, owner, role),
                )
                if cursor.rowcount > 0:
                    insertadas += 1
                else:
                    omitidas += 1
            conn.commit()

    print(f"[✔] Importación de wallets finalizada -> Nuevas: {insertadas} | Omitidas/Duplicadas: {omitidas}")


def importar_activos_y_tokens_csv(ruta_csv):
    """
    Importa activos y tokens desde un CSV con columnas:
    asset_id, name, description, total_valuation, created_at, token_id, symbol, total_supply, decimals
    (created_at y decimals son opcionales).
    """
    archivo = Path(ruta_csv)
    if not archivo.is_absolute():
        archivo = BASE_DIR / archivo

    if not archivo.exists():
        print(f"[✘] No se encontró el archivo CSV: {archivo}")
        return

    init_db()
    activos_nuevos = 0
    tokens_nuevos = 0
    errores = 0

    with open(archivo, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"asset_id", "name", "total_valuation", "token_id", "symbol", "total_supply"}
        if not reader.fieldnames or not required.issubset({c.strip() for c in reader.fieldnames}):
            print(
                "[✘] Encabezados inválidos en CSV de activos/tokens. Se requieren al menos: "
                "asset_id, name, total_valuation, token_id, symbol, total_supply"
            )
            return

        with get_connection() as conn:
            cursor = conn.cursor()
            for idx, fila in enumerate(reader, start=2):
                try:
                    asset_id = (fila.get("asset_id") or "").strip()
                    name = (fila.get("name") or "").strip()
                    description = (fila.get("description") or "").strip()
                    total_valuation = float(fila.get("total_valuation"))
                    created_at = (fila.get("created_at") or "").strip() or "2026-11-19T00:00:00"

                    token_id = (fila.get("token_id") or "").strip()
                    symbol = (fila.get("symbol") or "").strip()
                    total_supply = float(fila.get("total_supply"))
                    decimals_raw = (fila.get("decimals") or "2").strip()
                    decimals = int(decimals_raw) if decimals_raw else 2

                    if not asset_id or not name or not token_id or not symbol:
                        raise ValueError("Campos obligatorios vacíos.")

                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO assets (asset_id, name, description, total_valuation, created_at)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (asset_id, name, description, total_valuation, created_at),
                    )
                    if cursor.rowcount > 0:
                        activos_nuevos += 1

                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO tokens (token_id, asset_id, symbol, total_supply, decimals)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (token_id, asset_id, symbol, total_supply, decimals),
                    )
                    if cursor.rowcount > 0:
                        tokens_nuevos += 1

                except Exception as e:
                    errores += 1
                    print(f"[⚠] Fila {idx} omitida por error: {e}")

            conn.commit()

    print(
        f"[✔] Importación finalizada -> Activos nuevos: {activos_nuevos} | "
        f"Tokens nuevos: {tokens_nuevos} | Errores: {errores}"
    )


def importar_transacciones_csv(ruta_csv):
    """
    Importa operaciones del ledger desde un CSV con columnas:
    tx_hash, token_id, from_wallet, to_wallet, amount, tx_type
    - Si tx_type == 'ISSUE': llama a issue_tokens(...) validando el supply máximo.
    - Si tx_type == 'TRANSFER': llama a transfer_tokens(...) validando saldo disponible.
    """
    archivo = Path(ruta_csv)
    if not archivo.is_absolute():
        archivo = BASE_DIR / archivo

    if not archivo.exists():
        print(f"[✘] No se encontró el archivo CSV: {archivo}")
        return

    init_db()
    procesadas = 0
    errores = 0

    with open(archivo, mode="r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"tx_hash", "token_id", "to_wallet", "amount", "tx_type"}
        if not reader.fieldnames or not required.issubset({c.strip() for c in reader.fieldnames}):
            print(
                "[✘] Encabezados inválidos en CSV de transacciones. Se requieren al menos: "
                "tx_hash, token_id, to_wallet, amount, tx_type (y from_wallet para TRANSFER)"
            )
            return

        for idx, fila in enumerate(reader, start=2):
            try:
                tx_hash = (fila.get("tx_hash") or "").strip()
                token_id = (fila.get("token_id") or "").strip()
                from_wallet = (fila.get("from_wallet") or "").strip() or None
                to_wallet = (fila.get("to_wallet") or "").strip()
                tx_type = (fila.get("tx_type") or "").strip().upper()
                amount = float(fila.get("amount"))

                if not tx_hash or not token_id or not to_wallet or not tx_type:
                    raise ValueError("Faltan campos obligatorios en la transacción.")

                if tx_type == "ISSUE":
                    issue_tokens(tx_hash, token_id, to_wallet, amount)
                    procesadas += 1
                elif tx_type == "TRANSFER":
                    if not from_wallet:
                        raise ValueError("Una transacción TRANSFER requiere 'from_wallet'.")
                    transfer_tokens(tx_hash, token_id, from_wallet, to_wallet, amount)
                    procesadas += 1
                else:
                    raise ValueError(f"Tipo de transacción no soportado: '{tx_type}' (usa ISSUE o TRANSFER).")

            except Exception as e:
                errores += 1
                print(f"[⚠] Fila {idx} omitida por error: {e}")

    print(f"[✔] Lote de transacciones procesado -> Intentos válidos: {procesadas} | Errores de formato: {errores}")


def menu_importacion():
    while True:
        print("\n" + "-" * 65)
        print("SUBMENÚ DE IMPORTACIÓN DESDE CSV")
        print("-" * 65)
        print("1. Importar wallets (wallet_address, owner_name, role)")
        print("2. Importar activos y tokens (asset_id, name, total_valuation, token_id, symbol, total_supply)")
        print("3. Importar transacciones ISSUE / TRANSFER (tx_hash, token_id, from_wallet, to_wallet, amount, tx_type)")
        print("0. Volver al menú principal")

        sub = input("\nElige una opción de importación: ").strip()
        if sub == "1":
            ruta = input("Ruta del CSV de wallets (ej. importaciones/wallets.csv): ").strip()
            if ruta:
                importar_wallets_csv(ruta)
        elif sub == "2":
            ruta = input("Ruta del CSV de activos/tokens (ej. importaciones/activos_tokens.csv): ").strip()
            if ruta:
                importar_activos_y_tokens_csv(ruta)
        elif sub == "3":
            ruta = input("Ruta del CSV de transacciones (ej. importaciones/txs.csv): ").strip()
            if ruta:
                importar_transacciones_csv(ruta)
        elif sub == "0":
            break
        else:
            print("[✘] Opción no válida.")


def menu_interactivo():
    init_db()
    while True:
        print("\n" + "=" * 65)
        print("SIMULADOR RWA / BONOS MUNICIPALES — MENÚ INTERACTIVO")
        print("=" * 65)
        print("1. Consultar resumen de activos y tokens")
        print("2. Consultar estado de suministro y reconciliación")
        print("3. Consultar posiciones / saldos por wallet")
        print("4. Consultar historial de movimientos (ledger)")
        print("5. Realizar transferencia de tokens")
        print("6. Reconciliar un token específico")
        print("7. Exportar reporte a CSV")
        print("8. Importar datos desde CSV")
        print("9. Cargar datos base / masivos de prueba")
        print("0. Salir")

        opcion = input("\nSelecciona una opción: ").strip()

        if opcion == "1":
            lim = input("Límite de filas (Enter para 20): ").strip()
            consultar_esquema(vista="activos", limite=int(lim) if lim.isdigit() else 20)

        elif opcion == "2":
            tok = input("Filtrar por token_id (Enter para todos): ").strip() or None
            lim = input("Límite de filas (Enter para 20): ").strip()
            consultar_esquema(vista="suministro", token_id=tok, limite=int(lim) if lim.isdigit() else 20)

        elif opcion == "3":
            tok = input("Filtrar por token_id (Enter para todos): ").strip() or None
            wal = input("Filtrar por wallet_address (Enter para todas): ").strip() or None
            lim = input("Límite de filas (Enter para 20): ").strip()
            consultar_esquema(vista="posiciones", token_id=tok, wallet_address=wal, limite=int(lim) if lim.isdigit() else 20)

        elif opcion == "4":
            tok = input("Filtrar por token_id (Enter para todos): ").strip() or None
            wal = input("Filtrar por wallet_address (Enter para todas): ").strip() or None
            tipo = input("Filtrar por tipo ISSUE/TRANSFER (Enter para todos): ").strip() or None
            lim = input("Límite de filas (Enter para 20): ").strip()
            consultar_esquema(
                vista="movimientos",
                token_id=tok,
                wallet_address=wal,
                tx_type=tipo,
                limite=int(lim) if lim.isdigit() else 20,
            )

        elif opcion == "5":
            tx_hash = input("Hash único de transacción: ").strip()
            token_id = input("Token ID: ").strip()
            from_wallet = input("Wallet origen: ").strip()
            to_wallet = input("Wallet destino: ").strip()
            monto_str = input("Monto a transferir: ").strip()
            try:
                monto = float(monto_str)
                transfer_tokens(tx_hash, token_id, from_wallet, to_wallet, monto)
            except ValueError:
                print("[✘] Monto inválido.")

        elif opcion == "6":
            token_id = input("Token ID a reconciliar: ").strip()
            if token_id:
                reconciliar_token(token_id)

        elif opcion == "7":
            vista = input("Vista a exportar (activos / suministro / posiciones / movimientos): ").strip().lower() or "suministro"
            tok = input("Filtrar por token_id (Enter para todos): ").strip() or None
            wal = input("Filtrar por wallet_address (Enter para todas): ").strip() or None
            exportar_reporte_csv(vista=vista, token_id=tok, wallet_address=wal)

        elif opcion == "8":
            menu_importacion()

        elif opcion == "9":
            seed_simulation_data()
            seed_mass_data()

        elif opcion == "0":
            print("[👋] Saliendo del menú interactivo.")
            break

        else:
            print("[✘] Opción no válida. Intenta nuevamente.")


if __name__ == "__main__":
    menu_interactivo()
