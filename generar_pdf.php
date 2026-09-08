<?php
// generar_pdf.php - Versión con Traducción Total de Rangos y Ajuste de Hojas Limpio
require_once __DIR__ . '/vendor/autoload.php';
require_once __DIR__ . '/config/conexion.php';
require_once __DIR__ . '/config/traductor.php';
require_once __DIR__ . '/includes/qr_generator.php';
require_once 'includes/auth.php';

if (!esSuperAdmin()) {
    die("Acceso denegado: No posee permisos de Administrador para realizar esta operación.");
}

use Dompdf\Dompdf;
use Dompdf\Options;

$id   = $_GET['id']   ?? null;
$lang = $_GET['lang'] ?? 'es';

if (!$id) { die("Error: ID no especificado."); }

$stmt = $pdo->prepare("SELECT * FROM certificados WHERE id = :id");
$stmt->execute(['id' => $id]);
$cert = $stmt->fetch();

if (!$cert) { die("Error: Certificado no encontrado."); }

// TRADUCCIÓN COMPLETA DE CAMPOS
$tipoCertTrad   = traducirTexto($cert['tipo_certificado'] ?? 'CERTIFICATE OF COMPLIANCE', $lang);
$fabricanteTrad = traducirTexto($cert['fabricante'], $lang);
$dirFabTrad     = traducirTexto($cert['direccion_fabricante'] ?? '', $lang);
$productoTrad   = traducirTexto($cert['producto'], $lang);
$descProdTrad   = traducirTexto($cert['descripcion_producto'] ?? '', $lang);
$marcasTrad     = traducirTexto($cert['marcas'], $lang);
$paramTrad      = traducirTexto($cert['parametros_ensayo'] ?? '', $lang);
$normasTrad     = traducirTexto($cert['normas_ensayo'] ?? '', $lang);
$reporteTrad    = traducirTexto($cert['reporte_ensayo'] ?? '', $lang);

// ETIQUETAS FIJAS
$lblMfr    = traducirTexto('Fabricante:', $lang);
$lblProd   = traducirTexto('Producto:', $lang);
$lblBrand  = traducirTexto('Marca Comercial:', $lang);
$lblModels = traducirTexto('Modelo(s):', $lang);
$lblParams = traducirTexto('Parámetros de Ensayo:', $lang);
$lblTested = traducirTexto('Probado según norma:', $lang);
$lblReport = traducirTexto('Informe de ensayo N°:', $lang);
$lblValid  = traducirTexto('Validez:', $lang);
$lblIssue  = traducirTexto('Emisión', $lang);

$lblUntil  = ($lang === 'en') ? 'Expiry' : (($lang === 'zh') ? '到期日' : 'Vencimiento');
$lblAtt    = traducirTexto('ANEXO DE MODELOS CERTIFICADOS', $lang);
$lblLegal  = traducirTexto('El producto fue probado de forma voluntaria y cumple con los requisitos esenciales de calidad y seguridad.', $lang);

// PAGINACIÓN MULTILINGÜE
if ($lang === 'en') {
    $txtPageWord = 'Page';
    $txtOfWord   = 'of';
} elseif ($lang === 'zh') {
    $txtPageWord = '第';
    $txtOfWord   = '页 共';
} else {
    $txtPageWord = 'Página';
    $txtOfWord   = 'de';
}

// PROCESAMIENTO DE MODELOS
$modelos_raw = array_map('trim', explode(',', $cert['modelos_adjuntos']));
$modelos_array = [];
foreach ($modelos_raw as $mod) {
    if (!empty($mod) && strtolower($mod) !== 'modelos' && strtolower($mod) !== 'modelo') {
        $mod = str_replace(['<br>', '<br/>', '<br />'], '', $mod);
        $mod = trim($mod);
        if (!empty($mod)) {
            $modelos_array[] = $mod;
        }
    }
}

// CAPACIDAD POR HOJA DE ANEXO
$modelos_por_pagina = 270;
$total_modelos = count($modelos_array);

if ($total_modelos > 10) {
    $bloques_anexo = array_chunk($modelos_array, $modelos_por_pagina);
    $cant_paginas_anexo = count($bloques_anexo);
    $totalPaginasInt = 1 + $cant_paginas_anexo;
    $totalPaginas = str_pad($totalPaginasInt, 2, '0', STR_PAD_LEFT);

    if ($cant_paginas_anexo > 1) {
        $hastaPagina = $totalPaginasInt;
        if ($lang === 'zh') {
            $txtModels = "见附件(第2至{$hastaPagina}页)";
        } elseif ($lang === 'en') {
            $txtModels = "See Attached Annex (Pages 2 to {$hastaPagina})";
        } else {
            $txtModels = "Ver Anexo Adjunto (Páginas 2 a {$hastaPagina})";
        }
    } else {
        $txtModels = traducirTexto('Ver Anexo Adjunto (Página 2)', $lang);
    }
} else {
    $bloques_anexo = [];
    $totalPaginas = '01';
    $txtModels = implode(', ', $modelos_array);
}

function getBase64Img($path) {
    return file_exists($path) ? 'data:image/png;base64,' . base64_encode(file_get_contents($path)) : '';
}

$marcoPagina1 = getBase64Img(__DIR__ . '/assets/img/marco_dorado.png');
$marcoPagina2 = getBase64Img(__DIR__ . '/assets/img/marco_dorado 2.png');
$qrBase64     = getBase64Img(obtenerRutaQR($cert['token_verificacion']));

$options = new Options();
$options->set('isRemoteEnabled', true);
$options->set('isHtml5ParserEnabled', true);
$options->set('isFontSubsettingEnabled', true);
$options->set('defaultFont', 'sans-serif');
$options->set('chroot', __DIR__);

$dompdf = new Dompdf($options);

$fontFamily = ($lang === 'zh') ? "'wqy-zenhei', sans-serif" : "'Helvetica', 'Arial', sans-serif";
$lblScan    = ($lang === 'zh') ? '扫码验证' : (($lang === 'en') ? 'Scan to verify' : 'Escanear para verificar');

if (!empty($dirFabTrad)) {
    $dirFabTrad = str_replace(['<br>', '<br/>', '<br />'], ' ', $dirFabTrad);
}

ob_start();
?>
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8"/>
<style>
    @page { 
        margin: 0px; 
        size: A4 portrait;
    }

    body { 
        margin: 0px; 
        padding: 0px; 
        font-family: <?= $fontFamily ?>; 
        color: #0b2c5b; 
        font-size: 11px;
        line-height: 1.35;
    }

    .bg-frame { 
        position: fixed; 
        top: 0px; 
        left: 0px; 
        width: 210mm; 
        height: 297mm; 
        z-index: -1000; 
    }

    .page-1 {
        padding-top: 170px;
        padding-left: 80px;
        padding-right: 80px;
        box-sizing: border-box;
    }

    .page-anexo {
        page-break-before: always;
        padding-top: 150px;
        padding-left: 80px;
        padding-right: 80px;
        box-sizing: border-box;
    }

    .subtitle-type { 
        font-size: 19px; 
        font-weight: bold; 
        color: #c5a059; 
        text-align: center; 
        margin-bottom: 4px; 
        text-transform: uppercase; 
        line-height: 1.25;
    }
    
    .cert-no { 
        font-size: 13.5px; 
        font-weight: bold; 
        color: #0b2c5b; 
        text-align: center; 
        margin-bottom: 14px; 
    }

    .data-table { 
        width: 100%; 
        border-collapse: collapse; 
        table-layout: fixed;
    }
    
    .data-table td { 
        padding: 3.5px 0; 
        font-size: 11px; 
        vertical-align: top; 
        line-height: 1.35; 
        word-wrap: break-word;
        overflow-wrap: break-word;
        text-align: left;
    }
    
    .lbl { 
        font-weight: bold; 
        color: #0b2c5b; 
        width: 32%; 
        padding-right: 8px;
    }

    .dir-address {
        color: #475569;
        font-size: 9.5px;
        line-height: 1.25;
        display: block;
        margin-top: 2px;
    }

    .legal-text {
        font-size: 8.5px;
        color: #475569;
        text-align: justify;
        margin-top: 12px;
        line-height: 1.3;
    }

    .models-box {
        width: 100%;
        font-size: 10px; 
        line-height: 1.5; 
        color: #1e293b; 
        text-align: justify;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }

    .models-title {
        font-size: 11px;
        font-weight: bold;
        color: #0b2c5b;
        display: block;
        margin-bottom: 6px;
    }

    .footer-container {
        position: absolute;
        bottom: 120px;
        left: 80px;
        right: 80px;
        height: 75px;
    }

    .qr-box { 
        float: right;
        width: 110px; 
        text-align: center;
        margin-top: -25px; 
    }
    
    .qr-img { 
        width: 100px; 
        height: 100px; 
        display: block;
        margin: 0 auto;
    }

    .page-num { 
        float: left;
        margin-top: 45px;
        font-size: 8.5px; 
        color: #ec0a0a; 
        font-weight: bold;
    }
</style>
</head>
<body>

<!-- PÁGINA 1 -->
<div class="page-1">
    <?php if ($marcoPagina1): ?>
        <img src="<?= $marcoPagina1 ?>" class="bg-frame">
    <?php endif; ?>

    <div class="subtitle-type"><?= htmlspecialchars($tipoCertTrad, ENT_QUOTES, 'UTF-8') ?></div>
    <div class="cert-no">No. <?= htmlspecialchars($cert['codigo_certificado'], ENT_QUOTES, 'UTF-8') ?></div>

    <table class="data-table">
        <tr>
            <td class="lbl"><?= htmlspecialchars($lblMfr, ENT_QUOTES, 'UTF-8') ?></td>
            <td>
                <b><?= htmlspecialchars($fabricanteTrad, ENT_QUOTES, 'UTF-8') ?></b>
                <?php if (!empty($dirFabTrad)): ?>
                    <br><span class="dir-address"><?= htmlspecialchars($dirFabTrad, ENT_QUOTES, 'UTF-8') ?></span>
                <?php endif; ?>
            </td>
        </tr>
        <tr>
            <td class="lbl"><?= htmlspecialchars($lblProd, ENT_QUOTES, 'UTF-8') ?></td>
            <td><b><?= htmlspecialchars($productoTrad, ENT_QUOTES, 'UTF-8') ?></b></td>
        </tr>
        <tr>
            <td class="lbl"><?= htmlspecialchars($lblBrand, ENT_QUOTES, 'UTF-8') ?></td>
            <td><?= htmlspecialchars($marcasTrad, ENT_QUOTES, 'UTF-8') ?></td>
        </tr>
        <tr>
            <td class="lbl"><?= htmlspecialchars($lblModels, ENT_QUOTES, 'UTF-8') ?></td>
            <td><?= htmlspecialchars($txtModels, ENT_QUOTES, 'UTF-8') ?></td>
        </tr>

        <?php if (($cert['mostrar_parametros'] ?? 'SI') === 'SI' && !empty($paramTrad)): ?>
        <tr>
            <td class="lbl"><?= htmlspecialchars($lblParams, ENT_QUOTES, 'UTF-8') ?></td>
            <td><?= htmlspecialchars($paramTrad, ENT_QUOTES, 'UTF-8') ?></td>
        </tr>
        <?php endif; ?>

        <tr>
            <td class="lbl"><?= htmlspecialchars($lblTested, ENT_QUOTES, 'UTF-8') ?></td>
            <td><?= htmlspecialchars($normasTrad, ENT_QUOTES, 'UTF-8') ?></td>
        </tr>
        <tr>
            <td class="lbl"><?= htmlspecialchars($lblReport, ENT_QUOTES, 'UTF-8') ?></td>
            <td><?= htmlspecialchars($reporteTrad, ENT_QUOTES, 'UTF-8') ?></td>
        </tr>
        <tr>
            <td class="lbl"><?= htmlspecialchars($lblValid, ENT_QUOTES, 'UTF-8') ?></td>
            <td><?= htmlspecialchars($lblIssue, ENT_QUOTES, 'UTF-8') ?>: <?= htmlspecialchars($cert['fecha_emision']) ?> | <?= htmlspecialchars($lblUntil, ENT_QUOTES, 'UTF-8') ?>: <?= htmlspecialchars($cert['fecha_expiracion']) ?></td>
        </tr>

        <?php if (!empty($descProdTrad)): ?>
        <tr>
            <td colspan="2" style="font-size: 9.5px; color: #334155; padding-top: 6px; line-height: 1.3;">
                <?= nl2br(htmlspecialchars($descProdTrad, ENT_QUOTES, 'UTF-8')) ?>
            </td>
        </tr>
        <?php endif; ?>
    </table>

    <div class="legal-text">
        <?= htmlspecialchars($lblLegal, ENT_QUOTES, 'UTF-8') ?>
    </div>

    <div class="footer-container">
        <div class="page-num">
            <?php if ($lang === 'zh'): ?>
                <?= "{$txtPageWord} 01 {$txtOfWord} {$totalPaginas} 页" ?>
            <?php else: ?>
                <?= "{$txtPageWord} 01 {$txtOfWord} {$totalPaginas}" ?>
            <?php endif; ?>
        </div>

        <div class="qr-box">
            <?php if (!empty($qrBase64)): ?>
                <img src="<?= $qrBase64 ?>" class="qr-img"><br>
            <?php endif; ?>
            <span style="font-size: 6.5px; color: #64748b; font-weight: bold;"><?= htmlspecialchars($lblScan, ENT_QUOTES, 'UTF-8') ?></span>
        </div>
    </div>
</div>

<!-- PÁGINAS DE ANEXO -->
<?php if (!empty($bloques_anexo)): ?>
    <?php foreach ($bloques_anexo as $index => $bloque_modelos): ?>
        <?php 
            $numPaginaActualInt = 2 + $index;
            $numPaginaActual = str_pad($numPaginaActualInt, 2, '0', STR_PAD_LEFT);
            $string_bloque = implode(', ', $bloque_modelos);
        ?>
        <div class="page-anexo">
            <?php if ($marcoPagina2): ?>
                <img src="<?= $marcoPagina2 ?>" class="bg-frame">
            <?php endif; ?>

            <div style="text-align: center; margin-bottom: 14px;">
                <div style="font-size: 15px; font-weight: bold; color: #0b2c5b; text-transform: uppercase;"><?= htmlspecialchars($lblAtt, ENT_QUOTES, 'UTF-8') ?></div>
                <div style="font-size: 12px; font-weight: bold; color: #c5a059; margin-top: 2px;">Certificate No. <?= htmlspecialchars($cert['codigo_certificado'], ENT_QUOTES, 'UTF-8') ?></div>
            </div>

            <div class="models-box">
                <span class="models-title"><?= htmlspecialchars(traducirTexto('Lista de Modelos Certificados:', $lang), ENT_QUOTES, 'UTF-8') ?></span>
                <?= htmlspecialchars($string_bloque, ENT_QUOTES, 'UTF-8') ?>
            </div>

            <div class="footer-container">
                <div class="page-num">
                    <?php if ($lang === 'zh'): ?>
                        <?= "{$txtPageWord} {$numPaginaActual} {$txtOfWord} {$totalPaginas} 页 - S-" . htmlspecialchars($cert['codigo_certificado'], ENT_QUOTES, 'UTF-8') ?>
                    <?php else: ?>
                        <?= "{$txtPageWord} {$numPaginaActual} {$txtOfWord} {$totalPaginas} - S-" . htmlspecialchars($cert['codigo_certificado'], ENT_QUOTES, 'UTF-8') ?>
                    <?php endif; ?>
                </div>
            </div>
        </div>
    <?php endforeach; ?>
<?php endif; ?>

</body>
</html>
<?php
$html = ob_get_clean();

if ($lang === 'zh') {
    ini_set('memory_limit', '512M');
    set_time_limit(120);
}

$dompdf->loadHtml($html, 'UTF-8');
$dompdf->setPaper('A4', 'portrait');
$dompdf->render();
$dompdf->stream("Certificado_" . $cert['codigo_certificado'] . "_" . strtoupper($lang) . ".pdf", ["Attachment" => false]);
exit;
?>