from flask import Flask, request, jsonify
from delta_client import DeltaClient
from telegram_bot import TelegramBot
from risk_manager import RiskManager
import threading
import requests
import time
import os

app = Flask(__name__)

WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "change_me")
TRADE_SIZE     = float(os.environ.get("TRADE_SIZE", 500))
MAX_TRADES     = int(os.environ.get("MAX_TRADES", 3))
DAILY_LOSS     = float(os.environ.get("DAILY_LOSS", 1000))
RENDER_URL     = os.environ.get("RENDER_URL", "")

delta    = DeltaClient()
telegram = TelegramBot()
risk     = RiskManager(max_trades=MAX_TRADES, daily_loss_limit=DAILY_LOSS)


# ── Keep-alive ────────────────────────────────────
def keep_alive():
    if not RENDER_URL:
        return
    while True:
        try:
            requests.get(RENDER_URL)
            print("Keep-alive ping sent")
        except Exception as e:
            print(f"Keep-alive error: {e}")
        time.sleep(600)

threading.Thread(target=keep_alive, daemon=True).start()


# ── Routes ────────────────────────────────────────
@app.route("/", methods=["GET"])
def health():
    return jsonify({
        "status"      : "FTM PRO Bot is running ✅",
        "open_trades" : risk.open_trades,
        "daily_pnl"   : risk.daily_pnl
    }), 200


@app.route("/status", methods=["GET"])
def status():
    msg = (
        f"📊 <b>FTM PRO Status</b>\n"
        f"Open Trades : {risk.open_trades}\n"
        f"Daily P&L   : ₹{risk.daily_pnl:.2f}\n"
        f"Max Trades  : {MAX_TRADES}\n"
        f"Daily Limit : ₹{DAILY_LOSS}"
    )
    telegram.send(msg)
    return jsonify({"status": "ok"}), 200


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()

    # ── Auth ──────────────────────────────────────
    if not data or data.get("secret") != WEBHOOK_SECRET:
        print("Unauthorized webhook attempt")
        return jsonify({"error": "Unauthorized"}), 401

    symbol = data.get("symbol", "BTCUSDT")
    side   = data.get("side", "").lower()
    price  = float(data.get("price", 0))
    sl     = float(data.get("sl", 0))
    tp     = float(data.get("tp", 0))
    regime = data.get("regime", "")

    print(f"Signal received: {side.upper()} {symbol} @ {price}")

    # ── Risk check ────────────────────────────────
    blocked, reason = risk.check(side)
    if blocked:
        telegram.send(
            f"🚫 <b>Trade Blocked</b>\n"
            f"Reason : {reason}\n"
            f"Signal : {side.upper()} {symbol}"
        )
        return jsonify({"status": "blocked", "reason": reason}), 200

    # ── Place order ───────────────────────────────
    try:
        qty    = round(TRADE_SIZE / price, 4)
        result = delta.place_order(symbol, side, qty, sl, tp)
        risk.record_trade(side)

        emoji = "🟢" if side == "buy" else "🔴"
        telegram.send(
            f"{emoji} <b>ORDER PLACED</b>\n"
            f"Symbol  : {symbol}\n"
            f"Side    : {side.upper()}\n"
            f"Price   : ₹{price:,.2f}\n"
            f"Qty     : {qty}\n"
            f"SL      : ₹{sl:,.2f}\n"
            f"TP      : ₹{tp:,.2f}\n"
            f"Regime  : {regime}\n"
            f"Value   : ₹{TRADE_SIZE:,.2f}"
        )
        return jsonify({"status": "ok", "order": result}), 200

    except Exception as e:
        telegram.send(
            f"❌ <b>Order Failed</b>\n"
            f"Symbol : {symbol}\n"
            f"Side   : {side.upper()}\n"
            f"Error  : {str(e)}"
        )
        return jsonify({"error": str(e)}), 500


@app.route("/close/<symbol>", methods=["POST"])
def close_position(symbol):
    try:
        result = delta.close_position(symbol)
        telegram.send(
            f"🔒 <b>Position Closed Manually</b>\n"
            f"Symbol: {symbol}"
        )
        return jsonify({"status": "closed", "result": result}), 200
    except Exception as e:
        telegram.send(
            f"❌ <b>Manual Close Failed</b>\n"
            f"Symbol : {symbol}\n"
            f"Error  : {str(e)}"
        )
        return jsonify({"error": str(e)}), 500


@app.route("/reset", methods=["POST"])
def reset():
    data = request.get_json()
    if not data or data.get("secret") != WEBHOOK_SECRET:
        return jsonify({"error": "Unauthorized"}), 401
    risk.reset_daily()
    telegram.send("🔄 <b>Daily Stats Reset</b>\nOpen trades and P&L cleared.")
    return jsonify({"status": "reset done"}), 200


if __name__ == "__main__":
    telegram.send("🚀 <b>FTM PRO Bot Started</b>\nListening for signals...")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
