<?php
// owner/tokens.php
require_once '../includes/auth.php';
requireRole('owner');

require_once '../includes/db.php';
require_once '../includes/helpers.php';

$stmt = $pdo->prepare("
    SELECT
        ct.id_token,
        ct.token_serial,
        ct.vintage_year,
        ct.status_token,
        ct.created_at,
        p.nama_project,
        c.nama_kategori
    FROM carbon_tokens ct
    JOIN projects p ON ct.id_project = p.id_project
    JOIN project_categories c ON p.id_kategori = c.id_kategori
    WHERE p.id_user = ?
    ORDER BY ct.created_at DESC, ct.id_token DESC
    LIMIT 50
");
$stmt->execute([$_SESSION['user_id']]);
$tokens = $stmt->fetchAll();

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
$stats = $stmt->fetch() ?: [
    'total_tokens' => 0,
    'available_tokens' => 0,
    'listed_tokens' => 0,
    'sold_tokens' => 0,
];

require_once '../includes/header.php';
?>

<div class="dashboard-layout fade-up">
    <div class="dashboard-header">
        <div>
            <h2 class="dashboard-title">Token Proyek Saya</h2>
            <p class="dashboard-subtitle">Daftar token yang diterbitkan dari proyek milik owner.</p>
        </div>
        <div class="quick-actions">
            <a href="wallet.php" class="btn-outline"><i data-lucide="wallet" width="16"></i> Lihat Wallet</a>
            <a href="project-form.php" class="btn-primary"><i data-lucide="plus-circle" width="16"></i> Proyek Baru</a>
        </div>
    </div>

    <div class="stats-grid">
        <div class="card">
            <p class="metric-label">Total Token</p>
            <p class="metric-value"><?= formatCO2e((float)$stats['total_tokens']) ?></p>
        </div>
        <div class="card">
            <p class="metric-label">Available</p>
            <p class="metric-value" style="color: var(--color-primary);"><?= formatCO2e((float)$stats['available_tokens']) ?></p>
        </div>
        <div class="card">
            <p class="metric-label">Listed</p>
            <p class="metric-value" style="color: var(--color-transfer);"><?= formatCO2e((float)$stats['listed_tokens']) ?></p>
        </div>
        <div class="card">
            <p class="metric-label">Sold</p>
            <p class="metric-value" style="color: var(--color-verified);"><?= formatCO2e((float)$stats['sold_tokens']) ?></p>
        </div>
    </div>

    <h3>Token Terbaru</h3>
    <div class="table-responsive">
        <table class="table">
            <thead>
                <tr>
                    <th>Serial Token</th>
                    <th>Proyek</th>
                    <th>Kategori</th>
                    <th>Vintage</th>
                    <th>Status</th>
                    <th>Diterbitkan</th>
                </tr>
            </thead>
            <tbody>
                <?php if (empty($tokens)): ?>
                <tr>
                    <td colspan="6" style="text-align: center; padding: 40px; color: var(--color-text-muted);">Belum ada token. Token akan muncul setelah proyek diverifikasi.</td>
                </tr>
                <?php endif; ?>
                <?php foreach($tokens as $token): ?>
                <tr>
                    <td><span class="hash-display"><?= htmlspecialchars($token['token_serial']) ?></span></td>
                    <td style="font-weight: 600;"><?= htmlspecialchars($token['nama_project']) ?></td>
                    <td><span class="badge badge-cat-<?= strtolower(strtok($token['nama_kategori'], " ")) ?>"><?= htmlspecialchars($token['nama_kategori']) ?></span></td>
                    <td><?= htmlspecialchars($token['vintage_year']) ?></td>
                    <td>
                        <?php if ($token['status_token'] === 'available'): ?>
                            <span class="badge badge--verified">Available</span>
                        <?php elseif ($token['status_token'] === 'listed'): ?>
                            <span class="badge badge--transfer">Listed</span>
                        <?php elseif ($token['status_token'] === 'sold'): ?>
                            <span class="badge badge--pending">Sold</span>
                        <?php else: ?>
                            <span class="badge badge--dark"><?= htmlspecialchars($token['status_token']) ?></span>
                        <?php endif; ?>
                    </td>
                    <td class="text-muted text-sm"><?= formatDate($token['created_at']) ?></td>
                </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
    </div>
</div>

<?php require_once '../includes/footer.php'; ?>
