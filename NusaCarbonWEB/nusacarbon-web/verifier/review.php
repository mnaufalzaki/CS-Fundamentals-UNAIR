<?php
// verifier/review.php
require_once '../includes/auth.php';
requireRole('verifier');
require_once '../includes/db.php';
require_once '../includes/helpers.php';
require_once '../includes/blockchain.php';

$id_project = $_GET['id'] ?? null;
if (!$id_project) {
    header("Location: queue.php"); exit;
}

$stmt = $pdo->prepare("SELECT p.*, c.nama_kategori FROM projects p JOIN project_categories c ON p.id_kategori = c.id_kategori WHERE p.id_project = ? AND p.status_project = 'submitted'");
$stmt->execute([$id_project]);
$project = $stmt->fetch();

if (!$project) {
    die("Proyek tidak ditemukan atau sudah diproses.");
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $hasil = $_POST['hasil']; // approve / reject
    $volume = $_POST['volume_co2e'] ?? 0;
    $default_price = (float)$pdo->query("SELECT COALESCE(AVG(harga_per_token), 5000) FROM listings WHERE status_listing = 'active'")->fetchColumn();
    if ($default_price <= 0) {
        $default_price = 5000;
    }
    
    // Simulate verifier approving triggers mint
    if ($hasil === 'approve') {
        $pdo->prepare("UPDATE projects SET status_project = 'verified' WHERE id_project = ?")->execute([$id_project]);
        // Insert mock token allocation
        $carbon_tokens_stmt = $pdo->prepare("INSERT INTO carbon_tokens (id_project, token_serial, vintage_year, status_token, owner_user_id) VALUES (?, ?, ?, 'available', ?)");
        $serial = generateTokenSerial(date('Y'), $id_project, rand(1,999));
        $carbon_tokens_stmt->execute([$id_project, $serial, date('Y'), $project['id_user']]);
        $id_token = $pdo->lastInsertId();
        
        // Append to blockchain
        $tx = appendToLedger($pdo, 'mint', $id_token, 'carbon_tokens', $volume, null, '0xProjectOwnerMock');
        $pdo->prepare("UPDATE carbon_tokens SET tx_mint_hash = ? WHERE id_token = ?")->execute([$tx, $id_token]);
        
        // Setup initial marketplace listing automatically for simulation
        $pdo->prepare("INSERT INTO listings (id_user, id_project, harga_per_token, jumlah_token) VALUES (?, ?, ?, ?)")->execute([$project['id_user'], $id_project, $default_price, $volume]);
    } else {
        $pdo->prepare("UPDATE projects SET status_project = 'rejected' WHERE id_project = ?")->execute([$id_project]);
    }

    header("Location: queue.php");
    exit;
}

require_once '../includes/header.php';
?>

<div class="dashboard-layout fade-up">
    <div class="dashboard-header">
        <a href="queue.php" class="text-sm text-muted hover-primary" style="display: block; margin-bottom: var(--space-xs);">&larr; Kembali ke Antrian</a>
        <h2 class="dashboard-title">Review Laporan MRV</h2>
        <p class="dashboard-subtitle">Evaluasi laporan pendaftaran proyek dan dMRV: <?= htmlspecialchars($project['nama_project']) ?></p>
    </div>

    <div class="split-layout">
        <div>
            <div class="card" style="margin-bottom: var(--space-md);">
                <h3>Detail Proyek</h3>
                <p><strong>Lokasi:</strong> <?= htmlspecialchars($project['lokasi']) ?></p>
                <p><strong>Luas Lahan:</strong> <?= number_format($project['luas_lahan'], 2, ',', '.') ?> Ha</p>
                <p><strong>Deskripsi:</strong><br><?= nl2br(htmlspecialchars($project['deskripsi'])) ?></p>
                
                <hr style="border: 0; border-top: 1px solid var(--color-border); margin: var(--space-md) 0;">
                
                <h3>Dokumen MRV Tersedia</h3>
                <ul style="list-style: none; padding: 0; display: flex; flex-direction: column; gap: var(--space-xs);">
                    <li><a href="#" style="display: flex; align-items: center; gap: 8px;"><i data-lucide="file-text" width="16"></i> Sertifikat Lahan & Izin.pdf</a></li>
                    <li><a href="#" style="display: flex; align-items: center; gap: 8px;"><i data-lucide="map" width="16"></i> Polygon Map.kml</a></li>
                </ul>
            </div>
        </div>

        <div>
            <div class="card">
                <h3>Keputusan Evaluasi</h3>
                <form method="POST">
                    <div class="form-group">
                        <label>Hasil Penilaian</label>
                        <select name="hasil" class="form-control" id="hasilPilihan" required>
                            <option value="">Pilih Keputusan</option>
                            <option value="approve">Setujui (Approve) & Minting</option>
                            <option value="reject">Tolak (Reject)</option>
                        </select>
                    </div>

                    <div class="form-group" id="volumeField" style="display: none;">
                        <label>Volume CO₂ Disetujui (tCO₂e)</label>
                        <input type="number" name="volume_co2e" class="form-control" placeholder="Volume dMRV">
                        <p class="text-xs text-muted" style="margin-top: 4px;">Angka ini akan di-mint menjadi supply carbon credits awal.</p>
                    </div>

                    <div class="form-group">
                        <label>Catatan Audit</label>
                        <textarea class="form-control" rows="3" required placeholder="Alasan keputusan..."></textarea>
                    </div>

                    <button type="submit" class="btn-primary btn-full" style="padding: 12px; margin-top: var(--space-md);">Konfirmasi Keputusan</button>
                    <p class="text-xs text-muted" style="text-align: center; margin-top: var(--space-sm);">Keputusan Approve akan memicu Smart Contract *Mint* di Blockchain.</p>
                </form>
            </div>
        </div>
    </div>
</div>

<script>
    document.getElementById('hasilPilihan').addEventListener('change', function(e) {
        document.getElementById('volumeField').style.display = (e.target.value === 'approve') ? 'block' : 'none';
        if(e.target.value === 'approve'){
           document.querySelector('input[name="volume_co2e"]').setAttribute('required', 'required');
        } else {
           document.querySelector('input[name="volume_co2e"]').removeAttribute('required');
        }
    });
</script>

<?php require_once '../includes/footer.php'; ?>
