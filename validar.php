<?php
// validar.php - Verificación Oficial con Despliegue de Modelos Certificados
require_once 'config/conexion.php';

$token = $_GET['token'] ?? '';
$certificado = null;

if (!empty($token)) {
    $stmt = $pdo->prepare("SELECT c.*, u.nombre as analista FROM certificados c LEFT JOIN usuarios u ON c.analista_id = u.id WHERE c.token_verificacion = :token");
    $stmt->execute(['token' => $token]);
    $certificado = $stmt->fetch();
}

// PROCESAMIENTO Y LIMPIEZA DE MODELOS
$modelos_array = [];
if ($certificado && !empty($certificado['modelos_adjuntos'])) {
    $modelos_raw = array_map('trim', explode(',', $certificado['modelos_adjuntos']));
    foreach ($modelos_raw as $mod) {
        if (!empty($mod) && strtolower($mod) !== 'modelos' && strtolower($mod) !== 'modelo') {
            $mod = str_replace(['<br>', '<br/>', '<br />'], '', $mod);
            $mod = trim($mod);
            if (!empty($mod)) {
                $modelos_array[] = $mod;
            }
        }
    }
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Validación de Certificado de Calidad</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #f4f6f9; user-select: none; }
        .cert-card { max-width: 750px; margin: 40px auto; border-top: 5px solid #0d6efd; }
        .models-container { max-height: 200px; overflow-y: auto; background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 6px; padding: 10px; }
    </style>
</head>
<body>

<div class="container">
    <div class="card cert-card shadow-lg p-4">
        <?php if ($certificado): ?>
            <div class="text-center mb-4">
                <span class="badge bg-success p-2 fs-6">✓ CERTIFICADO VÁLIDO Y AUTÉNTICO</span>
                <h3 class="mt-3 text-primary"><?= htmlspecialchars($certificado['codigo_certificado']) ?></h3>
            </div>
            
            <table class="table table-striped table-bordered align-middle">
                <tr><th style="width: 30%;">Producto:</th><td><?= htmlspecialchars($certificado['producto']) ?></td></tr>
                <tr><th>Solicitante:</th><td><?= htmlspecialchars($certificado['solicitante']) ?></td></tr>
                <tr><th>Fabricante:</th><td><?= htmlspecialchars($certificado['fabricante']) ?></td></tr>
                
                <!-- MOSTRAR MODELOS CERTIFICADOS -->
                <tr>
                    <th>Modelo(s) Certificado(s):</th>
                    <td>
                        <?php if (!empty($modelos_array)): ?>
                            <div class="d-flex flex-wrap gap-1">
                                <?php if (count($modelos_array) <= 12): ?>
                                    <?php foreach ($modelos_array as $mod): ?>
                                        <span class="badge bg-secondary font-monospace"><?= htmlspecialchars($mod) ?></span>
                                    <?php endforeach; ?>
                                <?php else: ?>
                                    <div class="models-container w-100">
                                        <small class="text-muted d-block mb-1 fw-bold">Total: <?= count($modelos_array) ?> modelos asociados</small>
                                        <?php foreach ($modelos_array as $mod): ?>
                                            <span class="badge bg-secondary font-monospace mb-1"><?= htmlspecialchars($mod) ?></span>
                                        <?php endforeach; ?>
                                    </div>
                                <?php endif; ?>
                            </div>
                        <?php else: ?>
                            <span class="text-muted">Sin modelos especificados</span>
                        <?php endif; ?>
                    </td>
                </tr>

                <tr><th>Norma / Estándar:</th><td><?= htmlspecialchars($certificado['estandar_norma'] ?? $certificado['normas_ensayo'] ?? 'N/A') ?></td></tr>
                <tr><th>Fecha de Emisión:</th><td><?= htmlspecialchars($certificado['fecha_emision']) ?></td></tr>
                <tr><th>Vencimiento:</th><td><?= htmlspecialchars($certificado['fecha_expiracion']) ?></td></tr>
            </table>

            <div class="d-grid gap-2 mt-4">
                <a href="generar_pdf.php?id=<?= $certificado['id'] ?>&lang=es" target="_blank" class="btn btn-outline-primary fw-bold">
                    📄 Ver Documento PDF Certificado
                </a>
            </div>
        <?php else: ?>
            <div class="text-center py-5">
                <span class="badge bg-danger p-2 fs-6">❌ CERTIFICADO NO ENCONTRADO O INVÁLIDO</span>
                <p class="mt-3 text-muted">El código QR escaneado no corresponde a un documento registrado en el sistema oficial de control de calidad.</p>
            </div>
        <?php endif; ?>
    </div>
</div>

</body>
</html>