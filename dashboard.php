<?php
// dashboard.php - Panel de Control Principal con Control de Acceso por Roles
require_once 'includes/auth.php';
require_once 'config/conexion.php';

// Obtener certificados con información del analista
$stmt = $pdo->query("
    SELECT c.*, u.nombre AS analista_nombre 
    FROM certificados c 
    LEFT JOIN usuarios u ON c.analista_id = u.id 
    ORDER BY c.id DESC
");
$certificados = $stmt->fetchAll();
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Panel de Control - Control de Calidad</title>
    
    <!-- Bootstrap 5 CSS & Icons -->
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    
    <!-- DataTables CSS (Buscador y Paginación) -->
    <link rel="stylesheet" href="https://cdn.datatables.net/1.13.6/css/dataTables.bootstrap5.min.css">
    <link rel="stylesheet" href="assets/css/style.css">
</head>
<body>

<!-- BARRA DE NAVEGACIÓN INSTITUCIONAL -->
<nav class="navbar navbar-expand-lg navbar-dark navbar-corporate mb-4">
    <div class="container-fluid px-4">
        <a class="navbar-brand d-flex align-items-center" href="dashboard.php">
            <i class="bi bi-shield-check fs-3 me-2 text-warning"></i>
            <span class="brand-title fs-5">SISTEMA DE CERTIFICACIONES DE CALIDAD</span>
        </a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
            <span class="navbar-toggler-icon"></span>
        </button>
        
        <div class="collapse navbar-collapse" id="navbarNav">
            <ul class="navbar-nav me-auto mb-2 mb-lg-0 ms-3">
                <li class="nav-item">
                    <a class="nav-link active fw-semibold" href="dashboard.php">
                        <i class="bi bi-speedometer2 me-1"></i> Dashboard
                    </a>
                </li>
                <li class="nav-item">
                    <a class="nav-link text-white fw-semibold" href="nuevo_certificado.php">
                        <i class="bi bi-file-earmark-plus me-1"></i> Nuevo Certificado
                    </a>
                </li>

                <?php if (esSuperAdmin()): ?>
                    <li class="nav-item">
                        <a class="nav-link text-warning fw-semibold" href="crear_usuario.php">
                            <i class="bi bi-people me-1"></i> Gestionar Analistas
                        </a>
                    </li>
                <?php endif; ?>
            </ul>

            <div class="d-flex align-items-center text-white">
                <div class="me-3 text-end d-none d-sm-block">
                    <div class="fw-bold"><?= htmlspecialchars($_SESSION['usuario_nombre'] ?? 'Usuario') ?></div>
                    <small class="badge bg-light text-dark"><?= strtoupper($_SESSION['usuario_rol'] ?? 'Analista') ?></small>
                </div>
                <a href="logout.php" class="btn btn-outline-light btn-sm fw-bold">
                    <i class="bi bi-box-arrow-right"></i> Salir
                </a>
            </div>
        </div>
    </div>
</nav>

<!-- CONTENIDO PRINCIPAL -->
<div class="container-fluid px-4">

    <!-- TABLA PRINCIPAL DE CERTIFICADOS -->
    <div class="clean-card mb-5">
        <div class="p-3 bg-light border-bottom d-flex justify-content-between align-items-center">
            <h5 class="m-0 fw-bold text-primary">
                <i class="bi bi-table me-2"></i> Certificados Registrados en el Sistema
            </h5>
            <a href="nuevo_certificado.php" class="btn btn-primary-corp btn-sm px-3">
                <i class="bi bi-plus-lg me-1"></i> Registrar Certificado
            </a>
        </div>
        
        <div class="p-3">
            <div class="table-responsive">
                <table id="tablaCertificados" class="table table-corporate align-middle mb-0 w-100">
                    <thead>
                        <tr>
                            <th class="ps-3">N° Certificado</th>
                            <th>Solicitante</th>
                            <th>Fabricante</th>
                            <th>Producto</th>
                            <th>Vencimiento</th>
                            <th class="text-center">Estado</th>
                            <th class="text-center">Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php if (!empty($certificados)): ?>
                            <?php foreach ($certificados as $row): ?>
                            <tr>
                                <td class="ps-3 fw-bold text-primary"><?= htmlspecialchars($row['codigo_certificado']) ?></td>
                                <td><?= htmlspecialchars($row['solicitante']) ?></td>
                                <td><?= htmlspecialchars($row['fabricante']) ?></td>
                                <td>
                                    <span class="fw-semibold"><?= htmlspecialchars($row['producto']) ?></span>
                                    <small class="d-block text-muted text-truncate" style="max-width: 200px;">
                                        <?= htmlspecialchars($row['descripcion_producto']) ?>
                                    </small>
                                </td>
                                <td><?= htmlspecialchars($row['fecha_expiracion']) ?></td>
                                
                                <!-- ESTADO -->
                                <td class="text-center">
                                    <?php if (($row['estado'] ?? 'activo') === 'activo'): ?>
                                        <span class="badge bg-success">Activo</span>
                                    <?php else: ?>
                                        <span class="badge bg-danger">Bloqueado / Impago</span>
                                    <?php endif; ?>
                                </td>

                                <!-- ACCIONES CONTROLADAS POR ROL -->
                                <td class="text-center py-3">
                                    <div class="btn-group" role="group">
                                        
                                        <!-- EDITAR: DISPONIBLE PARA ANALISTAS Y ADMINS -->
                                        <a href="editar_certificado.php?id=<?= $row['id'] ?>" class="btn btn-sm btn-outline-warning fw-bold me-1" title="Editar Registro">
                                            <i class="bi bi-pencil-square"></i> Editar
                                        </a>

                                        <?php if (esSuperAdmin()): ?>
                                            <!-- DESPLEGABLE PDF: EXCLUSIVO PARA ADMINISTRADORES -->
                                            <div class="btn-group me-1" role="group">
                                                <button type="button" class="btn btn-sm btn-outline-danger dropdown-toggle fw-bold" data-bs-toggle="dropdown" aria-expanded="false">
                                                    <i class="bi bi-file-earmark-pdf"></i> PDF
                                                </button>
                                                <ul class="dropdown-menu shadow">
                                                    <li><a class="dropdown-item" href="generar_pdf.php?id=<?= $row['id'] ?>&lang=es" target="_blank">🇪🇸 Español</a></li>
                                                    <li><a class="dropdown-item" href="generar_pdf.php?id=<?= $row['id'] ?>&lang=en" target="_blank">🇬🇧 Inglés</a></li>
                                                    <li><a class="dropdown-item" href="generar_pdf.php?id=<?= $row['id'] ?>&lang=zh" target="_blank">🇨🇳 Chino</a></li>
                                                </ul>
                                            </div>

                                            <!-- BLOQUEO / ACTIVACIÓN: EXCLUSIVO PARA ADMINISTRADORES -->
                                            <?php if (($row['estado'] ?? 'activo') === 'activo'): ?>
                                                <a href="cambiar_estado.php?id=<?= $row['id'] ?>&estado=bloqueado" 
                                                   class="btn btn-sm btn-outline-danger fw-bold" 
                                                   title="Bloquear por impago"
                                                   onclick="return confirm('¿Desea bloquear este certificado? Al escanear el QR figurará como NO VÁLIDO.');">
                                                    <i class="bi bi-lock-fill"></i> Bloquear
                                                </a>
                                            <?php else: ?>
                                                <a href="cambiar_estado.php?id=<?= $row['id'] ?>&estado=activo" 
                                                   class="btn btn-sm btn-success fw-bold" 
                                                   title="Reactivar certificado"
                                                   onclick="return confirm('¿Desea reactivar este certificado?');">
                                                    <i class="bi bi-unlock-fill"></i> Activar
                                                </a>
                                            <?php endif; ?>
                                        <?php endif; ?>

                                    </div>
                                </td>
                            </tr>
                            <?php endforeach; ?>
                        <?php endif; ?>
                    </tbody>
                </table>
            </div>
        </div>
    </div>

</div>

<!-- Scripts Necesarios (jQuery, Bootstrap y DataTables) -->
<script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js"></script>
<script src="https://cdn.datatables.net/1.13.6/js/dataTables.bootstrap5.min.js"></script>

<script>
$(document).ready(function() {
    $('#tablaCertificados').DataTable({
        "dom": '<"row mb-3"<"col-md-6"l><"col-md-6"f>>rt<"row mt-3"<"col-md-5"i><"col-md-7"p>>',
        "language": {
            "sProcessing":     "Procesando...",
            "sLengthMenu":     "Mostrar _MENU_ registros por página",
            "sZeroRecords":    "No se encontraron certificados coincidentes",
            "sEmptyTable":     "No hay certificados registrados actualmente",
            "sInfo":           "Mostrando certificados del _START_ al _END_ de un total de _TOTAL_",
            "sInfoEmpty":      "Mostrando 0 certificados",
            "sInfoFiltered":   "(filtrado de un total de _MAX_ registros)",
            "sSearch":         "🔎 Buscar Certificado:",
            "oPaginate": {
                "sFirst":    "Primero",
                "sLast":     "Último",
                "sNext":     "Siguiente",
                "sPrevious": "Anterior"
            }
        },
        "pageLength": 10,
        "order": [[ 0, "desc" ]]
    });
});
</script>

</body>
</html>