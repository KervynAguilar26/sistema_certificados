<?php
// verificar.php - Consulta de Autenticidad Pública con Traducción Integral de Modelos
require_once 'config/conexion.php';
require_once 'config/traductor.php';

$token = $_GET['token'] ?? null;
$lang  = $_GET['lang']  ?? 'zh'; // Chino por defecto

$certificado = null;
$mensaje_error = "";

if ($token) {
    // Buscar certificado por su token único
    $stmt = $pdo->prepare("SELECT * FROM certificados WHERE token_verificacion = :token");
    $stmt->execute(['token' => $token]);
    $certificado = $stmt->fetch();

    if (!$certificado) {
        $mensaje_error = traducirTexto("The verification token is invalid or does not exist in our records.", $lang);
    }
} else {
    $mensaje_error = traducirTexto("No valid verification token was provided.", $lang);
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

// LÓGICA DE VALIDACIÓN (Vigencia + Estado Bloqueado)
$es_valido = false;
$es_bloqueado = false;

if ($certificado) {
    $fecha_actual = date('Y-m-d');
    
    // Verificar si el estado es 'bloqueado'
    $estado_actual = strtolower(trim($certificado['estado'] ?? 'activo'));
    $es_bloqueado  = ($estado_actual === 'bloqueado');
    
    // Solo es válido si NO está bloqueado Y la fecha no ha vencido
    $es_valido = (!$es_bloqueado && $certificado['fecha_expiracion'] >= $fecha_actual);
}

// ETIQUETAS TRADUCIDAS DINÁMICAMENTE
$companyName = traducirTexto("Qingdao Technology Engineering Institute", $lang);
$companySub  = traducirTexto("Official Quality Control & Certification Division", $lang);

$lblTitle    = traducirTexto("Certificate Authenticity Verification", $lang);
$lblValid    = traducirTexto("VALID CERTIFICATE", $lang);
$lblExpired  = traducirTexto("EXPIRED CERTIFICATE", $lang);

$lblType     = traducirTexto("Certificate Type:", $lang);
$lblNo       = traducirTexto("Certificate No.:", $lang);
$lblProd     = traducirTexto("Product Line:", $lang);
$lblModels   = traducirTexto("Model(s):", $lang);
$lblApplicant= traducirTexto("Applicant:", $lang);
$lblMfr      = traducirTexto("Manufacturer:", $lang);
$lblIssue    = traducirTexto("Issue Date:", $lang);
$lblUntil    = traducirTexto("Expiration Date:", $lang);
$lblFooter   = traducirTexto("This electronic document has been issued and authenticated by Qingdao Technology Engineering Institute.", $lang);

// TEXTO DEL CONTADOR DE MODELOS NATIVO POR IDIOMA
$totalCount = count($modelos_array);
if ($lang === 'zh') {
    $lblTotalModels = "共 {$totalCount} 个注册型号";
} elseif ($lang === 'en') {
    $lblTotalModels = "Total: {$totalCount} models registered";
} else {
    $lblTotalModels = "Total: {$totalCount} modelo(s) registrado(s)";
}
?>
<!DOCTYPE html>
<html lang="<?= htmlspecialchars($lang) ?>">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?= htmlspecialchars($lblTitle) ?></title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
    <style>
        body { background-color: #f8fafc; font-family: system-ui, -apple-system, sans-serif; }
        .verify-card { max-width: 620px; margin: 30px auto; border-radius: 16px; }
        .company-logo { max-height: 55px; width: auto; }
        .status-badge { font-size: 0.95rem; padding: 10px 20px; border-radius: 30px; letter-spacing: 0.5px; }
        .models-scroll { max-height: 140px; overflow-y: auto; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 8px; }
        .badge-model { background-color: #e2e8f0; color: #334155; font-family: monospace; font-size: 0.8rem; border: 1px solid #cbd5e1; }
    </style>
</head>
<body>

<div class="container px-3">
    <div class="card verify-card shadow-lg border-0">
        
        <!-- Language Selector Header -->
        <div class="card-header bg-white border-0 pt-3 px-4 d-flex justify-content-between align-items-center">
            <span class="text-muted small fw-bold"><i class="bi bi-globe me-1"></i> Language:</span>
            <div class="btn-group btn-group-sm" role="group">
                <a href="verificar.php?token=<?= urlencode($token) ?>&lang=zh" class="btn btn-outline-primary <?= $lang==='zh'?'active':'' ?>">中文</a>
                <a href="verificar.php?token=<?= urlencode($token) ?>&lang=en" class="btn btn-outline-primary <?= $lang==='en'?'active':'' ?>">English</a>
                <a href="verificar.php?token=<?= urlencode($token) ?>&lang=es" class="btn btn-outline-primary <?= $lang==='es'?'active':'' ?>">Español</a>
            </div>
        </div>

        <div class="card-body p-4 text-center">
            <!-- LOGO Y NOMBRE DE LA EMPRESA TRADUCIDO -->
            <div class="mb-3">
                <img src="assets/img/logo.png" alt="Company Logo" class="company-logo mb-2" onerror="this.style.display='none'">
                <h5 class="fw-bold text-dark m-0"><?= htmlspecialchars($companyName) ?></h5>
                <small class="text-muted d-block mt-1"><?= htmlspecialchars($companySub) ?></small>
            </div>

            <hr class="my-3 text-secondary opacity-25">

            <h5 class="fw-bold text-primary mb-3"><i class="bi bi-shield-check me-1"></i> <?= htmlspecialchars($lblTitle) ?></h5>
            
            <?php if ($es_bloqueado): ?>
                <!-- VISTA EXCLUSIVA PARA CERTIFICADOS BLOQUEADOS -->
                <div class="alert alert-danger p-4 my-3 rounded-4 shadow-sm text-center" role="alert">
                    <i class="bi bi-x-octagon-fill text-danger display-4 d-block mb-3"></i>
                    <h4 class="fw-bold mb-2">
                        <?= htmlspecialchars(traducirTexto("CERTIFICATE SUSPENDED", $lang)) ?>
                    </h4>
                    <p class="mb-0 text-muted">
                        <?= htmlspecialchars(traducirTexto("This certificate has been administratively suspended.", $lang)) ?>
                    </p>
                </div>

            <?php elseif ($certificado): ?>
                <!-- VISTA NORMAL CUANDO EL CERTIFICADO ESTÁ ACTIVO -->
                <?php if ($es_valido): ?>
                    <span class="badge bg-success text-white status-badge mb-4">
                        <i class="bi bi-check-circle-fill me-1"></i> <?= htmlspecialchars($lblValid) ?>
                    </span>
                <?php else: ?>
                    <span class="badge bg-warning text-dark status-badge mb-4">
                        <i class="bi bi-exclamation-triangle-fill me-1"></i> <?= htmlspecialchars($lblExpired) ?>
                    </span>
                <?php endif; ?>

                <!-- Tabla con datos del certificado -->
                <div class="table-responsive bg-light p-3 rounded-3 border text-start">
                    <table class="table table-borderless align-middle mb-0">
                        <tr>
                            <td class="fw-bold text-secondary" style="width: 38%;"><?= htmlspecialchars($lblType) ?></td>
                            <td class="fw-bold text-primary"><?= htmlspecialchars(traducirTexto($certificado['tipo_certificado'] ?? 'CERTIFICATE OF COMPLIANCE', $lang)) ?></td>
                        </tr>
                        <tr>
                            <td class="fw-bold text-secondary"><?= htmlspecialchars($lblNo) ?></td>
                            <td class="fw-bold text-dark"><?= htmlspecialchars($certificado['codigo_certificado']) ?></td>
                        </tr>
                        <tr>
                            <td class="fw-bold text-secondary"><?= htmlspecialchars($lblProd) ?></td>
                            <td class="fw-bold text-dark"><?= htmlspecialchars(traducirTexto($certificado['producto'], $lang)) ?></td>
                        </tr>
                        <tr>
                            <td class="fw-bold text-secondary"><?= htmlspecialchars($lblApplicant) ?></td>
                            <td><?= htmlspecialchars(traducirTexto($certificado['solicitante'], $lang)) ?></td>
                        </tr>
                        <tr>
                            <td class="fw-bold text-secondary"><?= htmlspecialchars($lblMfr) ?></td>
                            <td><?= htmlspecialchars(traducirTexto($certificado['fabricante'], $lang)) ?></td>
                        </tr>

                        <!-- FILA DE MODELOS ADJUNTOS -->
                        <tr>
                            <td class="fw-bold text-secondary align-top pt-2"><?= htmlspecialchars($lblModels) ?></td>
                            <td>
                                <?php if (!empty($modelos_array)): ?>
                                    <?php if (count($modelos_array) <= 8): ?>
                                        <div class="d-flex flex-wrap gap-1">
                                            <?php foreach ($modelos_array as $mod): ?>
                                                <span class="badge badge-model"><?= htmlspecialchars($mod) ?></span>
                                            <?php endforeach; ?>
                                        </div>
                                    <?php else: ?>
                                        <div class="models-scroll">
                                            <small class="text-muted d-block mb-1 fw-bold"><?= htmlspecialchars($lblTotalModels) ?></small>
                                            <div class="d-flex flex-wrap gap-1">
                                                <?php foreach ($modelos_array as $mod): ?>
                                                    <span class="badge badge-model"><?= htmlspecialchars($mod) ?></span>
                                                <?php endforeach; ?>
                                            </div>
                                        </div>
                                    <?php endif; ?>
                                <?php else: ?>
                                    <span class="text-muted small"><?= htmlspecialchars(traducirTexto("See Attached Annex in PDF", $lang)) ?></span>
                                <?php endif; ?>
                            </td>
                        </tr>

                        <tr>
                            <td class="fw-bold text-secondary"><?= htmlspecialchars($lblIssue) ?></td>
                            <td><?= htmlspecialchars($certificado['fecha_emision']) ?></td>
                        </tr>
                        <tr>
                            <td class="fw-bold text-secondary"><?= htmlspecialchars($lblUntil) ?></td>
                            <td><?= htmlspecialchars($certificado['fecha_expiracion']) ?></td>
                        </tr>
                    </table>
                </div>

                <div class="alert alert-info mt-4 mb-0 text-center border-0 shadow-sm" role="alert" style="background-color: #e0f2fe; color: #0369a1;">
                    <small><i class="bi bi-info-circle me-1"></i> <?= htmlspecialchars($lblFooter) ?></small>
                </div>

            <?php else: ?>
                <!-- ERROR SI EL TOKEN NO EXISTE EN LA BASE DE DATOS -->
                <div class="alert alert-danger text-center p-4 my-3" role="alert">
                    <i class="bi bi-shield-x text-danger display-4 d-block mb-2"></i>
                    <h5 class="fw-bold mb-2">Invalid or Non-Existent Document</h5>
                    <p class="mb-0 text-muted"><?= htmlspecialchars($mensaje_error) ?></p>
                </div>
            <?php endif; ?>
        </div>

        <div class="card-footer bg-light text-center py-3 border-0 rounded-bottom-4">
            <small class="text-muted">© <?= date('Y') ?> <?= htmlspecialchars($companyName) ?> - All Rights Reserved</small>
        </div>
    </div>
</div>

</body>
</html>