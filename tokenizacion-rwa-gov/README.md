# Prototipo de Tokenización de Activos (RWA) y Trazabilidad en SQLite

Proyecto desarrollado como parte de la **Academia de Blockchain para Gobiernos** (PNUD / MAP / ITLA).

## 🚀 Descripción
Simulador en Python y SQLite diseñado para la emisión, transferencia y auditoría inmutable de activos del mundo real (como bonos municipales tokenizados), asegurando trazabilidad y validación matemática de saldos entre carteras institucionales.

MI PROYECTO DE TOKENIZACION ECHO CON IA

Para entender cómo debe funcionar este sistema completo de tokenización de activos (como bonos municipales o RWA - Real World Assets), imagina que estamos construyendo la arquitectura lógica de un libro de contabilidad digital descentralizado, similar a cómo opera una red blockchain (como Algorand), pero simulado de forma transparente en una base de datos relacional local (SQLite).
El sistema simula el ciclo de vida completo de un activo financiero digital a través de 4 capas o tablas interconectadas:

1. El Activo Real o Subyacente (assets)
¿Qué es?: Representa el bien físico, proyecto u obligación legal del mundo real que le da valor al token (por ejemplo, el Bono Verde Municipal para financiar un parque solar).
Cómo funciona: Almacena la metadata legal y financiera (nombre, descripción, valoración total en dinero fiat y fecha de creación). Sin un activo real respaldándolo, el token sería solo un número sin sustento.

2. Los Participantes o Wallets (wallets)
¿Qué es?: Las cuentas o direcciones digitales que interactúan en la red (ej. el Ayuntamiento que emite el bono, fondos de inversión, ciudadanos o auditores).
Cómo funciona: Cada wallet tiene una dirección única (como una llave pública, ej. 0xWalletGov1) y un rol definido dentro del ecosistema de gobernanza pública (Emisor, Inversor, Auditor).

3. La Definición del Token (tokens)
¿Qué es?: El activo digital programable que representa una fracción o la totalidad del activo real.
Cómo funciona: Define el identificador único del token (TOKEN-GBOND-1), su símbolo abreviado (GBND1), el suministro total disponible y sus decimales (para permitir fraccionamientos exactos, como comprar centavos de un bono).

4. El Libro de Transacciones / Trazabilidad (transactions) — El núcleo
¿Qué es?: El equivalente al Ledger o cadena de bloques, donde se registra de forma secuencial, inmutable y auditable cada movimiento que ocurre en el sistema.
Cómo funciona cada transacción:

Emisión (ISSUE): Cuando el campo from_wallet es NULL (el sistema) y se acreditan tokens a la cuenta del emisor inicial (como viste en tu script con los 50 registros masivos).
Transferencia (TRANSFER): Cuando un participante mueve tokens a otro.
Validación de Saldos: Gracias a la lógica matemática que agregamos, el sistema consulta en tiempo real el balance (Total Recibido - Total Enviado) de la wallet emisora antes de autorizar la transacción. Si intentas transferir más de lo que posees, el sistema lo rechaza automáticamente (evitando sobregiros o doble gasto).

En Resumen: ¿Para qué sirve todo esto en la práctica?
Este prototipo demuestra cómo un gobierno o institución pública puede utilizar tecnología de registros distribuidos y bases de datos relacionales para:
Garantizar transparencia total: Cualquier ciudadano o auditor (como viste en la función audit_asset_trail) puede reconstruir la historia exacta de quién posee qué, cuándo se emitió y por cuáles manos pasó el título financiero.

Cumplir normativas: Asegura la trazabilidad y la integridad referencial (evitando que se inventen tokens de la nada o que existan transferencias fantasma).

<img width="1376" height="768" alt="Tokenizacion " src="https://github.com/user-attachments/assets/2d586ff2-75ea-4ea6-9f8c-0824c87a00d4" />




## 🛠️ Tecnologías utilizadas
* **Python 3.13**
* **SQLite** (Gestión relacional e integridad referencial)
* **PowerShell / VS Code**

## 📦 Estructura del Proyecto
* `tokenizacion_bonos.py`: Script principal que inicializa el esquema, carga los registros masivos y valida transferencias.
* `tokenized_assets.db`: Base de datos relacional local con los registros de prueba y auditoría.



