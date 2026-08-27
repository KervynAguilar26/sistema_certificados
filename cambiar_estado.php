<?php
// cambiar_estado.php
require_once 'includes/auth.php';
require_once 'config/conexion.php';

// Verificar que solo el SuperAdmin pueda ejecutar esta acción
if (!esSuperAdmin()) {
    die("Acceso denegado.");
}

$id     = $_GET['id']     ?? null;
$estado = $_GET['estado'] ?? null;

if ($id && in_array($estado, ['activo', 'bloqueado'])) {
    $stmt = $pdo->prepare("UPDATE certificados SET estado = :estado WHERE id = :id");
    $stmt->execute([
        'estado' => $estado,
        'id'     => $id
    ]);
}

header("Location: dashboard.php");
exit;