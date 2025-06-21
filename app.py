import streamlit as st
import time
import threading
from deriv_bot import DerivBot

st.set_page_config(page_title="Robô Famped", layout="centered")
st.title("🤖 Robô Famped - Estratégia Over 3 baseada em ticks")

# Inicializa elementos de interface e sessão
if "log_status" not in st.session_state:
    st.session_state.log_status = "🔄 Iniciando robô..."

if "stframe" not in st.session_state:
    st.session_state.stframe = st.empty()

# Campos de entrada
token = st.text_input("🔑 Token da Deriv", type="password")
symbol = st.selectbox("Símbolo", ["R_100", "R_10"])
stake = st.number_input("💰 Stake Inicial", value=0.35, step=0.01)
use_martingale = st.checkbox("🎯 Ativar Martingale")
factor = st.number_input("📈 Fator Martingale", value=2.0, step=0.1)
target_profit = st.number_input("🏆 Meta de Lucro", value=5.0)
stop_loss = st.number_input("🛑 Limite de Perda", value=5.0)
selected_ticks = st.selectbox("📊 Analisar últimos Ticks", [33, 50, 100, 200])
percento = st.selectbox("📌 Porcentagem mínima de acerto para entrar", [40, 65, 70, 80])

# Atualização de status contínua na interface
def atualizar_status():
    while True:
        try:
            st.session_state.stframe.text(st.session_state.log_status)
            time.sleep(2)
        except:
            break

if st.button("▶️ Iniciar Robô"):
    st.session_state.stframe.text("🔄 Iniciando robô...")

    bot = DerivBot(
        token=token,
        symbol=symbol,
        stake=stake,
        use_martingale=use_martingale,
        factor=factor,
        target_profit=target_profit,
        stop_loss=stop_loss,
        selected_ticks=selected_ticks,
        percento_entrada=percento
    )

    threading.Thread(target=bot.run_interface, daemon=True).start()
    threading.Thread(target=atualizar_status, daemon=True).start()