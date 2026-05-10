"""Contexto institucional de Banxico para anclar a los agentes.

Se inyecta como SystemMessage en cada turno de un debate (ver `_agent_turn`
en `debate.py`). Contiene un resumen ejecutivo de las decisiones recientes
de la Junta de Gobierno real y la postura conocida de cada miembro.

Cuando se publique una nueva minuta:
1. Agregar el archivo .md correspondiente en `backend/app/data/banxico_history/`.
2. Actualizar `INSTITUTIONAL_CONTEXT` con los datos nuevos (decisión, fecha,
   votación, INPC más reciente).
3. Commit + redeploy.
"""
from __future__ import annotations


INSTITUTIONAL_CONTEXT = """\
=== Contexto institucional Banxico (referencia obligada en tu razonamiento) ===

ÚLTIMA DECISIÓN — 7 de mayo de 2026
- Recorte de 25 pb a 6.50% (mínimo desde mar-2022).
- Cierre formal del ciclo de recortes iniciado en mar-2024 (15 recortes,
  -450 pb desde el máximo histórico de 11.25%).
- Votación: 3-2.
  - A favor: Victoria Rodríguez Ceja (Gobernadora), Gabriel Cuadra García,
    Omar Mejía Castelazo.
  - En contra (mantener): Galia Borja Gómez, Jonathan Heath.

DECISIÓN PREVIA — 26 de marzo de 2026 (Minuta 123)
- Recorte de 25 pb de 7.00% a 6.75%.
- Misma votación 3-2 (mismo split de miembros).

INDICADORES CLAVE MÁS RECIENTES
- INPC general abril-2026: 4.45% YoY (subyacente 4.26%). Aún arriba del
  objetivo de 3%.
- PIB 1T-2026: -0.8% (mayor caída desde fin-2024). Brecha del producto
  negativa, holgura ampliándose.
- Pronóstico Banxico: convergencia al 3% en 2T-2027.
- Balance de riesgos para la inflación: sesgo al alza.

POSTURAS CONOCIDAS DE LOS MIEMBROS REALES
- Heath: 10 votaciones consecutivas a favor de mantener desde el inicio del
  ciclo. Argumenta persistencia de la subyacente, debilitamiento de los
  determinantes tradicionales y necesidad de no comprometer la meta.
- Borja Gómez: dos votaciones consecutivas a mantener. Argumenta tasa real
  ex-ante ya en rango neutral; prefiere evaluar el alcance del choque de
  Medio Oriente antes de recortar más.
- Rodríguez Ceja, Cuadra García, Mejía Castelazo: priorizan la debilidad
  económica y la ausencia de presiones de demanda; consideran que el grado
  de restricción acumulado da margen para flexibilizar.

CHOQUES Y RIESGOS ACTIVOS
- Conflicto Medio Oriente desde finales de feb-2026: petróleo Brent llegó a
  USD 100+/bbl, fertilizantes +30%, gas natural europeo +85%.
- Reserva Federal: tasa de fondos federales en 3.50–3.75% (rango), tono más
  cauteloso, mediana de pronóstico inflación 2026 USA subió a 2.7%.
- Política mexicana de precio máximo de gasolina ($24/litro) y acceso a gas
  natural de USA mitigan el traspaso del choque externo.

HERRAMIENTA PARA PROFUNDIZAR
Si necesitas citar literalmente decisiones, votos, argumentos o pasajes de
las minutas oficiales, invoca `consult_banxico_history(query)`. Devuelve
los párrafos relevantes con cita de la fuente y fecha.
"""


def get_institutional_context() -> str:
    """Devuelve el bloque de contexto institucional Banxico para inyectar
    como SystemMessage en cada turno de un debate."""
    return INSTITUTIONAL_CONTEXT
