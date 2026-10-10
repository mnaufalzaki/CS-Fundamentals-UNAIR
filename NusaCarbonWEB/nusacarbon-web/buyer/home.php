<?php
// buyer/home.php
require_once '../includes/auth.php';
requireRole('buyer');

require_once '../includes/db.php';
require_once '../includes/helpers.php';

// ─── Dynamic portfolio from database ───
$stmt = $pdo->prepare("SELECT saldo_token, saldo_rupiah FROM wallets WHERE id_user = ?");
$stmt->execute([$_SESSION['user_id']]);
$walletData = $stmt->fetch();

$saldo_token = $walletData ? (float)$walletData['saldo_token'] : 0;
$saldo_rupiah = $walletData ? (float)$walletData['saldo_rupiah'] : 0;

// Portfolio value = saldo_token * harga base Rp 5.000 per tCO₂e
$harga_base = (float)$pdo->query("SELECT COALESCE(AVG(harga_per_token), 0) FROM listings WHERE status_listing = 'active'")->fetchColumn();
if ($harga_base <= 0) {
    $harga_base = 5000;
}
$portfolio_value = $saldo_token * $harga_base;

$stmt_distribution = $pdo->prepare("
    SELECT pc.nama_kategori, COUNT(*) AS total
    FROM carbon_tokens ct
    JOIN projects p ON ct.id_project = p.id_project
    JOIN project_categories pc ON p.id_kategori = pc.id_kategori
    WHERE ct.owner_user_id = ? AND ct.status_token IN ('sold', 'available', 'listed')
    GROUP BY pc.nama_kategori
    ORDER BY total DESC
");
$stmt_distribution->execute([$_SESSION['user_id']]);
$portfolio_distribution = $stmt_distribution->fetchAll();

$chart_labels = array_column($portfolio_distribution, 'nama_kategori');
$chart_values = array_map('intval', array_column($portfolio_distribution, 'total'));
if (empty($chart_labels)) {
    $chart_labels = ['Belum Ada Token'];
    $chart_values = [1];
}

$price_chart_values = [];
foreach ([-0.04, -0.02, 0, -0.01, 0.01, 0, 0.02] as $change) {
    $price_chart_values[] = round($harga_base * (1 + $change));
}

require_once '../includes/header.php';
?>

<div class="dashboard-layout fade-up">
    <!-- Premium Glass Header -->
    <div class="glass-card" style="margin-bottom: var(--space-xl); background: var(--gradient-hero); color: white; border: none; overflow: hidden; position: relative;">
        <!-- Decorative blob -->
        <div style="position: absolute; top: -50px; right: -50px; width: 300px; height: 300px; background: rgba(255,255,255,0.1); filter: blur(60px); border-radius: 50%;"></div>
        
        <div style="position: relative; z-index: 1; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: var(--space-md);">
            <div>
                <h2 style="margin: 0 0 8px; font-size: var(--text-3xl); color: #ffffff;">Selamat datang, <?= htmlspecialchars($_SESSION['user_name']) ?></h2>
                <p style="margin: 0; color: rgba(255,255,255,0.9);">Pantau dampak karbon dan portofolio hijau Anda hari ini.</p>
            </div>
            <div class="quick-actions">
                <a href="marketplace.php" class="btn-primary" style="background: #ffffff; color: var(--color-primary) !important; font-weight: 600;">🚀 Beli Token</a>
                <a href="wallet.php" class="btn-outline" style="color: #ffffff; border-color: rgba(255,255,255,0.4);">Lihat Wallet</a>
            </div>
        </div>
    </div>

    <!-- Enhanced Hero Metric -->
    <div class="card" style="margin-bottom: var(--space-xl); text-align: center; border-top: 4px solid var(--color-primary);">
        <p class="text-muted text-sm text-uppercase" style="letter-spacing: 1px;">Total Portfolio Terkini</p>
        <h1 style="font-size: var(--text-5xl); color: var(--color-dark); margin: var(--space-sm) 0;">
            <?= formatIDR($portfolio_value) ?>
        </h1>
        <div style="display: inline-block; padding: 6px 12px; background: var(--color-verified-bg); color: var(--color-verified); border-radius: var(--radius-full); font-size: var(--text-sm); font-weight: 500; margin-bottom: var(--space-lg);">
            <i data-lucide="trending-up" width="14"></i> Saldo Rupiah: <?= formatIDR($saldo_rupiah) ?>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-md); border-top: 1px solid var(--color-border); padding-top: var(--space-md);">
            <div>
                <p class="text-xs text-muted" style="margin:0;">Total Token Dimiliki</p>
                <p style="font-size: var(--text-xl); font-weight: 600; margin:0;"><?= formatCO2e($saldo_token) ?></p>
            </div>
            <div style="border-left: 1px solid var(--color-border);">
                <p class="text-xs text-muted" style="margin:0;">Harga Base per Token</p>
                <p style="font-size: var(--text-xl); font-weight: 600; margin:0; color: var(--color-primary);"><?= formatIDR($harga_base) ?></p>
            </div>
        </div>
    </div>

    <div class="split-layout">
        <div class="card">
            <h3>Harga Token (7 Hari)</h3>
            <p class="text-sm text-muted">Harga saat ini: Rp 5.000 per tCO₂e</p>
            <div class="chart-container-sm">
                <canvas id="priceChart"></canvas>
            </div>
        </div>

        <div class="card">
            <h3>Portfolio Distribusi</h3>
            <div class="chart-container-sm">
                <canvas id="portfolioChart"></canvas>
            </div>
        </div>
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    const ctxPrice = document.getElementById('priceChart').getContext('2d');
    new Chart(ctxPrice, {
        type: 'line',
        data: {
            labels: ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Min'],
            datasets: [{
                label: 'Harga (IDR)',
                data: <?= json_encode($price_chart_values) ?>,
                borderColor: '#059669',
                backgroundColor: 'rgba(5,150,105,0.08)',
                borderWidth: 2.5,
                tension: 0.4,
                fill: true,
                pointBackgroundColor: '#059669',
                pointRadius: 4,
            }]
        },
        options: {
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: {
                x: { grid: { display: false } },
                y: { grid: { color: '#E5E7EB' }, border: { display: false } }
            }
        }
    });

    const ctxPort = document.getElementById('portfolioChart').getContext('2d');
    new Chart(ctxPort, {
        type: 'doughnut',
        data: {
            labels: <?= json_encode($chart_labels) ?>,
            datasets: [{
                data: <?= json_encode($chart_values) ?>,
                backgroundColor: ['#059669', '#0D9488', '#2563EB'],
                borderWidth: 0,
                cutout: '75%'
            }]
        },
        options: {
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom' }
            }
        }
    });
});
</script>

<?php require_once '../includes/footer.php'; ?>
