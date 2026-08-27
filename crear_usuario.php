<?php
// crear_usuario.php
require_once 'includes/auth.php';
require_once 'config/conexion.php';

// Restricción: Solo el rol Superadmin tiene acceso a este módulo
if (!esSuperAdmin()) {
    die("Acceso denegado: No tienes permisos para administrar usuarios.");
}

$mensaje = "";

// 1. Procesar Registro de Nuevo Usuario Analista
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['accion_crear'])) {
    $nombre   = trim($_POST['nombre']);
    $email    = trim($_POST['email']);
    $password = trim($_POST['password']);
    $rol_id   = (int)$_POST['rol_id'];

    if (!empty($nombre) && !empty($email) && !empty($password)) {
        // Encriptar la contraseña con Bcrypt
        $password_hash = password_hash($password, PASSWORD_BCRYPT);

        try {
            $stmt = $pdo->prepare("INSERT INTO usuarios (nombre, email, password_hash, rol_id) VALUES (:nombre, :email, :hash, :rol_id)");
            $stmt->execute([
                'nombre' => $nombre,
                'email'  => $email,
                'hash'   => $password_hash,
                'rol_id' => $rol_id
            ]);
            $mensaje = "<div class='alert alert-success'>✅ Usuario <strong>$nombre</strong> registrado exitosamente.</div>";
        } catch (PDOException $e) {
            $mensaje = "<div class='alert alert-danger'>❌ Error al crear usuario (el correo podría estar duplicado): " . $e->getMessage() . "</div>";
        }
    }
}

// 2. Cambiar Estado del Usuario (Activar/Desactivar)
if (isset($_GET['toggle_status']) && isset($_GET['id'])) {
    $user_id = (int)$_GET['id'];
    $stmt = $pdo->prepare("UPDATE usuarios SET activo = NOT activo WHERE id = :id AND id != :my_id");
    $stmt->execute(['id' => $user_id, 'my_id' => $_SESSION['usuario_id']]);
    header("Location: crear_usuario.php");
    exit;
}

// 3. Obtener Lista de Usuarios Registrados
$usuarios = $pdo->query("
    SELECT u.id, u.nombre, u.email, u.activo, u.creado_en, r.nombre AS rol 
    FROM usuarios u 
    JOIN roles r ON u.rol_id = r.id 
    ORDER BY u.id DESC
")->fetchAll();

// Obtener Roles disponibles para la selección
$roles = $pdo->query("SELECT * FROM roles ORDER BY id ASC")->fetchAll();
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Gestión de Analistas - Sistema de Certificaciones</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">

<div class="container my-5">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2>👥 Administración de Analistas y Usuarios</h2>
        <a href="dashboard.php" class="btn btn-secondary">Volver al Dashboard</a>
    </div>

    <?= $mensaje ?>

    <div class="row g-4">
        <!-- Formulario para Registrar Nuevo Analista -->
        <div class="col-md-4">
            <div class="card shadow-sm">
                <div class="card-header bg-primary text-white font-weight-bold">
                    ➕ Registrar Nuevo Analista
                </div>
                <div class="card-body">
                    <form method="POST" action="">
                        <input type="hidden" name="accion_crear" value="1">
                        
                        <div class="mb-3">
                            <label class="form-label fw-bold">Nombre Completo:</label>
                            <input type="text" name="nombre" class="form-control" placeholder="Ej: Maria Lopez" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-bold">Correo Electrónico:</label>
                            <input type="email" name="email" class="form-control" placeholder="analista@empresa.com" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-bold">Contraseña:</label>
                            <input type="password" name="password" class="form-control" placeholder="••••••••" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label fw-bold">Rol Asignado:</label>
                            <select name="rol_id" class="form-select" required>
                                <?php foreach ($roles as $r): ?>
                                    <option value="<?= $r['id'] ?>"><?= ucfirst($r['nombre']) ?></option>
                                <?php endforeach; ?>
                            </select>
                        </div>
                        <button type="submit" class="btn btn-primary w-100 fw-bold">Guardar Usuario</button>
                    </form>
                </div>
            </div>
        </div>

        <!-- Tabla de Usuarios Registrados -->
        <div class="col-md-8">
            <div class="card shadow-sm">
                <div class="card-header bg-dark text-white font-weight-bold">
                    📋 Lista de Usuarios en el Sistema
                </div>
                <div class="card-body p-0">
                    <div class="table-responsive">
                        <table class="table table-hover align-middle m-0">
                            <thead class="table-light">
                                <tr>
                                    <th>ID</th>
                                    <th>Nombre</th>
                                    <th>Email</th>
                                    <th>Rol</th>
                                    <th>Estado</th>
                                    <th>Acción</th>
                                </tr>
                            </thead>
                            <tbody>
                                <?php foreach ($usuarios as $u): ?>
                                <tr>
                                    <td><?= $u['id'] ?></td>
                                    <td class="fw-bold"><?= htmlspecialchars($u['nombre']) ?></td>
                                    <td><?= htmlspecialchars($u['email']) ?></td>
                                    <td><span class="badge bg-info text-dark"><?= ucfirst($u['rol']) ?></span></td>
                                    <td>
                                        <?php if ($u['activo']): ?>
                                            <span class="badge bg-success">Activo</span>
                                        <?php else: ?>
                                            <span class="badge bg-danger">Inactivo</span>
                                        <?php endif; ?>
                                    </td>
                                    <td>
                                        <?php if ($u['id'] != $_SESSION['usuario_id']): ?>
                                            <a href="crear_usuario.php?toggle_status=1&id=<?= $u['id'] ?>" class="btn btn-sm <?= $u['activo'] ? 'btn-outline-danger' : 'btn-outline-success' ?>">
                                                <?= $u['activo'] ? 'Desactivar' : 'Activar' ?>
                                            </a>
                                        <?php else: ?>
                                            <span class="text-muted small">Tu Sesión</span>
                                        <?php endif; ?>
                                    </td>
                                </tr>
                                <?php endforeach; ?>
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