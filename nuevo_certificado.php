<?php
// nuevo_certificado.php - Registro de Certificados con Control de Parámetros de Ensayo
require_once 'includes/auth.php';
require_once 'config/conexion.php';
require_once 'includes/qr_generator.php';

$mensaje = "";
$error   = "";

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $codigo_certificado  = trim($_POST['codigo_certificado'] ?? '');
    $tipo_certificado    = trim($_POST['tipo_certificado'] ?? '');
    $solicitante         = trim($_POST['solicitante'] ?? '');
    $fabricante          = trim($_POST['fabricante'] ?? '');
    $direccion_fab       = trim($_POST['direccion_fabricante'] ?? '');
    $producto            = trim($_POST['producto'] ?? '');
    $marcas              = trim($_POST['marcas'] ?? '');
    $modelos_adjuntos    = trim($_POST['modelos_adjuntos'] ?? '');
    $parametros_ensayo   = trim($_POST['parametros_ensayo'] ?? '');
    $mostrar_parametros  = $_POST['mostrar_parametros'] ?? 'SI'; // Control SI / NO exclusivo para parámetros
    $normas_ensayo       = trim($_POST['normas_ensayo'] ?? '');
    $reporte_ensayo      = trim($_POST['reporte_ensayo'] ?? '');
    $descripcion_prod    = trim($_POST['descripcion_producto'] ?? '');
    $fecha_emision       = $_POST['fecha_emision'] ?? date('Y-m-d');
    $fecha_expiracion    = $_POST['fecha_expiracion'] ?? '';
    
    // Procesar carga masiva de modelos desde CSV
    if (isset($_FILES['csv_modelos']) && $_FILES['csv_modelos']['error'] === UPLOAD_ERR_OK) {
        $tmpName = $_FILES['csv_modelos']['tmp_name'];
        $modelos_csv = [];
        if (($handle = fopen($tmpName, "r")) !== FALSE) {
            while (($data = fgetcsv($handle, 1000, ",")) !== FALSE) {
                if (isset($data[0]) && !empty(trim($data[0]))) {
                    $mod = trim($data[0]);
                    if (strtolower($mod) !== 'modelos' && strtolower($mod) !== 'modelo') {
                        $modelos_csv[] = $mod;
                    }
                }
            }
            fclose($handle);
        }
        if (!empty($modelos_csv)) {
            $modelos_adjuntos = implode(', ', $modelos_csv);
        }
    }

    if (!empty($codigo_certificado) && !empty($solicitante)) {
        $token_verificacion = bin2hex(random_bytes(16));
        $analista_id = $_SESSION['usuario_id'] ?? null;

        $stmt = $pdo->prepare("
            INSERT INTO certificados (
                codigo_certificado, tipo_certificado, solicitante, fabricante, 
                direccion_fabricante, producto, marcas, modelos_adjuntos, 
                parametros_ensayo, mostrar_parametros, normas_ensayo, reporte_ensayo, 
                descripcion_producto, fecha_emision, fecha_expiracion, token_verificacion, 
                analista_id, estado
            ) VALUES (
                :codigo, :tipo, :solicitante, :fabricante, 
                :direccion_fab, :producto, :marcas, :modelos, 
                :parametros, :mostrar_param, :normas, :reporte, 
                :descripcion, :emision, :expiracion, :token, 
                :analista, 'activo'
            )
        ");

        $ejecutado = $stmt->execute([
            'codigo'         => $codigo_certificado,
            'tipo'           => $tipo_certificado,
            'solicitante'    => $solicitante,
            'fabricante'     => $fabricante,
            'direccion_fab'  => $direccion_fab,
            'producto'       => $producto,
            'marcas'         => $marcas,
            'modelos'        => $modelos_adjuntos,
            'parametros'     => $parametros_ensayo,
            'mostrar_param'  => $mostrar_parametros,
            'normas'         => $normas_ensayo,
            'reporte'        => $reporte_ensayo,
            'descripcion'    => $descripcion_prod,
            'emision'        => $fecha_emision,
            'expiracion'     => $fecha_expiracion,
            'token'          => $token_verificacion,
            'analista'       => $analista_id
        ]);

        if ($ejecutado) {
            obtenerRutaQR($token_verificacion);
            header("Location: dashboard.php");
            exit;
        } else {
            $error = "Error al registrar el certificado en la base de datos.";
        }
    } else {
        $error = "Por favor complete los campos obligatorios (*).";
    }
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Nuevo Certificado - Control de Calidad</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <link rel="stylesheet" href="assets/css/style.css">
</head>
<body class="bg-light">

<div class="container py-4" style="max-width: 900px;">
    <div class="card shadow-sm border-0 rounded-3">
        <div class="card-header bg-primary text-white p-3">
            <h5 class="m-0 fw-bold"><i class="bi bi-file-earmark-plus me-2"></i>Registrar Nuevo Certificado</h5>
        </div>
        <div class="card-body p-4">
            
            <?php if ($error): ?>
                <div class="alert alert-danger"><?= htmlspecialchars($error) ?></div>
            <?php endif; ?>

            <form action="nuevo_certificado.php" method="POST" enctype="multipart/form-data">
                
                <div class="row g-3">
                    <div class="col-md-6">
                        <label class="form-label fw-bold">N° Certificado <span class="text-danger">*</span></label>
                        <input type="text" name="codigo_certificado" class="form-control" required placeholder="Ej: CE-SVV-21485-01">
                    </div>
                    <div class="col-md-6">
                        <label class="form-label fw-bold">Tipo de Certificado</label>
                        <input type="text" name="tipo_certificado" class="form-control" value="CERTIFICATE OF COMPLIANCE">
                    </div>

                    <div class="col-md-6">
                        <label class="form-label fw-bold">Solicitante <span class="text-danger">*</span></label>
                        <input type="text" name="solicitante" class="form-control" required placeholder="Ej: QUALITY TRADING COMPANY">
                    </div>
                    <div class="col-md-6">
                        <label class="form-label fw-bold">Fabricante</label>
                        <input type="text" name="fabricante" class="form-control">
                    </div>

                    <div class="col-12">
                        <label class="form-label fw-bold">Dirección del Fabricante</label>
                        <input type="text" name="direccion_fabricante" class="form-control">
                    </div>

                    <div class="col-md-6">
                        <label class="form-label fw-bold">Producto</label>
                        <input type="text" name="producto" class="form-control">
                    </div>
                    <div class="col-md-6">
                        <label class="form-label fw-bold">Marca Comercial</label>
                        <input type="text" name="marcas" class="form-control">
                    </div>

                    <!-- CONTROL DE PARÁMETROS DE ENSAYO -->
                    <div class="col-md-4">
                        <label class="form-label fw-bold">¿Mostrar Parámetros de Ensayo?</label>
                        <select name="mostrar_parametros" id="select_param" class="form-select" onchange="toggleParametros()">
                            <option value="SI" selected>Sí, incluir en PDF</option>
                            <option value="NO">No, ocultar en PDF</option>
                        </select>
                    </div>
                    <div class="col-md-8" id="container_param">
                        <label class="form-label fw-bold">Parámetros de Ensayo</label>
                        <input type="text" name="parametros_ensayo" class="form-control" placeholder="Ej: SHOCK ABSORBER">
                    </div>

                    <div class="col-md-6">
                        <label class="form-label fw-bold">Probado según Norma</label>
                        <input type="text" name="normas_ensayo" class="form-control" placeholder="Ej: ISO TS 16949:2009">
                    </div>
                    
                    <!-- INFORME DE ENSAYO N° (SIEMPRE VISIBLE Y EDITABLE) -->
                    <div class="col-md-6">
                        <label class="form-label fw-bold">Informe de Ensayo N°</label>
                        <input type="text" name="reporte_ensayo" class="form-control" placeholder="Ej: CE-SVV-21485-X23">
                    </div>

                    <!-- CARGA DUAL DE MODELOS -->
                    <div class="col-12">
                        <label class="form-label fw-bold">Modelos Adjuntos (Texto manual separado por comas)</label>
                        <textarea name="modelos_adjuntos" class="form-control" rows="2" placeholder="Ej: 333209, 333210, 1033..."></textarea>
                    </div>
                    <div class="col-12">
                        <label class="form-label fw-bold text-primary"><i class="bi bi-filetype-csv me-1"></i>O Cargar Modelos desde Archivo CSV / Excel</label>
                        <input type="file" name="csv_modelos" accept=".csv" class="form-control">
                    </div>

                    <div class="col-12">
                        <label class="form-label fw-bold">Descripción de Pruebas (Cláusulas)</label>
                        <textarea name="descripcion_producto" class="form-control" rows="4"></textarea>
                    </div>

                    <div class="col-md-4">
                        <label class="form-label fw-bold">Fecha de Emisión</label>
                        <input type="date" name="fecha_emision" id="fecha_emision" class="form-control" value="<?= date('Y-m-d') ?>">
                    </div>
                    <div class="col-md-8">
                        <label class="form-label fw-bold">Vigencia Dinámica</label>
                        <div class="d-flex align-items-center gap-2">
                            <button type="button" class="btn btn-outline-secondary" onclick="setVigencia(1)">1 Año</button>
                            <button type="button" class="btn btn-outline-secondary" onclick="setVigencia(2)">2 Años</button>
                            <button type="button" class="btn btn-outline-secondary" onclick="setVigencia(3)">3 Años</button>
                            <button type="button" class="btn btn-outline-secondary" onclick="setVigencia(5)">5 Años</button>
                            <input type="date" name="fecha_expiracion" id="fecha_expiracion" class="form-control ms-2" required>
                        </div>
                    </div>
                </div>

                <hr class="my-4">

                <div class="d-flex justify-content-end gap-2">
                    <a href="dashboard.php" class="btn btn-secondary">Cancelar</a>
                    <button type="submit" class="btn btn-primary px-4 fw-bold">Guardar Certificado</button>
                </div>
            </form>
        </div>
    </div>
</div>

<script>
function toggleParametros() {
    const val = document.getElementById('select_param').value;
    document.getElementById('container_param').style.display = (val === 'SI') ? 'block' : 'none';
}

function setVigencia(anos) {
    const emision = new Date(document.getElementById('fecha_emision').value);
    if (!isNaN(emision.getTime())) {
        emision.setFullYear(emision.getFullYear() + anos);
        document.getElementById('fecha_expiracion').value = emision.toISOString().split('T')[0];
    }
}

// Establecer 3 años por defecto y la visibilidad al cargar
setVigencia(3);
toggleParametros();
</script>

</body>
</html>