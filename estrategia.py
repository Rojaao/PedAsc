def analisar_ticks_famped(ticks, percentual_minimo):
    if not ticks or len(ticks) == 0:
        return {"entrada": "ESPERAR", "estrategia": "famped"}

    abaixo_de_4 = sum(1 for tick in ticks if tick < 4)
    percentual = (abaixo_de_4 / len(ticks)) * 100

    if percentual >= percentual_minimo:
        return {"entrada": "OVER3", "estrategia": "famped"}
    else:
        return {"entrada": "ESPERAR", "estrategia": "famped"}