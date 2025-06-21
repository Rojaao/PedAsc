
def analisar_ticks(ticks, percentual_minimo):
    if len(ticks) == 0:
        return False
    digitos_abaixo_de_4 = sum(1 for tick in ticks if tick < 4)
    percentual = (digitos_abaixo_de_4 / len(ticks)) * 100
    return percentual >= percentual_minimo  # Agora usa >= em vez de >
