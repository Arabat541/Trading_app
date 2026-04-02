# dashboard/app.py

from flask import Flask, jsonify, render_template_string
from agents.position_manager import get_open_positions, get_summary, load_positions
from execution.binance_executor import get_balance, get_price
import json
import os

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Trading Agent Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { background: #0d1117; color: #e6edf3; font-family: monospace; padding: 20px; }
        h1 { color: #58a6ff; margin-bottom: 8px; }
        .subtitle { color: #8b949e; font-size: 12px; margin-bottom: 20px; }
        .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin-bottom: 20px; }
        .grid2 { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin-bottom: 20px; }
        .card { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 15px; }
        .card h3 { color: #8b949e; font-size: 11px; margin-bottom: 8px; text-transform: uppercase; }
        .card .value { font-size: 22px; font-weight: bold; }
        .card .sub { font-size: 12px; color: #8b949e; margin-top: 4px; }
        .BUY, .positive { color: #3fb950; }
        .SELL, .negative { color: #f85149; }
        .HOLD, .neutral { color: #8b949e; }
        .WIN { color: #3fb950; }
        .LOSS { color: #f85149; }
        .OPEN { color: #58a6ff; }
        table { width: 100%; border-collapse: collapse; background: #161b22; border-radius: 8px; overflow: hidden; margin-bottom: 20px; }
        th { background: #21262d; padding: 10px 12px; text-align: left; color: #8b949e; font-size: 11px; text-transform: uppercase; }
        td { padding: 10px 12px; border-top: 1px solid #21262d; font-size: 13px; }
        .chart-container { background: #161b22; border: 1px solid #30363d; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
        .section-title { color: #58a6ff; font-size: 14px; margin-bottom: 10px; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; }
        .badge-green { background: #1a3a2a; color: #3fb950; }
        .badge-red { background: #3a1a1a; color: #f85149; }
        .badge-blue { background: #1a2a3a; color: #58a6ff; }
        .refresh { color: #8b949e; font-size: 11px; margin-bottom: 20px; }
        .pnl-positive { color: #3fb950; font-weight: bold; }
        .pnl-negative { color: #f85149; font-weight: bold; }
    </style>
</head>
<body>
    <h1>🤖 Trading Agent Dashboard</h1>
    <p class="subtitle">Paper Trading — Binance Testnet</p>
    <p class="refresh" id="timer">Actualisation dans 30s</p>

    <!-- KPIs -->
    <div class="grid" id="kpis"></div>

    <!-- Paires de marché -->
    <p class="section-title">💹 Marché en temps réel</p>
    <div class="grid" id="market-cards"></div>

    <!-- Positions ouvertes -->
    <p class="section-title">📂 Positions ouvertes</p>
    <table id="positions-table">
        <thead>
            <tr>
                <th>Paire</th>
                <th>Entrée</th>
                <th>Prix actuel</th>
                <th>SL</th>
                <th>TP</th>
                <th>PnL</th>
                <th>Statut</th>
            </tr>
        </thead>
        <tbody id="positions-body"></tbody>
    </table>

    <!-- Graphique RSI -->
    <p class="section-title">📊 RSI historique</p>
    <div class="chart-container">
        <canvas id="rsiChart" height="80"></canvas>
    </div>

    <!-- Graphique PnL -->
    <p class="section-title">💰 PnL cumulé</p>
    <div class="chart-container">
        <canvas id="pnlChart" height="60"></canvas>
    </div>

    <!-- Historique trades -->
    <p class="section-title">📋 Historique des trades</p>
    <table>
        <thead>
            <tr>
                <th>Heure</th>
                <th>Paire</th>
                <th>Prix</th>
                <th>RSI</th>
                <th>ML</th>
                <th>Signal</th>
            </tr>
        </thead>
        <tbody id="logs"></tbody>
    </table>

    <script>
        let rsiChart = null;
        let pnlChart = null;

        async function loadData() {
            const [logsRes, posRes, summaryRes, pricesRes] = await Promise.all([
                fetch("/api/logs"),
                fetch("/api/positions"),
                fetch("/api/summary"),
                fetch("/api/prices")
            ]);

            const logs     = await logsRes.json();
            const pos      = await posRes.json();
            const summary  = await summaryRes.json();
            const prices   = await pricesRes.json();

            // KPIs
            const kpis = document.getElementById("kpis");
            const pnlClass = summary.total_pnl >= 0 ? "pnl-positive" : "pnl-negative";
            const pnlSign = summary.total_pnl >= 0 ? "+" : "";
            kpis.innerHTML = `
                <div class="card">
                    <h3>💰 Solde USDT</h3>
                    <div class="value">${summary.balance?.toFixed(2) || "—"}</div>
                    <div class="sub">disponible</div>
                </div>
                <div class="card">
                    <h3>📊 PnL Total</h3>
                    <div class="value ${pnlClass}">${pnlSign}${summary.total_pnl?.toFixed(2)} USDT</div>
                    <div class="sub">réalisé</div>
                </div>
                <div class="card">
                    <h3>🏆 Win Rate</h3>
                    <div class="value">${summary.win_rate}%</div>
                    <div class="sub">${summary.wins}W / ${summary.losses}L</div>
                </div>
                <div class="card">
                    <h3>📂 Positions</h3>
                    <div class="value">${summary.open}</div>
                    <div class="sub">${summary.closed} fermées</div>
                </div>
            `;

            // Market cards
            const symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"];
            const latest = {};
            logs.forEach(r => latest[r.symbol] = r);
            const marketCards = document.getElementById("market-cards");
            marketCards.innerHTML = "";
            symbols.forEach(sym => {
                const r = latest[sym] || {};
                const price = prices[sym] || r.price || "—";
                const icon = r.signal === "BUY" ? "🟢" : r.signal === "SELL" ? "🔴" : "⚪";
                marketCards.innerHTML += `
                    <div class="card">
                        <h3>${sym}</h3>
                        <div class="value">${typeof price === "number" ? price.toFixed(2) : price}</div>
                        <div class="sub">RSI: ${r.rsi || "—"}</div>
                        <div class="${r.signal}" style="margin-top:8px;font-size:14px">${icon} ${r.signal || "—"}</div>
                    </div>`;
            });

            // Positions ouvertes
            const posBody = document.getElementById("positions-body");
            posBody.innerHTML = "";
            if (pos.length === 0) {
                posBody.innerHTML = `<tr><td colspan="7" style="color:#8b949e;text-align:center">Aucune position ouverte</td></tr>`;
            } else {
                pos.forEach(p => {
                    const current = prices[p.symbol] || p.entry_price;
                    const pnl = (current - p.entry_price) * p.quantity;
                    const pnlPct = (current - p.entry_price) / p.entry_price * 100;
                    const pnlClass = pnl >= 0 ? "pnl-positive" : "pnl-negative";
                    const pnlSign = pnl >= 0 ? "+" : "";
                    posBody.innerHTML += `
                        <tr>
                            <td><b>${p.symbol}</b></td>
                            <td>${p.entry_price}</td>
                            <td>${current.toFixed(2)}</td>
                            <td style="color:#f85149">${p.sl_price}</td>
                            <td style="color:#3fb950">${p.tp_price}</td>
                            <td class="${pnlClass}">${pnlSign}${pnl.toFixed(2)} (${pnlSign}${pnlPct.toFixed(2)}%)</td>
                            <td><span class="badge badge-blue">OPEN</span></td>
                        </tr>`;
                });
            }

            // Table logs
            const tbody = document.getElementById("logs");
            tbody.innerHTML = "";
            [...logs].reverse().slice(0, 50).forEach(r => {
                const icon = r.signal === "BUY" ? "🟢" : r.signal === "SELL" ? "🔴" : "⚪";
                const mlPct = r.ml_proba ? (r.ml_proba * 100).toFixed(1) + "%" : "—";
                tbody.innerHTML += `
                    <tr>
                        <td style="color:#8b949e">${r.timestamp}</td>
                        <td><b>${r.symbol}</b></td>
                        <td>${r.price}</td>
                        <td>${r.rsi}</td>
                        <td>${mlPct}</td>
                        <td class="${r.signal}">${icon} ${r.signal}</td>
                    </tr>`;
            });

            // RSI Chart
            const symColors = { BTCUSDT: "#f7931a", ETHUSDT: "#627eea", SOLUSDT: "#9945ff", BNBUSDT: "#f0b90b" };
            const labels = [...new Set(logs.map(r => r.timestamp))].slice(-20);
            const datasets = symbols.map(sym => ({
                label: sym,
                data: logs.filter(r => r.symbol === sym).slice(-20).map(r => r.rsi),
                borderColor: symColors[sym],
                tension: 0.3,
                fill: false,
                pointRadius: 3
            }));

            if (rsiChart) rsiChart.destroy();
            rsiChart = new Chart(document.getElementById("rsiChart"), {
                type: "line",
                data: { labels, datasets },
                options: {
                    plugins: {
                        legend: { labels: { color: "#e6edf3" } },
                        annotation: {}
                    },
                    scales: {
                        x: { ticks: { color: "#8b949e", maxTicksLimit: 8 }, grid: { color: "#21262d" } },
                        y: { ticks: { color: "#8b949e" }, grid: { color: "#21262d" }, min: 0, max: 100 }
                    }
                }
            });

            // PnL Chart
            const closedPos = await (await fetch("/api/closed_positions")).json();
            const pnlData = [];
            let cumPnl = 0;
            closedPos.forEach(p => {
                cumPnl += p.pnl || 0;
                pnlData.push({ x: p.close_time, y: cumPnl.toFixed(2) });
            });

            if (pnlChart) pnlChart.destroy();
            pnlChart = new Chart(document.getElementById("pnlChart"), {
                type: "line",
                data: {
                    labels: pnlData.map(d => d.x),
                    datasets: [{
                        label: "PnL cumulé (USDT)",
                        data: pnlData.map(d => d.y),
                        borderColor: "#3fb950",
                        backgroundColor: "rgba(63,185,80,0.1)",
                        fill: true,
                        tension: 0.3
                    }]
                },
                options: {
                    plugins: { legend: { labels: { color: "#e6edf3" } } },
                    scales: {
                        x: { ticks: { color: "#8b949e", maxTicksLimit: 8 }, grid: { color: "#21262d" } },
                        y: { ticks: { color: "#8b949e" }, grid: { color: "#21262d" } }
                    }
                }
            });
        }

        let seconds = 30;
        setInterval(() => {
            seconds--;
            document.getElementById("timer").textContent = `Actualisation dans ${seconds}s`;
            if (seconds <= 0) { seconds = 30; loadData(); }
        }, 1000);

        loadData();
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/api/logs")
def logs():
    log_file = "logs/trades.json"
    if not os.path.exists(log_file):
        return jsonify([])
    with open(log_file, "r") as f:
        return jsonify(json.load(f))

@app.route("/api/positions")
def positions():
    return jsonify(get_open_positions())

@app.route("/api/closed_positions")
def closed_positions():
    all_pos = load_positions()
    return jsonify([p for p in all_pos if p["status"] == "CLOSED"])

@app.route("/api/summary")
def summary():
    s = get_summary()
    try:
        s["balance"] = get_balance("USDT")
    except:
        s["balance"] = 0
    return jsonify(s)

@app.route("/api/prices")
def prices():
    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]
    result = {}
    for sym in symbols:
        try:
            result[sym] = get_price(sym)
        except:
            result[sym] = 0
    return jsonify(result)

if __name__ == "__main__":
    app.run(debug=True, port=5000)