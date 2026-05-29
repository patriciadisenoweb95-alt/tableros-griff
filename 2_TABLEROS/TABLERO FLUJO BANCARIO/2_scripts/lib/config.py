# -*- coding: utf-8 -*-
"""
Configuracion central del tablero de flujo bancario.
"""

# Cuentas bancarias (id interno, nombre, banco, saldo minimo a mantener)
CUENTAS = [
    {"id": "principal", "nombre": "Cuenta principal", "banco": "Galicia",
     "min_balance": 0},
]

# Buffer de seguridad sobre saldo minimo (ARS)
BUFFER_SEGURIDAD = 0

# TNAs de referencia para sugerir inversiones
TNA_FCI = 30.0          # FCI Money Market
TNA_CAUCION = 40.0      # Caucion bursatil

# Estados que afectan el cash flow proyectado (todavia no debitados)
ACTIVE_STATUSES = ["pendiente", "en_proceso_deposito"]

# Mapeo de estados de Galicia al modelo interno.
# Si Galicia genera una variante nueva, ver tambien `map_galicia_status` en
# cheques.py que aplica un fallback por palabras clave.
GALICIA_STATUS_MAP = {
    # --- Pendientes (todavia no depositados) ---
    "Aceptado": "pendiente",
    "Emitido": "pendiente",

    # --- En proceso de deposito (beneficiario lo deposito, banco procesando) ---
    "Depósito en proceso": "en_proceso_deposito",
    "Deposito en proceso": "en_proceso_deposito",
    "En depósito": "en_proceso_deposito",
    "En deposito": "en_proceso_deposito",
    "Depositado": "en_proceso_deposito",
    "En proceso": "en_proceso_deposito",
    "En proceso de depósito": "en_proceso_deposito",
    "En proceso de deposito": "en_proceso_deposito",
    "En cámara": "en_proceso_deposito",
    "En camara": "en_proceso_deposito",
    "En tránsito": "en_proceso_deposito",
    "En transito": "en_proceso_deposito",

    # --- Acreditado (ya se debito de la cuenta) ---
    "Pagado": "acreditado",
    "Acreditado": "acreditado",

    # --- Anulado ---
    "Anulado": "anulado",

    # --- Rechazado ---
    "Repudiado": "rechazado",
    "Rechazado": "rechazado",
    "Rechazado con acuerdo": "rechazado",
    "Rechazado sin acuerdo": "rechazado",
    "Rechazado con aviso": "rechazado",
    "Rechazado sin fondos": "rechazado",
    "Devuelto": "rechazado",
}

# Etiquetas para mostrar en el HTML
STATUS_LABELS = {
    "pendiente": "Pendiente",
    "en_proceso_deposito": "En proceso depósito",
    "acreditado": "Acreditado",
    "rechazado": "Rechazado",
    "anulado": "Anulado",
}

# Colores de marca Griff Salud
BRAND = {
    "primary": "#1a1ac7",
    "primary_strong": "#11118a",
    "primary_soft": "#e6e7fa",
    "accent": "#22c4ec",
    "accent_strong": "#0e9bc0",
    "accent_soft": "#def5fc",
    "success": "#0a8a5e",
    "warn": "#b25500",
    "danger": "#c0392b",
}
