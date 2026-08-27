<?php
// gestionar_plantillas.php
require_once 'includes/auth.php';
require_once 'config/conexion.php';

// Restricción: Solo el Superadministrador tiene acceso
if (!esSuperAdmin()) {
    die("Acceso denegado: No tienes permisos para gestionar plantillas.");
}

$mensaje = "";
$dirTemplates = __DIR__ . '/uploads/templates/';

// Crear el directorio si no existe
if (!file_exists($dirTemplates)) {
    mkdir($dirTemplates, 0777, true);
}

// 1. Procesar la subida de una nueva plantilla .pptx
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['archivo_pptx'])) {
    $archivo = $_FILES['archivo_pptx'];
    $nombreOriginal = pathinfo($archivo['name'], PATHINFO_FILENAME);
    $extension = strtolower(pathinfo($archivo['name'], PATHINFO_EXTENSION));

    if ($extension === 'pptx') {
        // Sanitizar el nombre del archivo
        $nombreLimpio = preg_replace('/[^a-zA-Z0-9_-]/', '_', $nombreOriginal) . '_' . time() . '.pptx';
        $rutaDestino = $dirTemplates . $nombreLimpio;

        if (move_uploaded_file($archivo['tmp_name'], $rutaDestino)) {
            $mensaje = "<div class='alert alert-success'>✅ Plantilla <strong>" . htmlspecialchars($archivo['name']) . "</strong> subida correctamente.</div>";
        } else {
            $mensaje = "<div class='alert alert-danger'>❌ Error al mover el archivo subido al servidor.</div>";
        }
    } else {
        $mensaje = "<div class='alert alert-danger'>❌ Formato no válido. Por favor sube un archivo con extensión <strong>.pptx</strong>.</div>";
    }
}

// 2. Establecer una plantilla como activa (copiándola a plantilla_base.pptx)
if (isset($_GET['activar'])) {
    $fileToActivate = basename($_GET['activar']);
    $sourcePath = $dirTemplates . $fileToActivate;
    $targetPath = $dirTemplates . 'plantilla_base.pptx';

    if (file_exists($sourcePath)) {
        copy($sourcePath, $targetPath);
        $mensaje = "<div class='alert alert-success'>✅ La plantilla <strong>" . htmlspecialchars($fileToActivate) . "</strong> ahora es la plantilla activa predeterminada.</div>";
    }
}

// 3. Eliminar una plantilla
if (isset($_GET['eliminar'])) {
    $fileToDelete = basename($_GET['eliminar']);
    if ($fileToDelete !== 'plantilla_base.pptx') {
        $filePath = $dirTemplates . $fileToDelete;
        if (file_exists($filePath)) {
            unlink($filePath);
            $mensaje = "<div class='alert alert-warning'>🗑️ Plantilla eliminada correctamente.</div>";
        }
    } else {
        $mensaje = "<div class='alert alert-danger'>❌ No se puede eliminar la plantilla base en uso.</div>";
    }
}

// 4. Leer archivos .pptx del directorio
$archivosTemplates = glob($dirTemplates . '*.pptx');
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Gestión de Plantillas PPTX</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">

<div class="container my-5">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2>🎨 Gestión de Plantillas Personalizadas (.pptx)</h2>
        <a href="dashboard.php" class="btn btn-secondary">Volver al Dashboard</a>
    </div>

    <?= $mensaje ?>

    <div class="row g-4">
        <!-- Formulario para subir nueva plantilla -->
        <div class="col-md-5">
            <div class="card shadow-sm">
                <div class="card-header bg-primary text-white fw-bold">
                    📤 Subir Nueva Plantilla PowerPoint
                </div>
                <div class="card-body">
                    <form method="POST" enctype="multipart/form-data" action="">
                        <div class="mb-3">
                            <label class="form-label fw-bold">Seleccionar archivo (.pptx):</label>
                            <input type="file" name="archivo_pptx" class="form-control" accept=".pptx" required>
                        </div>
                        <button type="submit" class="btn btn-success w-100 fw-bold">Subir Plantilla</button>
                    </form>

                    <hr class="my-4">

                    <div class="alert alert-info small mb-0">
                        <strong class="d-block mb-1">💡 Recordatorio de Marcadores:</strong>
                        Asegúrate de incluir en tu plantilla `.pptx` las variables de texto exactas:
                        <ul class="mb-0 mt-1 ps-3">
                            <li><code>${TITLE}</code>, <code>${CODIGO}</code></li>
                            <li><code>${FABRICANTE}</code>, <code>${DIR_FABRICANTE}</code></li>
                            <li><code>${PRODUCTO}</code>, <code>${DESC_PRODUCTO}</code></li>
                            <li><code>${MARCA}</code>, <code>${MODELOS_FRONT}</code></li>
                            <li><code>${MODELOS_BACK}</code>, <code>${PARAMETROS}</code></li>
                            <li><code>${NORMAS}</code>, <code>${REPORTE}</code></li>
                            <li><code>${FECHA_EMISION}</code>, <code>${FECHA_EXPIRACION}</code></li>
                        </ul>
                    </div>
                </div>
            </div>
        </div>

        <!-- Tabla de plantillas disponibles -->
        <div class="col-md-7">
            <div class="card shadow-sm">
                <div class="card-header bg-dark text-white fw-bold">
                    📁 Plantillas Disponibles en el Servidor
                </div>
                <div class="card-body p-0">
                    <div class="table-responsive">
                        <table class="table table-hover align-middle m-0">
                            <thead class="table-light">
                                <tr>
                                    <th>Nombre del Archivo</th>
                                    <th>Estado</th>
                                    <th class="text-end">Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                <?php if (!empty($archivosTemplates)): ?>
                                    <?php foreach ($archivosTemplates as $filePath): 
                                        $fileName = basename($filePath);
                                        $esBase = ($fileName === 'plantilla_base.pptx');
                                    ?>
                                    <tr>
                                        <td class="fw-bold text-truncate" style="max-width: 200px;"><?= htmlspecialchars($fileName) ?></td>
                                        <td>
                                            <?php if ($esBase): ?>
                                                <span class="badge bg-success">Activa / Predeterminada</span>
                                            <?php else: ?>
                                                <span class="badge bg-secondary">Almacenada</span>
                                            <?php endif; ?>
                                        </td>
                                        <td class="text-end">
                                            <?php if (!$esBase): ?>
                                                <a href="gestionar_plantillas.php?activar=<?= urlencode($fileName) ?>" class="btn btn-sm btn-outline-primary">
                                                    Activar
                                                </a>
                                                <a href="gestionar_plantillas.php?eliminar=<?= urlencode($fileName) ?>" class="btn btn-sm btn-outline-danger" onclick="return confirm('¿Seguro que deseas eliminar esta plantilla?');">
                                                    Eliminar
                                                </a>
                                            <?php else: ?>
                                                <span class="text-muted small">En uso</span>
                                            <?php endif; ?>
                                        </td>
                                    </tr>
                                    <?php endforeach; ?>
                                <?php else: ?>
                                    <tr>
                                        <td colspan="3" class="text-center py-4 text-muted">No hay plantillas registradas.</td>
                                    </tr>
                                <?php endif; ?>
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

</body>
</html>