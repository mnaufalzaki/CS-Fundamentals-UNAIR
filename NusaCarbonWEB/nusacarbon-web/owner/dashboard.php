<?php
// owner/dashboard.php
require_once '../includes/auth.php';
requireRole('owner');

require_once '../includes/db.php';
require_once '../includes/helpers.php';

$stmt = $pdo->prepare("
    SELECT p.*, c.nama_kategori 
    FROM projects p
    JOIN project_categories c ON p.id_kategori = c.id_kategori
    WHERE p.id_user = ?
    ORDER BY p.created_at DESC
");
$stmt->execute([$_SESSION['user_id']]);
$projects = $stmt->fetchAll();

$counts = ['verified' => 0, 'submitted' => 0, 'total' => count($projects)];
foreach($projects as $p) {
    if($p['status_project'] === 'verified') $counts['verified']++;
    if($p['status_project'] === 'submitted') $counts['submitted']++;
}

$stmt_tokens = $pdo->prepare("
    SELECT COUNT(*)
    FROM carbon_tokens ct
    JOIN projects p ON ct.id_project = p.id_project
    WHERE p.id_user = ?
");
$stmt_tokens->execute([$_SESSION['user_id']]);
$issued_tokens = (int)$stmt_tokens->fetchColumn();

require_once '../includes/header.php';
?>

<div class="dashboard-layout fade-up">
    <div class="dashboard-header">
        <div>
            <h2 class="dashboard-title">Dashboard Project Owner</h2>
            <p class="dashboard-subtitle">Kelola Proyek Karbon: <?= htmlspecialchars($_SESSION['user_name']) ?> (<?= htmlspecialchars($_SESSION['kyc']) ?>)</p>
        </div>
        <div class="quick-actions">
            <a href="project-form.php" class="btn-primary"><i data-lucide="plus-circle" width="16"></i> Daftarkan Proyek</a>
        </div>
    </div>

    <div class="stats-grid">
        <div class="card">
            <p class="metric-label">Total Proyek</p>
            <p class="metric-value" style="color: var(--color-primary);"><?= $counts['total'] ?></p>
        </div>
        <div class="card">
            <p class="metric-label">Token Diterbitkan</p>
            <p class="metric-value"><?= formatCO2e($issued_tokens) ?></p>
        </div>
        <div class="card">
            <p class="metric-label">Proyek Terverifikasi</p>
            <p class="metric-value" style="color: var(--color-verified);"><?= $counts['verified'] ?></p>
        </div>
        <div class="card">
            <p class="metric-label">Menunggu Review</p>
            <p class="metric-value" style="color: var(--color-pending);"><?= $counts['submitted'] ?></p>
        </div>
    </div>

    <h3>Daftar Proyek Anda</h3>
    <div class="table-responsive">
        <table class="table">
            <thead>
                <tr>
                    <th>Nama Proyek</th>
                    <th>Kategori</th>
                    <th>Lokasi</th>
                    <th>Status</th>
                    <th>Aksi</th>
                </tr>
            </thead>
            <tbody>
                <?php if (empty($projects)): ?>
                <tr><td colspan="5" style="text-align: center;">Belum ada proyek. <a href="project-form.php">Daftarkan sekarang</a>.</td></tr>
                <?php endif; ?>
                
                <?php foreach($projects as $p): ?>
                <tr>
                    <td style="font-weight: 500;"><?= htmlspecialchars($p['nama_project']) ?></td>
                    <td><span class="badge badge-cat-<?= strtolower(strtok($p['nama_kategori'], " ")) ?>"><?= htmlspecialchars($p['nama_kategori']) ?></span></td>
                    <td class="text-muted"><i data-lucide="map-pin" width="12"></i> <?= htmlspecialchars($p['lokasi']) ?></td>
                    <td>
                        <?php if ($p['status_project'] == 'verified'): ?>
                            <span class="badge badge--verified">Verified</span>
                        <?php elseif ($p['status_project'] == 'submitted'): ?>
                            <span class="badge badge--pending">Menunggu Review</span>
                        <?php else: ?>
                            <span class="badge badge--dark">Draft</span>
                        <?php endif; ?>
                    </td>
                    <td>
                        <?php if ($p['status_project'] == 'verified'): ?>
                            <button class="btn-outline btn-sm" onclick="showToast('Upload laporan MRV bulanan/tahunan (mock) dipanggil','info')"><i data-lucide="upload-cloud" width="14"></i> Upload MRV</button>
                        <?php else: ?>
                            <button class="btn-outline btn-sm" disabled>Menunggu Verifikasi</button>
                        <?php endif; ?>
                    </td>
                </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
    </div>
</div>

<?php require_once '../includes/footer.php'; ?>
