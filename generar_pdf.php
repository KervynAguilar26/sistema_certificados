<?php
// generar_pdf.php - Versión Con Maquetación Nativa Limpia para Evitar Desplazamientos
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

// TRADUCCIÓN AUTOMÁTICA DE CAMPOS
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
    $txtOfWord   = '页/共';
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

$mostrar_anexo   = count($modelos_array) > 10;
$totalPaginas    = $mostrar_anexo ? '02' : '01';
$string_modelos  = implode(', ', $modelos_array);
$txtModels       = $mostrar_anexo ? traducirTexto('Ver Anexo Adjunto (Página 2)', $lang) : $string_modelos;

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

// FUENTE OPTIMIZADA PARA CHINO
if ($lang === 'zh') {
    $fontFamily = "'Noto Sans SC', 'Source Han Sans SC', 'WenQuanYi Micro Hei', 'SimSun', 'STSong', 'DejaVu Sans', sans-serif";
    $fontSizeBase = '10px';
    $fontSizeSmall = '8px';
    $fontSizeSmaller = '6.5px';
    $lineHeight = '1.4';
    $labelWidth = '22%';
    $pagePadding = '85px';
    $footerBottom = '85px';
    $qrSize = '55px';
} else {
    $fontFamily = "'Helvetica', 'Arial', 'DejaVu Sans', sans-serif";
    $fontSizeBase = '11px';
    $fontSizeSmall = '9px';
    $fontSizeSmaller = '6.5px';
    $lineHeight = '1.3';
    $labelWidth = '32%';
    $pagePadding = '80px';
    $footerBottom = '110px';
    $qrSize = '70px';
}

$lblScan    = ($lang === 'zh') ? '扫码验证' : (($lang === 'en') ? 'Scan to verify' : 'Escanear para verificar');

// Limpiar dirección para chino
if ($lang === 'zh' && !empty($dirFabTrad)) {
    $dirFabTrad = str_replace(['<br>', '<br/>', '<br />'], ' ', $dirFabTrad);
    if (strlen($dirFabTrad) > 35) {
        $dirFabTrad = wordwrap($dirFabTrad, 30, '<br>', true);
    }
}

// Dividir modelos en columnas para mejor visualización en chino
$modelos_tabla = [];
if ($lang === 'zh' && $mostrar_anexo) {
    $modelos_tabla = array_chunk($modelos_array, 5);
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
        font-size: <?= $fontSizeBase ?>;
        line-height: <?= $lineHeight ?>;
    }

    /* CAPA DE MARCO DE FONDO FIJA */
    .bg-frame { 
        position: fixed; 
        top: 0px; 
        left: 0px; 
        width: 210mm; 
        height: 297mm; 
        z-index: -1000; 
    }

    .page-1 {
        padding-top: 175px;
        padding-left: <?= $pagePadding ?>;
        padding-right: <?= $pagePadding ?>;
        page-break-after: always;
    }

    .page-2 {
        padding-top: 150px;
        padding-left: <?= $pagePadding ?>;
        padding-right: <?= $pagePadding ?>;
    }

    .subtitle-type { 
        font-size: <?= ($lang === 'zh') ? '16px' : '20px' ?>;
        font-weight: bold; 
        color: #c5a059; 
        text-align: center; 
        margin-bottom: 2px; 
        text-transform: uppercase; 
        line-height: 1.3;
        letter-spacing: <?= ($lang === 'zh') ? '4px' : 'normal' ?>;
        word-break: keep-all;
    }
    
    .cert-no { 
        font-size: <?= ($lang === 'zh') ? '12px' : '16px' ?>;
        font-weight: bold; 
        color: #0b2c5b; 
        text-align: center; 
        margin-bottom: 14px; 
        letter-spacing: <?= ($lang === 'zh') ? '0.5px' : 'normal' ?>;
        word-break: keep-all;
    }

    .data-table { 
        width: 100%; 
        border-collapse: collapse; 
        table-layout: fixed;
    }
    
    .data-table td { 
        padding: <?= ($lang === 'zh') ? '2.5px 0' : '3px 0' ?>;
        font-size: <?= ($lang === 'zh') ? '9.5px' : '11px' ?>;
        vertical-align: top; 
        line-height: <?= ($lang === 'zh') ? '1.5' : '1.3' ?>; 
        word-wrap: break-word;
        overflow-wrap: break-word;
        word-break: break-word;
        text-align: left;
    }
    
    .lbl { 
        font-weight: bold; 
        color: #0b2c5b; 
        width: <?= $labelWidth ?>;
        font-size: <?= ($lang === 'zh') ? '9.5px' : '11px' ?>;
        white-space: <?= ($lang === 'zh') ? 'normal' : 'nowrap' ?>;
        padding-right: 8px;
        word-break: keep-all;
    }

    .lbl-value {
        font-size: <?= ($lang === 'zh') ? '9.5px' : '11px' ?>;
        word-break: break-word;
    }

    .dir-address {
        color: #475569;
        font-size: <?= ($lang === 'zh') ? '7px' : '9px' ?>;
        line-height: 1.3;
        display: block;
        margin-top: 2px;
        word-break: break-word;
    }

    .legal-text {
        font-size: <?= ($lang === 'zh') ? '7.5px' : '8.5px' ?>;
        color: #475569;
        text-align: justify;
        margin-top: 14px;
        line-height: <?= ($lang === 'zh') ? '1.4' : '1.3' ?>;
        word-break: break-word;
    }

    /* TABLA DE MODELOS PARA CHINO */
    .models-table {
        width: 100%;
        border-collapse: collapse;
        margin-top: 5px;
        font-size: <?= ($lang === 'zh') ? '8px' : '10px' ?>;
    }
    
    .models-table td {
        padding: <?= ($lang === 'zh') ? '2px 4px' : '3px 5px' ?>;
        vertical-align: top;
        font-size: <?= ($lang === 'zh') ? '8px' : '10px' ?>;
        line-height: <?= ($lang === 'zh') ? '1.7' : '1.5' ?>;
        word-break: break-word;
        border: none;
    }

    .models-title {
        font-size: <?= ($lang === 'zh') ? '10px' : '11px' ?>;
        font-weight: bold;
        color: #0b2c5b;
        display: block;
        margin-bottom: 4px;
        word-break: keep-all;
    }

    /* PIE DE PÁGINA FLOTANTE EN POSICIÓN ABSOLUTA LIMPIA */
    .footer-container {
        position: absolute;
        bottom: <?= $footerBottom ?>;
        left: <?= $pagePadding ?>;
        right: <?= $pagePadding ?>;
        height: 80px;
    }

    .qr-box { 
        float: right;
        width: <?= ($lang === 'zh') ? '75px' : '90px' ?>;
        text-align: center; 
    }
    
    .qr-img { 
        width: <?= $qrSize ?>;
        height: <?= $qrSize ?>;
        display: block;
        margin: 0 auto;
    }

    .page-num { 
        float: left;
        margin-top: <?= ($lang === 'zh') ? '35px' : '50px' ?>;
        font-size: <?= ($lang === 'zh') ? '7.5px' : '8.5px' ?>;
        color: #ec0a0a; 
        font-weight: bold;
        word-break: keep-all;
    }

    /* AJUSTES ESPECÍFICOS PARA CHINO */
    <?php if ($lang === 'zh'): ?>
    .page-1 {
        padding-top: 160px;
        padding-left: 85px;
        padding-right: 85px;
    }
    .page-2 {
        padding-top: 140px;
        padding-left: 85px;
        padding-right: 85px;
    }
    .footer-container {
        left: 85px;
        right: 85px;
        bottom: 75px;
    }
    .data-table td {
        font-size: 9.5px;
        padding: 2.5px 0;
    }
    .data-table td.lbl {
        font-size: 9.5px;
        width: 20%;
        padding-right: 6px;
    }
    .data-table td:not(.lbl) {
        font-size: 9.5px;
    }
    .cert-no {
        font-size: 12px;
        letter-spacing: 0.5px;
    }
    .subtitle-type {
        font-size: 16px;
        letter-spacing: 4px;
    }
    .page-num {
        font-size: 7.5px;
        margin-top: 30px;
    }
    .qr-box {
        width: 65px;
    }
    .qr-img {
        width: 50px;
        height: 50px;
    }
    .models-table td {
        font-size: 8px;
        padding: 2px 4px;
        line-height: 1.7;
    }
    .models-title {
        font-size: 10px;
    }
    .legal-text {
        font-size: 7.5px;
        margin-top: 12px;
    }
    <?php endif; ?>
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
            <td class="lbl-value">
                <b><?= htmlspecialchars($fabricanteTrad, ENT_QUOTES, 'UTF-8') ?></b>
                <?php if (!empty($dirFabTrad)): ?>
                    <br><span class="dir-address"><?= htmlspecialchars($dirFabTrad, ENT_QUOTES, 'UTF-8') ?></span>
                <?php endif; ?>
            </td>
        </tr>
        <tr>
            <td class="lbl"><?= htmlspecialchars($lblProd, ENT_QUOTES, 'UTF-8') ?></td>
            <td class="lbl-value"><b><?= htmlspecialchars($productoTrad, ENT_QUOTES, 'UTF-8') ?></b></td>
        </tr>
        <tr>
            <td class="lbl"><?= htmlspecialchars($lblBrand, ENT_QUOTES, 'UTF-8') ?></td>
            <td class="lbl-value"><?= htmlspecialchars($marcasTrad, ENT_QUOTES, 'UTF-8') ?></td>
        </tr>
        <tr>
            <td class="lbl"><?= htmlspecialchars($lblModels, ENT_QUOTES, 'UTF-8') ?></td>
            <td class="lbl-value"><?= htmlspecialchars($txtModels, ENT_QUOTES, 'UTF-8') ?></td>
        </tr>

        <?php if (($cert['mostrar_parametros'] ?? 'SI') === 'SI' && !empty($paramTrad)): ?>
        <tr>
            <td class="lbl"><?= htmlspecialchars($lblParams, ENT_QUOTES, 'UTF-8') ?></td>
            <td class="lbl-value"><?= htmlspecialchars($paramTrad, ENT_QUOTES, 'UTF-8') ?></td>
        </tr>
        <?php endif; ?>

        <tr>
            <td class="lbl"><?= htmlspecialchars($lblTested, ENT_QUOTES, 'UTF-8') ?></td>
            <td class="lbl-value"><?= htmlspecialchars($normasTrad, ENT_QUOTES, 'UTF-8') ?></td>
        </tr>
        <tr>
            <td class="lbl"><?= htmlspecialchars($lblReport, ENT_QUOTES, 'UTF-8') ?></td>
            <td class="lbl-value"><?= htmlspecialchars($reporteTrad, ENT_QUOTES, 'UTF-8') ?></td>
        </tr>
        <tr>
            <td class="lbl"><?= htmlspecialchars($lblValid, ENT_QUOTES, 'UTF-8') ?></td>
            <td class="lbl-value"><?= htmlspecialchars($lblIssue, ENT_QUOTES, 'UTF-8') ?>: <?= htmlspecialchars($cert['fecha_emision']) ?> | <?= htmlspecialchars($lblUntil, ENT_QUOTES, 'UTF-8') ?>: <?= htmlspecialchars($cert['fecha_expiracion']) ?></td>
        </tr>

        <?php if (!empty($descProdTrad)): ?>
        <tr>
            <td colspan="2" style="font-size: <?= ($lang === 'zh') ? '7.5px' : '9px' ?>; color: #334155; padding-top: 6px; line-height: <?= ($lang === 'zh') ? '1.4' : '1.3' ?>;">
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
                <?= "{$txtPageWord}01{$txtOfWord}{$totalPaginas}页" ?>
            <?php else: ?>
                <?= "{$txtPageWord} 01 {$txtOfWord} {$totalPaginas}" ?>
            <?php endif; ?>
        </div>

        <div class="qr-box">
            <?php if (!empty($qrBase64)): ?>
                <img src="<?= $qrBase64 ?>" class="qr-img"><br>
            <?php endif; ?>
            <span style="font-size: <?= ($lang === 'zh') ? '6px' : '6.5px' ?>; color: #64748b; font-weight: bold;"><?= htmlspecialchars($lblScan, ENT_QUOTES, 'UTF-8') ?></span>
        </div>
    </div>
</div>

<!-- PÁGINA 2 (ANEXO DE MODELOS) -->
<?php if ($mostrar_anexo): ?>
<div class="page-2">
    <?php if ($marcoPagina2): ?>
        <img src="<?= $marcoPagina2 ?>" class="bg-frame">
    <?php endif; ?>

    <div style="text-align: center; margin-bottom: 14px;">
        <div style="font-size: <?= ($lang === 'zh') ? '13px' : '15px' ?>; font-weight: bold; color: #0b2c5b; text-transform: uppercase; letter-spacing: <?= ($lang === 'zh') ? '3px' : 'normal' ?>; word-break: keep-all;"><?= htmlspecialchars($lblAtt, ENT_QUOTES, 'UTF-8') ?></div>
        <div style="font-size: <?= ($lang === 'zh') ? '9px' : '12px' ?>; font-weight: bold; color: #c5a059; margin-top: 2px; word-break: keep-all;">Certificate No. <?= htmlspecialchars($cert['codigo_certificado'], ENT_QUOTES, 'UTF-8') ?></div>
    </div>

    <?php if ($lang === 'zh' && !empty($modelos_tabla)): ?>
        <!-- TABLA DE MODELOS PARA CHINO -->
        <span class="models-title"><?= htmlspecialchars(traducirTexto('Lista de Modelos Certificados:', $lang), ENT_QUOTES, 'UTF-8') ?></span>
        <table class="models-table">
            <?php foreach ($modelos_tabla as $fila): ?>
                <tr>
                    <?php foreach ($fila as $modelo): ?>
                        <td><?= htmlspecialchars($modelo, ENT_QUOTES, 'UTF-8') ?></td>
                    <?php endforeach; ?>
                </tr>
            <?php endforeach; ?>
        </table>
    <?php else: ?>
        <!-- VISTA NORMAL PARA OTROS IDIOMAS -->
        <div class="models-box">
            <span class="models-title"><?= htmlspecialchars(traducirTexto('Lista de Modelos Certificados:', $lang), ENT_QUOTES, 'UTF-8') ?></span>
            <span style="font-size: <?= ($lang === 'zh') ? '8px' : '10px' ?>; line-height: <?= ($lang === 'zh') ? '1.8' : '1.5' ?>; word-break: break-word;"><?= htmlspecialchars($string_modelos, ENT_QUOTES, 'UTF-8') ?></span>
        </div>
    <?php endif; ?>

    <div class="footer-container">
        <div class="page-num">
            <?php if ($lang === 'zh'): ?>
                <?= "{$txtPageWord}02{$txtOfWord}02页 - S-" . htmlspecialchars($cert['codigo_certificado'], ENT_QUOTES, 'UTF-8') ?>
            <?php else: ?>
                <?= "{$txtPageWord} 02 {$txtOfWord} 02 - S-" . htmlspecialchars($cert['codigo_certificado'], ENT_QUOTES, 'UTF-8') ?>
            <?php endif; ?>
        </div>
    </div>
</div>
<?php endif; ?>

</body>
</html>
<?php
$html = ob_get_clean();

// Configuración adicional para chino - aumentar memoria y tiempo
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