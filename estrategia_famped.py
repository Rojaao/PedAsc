def analisar_ticks_famped(ticks, percentual_minimo):
    total = len(ticks)
    if total == 0:
        return {"entrada": "ESPERAR", "estrategia": "sem ticks"}
    abaixo_de_4 = [d for d in ticks if d < 4]
    perc = round((len(abaixo_de_4) / total) * 100, 2)
    if perc >= percentual_minimo:
        return {"entrada": "DIGITOVER", "estrategia": f"{perc}% < 4 (>= {percentual_minimo}%)"}
    else:
        return {"entrada": "ESPERAR", "estrategia": f"{perc}% < 4 (< {percentual_minimo}%)"}