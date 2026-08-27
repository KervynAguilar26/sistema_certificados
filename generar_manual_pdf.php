<?php
// generar_manual_pdf.php - Manual de Usuario con el Diseño Oficial del Sistema
require_once __DIR__ . '/vendor/autoload.php';

use Dompdf\Dompdf;
use Dompdf\Options;

$options = new Options();
$options->set('isRemoteEnabled', true);
$options->set('isHtml5ParserEnabled', true);

$dompdf = new Dompdf($options);

// Convertir logo y CSS a base64 / inline para asegurar el mismo diseño en Dompdf
function getBase64Img($path) {
    return file_exists($path) ? 'data:image/png;base64,' . base64_encode(file_get_contents($path)) : '';
}

$logoBase64 = getBase64Img(__DIR__ . '/assets/img/logo.png');

ob_start();
?>
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<style>
    @page {
        margin: 0px;
        size: A4 portrait;
    }
    body {
        font-family: 'Helvetica', 'Arial', sans-serif;
        color: #1e293b;
        background-color: #f8fafc;
        margin: 0;
        padding: 0;
        font-size: 11px;
        line-height: 1.5;
    }
    .page-break { page-break-before: always; }
    
    /* ENCABEZADO IDÉNTICO AL NAVBAR DEL DASHBOARD */
    .navbar-corporate {
        background-color: #0b2c5b;
        color: #ffffff;
        padding: 15px 30px;
        border-bottom: 3px solid #c5a059;
    }
    .brand-title {
        font-size: 14px;
        font-weight: bold;
        color: #ffffff;
        letter-spacing: 0.5px;
    }
    .brand-sub {
        font-size: 10px;
        color: #c5a059;
        font-weight: bold;
    }

    /* CONTENEDOR TIPO CLEAN-CARD COMO EN EL DASHBOARD */
    .content-container {
        padding: 30px;
    }
    .clean-card {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        margin-bottom: 20px;
        overflow: hidden;
    }
    .card-header-corp {
        background-color: #f1f5f9;
        border-bottom: 1px solid #e2e8f0;
        padding: 10px 15px;
        font-weight: bold;
        color: #0b2c5b;
        font-size: 13px;
    }
    .card-body-corp {
        padding: 15px;
    }

    /* BADGES Y BOTONES DENTRO DEL MANUAL */
    .badge {
        padding: 3px 7px;
        font-size: 9.5px;
        font-weight: bold;
        border-radius: 4px;
        color: #ffffff;
        display: inline-block;
    }
    .bg-success { background-color: #16a34a; }
    .bg-danger { background-color: #dc2626; }
    .bg-warning { background-color: #d97706; }
    .bg-primary { background-color: #0284c7; }
    
    /* TABLA SIMILADA AL DASHBOARD */
    .table-sim {
        width: 100%;
        border-collapse: collapse;
        margin-top: 10px;
    }
    .table-sim th {
        background-color: #0b2c5b;
        color: #ffffff;
        padding: 6px 8px;
        font-size: 10px;
        text-align: left;
    }
    .table-sim td {
        padding: 6px 8px;
        border-bottom: 1px solid #e2e8f0;
        font-size: 10px;
    }

    /* ALERTAS */
    .alert-info {
        background-color: #e0f2fe;
        border-left: 4px solid #0284c7;
        color: #0369a1;
        padding: 10px;
        border-radius: 4px;
        margin-top: 10px;
    }
    .alert-danger {
        background-color: #fef2f2;
        border-left: 4px solid #ef4444;
        color: #991b1b;
        padding: 10px;
        border-radius: 4px;
        margin-top: 10px;
    }

    .footer-bar {
        position: absolute;
        bottom: 0px;
        left: 0px;
        right: 0px;
        background-color: #f1f5f9;
        padding: 10px 30px;
        border-top: 1px solid #e2e8f0;
        font-size: 9px;
        color: #64748b;
    }
</style>
</head>
<body>

<!-- PÁGINA 1: DASHBOARD Y BÚSQUEDA -->
<div class="navbar-corporate">
    <?php if ($logoBase64): ?>
        <img src="<?= $logoBase64 ?>" style="height: 25px; float: right;">
    <?php endif; ?>
    <div class="brand-title">SISTEMA DE CERTIFICACIONES DE CALIDAD</div>
    <div class="brand-sub">MANUAL DE USUARIO OFICIAL</div>
</div>

<div class="content-container">

    <div class="clean-card">
        <div class="card-header-corp">
            1. Panel de Control (Dashboard) y Búsqueda Inteligente
        </div>
        <div class="card-body-corp">
            <p>El Panel de Control es la pantalla central para la administración de los certificados emitidos. Incluye herramientas de filtrado en tiempo real para gestionar grandes volúmenes de datos.</p>
            
            <div class="alert-info">
                <strong>🔎 Buscador y Paginación Automática:</strong> En la esquina superior derecha de la tabla del sistema, el buscador permite filtrar instantáneamente por <strong>N° Certificado, Solicitante, Fabricante o Producto</strong>.
            </div>

            <table class="table-sim">
                <thead>
                    <tr>
                        <th>N° Certificado</th>
                        <th>Solicitante</th>
                        <th>Producto</th>
                        <th>Estado</th>
                        <th>Acciones Disponibles</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="color:#0284c7; font-weight:bold;">CA01020304</td>
                        <td>QUALITIN C.A</td>
                        <td>BICICLETA 1</td>
                        <td><span class="badge bg-success">Activo</span></td>
                        <td>[Editar] [PDF 🇪🇸🇬🇧🇨🇳] [Bloquear]</td>
                    </tr>
                    <tr>
                        <td style="color:#0284c7; font-weight:bold;">TR-2026-881</td>
                        <td>KYONER S.A</td>
                        <td>CAFETERA</td>
                        <td><span class="badge bg-danger">Bloqueado</span></td>
                        <td>[Editar] [PDF 🇪🇸🇬🇧🇨🇳] [Activar]</td>
                    </tr>
                </tbody>
            </table>
        </div>
    </div>

    <div class="clean-card">
        <div class="card-header-corp">
            2. Control de Estado (Bloqueo por Impago)
        </div>
        <div class="card-body-corp">
            <p>Permite suspender la validez de un certificado directamente desde el Dashboard en caso de mora en el pago:</p>
            <ul>
                <li><strong>Botón Bloquear:</strong> Cambia el estado a <span class="badge bg-danger">Bloqueado / Impago</span>. Al escanear el QR, la pantalla pública notificará inmediatamente que el documento no es válido o está suspendido.</li>
                <li><strong>Botón Activar:</strong> Reactiva la validez del certificado una vez solventada la deuda.</li>
            </ul>
        </div>
    </div>

</div>

<div class="footer-bar">
    Qingdao Technology Engineering Institute &copy; <?= date('Y') ?> - Página 01
</div>

<!-- PÁGINA 2: REGISTRO Y QR -->
<div class="page-break"></div>

<div class="navbar-corporate">
    <div class="brand-title">SISTEMA DE CERTIFICACIONES DE CALIDAD</div>
    <div class="brand-sub">REGISTRO DE CERTIFICADOS Y VERIFICACIÓN QR</div>
</div>

<div class="content-container">

    <div class="clean-card">
        <div class="card-header-corp">
            3. Registro y Carga Dual de Modelos (CSV / Manual)
        </div>
        <div class="card-body-corp">
            <p>Al hacer clic en <strong>Nuevo Certificado</strong>, el analista completa los datos básicos y selecciona la vigencia mediante los accesos directos (1A, 2A, 3A, 4A, 5A).</p>
            
            <p><strong>Gestión de Modelos:</strong></p>
            <ul>
                <li><strong>Entrada Manual:</strong> Ingrese los modelos separados por coma en la casilla de texto.</li>
                <li><strong>Carga Masiva vía CSV:</strong> Adjunte un archivo Excel/CSV para cargar cientos de modelos automáticamente.</li>
            </ul>

            <div class="alert-info">
                <strong>Anexo Automático:</strong> Si el registro posee más de 3 modelos, el sistema genera automáticamente la <strong>Página 02 (Anexo de Modelos)</strong> en el PDF.
            </div>
        </div>
    </div>

    <div class="clean-card">
        <div class="card-header-corp">
            4. Descarga de PDF Multilingüe y Validación QR
        </div>
        <div class="card-body-corp">
            <p><strong>Generación de PDF:</strong> Desde la opción desplegable en la tabla se puede obtener la versión en 🇪🇸 <strong>Español</strong>, 🇬🇧 <strong>Inglés</strong> o 🇨🇳 <strong>Chino</strong>.</p>
            
            <p><strong>Verificación Pública vía QR:</strong></p>
            <ul>
                <li>Cualquier dispositivo móvil al escanear el QR abrirá la pantalla oficial de verificación.</li>
                <li>Muestra por defecto la consulta en <strong>Chino (ZH)</strong> con el logo y el nombre de la empresa traducidos.</li>
                <li>Permite cambiar el idioma a Inglés o Español desde la parte superior.</li>
            </ul>
        </div>
    </div>

</div>

<div class="footer-bar">
    Qingdao Technology Engineering Institute &copy; <?= date('Y') ?> - Página 02
</div>

</body>
</html>
<?php
$html = ob_get_clean();
$dompdf->loadHtml($html);
$dompdf->setPaper('A4', 'portrait');
$dompdf->render();
$dompdf->stream("Manual_de_Usuario_Sistema_Certificaciones.pdf", ["Attachment" => false]);
exit;
?>