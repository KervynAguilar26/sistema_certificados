<?php
// descargar_pptx.php - Reemplazo directo ZIP
ob_start();

require_once __DIR__ . '/config/conexion.php';
require_once __DIR__ . '/includes/auth.php';

$id   = $_GET['id']   ?? null;
$lang = $_GET['lang'] ?? 'es';

if (!$id) { die("Error: ID no especificado."); }

// 1. Consultar certificado
$stmt = $pdo->prepare("SELECT * FROM certificados WHERE id = :id");
$stmt->execute(['id' => $id]);
$cert = $stmt->fetch();

if (!$cert) { die("Error: Certificado no encontrado."); }

// 2. Ruta de plantilla base
$templatePath = __DIR__ . '/uploads/templates/plantilla_base.pptx';
if (!file_exists($templatePath)) {
    die("Error: No existe el archivo 'uploads/templates/plantilla_base.pptx'");
}

// 3. Crear copia temporal para modificar
$tempFile = sys_get_temp_dir() . '/cert_' . time() . '_' . rand(1000, 9999) . '.pptx';
copy($templatePath, $tempFile);

// 4. Preparar datos de reemplazo
$modelos_array = array_map('trim', explode(',', $cert['modelos_adjuntos']));
$texto_front   = (count($modelos_array) > 3) ? 'See attachment' : implode(', ', $modelos_array);
$texto_back    = implode(', ', $modelos_array);

$reemplazos = [
    '${CODIGO}'          => htmlspecialchars($cert['codigo_certificado'], ENT_XML1),
    '${FABRICANTE}'      => htmlspecialchars($cert['fabricante'], ENT_XML1),
    '${DIR_FABRICANTE}'  => htmlspecialchars($cert['direccion_fabricante'] ?? '', ENT_XML1),
    '${PRODUCTO}'        => htmlspecialchars($cert['producto'], ENT_XML1),
    '${DESC_PRODUCTO}'   => htmlspecialchars($cert['descripcion_producto'] ?? '', ENT_XML1),
    '${MARCA}'           => htmlspecialchars($cert['marcas'], ENT_XML1),
    '${MODELOS_FRONT}'   => htmlspecialchars($texto_front, ENT_XML1),
    '${MODELOS_BACK}'    => htmlspecialchars($texto_back, ENT_XML1),
    '${PARAMETROS}'      => htmlspecialchars($cert['parametros_ensayo'] ?? '', ENT_XML1),
    '${NORMAS}'          => htmlspecialchars($cert['normas_ensayo'] ?? '', ENT_XML1),
    '${REPORTE}'         => htmlspecialchars($cert['reporte_ensayo'] ?? '', ENT_XML1),
    '${FECHA_EMISION}'   => htmlspecialchars($cert['fecha_emision'], ENT_XML1),
    '${FECHA_EXPIRACION}'=> htmlspecialchars($cert['fecha_expiracion'], ENT_XML1)
];

// 5. Abrir el contenedor PPTX y reemplazar variables en las diapositivas
$zip = new ZipArchive();
if ($zip->open($tempFile) === TRUE) {
    for ($i = 0; $i < $zip->numFiles; $i++) {
        $filename = $zip->getNameIndex($i);
        if (strpos($filename, 'ppt/slides/slide') === 0 && strpos($filename, '.xml') !== false) {
            $slideXml = $zip->getFromIndex($i);
            foreach ($reemplazos as $search => $replace) {
                $slideXml = str_replace($search, $replace, $slideXml);
            }
            $zip->addFromString($filename, $slideXml);
        }
    }
    $zip->close();
} else {
    die("Error al procesar el archivo PowerPoint.");
}

// 6. Descarga limpia del archivo generado
while (ob_get_level()) { ob_end_clean(); }

$outputName = "Certificado_" . $cert['codigo_certificado'] . "_" . strtoupper($lang) . ".pptx";

header('Content-Type: application/vnd.openxmlformats-officedocument.presentationml.presentation');
header('Content-Disposition: attachment; filename="' . $outputName . '"');
header('Content-Length: ' . filesize($tempFile));
header('Cache-Control: max-age=0');

readfile($tempFile);
@unlink($tempFile);
exit;
?>