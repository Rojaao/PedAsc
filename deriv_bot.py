import websocket
import json
import streamlit as st
import threading
import time
from estrategia_famped import analisar_ticks_famped

class DerivBot:
    def __init__(self, token, symbol, stake, use_martingale, factor, target_profit, stop_loss, selected_ticks, percento_entrada):
        self.token = token
        self.symbol = symbol
        self.stake = stake
        self.use_martingale = use_martingale
        self.factor = factor
        self.target_profit = target_profit
        self.stop_loss = stop_loss
        self.selected_ticks = selected_ticks
        self.percento_entrada = percento_entrada
        self.logs = []
        self.lucro_acumulado = 0
        self.stake_atual = stake

    def run_interface(self):
        ws = websocket.create_connection("wss://ws.binaryws.com/websockets/v3?app_id=1089")
        ws.send(json.dumps({"authorize": self.token}))
        auth_response = json.loads(ws.recv())

        if 'error' in auth_response:
            st.session_state['log_status'] = '❌ Token inválido'
            return

        st.session_state['log_status'] = f"✅ Conectado | Conta: {'Real' if auth_response['authorize']['is_virtual'] == 0 else 'Demo'}"

        st.session_state['log_status'] += f"\n🔄 Analisando últimos {self.selected_ticks} ticks com {self.percento_entrada}%"
        threading.Thread(target=self.receber_ticks, daemon=True).start()

    def receber_ticks(self):
        try:
            ws = websocket.create_connection("wss://ws.binaryws.com/websockets/v3?app_id=1089")
            ws.send(json.dumps({"ticks": self.symbol}))
            ticks = []
            while True:
                tick_msg = json.loads(ws.recv())
                if 'tick' in tick_msg:
                    ticks.append(int(str(tick_msg["tick"]["quote"])[-1]))
                    if len(ticks) > self.selected_ticks:
                        ticks.pop(0)

                    analise = analisar_ticks_famped(ticks, self.percento_entrada)
                    if analise["entrada"] == "OVER3":
                        self.fazer_operacao()
                        ticks.clear()
        except Exception as e:
            st.session_state['log_status'] = f"❌ Erro nos ticks: {str(e)}"

    def fazer_operacao(self):
        try:
            ws = websocket.create_connection("wss://ws.binaryws.com/websockets/v3?app_id=1089")
            ws.send(json.dumps({"authorize": self.token}))
            ws.recv()

            proposal = {
                "proposal": 1,
                "amount": self.stake_atual,
                "basis": "stake",
                "contract_type": "DIGITOVER",
                "currency": "USD",
                "duration": 1,
                "duration_unit": "t",
                "symbol": self.symbol,
                "barrier": 3
            }

            ws.send(json.dumps(proposal))
            proposta = json.loads(ws.recv())

            ws.send(json.dumps({
                "buy": proposta["proposal"]["id"],
                "price": self.stake_atual
            }))
            resultado = json.loads(ws.recv())

            if "buy" not in resultado:
                self.logs.append("❌ Erro: resposta inesperada da Deriv (sem campo 'buy')")
                return

            contrato_id = resultado["buy"]["contract_id"]
            self.logs.append(f"🟡 Entrada enviada | Valor: {self.stake_atual}")

            while True:
                ws.send(json.dumps({"proposal_open_contract": 1, "contract_id": contrato_id}))
                status = json.loads(ws.recv())
                if "proposal_open_contract" in status and status["proposal_open_contract"]["is_sold"]:
                    lucro = status["proposal_open_contract"]["profit"]
                    if lucro > 0:
                        self.logs.append(f"✅ WIN | Lucro: {lucro:.2f}")
                        self.lucro_acumulado += lucro
                        self.stake_atual = self.stake
                    else:
                        self.logs.append(f"❌ LOSS | Prejuízo: {lucro:.2f}")
                        self.lucro_acumulado += lucro
                        if self.use_martingale:
                            self.stake_atual *= self.factor
                    break
                time.sleep(1)

            st.session_state['log_status'] = "\n".join(self.logs[-10:])
        except Exception as e:
            self.logs.append(f"❌ Erro ao operar: {str(e)}")
            st.session_state['log_status'] = "\n".join(self.logs[-10:])