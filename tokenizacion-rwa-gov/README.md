# Prototipo de Tokenización de Activos (RWA) y Trazabilidad en SQLite

Proyecto desarrollado como parte de la **Academia de Blockchain para Gobiernos** (PNUD / MAP / ITLA).

## 🚀 Descripción
Simulador en Python y SQLite diseñado para la emisión, transferencia y auditoría inmutable de activos del mundo real (como bonos municipales tokenizados), asegurando trazabilidad y validación matemática de saldos entre carteras institucionales.

## 🛠️ Tecnologías utilizadas
* **Python 3.13**
* **SQLite** (Gestión relacional e integridad referencial)
* **PowerShell / VS Code**

## 📦 Estructura del Proyecto
* `tokenizacion_bonos.py`: Script principal que inicializa el esquema, carga los registros masivos y valida transferencias.
* `tokenized_assets.db`: Base de datos relacional local con los registros de prueba y auditoría.