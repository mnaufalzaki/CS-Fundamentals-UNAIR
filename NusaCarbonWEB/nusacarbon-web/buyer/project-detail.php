<?php
// buyer/project-detail.php
require_once '../includes/auth.php';
requireRole('buyer');

require_once '../includes/db.php';
require_once '../includes/helpers.php';
require_once '../includes/blockchain.php';

$id_project = $_GET['id'] ?? null;

if (!$id_project) {
    header("Location: marketplace.php");
    exit;
}

$stmt = $pdo->prepare("
    SELECT p.*, l.harga_per_token, l.jumlah_token, c.nama_kategori 
    FROM projects p
    JOIN listings l ON p.id_project = l.id_project
    JOIN project_categories c ON p.id_kategori = c.id_kategori
    WHERE p.id_project = ? AND l.status_listing = 'active'
");
$stmt->execute([$id_project]);
$project = $stmt->fetch();

if (!$project) {
    die("Proyek tidak ditemukan atau tidak aktif.");
}

require_once '../includes/header.php';
?>

<div class="dashboard-layout fade-up">
    <div style="margin-bottom: var(--space-md);">
        <a href="marketplace.php" class="text-sm text-muted hover-primary">&larr; Kembali ke Marketplace</a>
    </div>

    <!-- Split Layout Desktop (2/3 + 1/3) -->
    <div class="split-layout">
        
        <!-- Left Col: Details -->
        <div class="project-details">
            <div class="card" style="padding: 0; overflow: hidden; margin-bottom: var(--space-xl);">
                <img
                    src="<?= htmlspecialchars(projectImageUrl($project['nama_project'], $project['nama_kategori'], (int)$project['id_project'])) ?>"
                    alt="Visual proyek <?= htmlspecialchars($project['nama_project']) ?>"
                    style="width: 100%; height: 260px; display: block; object-fit: cover;"
                >
                <div style="padding: var(--space-lg);">
                    <div style="display: flex; gap: var(--space-sm); align-items: center; margin-bottom: var(--space-sm);">
                        <span class="badge badge-cat-<?= strtolower(strtok($project['nama_kategori'], " ")) ?>"><?= htmlspecialchars($project['nama_kategori']) ?></span>
                        <span class="badge badge--verified"><i data-lucide="check-circle" width="12"></i> Verified</span>
                    </div>
                    <h1 style="margin: 0 0 var(--space-xs) 0; font-size: var(--text-2xl);"><?= htmlspecialchars($project['nama_project']) ?></h1>
                    <p class="text-muted" style="display: flex; align-items: center; gap: 4px;">
                        <i data-lucide="map-pin" width="16"></i> <?= htmlspecialchars($project['lokasi']) ?> &nbsp;&bull;&nbsp; Luas Lahan: <?= number_format($project['luas_lahan'], 2, ',', '.') ?> Ha
                    </p>
                    
                    <hr style="border: 0; border-top: 1px solid var(--color-border); margin: var(--space-lg) 0;">
                    
                    <h3>Deskripsi Proyek</h3>
                    <p><?= nl2br(htmlspecialchars($project['deskripsi'])) ?></p>

                    <h3 style="margin-top: var(--space-xl);">Data MRV Terbaru</h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-md); background: var(--color-bg); padding: var(--space-md); border-radius: var(--radius-md);">
                        <div>
                            <p class="text-xs text-muted" style="margin:0;">Periode</p>
                            <p style="font-weight: 500; margin:0;">Q4 2025</p>
                        </div>
                        <div>
                            <p class="text-xs text-muted" style="margin:0;">Koordinat</p>
                            <p style="font-family: var(--font-mono); font-size: var(--text-sm); margin:0;">-0.7892, 113.9213</p>
                        </div>
                        <div style="grid-column: 1 / -1;">
                            <a href="#" class="btn-outline btn-sm" style="display: inline-flex;"><i data-lucide="external-link" width="14"></i> Lihat Citra Satelit</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Right Col: Buy Widget (Sticky on Desktop) -->
        <div style="position: sticky; top: 90px;">
            <div class="card buy-widget">
                <h3 style="margin-top: 0;">Beli Token</h3>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: var(--space-lg);">
                    <span class="text-muted">Harga per tCO₂e</span>
                    <strong style="font-size: var(--text-lg);"><?= formatIDR($project['harga_per_token']) ?></strong>
                </div>
                
                <form id="buyForm" action="/api/buy-token.php" method="POST">
                    <input type="hidden" name="id_project" value="<?= $id_project ?>">
                     <input type="hidden" name="harga_per_token" id="hargaPerToken" value="<?= $project['harga_per_token'] ?>">
                    
                    <div class="form-group">
                        <label>Jumlah Token</label>
                        <div style="position: relative;">
                            <input type="number" name="jumlah_token" id="qty" class="form-control" min="1" max="<?= $project['jumlah_token'] ?>" placeholder="10" required>
                            <span style="position: absolute; right: 14px; top: 10px; color: var(--color-text-muted); pointer-events: none; font-size: var(--text-sm);">tCO₂e</span>
                        </div>
                        <p class="text-xs text-muted" style="margin-top: 4px; text-align: right;">Sisa: <?= formatCO2e($project['jumlah_token']) ?></p>
                    </div>

                    <div style="background: var(--color-bg); padding: var(--space-md); border-radius: var(--radius-md); margin-bottom: var(--space-lg);">
                        <div style="display: flex; justify-content: space-between; margin-bottom: var(--space-xs);">
                            <span class="text-sm">Subtotal</span>
                            <span class="text-sm font-semibold" id="subtotal">Rp 0</span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: var(--space-md);">
                            <span class="text-sm text-muted">Gas Fee (simulated)</span>
                            <span class="text-sm font-mono text-muted">~<span id="gasFee">0.004</span> ETH</span>
                        </div>
                        <div style="border-top: 1px dashed var(--color-border); padding-top: var(--space-sm); display: flex; justify-content: space-between;">
                            <strong>Total</strong>
                            <strong style="color: var(--color-primary);" id="total">Rp 0</strong>
                        </div>
                    </div>

                    <button type="button" onclick="confirmBuy()" class="btn-primary btn-full" style="padding: 14px;">Beli Token Sekarang</button>
                    <p class="text-xs text-muted" style="text-align: center; margin-top: var(--space-md);">* Transaksi ini adalah simulasi mock. Tidak ada tagihan nyata.</p>
                </form>
            </div>
        </div>

    </div>
</div>

<!-- Mock Success Modal Form Post Target handled gracefully via JS -->
<div class="toast-container"></div>

<script>
    const price = parseInt(document.getElementById('hargaPerToken').value);
    const qtyInput = document.getElementById('qty');
    const subtotalEl = document.getElementById('subtotal');
    const totalEl = document.getElementById('total');

    function updateCalc() {
        const qty = parseInt(qtyInput.value) || 0;
        const subtotal = qty * price;
        subtotalEl.textContent = formatIDRLocale(subtotal);
        totalEl.textContent = formatIDRLocale(subtotal);
        document.getElementById('gasFee').textContent = mockGasFee();
    }

    qtyInput.addEventListener('input', updateCalc);

    function confirmBuy() {
        const qty = parseInt(qtyInput.value);
        if(!qty || qty <= 0) {
            showToast('Silakan masukkan jumlah token yang valid.', 'error');
            return;
        }

        // Disable button while processing
        const buyBtn = document.querySelector('#buyForm button[type="button"]');
        buyBtn.disabled = true;
        buyBtn.textContent = 'Memproses...';

        showToast('Transaksi diproses dengan Smart Contract...', 'info');

        // Actually POST to the API
        const formData = new FormData(document.getElementById('buyForm'));

        fetch('/api/buy-token.php', {
            method: 'POST',
            body: formData
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                showToast('Pembelian berhasil! Tx: ' + (data.tx_hash ? data.tx_hash.substring(0, 10) + '...' : ''), 'success');
                // Reset form and update display
                qtyInput.value = '';
                updateCalc();
                // Redirect to wallet after short delay
                setTimeout(() => {
                    window.location.href = 'wallet.php';
                }, 2000);
            } else {
                showToast('Gagal: ' + (data.error || 'Unknown error'), 'error');
            }
        })
        .catch(err => {
            showToast('Network error: ' + err.message, 'error');
        })
        .finally(() => {
            buyBtn.disabled = false;
            buyBtn.textContent = 'Beli Token Sekarang';
        });
    }
</script>

<?php require_once '../includes/footer.php'; ?>
