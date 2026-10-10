<?php
// includes/header.php
// Ensures session is started if not already
if (session_status() === PHP_SESSION_NONE) {
    session_start();
}
// Get current page name for active nav state
$current_page = basename($_SERVER['PHP_SELF']);
$role = $_SESSION['role'] ?? null;
?>
<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NusaCarbon - Transparent. Verified. Tokenized Carbon Credits.</title>
    
    <!-- Google Fonts: Inter & JetBrains Mono -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono&display=swap" rel="stylesheet">
    
    <!-- Assets -->
    <link rel="stylesheet" href="/assets/css/main.css">
    <link rel="stylesheet" href="/assets/css/components.css">
    <link rel="stylesheet" href="/assets/css/dashboard.css">

    <!-- Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>

    <!-- Lucide Icons -->
    <script src="https://cdn.jsdelivr.net/npm/lucide@latest/dist/umd/lucide.min.js"></script>
</head>
<body>

<?php if ($role): ?>
<nav class="navbar">
    <a href="/<?= htmlspecialchars($role) ?>/dashboard.php" class="logo">
        <div class="logo-icon">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-leaf" width="20" height="20">
                <path d="M11 20A7 7 0 0 1 9.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10Z"/>
                <path d="M2 22 12 12"/>
            </svg>
        </div>
        <span class="logo-wordmark">NusaCarbon</span>
    </a>

    <ul class="nav-links">
        <?php if ($role === 'buyer'): ?>
            <li><a href="/buyer/home.php" class="<?= $current_page == 'home.php' ? 'active' : '' ?>">Dashboard</a></li>
            <li><a href="/buyer/tokens.php" class="<?= $current_page == 'tokens.php' ? 'active' : '' ?>">Token Saya</a></li>
            <li><a href="/buyer/marketplace.php" class="<?= $current_page == 'marketplace.php' ? 'active' : '' ?>">Marketplace</a></li>
            <li><a href="/buyer/wallet.php" class="<?= $current_page == 'wallet.php' ? 'active' : '' ?>">Wallet</a></li>
        <?php elseif ($role === 'owner'): ?>
            <li><a href="/owner/dashboard.php" class="<?= $current_page == 'dashboard.php' ? 'active' : '' ?>">Dashboard</a></li>
            <li><a href="/owner/project-form.php" class="<?= $current_page == 'project-form.php' ? 'active' : '' ?>">Tambahkan Project</a></li>
            <li><a href="/owner/tokens.php" class="<?= $current_page == 'tokens.php' ? 'active' : '' ?>">Token Saya</a></li>
            <li><a href="/owner/wallet.php" class="<?= $current_page == 'wallet.php' ? 'active' : '' ?>">Wallet</a></li>
        <?php elseif ($role === 'verifier'): ?>
            <li><a href="/verifier/dashboard.php" class="<?= $current_page == 'dashboard.php' ? 'active' : '' ?>">Dashboard</a></li>
            <li><a href="/verifier/queue.php" class="<?= in_array($current_page, ['queue.php', 'review.php']) ? 'active' : '' ?>">Antrian Review</a></li>
        <?php elseif ($role === 'admin'): ?>
            <li><a href="/admin/dashboard.php" class="<?= $current_page == 'dashboard.php' ? 'active' : '' ?>">Dashboard</a></li>
        <?php endif; ?>
    </ul>

    <div class="nav-actions">
        <button class="btn-icon" title="Notifikasi"><i data-lucide="bell"></i></button>
        <a href="/logout.php" class="btn-outline btn-sm">Keluar</a>
    </div>
</nav>
<?php endif; ?>

<main class="container">
