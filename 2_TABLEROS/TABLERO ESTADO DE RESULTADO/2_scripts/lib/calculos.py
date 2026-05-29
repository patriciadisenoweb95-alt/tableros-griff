# -*- coding: utf-8 -*-
"""
Calculos del Estado de Resultado: combina los datos de cada mes con los
impuestos y arma la estructura final que consume el dashboard.

Para cada mes y cada obra social calcula:
  resultado_antes_imp = ingresos_netos - costos_prestacionales - costos_fijos
  impuestos_os        = impuestos_totales_del_mes * participacion_en_ingresos
  resultado_neto      = resultado_antes_imp - impuestos_os
  margen              = resultado_neto / ingresos_netos
"""

from .utils import periodo_sort_key, periodo_label, periodo_corto


def construir_estado_resultado(er_por_periodo, impuestos_por_periodo):
    """Combina los datos de Estado de Resultado con los impuestos.
    Devuelve un dict {periodo: {...}} listo para el dashboard."""
    resultado = {}
    for periodo, data in er_por_periodo.items():
        imp = impuestos_por_periodo.get(periodo,
                                        {"iibb": 0.0, "iva": 0.0, "munic": 0.0})
        imp_total = imp["iibb"] + imp["iva"] + imp["munic"]

        obras = []
        for o in data["obras_sociales"]:
            tax = imp_total * o["income_share"]
            res_antes = (o["ingresos_netos"] - o["costos_prestacionales"]
                         - o["costos_fijos"])
            res_neto = res_antes - tax
            margen = res_neto / o["ingresos_netos"] if o["ingresos_netos"] else 0
            obras.append({
                **o,
                "impuestos": tax,
                "resultado_antes": res_antes,
                "resultado_neto": res_neto,
                "margen": margen,
            })

        t = data["totals"]
        res_antes_total = (t["ingresos_netos"] - t["costos_prestacionales"]
                           - t["costos_fijos"])
        res_neto_total = res_antes_total - imp_total
        totals = {
            **t,
            "iibb": imp["iibb"], "iva": imp["iva"], "munic": imp["munic"],
            "impuestos": imp_total,
            "resultado_antes": res_antes_total,
            "resultado_neto": res_neto_total,
            "margen": res_neto_total / t["ingresos_netos"]
                      if t["ingresos_netos"] else 0,
        }

        resultado[periodo] = {
            "periodo": periodo,
            "month": data["month"],
            "month_short": periodo_corto(periodo),
            "archivo": data["archivo"],
            "totals": totals,
            "obras_sociales": obras,
            "ospif_breakdown": data["ospif_breakdown"],
            "impuestos_detalle": imp,
        }
    return resultado


def periodos_ordenados(*dicts):
    """Devuelve la lista de periodos presentes en cualquiera de los dicts,
    ordenados cronologicamente."""
    todos = set()
    for d in dicts:
        todos.update(d.keys())
    return sorted(todos, key=periodo_sort_key)


def construir_payload(estado_resultado, costos_prest, periodos):
    """Arma el payload final (dict) que se inyecta en el dashboard.html."""
    return {
        "periodos": periodos,
        "periodos_label": {p: periodo_label(p) for p in periodos},
        "periodos_short": {p: periodo_corto(p) for p in periodos},
        "estado_resultado": estado_resultado,
        "costos_prestacionales": costos_prest,
    }
