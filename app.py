
import streamlit as st
from deriv_bot import DerivBot
import time
import websocket
import json

st.set_page_config(page_title="Robô Famped Deriv", layout="centered")
st.title("🤖 Robô Deriv - Estratégia FAMPED")

token = st.text_input("🔑 Token da API (Demo ou Real)", type="password")
symbol = st.selectbox("📈 Ativo para operar", ["R_100", "R_10"])
stake = st.number_input("💰 Stake inicial (ex: 0.35)", min_value=0.01, value=0.35)
use_martingale = st.checkbox("🔁 Usar Martingale", value=True)
factor = st.number_input("📈 Fator do Martingale", min_value=1.0, value=2.0)
stop_gain = st.number_input("🎯 Meta de lucro (USD)", min_value=1.0, value=10.0)
stop_loss = st.number_input("🛑 Limite de perda (USD)", min_value=1.0, value=10.0)
max_losses = st.number_input("❌ Máx. perdas consecutivas", min_value=1, value=3)

stframe = st.empty()
lucro_display = st.empty()
alerta_final = st.empty()

if st.button("🚀 Iniciar Robô"):
    st.success("Robô iniciado com sucesso!")

    bot = DerivBot(token, symbol, stake, use_martingale, factor, stop_gain, stop_loss, max_losses)

    try:
        ws_ticks = websocket.WebSocket()
        ws_ticks.connect("wss://ws.binaryws.com/websockets/v3?app_id=1089")
        ws_ticks.send(json.dumps({"authorize": token}))
        ws_ticks.recv()
        ws_ticks.send(json.dumps({"ticks": symbol}))
    except Exception:
        stframe.text("❌ Erro ao conectar no WebSocket de ticks.")
        st.stop()

    try:
        ws_op = websocket.WebSocket()
        ws_op.connect("wss://ws.binaryws.com/websockets/v3?app_id=1089")
        ws_op.send(json.dumps({"authorize": token}))
        auth_response = json.loads(ws_op.recv())
        if 'error' in auth_response:
            stframe.text("❌ Erro ao autorizar token.")
            st.stop()
    except Exception:
        stframe.text("❌ Erro ao conectar no WebSocket de operações.")
        st.stop()

    stframe.text(f"✅ Conectado | Conta: {'Real' if auth_response['authorize']['is_virtual']==0 else 'Demo'}")

    from estrategia import analisar_ticks_famped

    saldo = 0
    consecutivas = 0
    ganho_total = 0
    stake_inicial = stake
    stake_atual = stake
    martingale_nivel = 0
    ticks = []

    while True:
        try:
            msg = json.loads(ws_ticks.recv())
            if msg.get("msg_type") == "tick":
                ticks.append(int(str(msg["tick"]["quote"])[-1]))
                if len(ticks) > 100:
                    ticks = ticks[-100:]
        except:
            time.sleep(1)
            continue

        if len(ticks) < 33:
            stframe.text("⏳ Aguardando ticks suficientes para análise...")
            time.sleep(1)
            continue

        analise = analisar_ticks_famped(ticks[-33:])
        entrada = analise['entrada']
        estrategia = analise['estrategia']

        if entrada == "ESPERAR":
            stframe.text("⏸ Aguardando oportunidade...")
            time.sleep(2)
            continue

        barrier = entrada.split()[-1]

        contrato = {
            "buy": 1,
            "price": round(stake_atual, 2),
            "parameters": {
                "amount": round(stake_atual, 2),
                "basis": "stake",
                "contract_type": "DIGITOVER",
                "currency": "USD",
                "duration": 1,
                "duration_unit": "t",
                "symbol": symbol,
                "barrier": barrier
            },
            "req_id": 1
        }

        try:
            ws_op.send(json.dumps(contrato))
            result = json.loads(ws_op.recv())
        except:
            stframe.text("❌ Erro ao enviar operação.")
            time.sleep(2)
            continue

        if result.get("msg_type") != "buy" or "buy" not in result:
            stframe.text("❌ Erro: resposta inesperada da Deriv (sem campo 'buy')")
            time.sleep(3)
            continue

        buy_id = result["buy"]["contract_id"]
        resultado = "Desconhecido"

        for _ in range(20):
            time.sleep(1)
            ws_op.send(json.dumps({
                "proposal_open_contract": 1,
                "contract_id": buy_id
            }))
            res = json.loads(ws_op.recv())
            if res.get("msg_type") == "proposal_open_contract":
                contrato_info = res["proposal_open_contract"]
                if contrato_info.get("is_sold"):
                    lucro = contrato_info.get("profit", 0)
                    resultado = "WIN" if lucro > 0 else "LOSS"
                    break

        if resultado == "WIN":
            ganho_total += stake_atual
            consecutivas = 0
            stake_atual = stake_inicial
            martingale_nivel = 0
            stframe.text(f"✅ WIN | +${round(lucro, 2)} | Stake: {round(stake_atual, 2)}")
        else:
            ganho_total -= stake_atual
            consecutivas += 1
            if use_martingale:
                martingale_nivel += 1
                stake_atual = round(stake_inicial * (factor ** martingale_nivel), 2)
                stframe.text(f"❌ LOSS | -${round(stake_atual, 2)} | Próxima stake: {stake_atual}")
            else:
                stframe.text(f"❌ LOSS | -${round(stake_atual, 2)}")

        lucro_display.markdown(
            f"### {'🟢' if ganho_total > 0 else '🔴' if ganho_total < 0 else '⚪'} Lucro acumulado: **${ganho_total:.2f}**"
        )

        if ganho_total >= stop_gain:
            alerta_final.success("🔥 Tropa do AMASSA OTÁRIO! Meta de lucro atingida!")
            break
        if ganho_total <= -stop_loss or consecutivas >= max_losses:
            alerta_final.error("💀 Perdeu doidão! Stop Loss atingido.")
            break

        ticks.clear()
        time.sleep(5)
