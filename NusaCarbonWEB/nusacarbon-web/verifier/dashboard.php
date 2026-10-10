<?php
// verifier/dashboard.php
require_once '../includes/auth.php';
requireRole('verifier');

require_once '../includes/db.php';
require_once '../includes/helpers.php';

// Verifier sees submitted projects/MRV that need review
$stmt = $pdo->query("
    SELECT p.*, c.nama_kategori 
    FROM projects p
    JOIN project_categories c ON p.id_kategori = c.id_kategori
    WHERE p.status_project = 'submitted'
    ORDER BY p.created_at ASC
");
$queue = $stmt->fetchAll();

$approved_this_month = (int)$pdo->query("
    SELECT COUNT(*)
    FROM projects
    WHERE status_project = 'verified'
      AND YEAR(created_at) = YEAR(CURRENT_DATE())
      AND MONTH(created_at) = MONTH(CURRENT_DATE())
")->fetchColumn();

$rejected_projects = (int)$pdo->query("SELECT COUNT(*) FROM projects WHERE status_project = 'rejected'")->fetchColumn();
$issued_tokens = (int)$pdo->query("SELECT COUNT(*) FROM carbon_tokens")->fetchColumn();

require_once '../includes/header.php';
?>

<div class="dashboard-layout fade-up">
    <div class="dashboard-header">
        <div>
            <h2 class="dashboard-title">Dashboard Verifier</h2>
            <p class="dashboard-subtitle">Antrian Review Laporan MRV</p>
        </div>
    </div>

    <div class="stats-grid">
        <div class="card">
            <p class="metric-label">Antrian Review</p>
            <p class="metric-value" style="color: var(--color-pending);"><?= count($queue) ?></p>
        </div>
        <div class="card">
            <p class="metric-label">Disetujui Bulan Ini</p>
            <p class="metric-value" style="color: var(--color-verified);"><?= $approved_this_month ?></p>
        </div>
        <div class="card">
            <p class="metric-label">Ditolak / Revisi</p>
            <p class="metric-value"><?= $rejected_projects ?></p>
        </div>
        <div class="card">
            <p class="metric-label">Token Diterbitkan</p>
            <p class="metric-value"><?= formatCO2e($issued_tokens) ?></p>
        </div>
    </div>

    <h3>Daftar Antrian</h3>
    <div class="table-responsive">
        <table class="table">
            <thead>
                <tr>
                    <th>Nama Proyek</th>
                    <th>Kategori</th>
                    <th>Lokasi</th>
                    <th>Tanggal Submit</th>
                    <th>Aksi</th>
                </tr>
            </thead>
            <tbody>
                <?php if (empty($queue)): ?>
                <tr><td colspan="5" style="text-align: center;">Tidak ada antrian saat ini.</td></tr>
                <?php endif; ?>

                <?php foreach($queue as $q): ?>
                <tr>
                    <td style="font-weight: 500;"><?= htmlspecialchars($q['nama_project']) ?></td>
                    <td><span class="badge badge-cat-<?= strtolower(strtok($q['nama_kategori'], " ")) ?>"><?= htmlspecialchars($q['nama_kategori']) ?></span></td>
                    <td class="text-muted"><i data-lucide="map-pin" width="12"></i> <?= htmlspecialchars($q['lokasi']) ?></td>
                    <td class="text-sm"><?= formatDate($q['created_at']) ?></td>
                    <td>
                        <a href="review.php?id=<?= $q['id_project'] ?>" class="btn-primary btn-sm"><i data-lucide="search" width="14"></i> Review MRV</a>
                    </td>
                </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
    </div>
</div>

<?php require_once '../includes/footer.php'; ?>
