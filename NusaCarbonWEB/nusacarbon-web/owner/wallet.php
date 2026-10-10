<?php
// owner/wallet.php
require_once '../includes/auth.php';
requireRole('owner');

require_once '../includes/db.php';
require_once '../includes/helpers.php';

$stmt = $pdo->prepare("SELECT * FROM wallets WHERE id_user = ?");
$stmt->execute([$_SESSION['user_id']]);
$wallet = $stmt->fetch();

if (!$wallet) {
    $wallet = [
        'wallet_address' => generateMockWalletAddress(),
        'saldo_token' => 0,
        'saldo_rupiah' => 0,
    ];
}

$stmt = $pdo->prepare("
    SELECT
        COUNT(*) AS total_tokens,
        COALESCE(SUM(CASE WHEN ct.status_token = 'available' THEN 1 ELSE 0 END), 0) AS available_tokens,
        COALESCE(SUM(CASE WHEN ct.status_token = 'listed' THEN 1 ELSE 0 END), 0) AS listed_tokens,
        COALESCE(SUM(CASE WHEN ct.status_token = 'sold' THEN 1 ELSE 0 END), 0) AS sold_tokens
    FROM carbon_tokens ct
    JOIN projects p ON ct.id_project = p.id_project
    WHERE p.id_user = ?
");
$stmt->execute([$_SESSION['user_id']]);
$tokenStats = $stmt->fetch() ?: [
    'total_tokens' => 0,
    'available_tokens' => 0,
    'listed_tokens' => 0,
    'sold_tokens' => 0,
];

$stmt = $pdo->prepare("
    SELECT COALESCE(SUM(jumlah_token * harga_per_token), 0)
    FROM listings
    WHERE id_user = ? AND status_listing = 'active'
");
$stmt->execute([$_SESSION['user_id']]);
$activeListingValue = (float)$stmt->fetchColumn();

$stmt = $pdo->prepare("
    SELECT COUNT(*) AS total_sales, COALESCE(SUM(total_harga), 0) AS total_revenue
    FROM trade_transactions
    WHERE seller_user_id = ? AND status IN ('paid', 'success')
");
$stmt->execute([$_SESSION['user_id']]);
$salesStats = $stmt->fetch() ?: ['total_sales' => 0, 'total_revenue' => 0];

$stmt = $pdo->prepare("
    SELECT tt.*, p.nama_project
    FROM trade_transactions tt
    JOIN listings l ON tt.id_listing = l.id_listing
    JOIN projects p ON l.id_project = p.id_project
    WHERE tt.seller_user_id = ?
    ORDER BY tt.tanggal_transaksi DESC
    LIMIT 5
");
$stmt->execute([$_SESSION['user_id']]);
$recentSales = $stmt->fetchAll();

$walletActivities = [
    ['label' => 'Akumulasi pendapatan proyek', 'meta' => 'Estimasi settlement bulanan', 'amount' => 12500000, 'status' => 'Simulasi'],
    ['label' => 'Nilai listing marketplace aktif', 'meta' => 'Berdasarkan harga listing yang sedang aktif', 'amount' => $activeListingValue, 'status' => 'Aktif'],
    ['label' => 'Estimasi biaya operasional jaringan', 'meta' => 'Perhitungan mock untuk kebutuhan demo', 'amount' => -35000, 'status' => 'Estimasi'],
];

require_once '../includes/header.php';
?>

<div class="dashboard-layout owner-wallet-layout fade-up">
    <div class="dashboard-header">
        <div>
            <h2 class="dashboard-title">Owner Wallet</h2>
            <p class="dashboard-subtitle">Pantau saldo, nilai listing aktif, dan performa token proyek secara ringkas.</p>
        </div>
        <div class="quick-actions">
            <button class="btn-outline" onclick="copyToClipboard('<?= htmlspecialchars($wallet['wallet_address']) ?>')"><i data-lucide="copy" width="16"></i> Salin Alamat</button>
        </div>
    </div>

    <section class="wallet-overview-grid">
        <article class="card wallet-profile-card">
            <span class="badge badge--verified">Wallet Owner</span>
            <h3><?= htmlspecialchars($_SESSION['user_name'] ?? 'Project Owner') ?></h3>
            <p class="dashboard-subtitle">Alamat wallet digunakan untuk pencatatan token dan settlement simulasi.</p>
            <div class="wallet-address-line">
                <span><?= htmlspecialchars(truncateHash($wallet['wallet_address'], 10, 8)) ?></span>
                <button class="hash-btn" onclick="copyToClipboard('<?= htmlspecialchars($wallet['wallet_address']) ?>')"><i data-lucide="copy" width="14"></i></button>
            </div>
        </article>

        <article class="card wallet-balance-card">
            <p class="metric-label">Saldo Rupiah Mock</p>
            <h1><?= formatIDR((float)($wallet['saldo_rupiah'] ?? 0)) ?></h1>
            <p><?= formatCO2e((float)($wallet['saldo_token'] ?? 0)) ?> saldo token tersimpan</p>
        </article>
    </section>

    <div class="stats-grid wallet-stats-grid">
        <div class="card wallet-metric-card">
            <p class="metric-label">Token Diterbitkan</p>
            <p class="metric-value"><?= formatCO2e((float)$tokenStats['total_tokens']) ?></p>
        </div>
        <div class="card wallet-metric-card">
            <p class="metric-label">Siap Listing</p>
            <p class="metric-value" style="color: var(--color-primary);"><?= formatCO2e((float)$tokenStats['available_tokens']) ?></p>
        </div>
        <div class="card wallet-metric-card">
            <p class="metric-label">Nilai Listing Aktif</p>
            <p class="metric-value"><?= formatIDR($activeListingValue) ?></p>
        </div>
        <div class="card wallet-metric-card">
            <p class="metric-label">Pendapatan Tercatat</p>
            <p class="metric-value" style="color: var(--color-verified);"><?= formatIDR((float)$salesStats['total_revenue']) ?></p>
        </div>
    </div>

    <div class="wallet-content-grid">
        <section class="wallet-activity-card">
            <div class="wallet-section-header">
                <div>
                    <h3>Aktivitas Wallet</h3>
                    <p class="dashboard-subtitle">Ringkasan aktivitas dan estimasi nilai wallet owner.</p>
                </div>
            </div>
            <div class="table-responsive wallet-table">
                <table class="table">
                    <thead>
                        <tr>
                            <th>Aktivitas</th>
                            <th>Nilai</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach($walletActivities as $activity): ?>
                        <tr>
                            <td>
                                <strong><?= htmlspecialchars($activity['label']) ?></strong>
                                <p class="text-xs text-muted" style="margin: 4px 0 0;"><?= htmlspecialchars($activity['meta']) ?></p>
                            </td>
                            <td class="wallet-amount <?= $activity['amount'] < 0 ? 'wallet-amount--negative' : '' ?>"><?= formatIDR((float)$activity['amount']) ?></td>
                            <td><span class="badge badge--verified"><?= htmlspecialchars($activity['status']) ?></span></td>
                        </tr>
                        <?php endforeach; ?>
                        <?php foreach($recentSales as $sale): ?>
                        <tr>
                            <td>
                                <strong>Penjualan token - <?= htmlspecialchars($sale['nama_project']) ?></strong>
                                <p class="text-xs text-muted" style="margin: 4px 0 0;"><?= formatDate($sale['tanggal_transaksi']) ?></p>
                            </td>
                            <td style="font-weight: 700;"><?= formatIDR((float)$sale['total_harga']) ?></td>
                            <td><span class="badge badge--transfer"><?= htmlspecialchars($sale['status']) ?></span></td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
        </section>

        <aside class="card wallet-side-panel">
            <div class="wallet-side-heading">
                <span class="badge badge--transfer">Settlement</span>
                <h3>Ringkasan Owner</h3>
                <p class="dashboard-subtitle">Status komersialisasi token dari proyek Anda.</p>
            </div>
            <dl class="wallet-settlement-list">
                <div class="wallet-settlement-row">
                    <dt>Penjualan sukses</dt>
                    <dd><?= number_format((int)$salesStats['total_sales'], 0, ',', '.') ?> transaksi</dd>
                </div>
                <div class="wallet-settlement-row">
                    <dt>Token listed</dt>
                    <dd><?= formatCO2e((float)$tokenStats['listed_tokens']) ?></dd>
                </div>
                <div class="wallet-settlement-row">
                    <dt>Token terjual</dt>
                    <dd><?= formatCO2e((float)$tokenStats['sold_tokens']) ?></dd>
                </div>
            </dl>
            <button class="btn-primary btn-full" onclick="showToast('Laporan settlement mock sedang disiapkan','info')">
                <i data-lucide="download" width="16"></i> Unduh Rekap
            </button>
        </aside>
    </div>
</div>

<?php require_once '../includes/footer.php'; ?>
