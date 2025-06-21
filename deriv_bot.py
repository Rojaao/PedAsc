import websocket, json, time, threading
import streamlit as st
from estrategia_famped import analisar_ticks_famped
from datetime import datetime

class DerivBot:
    def __init__(self, token, symbol, stake, use_martingale, factor, target_profit, stop_loss, selected_ticks, percento_entrada):
        self.token = token
        self.symbol = symbol
        self.stake_inicial = stake
        self.stake_atual = stake
        self.use_martingale = use_martingale
        self.factor = factor
        self.target_profit = target_profit
        self.stop_loss = stop_loss
        self.selected_ticks = selected_ticks
        self.percento_entrada = percento_entrada
        self.logs = []
        self.resultados = []
        self.lucro_acumulado = 0
        self.ticks = []
        self.running = True

    def log(self, msg):
        self.logs.append(f"{msg}")

    def fazer_operacao(self):
        try:
            ws = websocket.create_connection("wss://ws.binaryws.com/websockets/v3?app_id=1089")
            ws.send(json.dumps({"authorize": self.token}))
            auth = json.loads(ws.recv())
            if "error" in auth:
                self.log("❌ Token inválido.")
                return

            # Envia proposta
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
            resposta = json.loads(ws.recv())

            if "proposal" not in resposta:
                self.log("❌ Erro: resposta inesperada da Deriv (sem campo 'proposal')")
                return

            proposal_id = resposta["proposal"]["id"]

            # Envia ordem de compra
            ws.send(json.dumps({"buy": proposal_id, "price": self.stake_atual}))
            result = json.loads(ws.recv())

            if "buy" not in result:
                self.log("❌ Erro ao operar: resposta sem campo 'buy'")
                return

            contract_id = result["buy"]["contract_id"]
            self.log(f"🟢 Entrada realizada! Contract ID: {contract_id} | Stake: ${self.stake_atual:.2f}")

            # Aguarda resultado
            while True:
                status = json.loads(ws.recv())
                if "contract_update" in status:
                    continue
                if "proposal" in status:
                    continue
                if "error" in status:
                    self.log("❌ Erro durante contrato.")
                    break
                if "sell" in status:
                    continue
                if "profit" in status.get("buy", {}):
                    break
                if "msg_type" in status and status["msg_type"] == "contract":
                    profit = float(status["contract"]["profit"])
                    resultado = "WIN" if profit > 0 else "LOSS"
                    self.log(f"🏁 Resultado: {resultado} | Lucro: ${profit:.2f}")
                    self.resultados.append((datetime.now().strftime("%H:%M:%S"), resultado, self.stake_atual))
                    self.lucro_acumulado += profit

                    if resultado == "WIN":
                        self.stake_atual = self.stake_inicial
                        self.ticks.clear()
                    elif resultado == "LOSS" and self.use_martingale:
                        self.stake_atual *= self.factor

                    break

            ws.close()
        except Exception as e:
            self.log(f"❌ Exceção: {str(e)}")

    def run_interface(self):
        while self.running:
            if len(self.ticks) < self.selected_ticks:
                time.sleep(1)
                continue

            self.log(f"📊 Dígitos analisados: {self.ticks[-self.selected_ticks:]}")
            entrada_info = analisar_ticks_famped(self.ticks, self.percento_entrada)

            if entrada_info.get("entrada") == "ENTRAR":
                self.fazer_operacao()
            else:
                self.log("🔍 Aguardando oportunidade...")

            time.sleep(2)

    def receber_ticks(self):
        try:
            ws = websocket.create_connection("wss://ws.binaryws.com/websockets/v3?app_id=1089")
            ws.send(json.dumps({"ticks": self.symbol}))
            while self.running:
                tick_msg = json.loads(ws.recv())
                if "tick" in tick_msg:
                    tick = int(str(tick_msg["tick"]["quote"])[-1])
                    self.ticks.append(tick)
                    if len(self.ticks) > self.selected_ticks:
                        self.ticks = self.ticks[-self.selected_ticks:]
        except Exception as e:
            self.log(f"❌ Erro nos ticks: {str(e)}")

    def stop(self):
        self.running = False