<?php
// validar.php
require_once 'config/conexion.php';

$token = $_GET['token'] ?? '';
$certificado = null;

if (!empty($token)) {
    $stmt = $pdo->prepare("SELECT c.*, u.nombre as analista FROM certificados c LEFT JOIN usuarios u ON c.analista_id = u.id WHERE c.token_verificacion = :token");
    $stmt->execute(['token' => $token]);
    $certificado = $stmt->fetch();
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
        .cert-card { max-width: 650px; margin: 40px auto; border-top: 5px solid #0d6efd; }
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
            
            <table class="table table-striped table-bordered">
                <tr><th>Producto:</th><td><?= htmlspecialchars($certificado['producto']) ?></td></tr>
                <tr><th>Solicitante:</th><td><?= htmlspecialchars($certificado['solicitante']) ?></td></tr>
                <tr><th>Fabricante:</th><td><?= htmlspecialchars($certificado['fabricante']) ?></td></tr>
                <tr><th>Norma / Estándar:</th><td><?= htmlspecialchars($certificado['estandar_norma']) ?></td></tr>
                <tr><th>Fecha de Emisión:</th><td><?= htmlspecialchars($certificado['fecha_emision']) ?></td></tr>
                <tr><th>Vencimiento:</th><td><?= htmlspecialchars($certificado['fecha_expiracion']) ?></td></tr>
            </table>

            <div class="d-grid gap-2 mt-4">
                <a href="generar_pdf.php?token=<?= $certificado['token_verificacion'] ?>" target="_blank" class="btn btn-outline-primary fw-bold">
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