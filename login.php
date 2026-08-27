<?php
// login.php
session_start();
require_once 'config/conexion.php';

$error = "";

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email    = trim($_POST['email']);
    $password = trim($_POST['password']);

    if (!empty($email) && !empty($password)) {
        $stmt = $pdo->prepare("SELECT u.*, r.nombre as rol_nombre FROM usuarios u JOIN roles r ON u.rol_id = r.id WHERE u.email = :email AND u.activo = TRUE");
        $stmt->execute(['email' => $email]);
        $usuario = $stmt->fetch();

        if ($usuario && password_verify($password, $usuario['password_hash'])) {
            $_SESSION['usuario_id']     = $usuario['id'];
            $_SESSION['usuario_nombre'] = $usuario['nombre'];
            $_SESSION['usuario_rol']    = $usuario['rol_nombre'];

            header("Location: dashboard.php");
            exit;
        } else {
            $error = "Credenciales incorrectas o usuario inactivo.";
        }
    } else {
        $error = "Por favor, ingresa tu correo y contraseña.";
    }
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Iniciar Sesión - Sistema de Certificaciones</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #0d2c5b; display: flex; align-items: center; justify-content: center; height: 100vh; }
        .card-login { width: 100%; max-width: 400px; border-radius: 12px; }
    </style>
</head>
<body>

<div class="card card-login shadow-lg p-4 bg-white">
    <div class="text-center mb-4">
        <h4 class="fw-bold text-primary">Control de Calidad</h4>
        <p class="text-muted small">Sistema de Emisión de Certificados</p>
    </div>

    <?php if ($error): ?>
        <div class="alert alert-danger py-2 small text-center"><?= $error ?></div>
    <?php endif; ?>

    <form method="POST" action="">
        <div class="mb-3">
            <label class="form-label fw-bold small">Correo Electrónico:</label>
            <input type="email" name="email" class="form-control" placeholder="admin@sistema.com" required>
        </div>
        <div class="mb-3">
            <label class="form-label fw-bold small">Contraseña:</label>
            <input type="password" name="password" class="form-control" placeholder="••••••••" required>
        </div>
        <button type="submit" class="btn btn-primary w-100 fw-bold py-2 mt-2">Ingresar al Sistema</button>
    </form>
</div>

</body>
</html>