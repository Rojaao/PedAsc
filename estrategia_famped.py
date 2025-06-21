def analisar_ticks_famped(ticks, percentual_minimo):
    """
    Recebe lista `ticks` (inteiros 0–9) e percentual mínimo (ex: 65).
    Retorna dict com:
      - 'entrada': "DIGITOVER" ou "ESPERAR"
      - 'estrategia': descrição ou percentual calculado.
    """
    total = len(ticks)
    if total == 0:
        return {"entrada": "ESPERAR", "estrategia": "sem ticks"}
    abaixo_de_4 = [d for d in ticks if d < 4]
    perc = round((len(abaixo_de_4) / total) * 100, 2)
    if perc >= percentual_minimo:
        return {"entrada": "DIGITOVER", "estrategia": f"{perc}% < 4 (>= {percentual_minimo}%)"}
    else:
        return {"entrada": "ESPERAR", "estrategia": f"{perc}% < 4 (< {percentual_minimo}%)"}
