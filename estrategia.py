
def analisar_ticks(ticks, percentual_minimo):
    if len(ticks) == 0:
        return {"entrada": "ESPERAR", "estrategia": "Famped"}

    qtd_abaixo_4 = sum(1 for d in ticks if d < 4)
    percentual = (qtd_abaixo_4 / len(ticks)) * 100

    if percentual >= percentual_minimo:
        return {"entrada": "OVER", "estrategia": f"Famped {percentual_minimo}%"}
    else:
        return {"entrada": "ESPERAR", "estrategia": f"Famped {percentual_minimo}%"}
