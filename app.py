
import streamlit as st
import time
from deriv_bot import DerivBot

st.title("🤖 Robô Famped - Estratégia Over 3 baseada em ticks")

token = st.text_input("🎯 Insira seu token da Deriv", type="password")
symbol = st.selectbox("Símbolo", ["R_100", "R_10"])
stake = st.number_input("Stake inicial", min_value=0.35, step=0.01, value=0.35)
use_martingale = st.checkbox("Usar Martingale?", value=True)
factor = st.number_input("Fator de Martingale", min_value=1.0, step=0.1, value=2.0)
max_loss = st.number_input("Limite de perda", min_value=0.0, step=0.5, value=10.0)
target_profit = st.number_input("Meta de lucro", min_value=0.0, step=0.5, value=10.0)
percentual_minimo = st.selectbox("Porcentagem mínima de dígitos abaixo de 4 para entrada", [40, 65, 70, 80])
analisar_ultimos = st.selectbox("Quantidade de últimos ticks para análise", [33, 50, 200])

start = st.button("🚀 Iniciar Robô")

if start and token:
    stframe = st.empty()
    st.session_state.stframe = stframe
    stframe.text("🔄 Iniciando robô...")
    bot = DerivBot(token, symbol, stake, use_martingale, factor, target_profit, max_loss, analisar_ultimos, percentual_minimo)
    import threading
    threading.Thread(target=bot.run_interface, daemon=True).start()
