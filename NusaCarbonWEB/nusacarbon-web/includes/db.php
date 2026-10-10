<?php
// includes/db.php

// Default: Docker lokal (sesuai docker-compose.yml)
$host = 'db';
$db = 'nusacarbon';
$user = 'nusa_user';
$pass = 'nusa_password';
$port = '3306';
$charset = 'utf8mb4';

$dbUrl = getenv('MYSQL_URL') ?: getenv('MYSQL_PUBLIC_URL') ?: getenv('DATABASE_URL');

// Parsing URL jika ada
if ($dbUrl) {
    $parsed = parse_url($dbUrl);
    if ($parsed) {
        $host = $parsed['host'] ?? $host;
        $port = $parsed['port'] ?? $port;
        $user = $parsed['user'] ?? $user;
        $pass = $parsed['pass'] ?? $pass;
        $db = ltrim($parsed['path'], '/') ?: $db;
    }
} else {
    // Cadangan: ambil dari individual variable jika ada
    $host = getenv('MYSQLHOST') ?: (isset($_SERVER['MYSQLHOST']) ? $_SERVER['MYSQLHOST'] : $host);
    $db = getenv('MYSQLDATABASE') ?: (isset($_SERVER['MYSQLDATABASE']) ? $_SERVER['MYSQLDATABASE'] : $db);
    $user = getenv('MYSQLUSER') ?: (isset($_SERVER['MYSQLUSER']) ? $_SERVER['MYSQLUSER'] : $user);
    $pass = getenv('MYSQLPASSWORD') ?: (isset($_SERVER['MYSQLPASSWORD']) ? $_SERVER['MYSQLPASSWORD'] : $pass);
    $port = getenv('MYSQLPORT') ?: (isset($_SERVER['MYSQLPORT']) ? $_SERVER['MYSQLPORT'] : $port);
}

$dsn = "mysql:host=$host;port=$port;dbname=$db;charset=$charset";
$options = [
    PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
    PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    PDO::ATTR_EMULATE_PREPARES => false,
];

try {
    $pdo = new PDO($dsn, $user, $pass, $options);
    
    // Auto-migrate schema for user feature request (IDR Balance & Token Tracking)
    // Each ALTER in its own try-catch so one failure doesn't skip the rest
    try { $pdo->exec("ALTER TABLE wallets ADD COLUMN saldo_rupiah DECIMAL(16,2) DEFAULT 1000000000.00"); } catch(Exception $e) {}
    try { $pdo->exec("UPDATE wallets SET saldo_rupiah = 1000000000.00 WHERE saldo_rupiah IS NULL"); } catch(Exception $e) {}
    try { $pdo->exec("ALTER TABLE trade_transactions ADD COLUMN jumlah_token INT AFTER total_harga"); } catch(Exception $e) {}

    // Auto-seed carbon_tokens if table is empty (tokens must exist for buy to work)
    try {
        $tokenCount = (int)$pdo->query("SELECT COUNT(*) FROM carbon_tokens")->fetchColumn();
        if ($tokenCount === 0) {
            // Get all active listings to seed tokens for
            $listings = $pdo->query(
                "SELECT l.id_project, l.jumlah_token, l.id_user, p.nama_project
                 FROM listings l JOIN projects p ON l.id_project = p.id_project
                 WHERE l.status_listing = 'active'"
            )->fetchAll();

            foreach ($listings as $listing) {
                $projectId = (int)$listing['id_project'];
                $ownerId   = (int)$listing['id_user'];
                $qty       = (int)$listing['jumlah_token'];
                $year      = (int)date('Y');

                // Batch insert in groups of 500
                $batchSize = 500;
                for ($i = 0; $i < $qty; $i += $batchSize) {
                    $values = [];
                    $params = [];
                    $batchEnd = min($i + $batchSize, $qty);
                    for ($j = $i; $j < $batchEnd; $j++) {
                        $seq = $j + 1;
                        $serial = sprintf('NC-%d-%03d-%06d', $year, $projectId, $seq);
                        $mintHash = '0x' . hash('sha256', "mint|{$projectId}|{$seq}|{$year}");
                        $metaHash = '0x' . hash('sha256', "meta|{$serial}");
                        $values[] = "(?, ?, ?, 'available', ?, ?, ?)";
                        array_push($params, $projectId, $serial, $year, $ownerId, $mintHash, $metaHash);
                    }
                    $sql = "INSERT INTO carbon_tokens (id_project, token_serial, vintage_year, status_token, owner_user_id, tx_mint_hash, metadata_hash) VALUES " . implode(',', $values);
                    $stmt = $pdo->prepare($sql);
                    $stmt->execute($params);
                }
            }
        }
    } catch(Exception $e) {
        // Silently fail seed — non-critical for page load
    }

} catch (\PDOException $e) {
    die("Database connection failed: " . $e->getMessage());
}
?>
