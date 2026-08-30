<?php
// test_fuentes_zh.php - Genera un PDF minúsculo comparando OTF vs TTF
// Ejecutar: php test_fuentes_zh.php
// Genera test_fuentes_zh.pdf en la misma carpeta

require_once __DIR__ . '/vendor/autoload.php';

use Dompdf\Dompdf;
use Dompdf\Options;

$options = new Options();
$options->set('isRemoteEnabled', true);
$options->set('isHtml5ParserEnabled', true);
$options->set('isFontSubsettingEnabled', true);
$options->set('chroot', __DIR__);

$dompdf = new Dompdf($options);

$html = <<<HTML
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
<style>
    body { font-size: 20px; }
    .otf { font-family: 'noto-sans-sc', sans-serif; margin-bottom: 20px; }
    .ttf { font-family: 'Noto Sans SC', sans-serif; margin-bottom: 20px; }
    .label { font-weight: bold; color: #333; font-size: 12px; }
</style>
</head>
<body>
    <div class="label">Usando 'noto-sans-sc' (OTF registrado hoy):</div>
    <div class="otf">制造商: 产品 商标 测试文字 中文</div>

    <div class="label">Usando 'Noto Sans SC' (TTF que ya existía):</div>
    <div class="ttf">制造商: 产品 商标 测试文字 中文</div>
</body>
</html>
HTML;

$dompdf->loadHtml($html, 'UTF-8');
$dompdf->setPaper('A4', 'portrait');
$dompdf->render();

file_put_contents(__DIR__ . '/test_fuentes_zh.pdf', $dompdf->output());
echo "PDF generado en: " . __DIR__ . "/test_fuentes_zh.pdf\n";