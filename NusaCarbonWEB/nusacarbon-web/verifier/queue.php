<?php
// verifier/queue.php
require_once '../includes/auth.php';
requireRole('verifier');

require_once '../includes/db.php';
require_once '../includes/helpers.php';

$stmt = $pdo->query("
    SELECT p.*, c.nama_kategori, u.nama_user AS owner_name
    FROM projects p
    JOIN project_categories c ON p.id_kategori = c.id_kategori
    JOIN users u ON p.id_user = u.id_user
    WHERE p.status_project = 'submitted'
    ORDER BY p.created_at ASC
");
$queue = $stmt->fetchAll();

$stmt = $pdo->query("
    SELECT p.*, c.nama_kategori, u.nama_user AS owner_name
    FROM projects p
    JOIN project_categories c ON p.id_kategori = c.id_kategori
    JOIN users u ON p.id_user = u.id_user
    WHERE p.status_project IN ('verified', 'rejected')
    ORDER BY p.created_at DESC
    LIMIT 6
");
$recentReviews = $stmt->fetchAll();

$avgArea = 0;
if (!empty($queue)) {
    $totalArea = array_reduce($queue, fn($carry, $item) => $carry + (float)$item['luas_lahan'], 0);
    $avgArea = $totalArea / count($queue);
}

require_once '../includes/header.php';
?>

<div class="dashboard-layout fade-up">
    <div class="dashboard-header">
        <div>
            <h2 class="dashboard-title">Antrian Review</h2>
            <p class="dashboard-subtitle">Kelola pengajuan proyek yang menunggu validasi verifier.</p>
        </div>
        <div class="quick-actions">
            <a href="dashboard.php" class="btn-outline"><i data-lucide="layout-dashboard" width="16"></i> Dashboard</a>
        </div>
    </div>

    <div class="stats-grid">
        <div class="card">
            <p class="metric-label">Total Antrian</p>
            <p class="metric-value" style="color: var(--color-pending);"><?= count($queue) ?></p>
        </div>
        <div class="card">
            <p class="metric-label">Rata-rata Luas</p>
            <p class="metric-value"><?= number_format($avgArea, 0, ',', '.') ?> Ha</p>
        </div>
        <div class="card">
            <p class="metric-label">SLA Review Mock</p>
            <p class="metric-value" style="color: var(--color-primary);">3 Hari</p>
        </div>
        <div class="card">
            <p class="metric-label">Prioritas</p>
            <p class="metric-value"><?= count(array_filter($queue, fn($item) => (float)$item['luas_lahan'] >= 1000)) ?></p>
        </div>
    </div>

    <div class="split-layout">
        <section>
            <h3>Daftar Pengajuan</h3>
            <div class="queue-list">
                <?php if (empty($queue)): ?>
                    <div class="card queue-empty">
                        <i data-lucide="clipboard-check" width="32"></i>
                        <h3>Tidak ada antrian review</h3>
                        <p class="dashboard-subtitle">Semua pengajuan proyek sudah diproses.</p>
                    </div>
                <?php endif; ?>

                <?php foreach($queue as $item): ?>
                    <article class="card queue-card">
                        <div class="queue-card-main">
                            <img src="<?= htmlspecialchars(projectImageUrl($item['nama_project'], $item['nama_kategori'], (int)$item['id_project'])) ?>" alt="Visual proyek <?= htmlspecialchars($item['nama_project']) ?>" class="queue-card-img">
                            <div>
                                <div class="queue-card-title-row">
                                    <h3><?= htmlspecialchars($item['nama_project']) ?></h3>
                                    <span class="badge badge-cat-<?= strtolower(strtok($item['nama_kategori'], " ")) ?>"><?= htmlspecialchars($item['nama_kategori']) ?></span>
                                </div>
                                <p class="dashboard-subtitle"><?= htmlspecialchars($item['owner_name']) ?> &bull; <?= htmlspecialchars($item['lokasi']) ?></p>
                                <p class="queue-description"><?= htmlspecialchars($item['deskripsi'] ?: 'Deskripsi proyek belum tersedia.') ?></p>
                                <div class="queue-meta-row">
                                    <span><i data-lucide="map" width="14"></i> <?= number_format((float)$item['luas_lahan'], 0, ',', '.') ?> Ha</span>
                                    <span><i data-lucide="calendar-days" width="14"></i> <?= formatDate($item['created_at']) ?></span>
                                </div>
                            </div>
                        </div>
                        <div class="queue-card-action">
                            <span class="badge badge--pending">Menunggu Review</span>
                            <a href="review.php?id=<?= $item['id_project'] ?>" class="btn-primary btn-sm"><i data-lucide="search" width="14"></i> Review MRV</a>
                        </div>
                    </article>
                <?php endforeach; ?>
            </div>
        </section>

        <aside class="card verifier-guide-panel">
            <h3>Checklist Verifier</h3>
            <div class="owner-guide-list">
                <div class="owner-guide-item">
                    <i data-lucide="file-search" width="18"></i>
                    <span>Periksa kelengkapan dokumen lahan dan izin.</span>
                </div>
                <div class="owner-guide-item">
                    <i data-lucide="map-pinned" width="18"></i>
                    <span>Validasi lokasi, luas area, dan kategori proyek.</span>
                </div>
                <div class="owner-guide-item">
                    <i data-lucide="scale" width="18"></i>
                    <span>Tentukan volume tCO2e yang layak diminting.</span>
                </div>
            </div>
        </aside>
    </div>

    <section style="margin-top: var(--space-xl);">
        <h3>Riwayat Review Terakhir</h3>
        <div class="table-responsive">
            <table class="table">
                <thead>
                    <tr>
                        <th>Proyek</th>
                        <th>Owner</th>
                        <th>Kategori</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    <?php if (empty($recentReviews)): ?>
                    <tr>
                        <td colspan="4" style="text-align: center; padding: 32px; color: var(--color-text-muted);">Belum ada riwayat review.</td>
                    </tr>
                    <?php endif; ?>
                    <?php foreach($recentReviews as $review): ?>
                    <tr>
                        <td style="font-weight: 600;"><?= htmlspecialchars($review['nama_project']) ?></td>
                        <td><?= htmlspecialchars($review['owner_name']) ?></td>
                        <td><span class="badge badge-cat-<?= strtolower(strtok($review['nama_kategori'], " ")) ?>"><?= htmlspecialchars($review['nama_kategori']) ?></span></td>
                        <td>
                            <?php if ($review['status_project'] === 'verified'): ?>
                                <span class="badge badge--verified">Verified</span>
                            <?php else: ?>
                                <span class="badge badge--rejected">Rejected</span>
                            <?php endif; ?>
                        </td>
                    </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        </div>
    </section>
</div>

<?php require_once '../includes/footer.php'; ?>
