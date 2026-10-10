<?php
// buyer/marketplace.php
require_once '../includes/auth.php';
requireRole('buyer');

require_once '../includes/db.php';
require_once '../includes/helpers.php';

// Handle Filters
$search = $_GET['search'] ?? '';
$kategori = $_GET['kategori'] ?? '';

$query = "
    SELECT l.*, p.nama_project, p.lokasi, c.nama_kategori 
    FROM listings l
    JOIN projects p ON l.id_project = p.id_project
    JOIN project_categories c ON p.id_kategori = c.id_kategori
    WHERE l.status_listing = 'active'
";
$params = [];

if ($search) {
    $query .= " AND p.nama_project LIKE ?";
    $params[] = "%$search%";
}
if ($kategori) {
    $query .= " AND p.id_kategori = ?";
    $params[] = $kategori;
}

$stmt = $pdo->prepare($query);
$stmt->execute($params);
$listings = $stmt->fetchAll();

// Fetch categories for dropdown
$stmt_cats = $pdo->query("SELECT * FROM project_categories");
$categories = $stmt_cats->fetchAll();

require_once '../includes/header.php';
?>

<div class="dashboard-layout fade-up">
    <div class="dashboard-header">
        <div>
            <h2 class="dashboard-title">Marketplace</h2>
            <p class="dashboard-subtitle">Beli token kredit karbon terverifikasi</p>
        </div>
    </div>

    <!-- Filter Bar -->
    <form method="GET" action="marketplace.php" class="filter-bar">
        <div class="form-group" style="margin-bottom: 0;">
            <div style="position: relative;">
                <i data-lucide="search" style="position: absolute; left: 10px; top: 10px; color: var(--color-text-muted); width: 18px;"></i>
                <input type="text" name="search" class="form-control" placeholder="Cari proyek..." style="padding-left: 36px;" value="<?= htmlspecialchars($search) ?>">
            </div>
        </div>
        <div class="form-group" style="margin-bottom: 0;">
            <select name="kategori" class="form-control" onchange="this.form.submit()">
                <option value="">Kategori (Semua)</option>
                <?php foreach ($categories as $cat): ?>
                    <option value="<?= $cat['id_kategori'] ?>" <?= ($kategori == $cat['id_kategori']) ? 'selected' : '' ?>>
                        <?= htmlspecialchars($cat['nama_kategori']) ?>
                    </option>
                <?php endforeach; ?>
            </select>
        </div>
        <button type="submit" class="btn-outline" style="height: 42px;"><i data-lucide="sliders-horizontal" width="16"></i> Filter</button>
    </form>

    <!-- Grid -->
    <?php if (empty($listings)): ?>
        <div class="card" style="text-align: center; padding: var(--space-2xl);">
            <i data-lucide="search-x" width="48" height="48" style="color: var(--color-text-muted); margin-bottom: var(--space-md);"></i>
            <h3 style="color: var(--color-text-muted);">Tidak Ditemukan</h3>
            <p class="text-muted">Proyek dengan kriteria pencarian tersebut tidak tersedia saat ini.</p>
            <a href="marketplace.php" class="btn-outline" style="margin-top: var(--space-md);">Reset Filter</a>
        </div>
    <?php else: ?>
    <div class="marketplace-grid">
        <?php foreach ($listings as $listing): ?>
        <div class="card marketplace-card" style="animation: fadeUp 0.35s ease forwards;">
            <img
                class="card-img"
                src="<?= htmlspecialchars(projectImageUrl($listing['nama_project'], $listing['nama_kategori'], (int)$listing['id_project'])) ?>"
                alt="Visual proyek <?= htmlspecialchars($listing['nama_project']) ?>"
                loading="lazy"
            >
            <div class="card-body">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <span class="badge badge-cat-<?= strtolower(strtok($listing['nama_kategori'], " ")) ?>">
                        <?= htmlspecialchars($listing['nama_kategori']) ?>
                    </span>
                    <span class="badge badge--verified" title="Terverifikasi VCS/Gold Standard"><i data-lucide="check-circle" width="12"></i> Verified</span>
                </div>
                <h3 style="margin: 0; font-size: var(--text-lg);"><?= htmlspecialchars($listing['nama_project']) ?></h3>
                <p class="text-sm text-muted" style="display: flex; align-items: center; gap: 4px; margin-bottom: 0;">
                    <i data-lucide="map-pin" width="14"></i> <?= htmlspecialchars($listing['lokasi']) ?>
                </p>
                <div style="margin-top: auto; border-top: 1px solid var(--color-border); padding-top: var(--space-sm);">
                    <div style="display: flex; justify-content: space-between; align-items: flex-end;">
                        <div>
                            <p class="text-xs text-muted" style="margin:0;">Harga Token</p>
                            <span style="font-weight: 700; color: var(--color-text-primary);"><?= formatIDR($listing['harga_per_token']) ?> <span class="text-xs font-normal">/ tCO₂e</span></span>
                        </div>
                        <div style="text-align: right;">
                            <p class="text-xs text-muted" style="margin:0;">Tersedia</p>
                            <span style="font-weight: 600;"><?= formatCO2e($listing['jumlah_token']) ?></span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="card-footer">
                <a href="project-detail.php?id=<?= $listing['id_project'] ?>" class="btn-primary btn-full">Review & Beli Token</a>
            </div>
        </div>
        <?php endforeach; ?>
    </div>
    <?php endif; ?>
</div>

<?php require_once '../includes/footer.php'; ?>
