<?php
// editar_certificado.php
require_once 'includes/auth.php';
require_once 'config/conexion.php';

$id = $_GET['id'] ?? null;
if (!$id) {
    header("Location: dashboard.php");
    exit;
}

// Obtener datos del certificado
$stmt = $pdo->prepare("SELECT * FROM certificados WHERE id = :id");
$stmt->execute(['id' => $id]);
$cert = $stmt->fetch();

if (!$cert) {
    header("Location: dashboard.php");
    exit;
}

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
    $mostrar_parametros  = $_POST['mostrar_parametros'] ?? 'SI';
    $normas_ensayo       = trim($_POST['normas_ensayo'] ?? '');
    $reporte_ensayo      = trim($_POST['reporte_ensayo'] ?? '');
    $descripcion_prod    = trim($_POST['descripcion_producto'] ?? '');
    $fecha_emision       = $_POST['fecha_emision'] ?? '';
    $fecha_expiracion    = $_POST['fecha_expiracion'] ?? '';

    // Procesar nuevo CSV de modelos si se adjunta
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
        $stmt_update = $pdo->prepare("
            UPDATE certificados SET 
                codigo_certificado   = :codigo,
                tipo_certificado     = :tipo,
                solicitante          = :solicitante,
                fabricante           = :fabricante,
                direccion_fabricante = :direccion_fab,
                producto             = :producto,
                marcas               = :marcas,
                modelos_adjuntos     = :modelos,
                parametros_ensayo    = :parametros,
                mostrar_parametros   = :mostrar_param,
                normas_ensayo        = :normas,
                reporte_ensayo       = :reporte,
                descripcion_producto = :descripcion,
                fecha_emision        = :emision,
                fecha_expiracion     = :expiracion
            WHERE id = :id
        ");

        $ejecutado = $stmt_update->execute([
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
            'id'             => $id
        ]);

        if ($ejecutado) {
            header("Location: dashboard.php");
            exit;
        } else {
            $error = "Error al actualizar el registro.";
        }
    } else {
        $error = "Por favor complete los campos obligatorios.";
    }
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Editar Certificado - Control de Calidad</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <link rel="stylesheet" href="assets/css/style.css">
</head>
<body class="bg-light">

<div class="container py-4" style="max-width: 900px;">
    <div class="card shadow-sm border-0 rounded-3">
        <div class="card-header bg-warning text-dark p-3 d-flex justify-content-between align-items-center">
            <h5 class="m-0 fw-bold"><i class="bi bi-pencil-square me-2"></i>Editar Certificado</h5>
            <span class="badge bg-dark">ID: <?= htmlspecialchars($cert['id']) ?></span>
        </div>
        <div class="card-body p-4">
            
            <?php if ($error): ?>
                <div class="alert alert-danger"><?= htmlspecialchars($error) ?></div>
            <?php endif; ?>

            <form action="editar_certificado.php?id=<?= $cert['id'] ?>" method="POST" enctype="multipart/form-data">
                
                <div class="row g-3">
                    <div class="col-md-6">
                        <label class="form-label fw-bold">N° Certificado <span class="text-danger">*</span></label>
                        <input type="text" name="codigo_certificado" class="form-control" required value="<?= htmlspecialchars($cert['codigo_certificado']) ?>">
                    </div>
                    <div class="col-md-6">
                        <label class="form-label fw-bold">Tipo de Certificado</label>
                        <input type="text" name="tipo_certificado" class="form-control" value="<?= htmlspecialchars($cert['tipo_certificado']) ?>">
                    </div>

                    <div class="col-md-6">
                        <label class="form-label fw-bold">Solicitante <span class="text-danger">*</span></label>
                        <input type="text" name="solicitante" class="form-control" required value="<?= htmlspecialchars($cert['solicitante']) ?>">
                    </div>
                    <div class="col-md-6">
                        <label class="form-label fw-bold">Fabricante</label>
                        <input type="text" name="fabricante" class="form-control" value="<?= htmlspecialchars($cert['fabricante']) ?>">
                    </div>

                    <div class="col-12">
                        <label class="form-label fw-bold">Dirección del Fabricante</label>
                        <input type="text" name="direccion_fabricante" class="form-control" value="<?= htmlspecialchars($cert['direccion_fabricante'] ?? '') ?>">
                    </div>

                    <div class="col-md-6">
                        <label class="form-label fw-bold">Producto</label>
                        <input type="text" name="producto" class="form-control" value="<?= htmlspecialchars($cert['producto']) ?>">
                    </div>
                    <div class="col-md-6">
                        <label class="form-label fw-bold">Marca Comercial</label>
                        <input type="text" name="marcas" class="form-control" value="<?= htmlspecialchars($cert['marcas']) ?>">
                    </div>

                    <!-- CONTROL EXCLUSIVO DE PARÁMETROS DE ENSAYO -->
                    <div class="col-md-4">
                        <label class="form-label fw-bold">¿Mostrar Parámetros de Ensayo?</label>
                        <select name="mostrar_parametros" id="select_param" class="form-select" onchange="toggleParametros()">
                            <option value="SI" <?= ($cert['mostrar_parametros'] ?? 'SI') === 'SI' ? 'selected' : '' ?>>Sí, incluir en PDF</option>
                            <option value="NO" <?= ($cert['mostrar_parametros'] ?? '') === 'NO' ? 'selected' : '' ?>>No, ocultar en PDF</option>
                        </select>
                    </div>
                    <div class="col-md-8" id="container_param">
                        <label class="form-label fw-bold">Parámetros de Ensayo</label>
                        <input type="text" name="parametros_ensayo" class="form-control" value="<?= htmlspecialchars($cert['parametros_ensayo'] ?? '') ?>">
                    </div>

                    <div class="col-md-6">
                        <label class="form-label fw-bold">Probado según Norma</label>
                        <input type="text" name="normas_ensayo" class="form-control" value="<?= htmlspecialchars($cert['normas_ensayo'] ?? '') ?>">
                    </div>
                    
                    <!-- INFORME DE ENSAYO SIEMPRE VISIBLE Y EDITABLE -->
                    <div class="col-md-6">
                        <label class="form-label fw-bold">Informe de Ensayo N°</label>
                        <input type="text" name="reporte_ensayo" class="form-control" value="<?= htmlspecialchars($cert['reporte_ensayo'] ?? '') ?>">
                    </div>

                    <div class="col-12">
                        <label class="form-label fw-bold">Modelos Adjuntos (Texto manual separado por comas)</label>
                        <textarea name="modelos_adjuntos" class="form-control" rows="3"><?= htmlspecialchars($cert['modelos_adjuntos'] ?? '') ?></textarea>
                    </div>
                    <div class="col-12">
                        <label class="form-label fw-bold text-primary"><i class="bi bi-filetype-csv me-1"></i>Reemplazar Modelos cargando archivo CSV</label>
                        <input type="file" name="csv_modelos" accept=".csv" class="form-control">
                    </div>

                    <div class="col-12">
                        <label class="form-label fw-bold">Descripción de Pruebas (Cláusulas)</label>
                        <textarea name="descripcion_producto" class="form-control" rows="4"><?= htmlspecialchars($cert['descripcion_producto'] ?? '') ?></textarea>
                    </div>

                    <div class="col-md-4">
                        <label class="form-label fw-bold">Fecha de Emisión</label>
                        <input type="date" name="fecha_emision" id="fecha_emision" class="form-control" value="<?= htmlspecialchars($cert['fecha_emision']) ?>">
                    </div>
                    <div class="col-md-8">
                        <label class="form-label fw-bold">Vigencia Dinámica</label>
                        <div class="d-flex align-items-center gap-2">
                            <button type="button" class="btn btn-outline-secondary" onclick="setVigencia(1)">1 Año</button>
                            <button type="button" class="btn btn-outline-secondary" onclick="setVigencia(2)">2 Años</button>
                            <button type="button" class="btn btn-outline-secondary" onclick="setVigencia(3)">3 Años</button>
                            <button type="button" class="btn btn-outline-secondary" onclick="setVigencia(5)">5 Años</button>
                            <input type="date" name="fecha_expiracion" id="fecha_expiracion" class="form-control ms-2" value="<?= htmlspecialchars($cert['fecha_expiracion']) ?>" required>
                        </div>
                    </div>
                </div>

                <hr class="my-4">

                <div class="d-flex justify-content-end gap-2">
                    <a href="dashboard.php" class="btn btn-secondary">Cancelar</a>
                    <button type="submit" class="btn btn-warning px-4 fw-bold">Actualizar Certificado</button>
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

// Inicializar visibilidad de Parámetros de Ensayo al cargar
toggleParametros();
</script>

</body>
</html>