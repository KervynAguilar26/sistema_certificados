<?php
// generar_pdf.php - Declaración Explícita de Fuente TrueType para Chino Simplificado
require_once __DIR__ . '/vendor/autoload.php';
require_once __DIR__ . '/config/conexion.php';
require_once __DIR__ . '/config/traductor.php';
require_once __DIR__ . '/includes/qr_generator.php';
require_once 'includes/auth.php';

// -----------------------------------------------------------------------------
// 1. CONTROL DE ACCESO Y PARÁMETROS
// -----------------------------------------------------------------------------
if (!esSuperAdmin()) {
    die("Acceso denegado: No posee permisos de Administrador para realizar esta operación.");
}

use Dompdf\Dompdf;
use Dompdf\Options;

$id = $_GET['id'] ?? null;

// Restricción exclusiva a Chino (zh) e Inglés (en)
$requestedLang = strtolower($_GET['lang'] ?? 'zh');
$lang = ($requestedLang === 'en') ? 'en' : 'zh';

if (!$id) { die("Error: ID no especificado."); }

// Obtención del registro del certificado
$stmt = $pdo->prepare("SELECT * FROM certificados WHERE id = :id");
$stmt->execute(['id' => $id]);
$cert = $stmt->fetch();

if (!$cert) { die("Error: Certificado no encontrado."); }

// -----------------------------------------------------------------------------
// 2. DICCIONARIO Y TRADUCCIONES POR IDIOMA
// -----------------------------------------------------------------------------
if ($lang === 'zh') {
    $tipoCertTrad   = '合规证书';
    $lblMfr         = '制造商:';
    $lblProd        = '产品:';
    $lblBrand       = '商标:';
    $lblModels      = '型号:';
    $lblParams      = '测试参数:';
    $lblTested      = '按标准测试:';
    $lblReport      = '检测报告编号:';
    $lblValid       = '有效性:';
    $lblIssue       = '排放';
    $lblUntil       = '到期日';
    $lblAtt         = '认证型号附件';
    $lblListModels  = '认证型号列表:';
    $lblScan        = '扫码验证';
    $txtPageWord    = '第';
    $txtOfWord      = '页 共';
} else {
    $tipoCertTrad   = 'CERTIFICATE OF COMPLIANCE';
    $lblMfr         = 'Manufacturer:';
    $lblProd        = 'Product:';
    $lblBrand       = 'Trademark:';
    $lblModels      = 'Model(s):';
    $lblParams      = 'Test Parameters:';
    $lblTested      = 'Tested according to standard:';
    $lblReport      = 'Test report No.:';
    $lblValid       = 'Validity:';
    $lblIssue       = 'Emission';
    $lblUntil       = 'Expiry';
    $lblAtt         = 'ANNEX OF CERTIFIED MODELS';
    $lblListModels  = 'List of Certified Models:';
    $lblScan        = 'Scan to verify';
    $txtPageWord    = 'Page';
    $txtOfWord      = 'of';
}

// Traducción de campos dinámicos traídos de la base de datos
$fabricanteTrad = traducirTexto($cert['fabricante'], $lang);
$dirFabTrad     = traducirTexto($cert['direccion_fabricante'] ?? '', $lang);
$productoTrad   = traducirTexto($cert['producto'], $lang);
$descProdTrad   = traducirTexto($cert['descripcion_producto'] ?? '', $lang);
$marcasTrad     = traducirTexto($cert['marcas'], $lang);
$paramTrad      = traducirTexto($cert['parametros_ensayo'] ?? '', $lang);
$normasTrad     = traducirTexto($cert['normas_ensayo'] ?? '', $lang);
$reporteTrad    = traducirTexto($cert['reporte_ensayo'] ?? '', $lang);

// -----------------------------------------------------------------------------
// 3. PROCESAMIENTO Y DEPURACIÓN DE MODELOS
// -----------------------------------------------------------------------------
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

// Capacidad por hoja del anexo
$modelos_por_pagina = 180;
$total_modelos = count($modelos_array);

if ($total_modelos > 10) {
    $bloques_anexo = array_chunk($modelos_array, $modelos_por_pagina);
    $cant_paginas_anexo = count($bloques_anexo);
    $totalPaginasInt = 1 + $cant_paginas_anexo;
    $totalPaginas = str_pad($totalPaginasInt, 2, '0', STR_PAD_LEFT);

    if ($cant_paginas_anexo > 1) {
        $hastaPagina = $totalPaginasInt;
        $txtModels = ($lang === 'zh') 
            ? "见附件(第2至{$hastaPagina}页)" 
            : "See Attached Annex (Pages 2 to {$hastaPagina})";
    } else {
        $txtModels = ($lang === 'zh') 
            ? '见附件(第2页)' 
            : 'See Attached Annex (Page 2)';
    }
} else {
    $bloques_anexo = [];
    $totalPaginas = '01';
    $txtModels = implode(', ', $modelos_array);
}

// Helper para convertir imágenes en código Base64 embebido
function getBase64Img($path) {
    return file_exists($path) ? 'data:image/png;base64,' . base64_encode(file_get_contents($path)) : '';
}

$marcoPagina1 = getBase64Img(__DIR__ . '/assets/img/marco_dorado.png');
$marcoPagina2 = getBase64Img(__DIR__ . '/assets/img/marco_dorado 2.png');
$qrBase64     = getBase64Img(obtenerRutaQR($cert['token_verificacion']));

// -----------------------------------------------------------------------------
// 4. CONFIGURACIÓN DE DOMPDF Y FUENTES
// -----------------------------------------------------------------------------
$options = new Options();
$options->set('isRemoteEnabled', true);
$options->set('isHtml5ParserEnabled', true);
$options->set('isFontSubsettingEnabled', true); // <--- OBLIGATORIO PARA FUENTES CJK EN DOMPDF[cite: 11]
$options->set('defaultFont', 'wqy-zenhei');
$options->set('chroot', __DIR__);

$dompdf = new Dompdf($options);

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
    /* REGISTRO Y ASIGNACIÓN DIRECTA DE FUENTE SEGURO EN CSS */
    @font-face {
        font-family: 'wqy-zenhei';
        font-style: normal;
        font-weight: normal;
        src: local('wqy-zenhei'), local('WenQuanYi Zen Hei');
    }

    * {
        font-family: 'wqy-zenhei', sans-serif !important; /* <--- FORZAR FUENTE EN TODOS LOS ELEMENTOS DEL DOM */
    }

    /* Configuración Global de la Hoja A4 */
    @page { 
        margin: 0px; 
        size: A4 portrait;
    }

    body { 
        margin: 0px; 
        padding: 0px; 
        color: #212121; 
        font-size: 14px; 
        line-height: 1.45;
    }

    /* Imagen de Marco Dorado de Fondo */
    .bg-frame { 
        position: fixed; 
        top: 0px; 
        left: 0px; 
        width: 210mm; 
        height: 297mm; 
        z-index: -1000; 
    }

    /* Contenedor de la Primera Página */
    .page-1 {
        padding-top: 150px;
        padding-left: 70px;
        padding-right: 70px;
        box-sizing: border-box;
    }

    /* Contenedor del Anexo (Página 2) */
    .page-anexo {
        page-break-before: always;
        padding-top: 130px;
        padding-left: 70px;
        padding-right: 70px;
        box-sizing: border-box;
    }

    /* TÍTULO PRINCIPAL UNIFICADO */
    .subtitle-type, .title-anexo { 
        font-size: 32px; 
        font-weight: bold; 
        color: #212121; 
        text-align: center; 
        margin-bottom: 2px; 
        text-transform: uppercase; 
        line-height: 1.15;
        letter-spacing: 0.5px;
    }
    
    /* Número de Certificado */
    .cert-no { 
        font-size: 18px; 
        font-weight: bold; 
        color: #212121; 
        text-align: center; 
        margin-bottom: 18px; 
    }

    /* Tabla Principal de Datos */
    .data-table { 
        width: 100%; 
        border-collapse: collapse; 
        table-layout: fixed;
    }
    
    .data-table td { 
        padding: 5px 0; 
        font-size: 14px; 
        color: #212121;
        vertical-align: top; 
        line-height: 1.45; 
        word-wrap: break-word;
        overflow-wrap: break-word;
        text-align: left;
    }
    
    .lbl { 
        font-weight: bold; 
        color: #212121; 
        width: 34%; 
        padding-right: 8px;
    }

    .dir-address {
        color: #212121;
        font-size: 13px;
        line-height: 1.35;
        display: block;
        margin-top: 3px;
    }

    /* Estilos de la Lista de Modelos del Anexo (Página 2) */
    .models-box {
        width: 100%;
        font-size: 14px; 
        line-height: 1.6; 
        color: #212121; 
        text-align: justify;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }

    .models-title {
        font-size: 16px; 
        font-weight: bold;
        color: #212121;
        display: block;
        margin-bottom: 10px;
    }

    /* Pie de página contenedor */
    .footer-container {
        position: absolute;
        bottom: 80px; 
        left: 70px;
        right: 70px;
        height: 85px;
    }

    /* Posicionamiento del QR */
    .qr-box { 
        position: absolute;
        right: 0px;
        bottom: -15px; 
        width: 115px; 
        text-align: center;
    }
    
    .qr-img { 
        width: 105px; 
        height: 105px; 
        display: block;
        margin: 0 auto;
    }

    /* PAGINACIÓN ROJA COLOCADA EN EL BORDE MÁS BAJO DE LA HOJA */
    .page-num-bottom { 
        position: absolute;
        bottom: 35px; 
        left: 0px;
        right: 0px; 
        text-align: center; 
        font-size: 11.5px; 
        color: #ec0a0a; 
        font-weight: bold;
    }
</style>
</head>
<body>

<!-- ======================================================================= -->
<!-- PÁGINA 1: CERTIFICADO PRINCIPAL                                         -->
<!-- ======================================================================= -->
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
            <td colspan="2" style="font-size: 14px; color: #212121; padding-top: 10px; line-height: 1.4;">
                <?= nl2br(htmlspecialchars($descProdTrad, ENT_QUOTES, 'UTF-8')) ?>
            </td>
        </tr>
        <?php endif; ?>
    </table>

    <div class="footer-container">
        <div class="qr-box">
            <?php if (!empty($qrBase64)): ?>
                <img src="<?= $qrBase64 ?>" class="qr-img"><br>
            <?php endif; ?>
            <span style="font-size: 8px; color: #212121; font-weight: bold;"><?= htmlspecialchars($lblScan, ENT_QUOTES, 'UTF-8') ?></span>
        </div>
    </div>

    <!-- Paginación Roja Centrada en el Borde Inferior de la Hoja -->
    <div class="page-num-bottom">
        <?php if ($lang === 'zh'): ?>
            <?= "{$txtPageWord} 01 {$txtOfWord} {$totalPaginas} 页" ?>
        <?php else: ?>
            <?= "{$txtPageWord} 01 {$txtOfWord} {$totalPaginas}" ?>
        <?php endif; ?>
    </div>
</div>

<!-- ======================================================================= -->
<!-- PÁGINA 2+: ANEXO DE MODELOS CERTIFICADOS                                -->
<!-- ======================================================================= -->
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

            <!-- Encabezado del Anexo -->
            <div style="text-align: center; margin-bottom: 24px;">
                <div class="title-anexo"><?= htmlspecialchars($lblAtt, ENT_QUOTES, 'UTF-8') ?></div>
                <div class="cert-no" style="margin-top: 4px;">Certificate No. <?= htmlspecialchars($cert['codigo_certificado'], ENT_QUOTES, 'UTF-8') ?></div>
            </div>

            <!-- Caja de Modelos -->
            <div class="models-box">
                <span class="models-title"><?= htmlspecialchars($lblListModels, ENT_QUOTES, 'UTF-8') ?></span>
                <?= htmlspecialchars($string_bloque, ENT_QUOTES, 'UTF-8') ?>
            </div>

            <!-- Paginación Roja Centrada en Borde Inferior para Anexos -->
            <div class="page-num-bottom">
                <?php if ($lang === 'zh'): ?>
                    <?= "{$txtPageWord} {$numPaginaActual} {$txtOfWord} {$totalPaginas} 页 - S-" . htmlspecialchars($cert['codigo_certificado'], ENT_QUOTES, 'UTF-8') ?>
                <?php else: ?>
                    <?= "{$txtPageWord} {$numPaginaActual} {$txtOfWord} {$totalPaginas} - S-" . htmlspecialchars($cert['codigo_certificado'], ENT_QUOTES, 'UTF-8') ?>
                <?php endif; ?>
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