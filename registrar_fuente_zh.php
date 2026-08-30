<?php
// registrar_fuente_zh.php - Ejecutar UNA sola vez desde la raíz del proyecto:
// php registrar_fuente_zh.php

require_once __DIR__ . '/vendor/autoload.php';

use Dompdf\Dompdf;
use Dompdf\Options;

$options = new Options();
$options->set('isRemoteEnabled', true);
$options->set('chroot', __DIR__);

$dompdf = new Dompdf($options);
$fontMetrics = $dompdf->getFontMetrics();

$regular = '/tmp/NotoSansSC-Regular.otf';
$bold    = '/tmp/NotoSansSC-Bold.otf';

if (!file_exists($regular) || !file_exists($bold)) {
    die("ERROR: no se encontraron los archivos .otf en /tmp. Verifica las rutas.\n");
}

echo "Registrando noto-sans-sc (normal)...\n";
$fontMetrics->registerFont(
    ['family' => 'noto-sans-sc', 'style' => 'normal', 'weight' => 'normal'],
    $regular
);

echo "Registrando noto-sans-sc (bold)...\n";
$fontMetrics->registerFont(
    ['family' => 'noto-sans-sc', 'style' => 'normal', 'weight' => 'bold'],
    $bold
);

echo "Registrando noto-sans-sc (italic, usando Regular como fallback)...\n";
$fontMetrics->registerFont(
    ['family' => 'noto-sans-sc', 'style' => 'italic', 'weight' => 'normal'],
    $regular
);

echo "Registrando noto-sans-sc (bold italic, usando Bold como fallback)...\n";
$fontMetrics->registerFont(
    ['family' => 'noto-sans-sc', 'style' => 'italic', 'weight' => 'bold'],
    $bold
);

echo "\n✅ Listo. Verifica que la familia quedó registrada:\n";
$families = $fontMetrics->getFontFamilies();
if (isset($families['noto-sans-sc'])) {
    print_r($families['noto-sans-sc']);
} else {
    echo "⚠️ No se encontró 'noto-sans-sc' en getFontFamilies(). Algo falló.\n";
}
