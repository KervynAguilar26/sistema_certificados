<?php
// registrar_fuente_zh.php - Version diagnostica
// Ejecutar: php registrar_fuente_zh.php

require_once __DIR__ . '/vendor/autoload.php';

use Dompdf\Dompdf;
use Dompdf\Options;

$options = new Options();
$options->set('isRemoteEnabled', true);
$options->set('chroot', __DIR__);

$dompdf = new Dompdf($options);
$fontMetrics = $dompdf->getFontMetrics();

// --- Diagnóstico de rutas y permisos ---
echo "== Diagnóstico de entorno ==\n";
echo "Usuario que ejecuta este script: " . get_current_user() . " (uid " . getmyuid() . ")\n";
echo "Font dir (options): " . $options->getFontDir() . "\n";
echo "Font cache dir (options): " . (method_exists($options, 'getFontCache') ? $options->getFontCache() : 'N/A') . "\n";

$fontDir = $options->getFontDir();
echo "Existe font dir? " . (is_dir($fontDir) ? 'sí' : 'NO') . "\n";
echo "Es escribible el font dir? " . (is_writable($fontDir) ? 'sí' : 'NO') . "\n";
echo "Permisos font dir: " . substr(sprintf('%o', fileperms($fontDir)), -4) . "\n";
echo "Dueño font dir: ";
$ownerId = fileowner($fontDir);
$ownerInfo = function_exists('posix_getpwuid') ? posix_getpwuid($ownerId) : null;
echo $ownerInfo ? $ownerInfo['name'] : $ownerId;
echo "\n\n";

$regular = __DIR__ . '/fonts/wqy-zenhei.ttf';
$bold    = __DIR__ . '/fonts/wqy-zenhei.ttf'; // WQY Zen Hei no trae bold real; reutilizamos el regular

if (!file_exists($regular)) {
    die("ERROR: no se encontró " . $regular . ". Copia el archivo ahí primero.\n");
}
echo "Regular existe: sí (" . filesize($regular) . " bytes)\n";
echo "Bold existe: sí (" . filesize($bold) . " bytes)\n\n";

echo "== Registrando fuentes (con captura de errores) ==\n";

function intentarRegistro($fontMetrics, $style, $file, $label) {
    echo "-> $label: ";
    try {
        $result = $fontMetrics->registerFont($style, $file);
        echo $result ? "OK\n" : "FALSE (registerFont devolvió false)\n";
        return $result;
    } catch (\Throwable $e) {
        echo "EXCEPCIÓN: " . $e->getMessage() . "\n";
        echo "   en " . $e->getFile() . ":" . $e->getLine() . "\n";
        return false;
    }
}

intentarRegistro($fontMetrics, ['family' => 'wqy-zenhei', 'style' => 'normal', 'weight' => 'normal'], $regular, 'normal');
intentarRegistro($fontMetrics, ['family' => 'wqy-zenhei', 'style' => 'normal', 'weight' => 'bold'], $bold, 'bold');
intentarRegistro($fontMetrics, ['family' => 'wqy-zenhei', 'style' => 'italic', 'weight' => 'normal'], $regular, 'italic');
intentarRegistro($fontMetrics, ['family' => 'wqy-zenhei', 'style' => 'italic', 'weight' => 'bold'], $bold, 'bold_italic');

echo "\n== Resultado final ==\n";
$families = $fontMetrics->getFontFamilies();
if (isset($families['wqy-zenhei'])) {
    print_r($families['wqy-zenhei']);
} else {
    echo "⚠️ Sigue sin aparecer 'wqy-zenhei'.\n";
    echo "Familias disponibles actualmente:\n";
    print_r(array_keys($families));
}