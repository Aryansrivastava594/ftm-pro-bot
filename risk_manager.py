class RiskManager:

    def __init__(self, max_trades=3, daily_loss_limit=1000):
        self.max_trades        = max_trades
        self.daily_loss_limit  = daily_loss_limit
        self.open_trades       = 0
        self.daily_pnl         = 0.0
        self.trade_log         = []

    def check(self, side):
        if self.open_trades >= self.max_trades:
            return True, f"Max open trades reached ({self.max_trades})"
        if self.daily_pnl <= -self.daily_loss_limit:
            return True, f"Daily loss limit hit (₹{self.daily_loss_limit})"
        return False, ""

    def record_trade(self, side):
        self.open_trades += 1
        self.trade_log.append({
            "side"   : side,
            "status" : "open"
        })
        print(f"Trade recorded: {side.upper()} | Open: {self.open_trades}")

    def record_close(self, pnl=0.0):
        self.open_trades  = max(0, self.open_trades - 1)
        self.daily_pnl   += pnl
        print(f"Trade closed | PnL: ₹{pnl:.2f} | Daily: ₹{self.daily_pnl:.2f}")

    def reset_daily(self):
        self.open_trades = 0
        self.daily_pnl   = 0.0
        self.trade_log   = []
        print("Daily stats reset")
