<?php
// owner/project-form.php
require_once '../includes/auth.php';
requireRole('owner');
require_once '../includes/db.php';

$stmt = $pdo->query("SELECT * FROM project_categories");
$categories = $stmt->fetchAll();

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $nama = $_POST['nama_project'];
    $kategori = $_POST['id_kategori'];
    $lokasi = $_POST['lokasi'];
    $luas = $_POST['luas_lahan'];
    $desc = $_POST['deskripsi'];

    $stmt = $pdo->prepare("INSERT INTO projects (id_user, id_kategori, nama_project, lokasi, luas_lahan, deskripsi, status_project) VALUES (?, ?, ?, ?, ?, ?, 'submitted')");
    $stmt->execute([$_SESSION['user_id'], $kategori, $nama, $lokasi, $luas, $desc]);
    
    header("Location: dashboard.php");
    exit;
}

require_once '../includes/header.php';
?>

<div class="dashboard-layout owner-workspace fade-up">
    <a href="dashboard.php" class="owner-back-link">&larr; Kembali ke Dashboard</a>

    <section class="card owner-form-panel">
        <div class="owner-form-heading">
            <span class="badge badge--verified">Registrasi Sertifikasi</span>
            <h2 class="dashboard-title">Daftarkan Proyek Baru</h2>
            <p class="dashboard-subtitle">Lengkapi detail inti proyek agar verifier dapat meninjau kelayakan awal.</p>
        </div>

        <form method="POST">
            <div class="form-group">
                <label>Nama Proyek</label>
                <input type="text" name="nama_project" class="form-control" required placeholder="Contoh: Konservasi Lahan Gambut X">
            </div>
            <div class="form-group">
                <label>Kategori Proyek</label>
                <select name="id_kategori" class="form-control" required>
                    <?php foreach($categories as $cat): ?>
                        <option value="<?= $cat['id_kategori'] ?>"><?= htmlspecialchars($cat['nama_kategori']) ?></option>
                    <?php endforeach; ?>
                </select>
            </div>
            <div class="owner-form-row">
                <div class="form-group">
                    <label>Lokasi (Provinsi/Pulau)</label>
                    <input type="text" name="lokasi" class="form-control" required placeholder="Contoh: Kalimantan Barat">
                </div>
                <div class="form-group">
                    <label>Luas Lahan (Ha)</label>
                    <input type="number" step="0.01" name="luas_lahan" class="form-control" required placeholder="1250">
                </div>
            </div>
            <div class="form-group">
                <label>Deskripsi Tujuan & Dampak</label>
                <textarea name="deskripsi" class="form-control" rows="5" required placeholder="Ringkas tujuan konservasi, estimasi dampak karbon, dan manfaat komunitas."></textarea>
            </div>

            <div class="supporting-doc-box">
                <div>
                    <h3>Dokumen Pendukung (Mock)</h3>
                    <p class="text-xs text-muted">Sistem otomatis menganggap dokumen valid untuk simulasi demo.</p>
                </div>
                <div class="form-group">
                    <label>Surat Keterangan Lahan & Izin (PDF)</label>
                    <input type="file" class="form-control" style="padding: 8px;">
                </div>
            </div>

            <button type="submit" class="btn-primary btn-full owner-submit-btn">Submit Proyek ke Verifikator</button>
        </form>
    </section>
</div>

<?php require_once '../includes/footer.php'; ?>
