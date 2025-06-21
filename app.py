import streamlit as st
import time
import threading
from deriv_bot import DerivBot

st.set_page_config(page_title="Robô Famped", layout="centered")
st.title("🤖 Robô Famped - Estratégia Over 3 baseada em ticks")

token = st.text_input("🎯 Token da Deriv")
symbol = st.selectbox("Símbolo", ["R_100", "R_10"])
stake = st.number_input("Stake Inicial", min_value=0.35, step=0.01, value=0.35)
factor = st.number_input("Fator de Martingale", min_value=1.0, step=0.1, value=2.0)
max_loss = st.number_input("Limite de perda (stop loss)", min_value=1.0, value=10.0)
target_profit = st.number_input("Meta de lucro (take profit)", min_value=1.0, value=10.0)
percentual_minimo = st.selectbox("Percentual mínimo de dígitos abaixo de 4", [40, 65, 70, 80])
analisar_ultimos = st.selectbox("Quantidade de ticks para analisar", [33, 50, 100, 200])

if st.button("🚀 Iniciar Robô"):
    if "stframe" not in st.session_state:
        st.session_state.stframe = st.empty()
    if "log_area" not in st.session_state:
        st.session_state.log_area = st.empty()
    if "log_status" not in st.session_state:
        st.session_state.log_status = []

    st.session_state.stframe.info("🔄 Iniciando conexão com a corretora...")

    bot = DerivBot(
        token=token,
        symbol=symbol,
        stake=stake,
        use_martingale=True,
        factor=factor,
        target_profit=target_profit,
        stop_loss=max_loss,
        selected_ticks=analisar_ultimos,
        percento_entrada=percentual_minimo
    )

    def atualizar_status():
        while True:
            lucro = bot.lucro_acumulado
            if lucro >= 0:
                st.session_state.stframe.success(f"💰 Lucro acumulado: +${lucro:.2f}")
            else:
                st.session_state.stframe.error(f"📉 Lucro acumulado: -${abs(lucro):.2f}")
            st.session_state.log_area.text("\n".join(st.session_state.get("log_status", [])))
            time.sleep(2)

    threading.Thread(target=bot.run_interface, daemon=True).start()
    threading.Thread(target=atualizar_status, daemon=True).start()