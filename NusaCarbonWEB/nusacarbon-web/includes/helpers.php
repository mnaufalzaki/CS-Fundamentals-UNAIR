<?php
// includes/helpers.php

function formatIDR(float $amount): string {
    return 'Rp ' . number_format($amount, 0, ',', '.');
}

function formatCO2e(float $amount, int $decimals = 0): string {
    return number_format($amount, $decimals, ',', '.') . ' tCO₂e';
}

function truncateHash(string $hash, int $prefixLen = 6, int $suffixLen = 4): string {
    if (strlen($hash) <= $prefixLen + $suffixLen + 3) return $hash;
    return substr($hash, 0, $prefixLen) . '...' . substr($hash, -$suffixLen);
}

function formatDate(string $datetime): string {
    $months = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des'];
    $d = new DateTime($datetime);
    return $d->format('d') . ' ' . $months[(int)$d->format('m') - 1] . ' ' . $d->format('Y');
}

function generateMockWalletAddress(): string {
    return '0x' . bin2hex(random_bytes(20));
}

function generateTokenSerial(int $year, int $projectId, int $seq): string {
    return sprintf('NC-%d-%03d-%06d', $year, $projectId, $seq);
}

function generateCertNumber(int $year, int $seq): string {
    return sprintf('CERT-NC-%d-%03d', $year, $seq);
}

function projectImageUrl(string $projectName, string $categoryName = '', int $projectId = 0): string {
    $haystack = strtolower($projectName . ' ' . $categoryName);

    if (str_contains($haystack, 'mangrove') || str_contains($haystack, 'blue carbon')) {
        return '/assets/img/projects/mangrove.svg';
    }
    if (str_contains($haystack, 'solar') || str_contains($haystack, 'surya')) {
        return '/assets/img/projects/solar.svg';
    }
    if (str_contains($haystack, 'wind') || str_contains($haystack, 'angin')) {
        return '/assets/img/projects/wind.svg';
    }
    if (str_contains($haystack, 'forest') || str_contains($haystack, 'hutan') || str_contains($haystack, 'rainforest')) {
        return '/assets/img/projects/rainforest.svg';
    }

    $fallbacks = [
        '/assets/img/projects/seedling.svg',
        '/assets/img/projects/rainforest.svg',
        '/assets/img/projects/mangrove.svg',
        '/assets/img/projects/solar.svg',
        '/assets/img/projects/wind.svg',
    ];

    return $fallbacks[abs($projectId) % count($fallbacks)];
}
?>
