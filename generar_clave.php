<?php
// generar_clave.php
require_once 'config/conexion.php';

$nueva_clave = "admin123";
$hash_real   = password_hash($nueva_clave, PASSWORD_BCRYPT);
$email_admin = "admin@sistema.com";

try {
    $stmt = $pdo->prepare("
        INSERT INTO usuarios (nombre, email, password_hash, rol_id, activo)
        VALUES ('Administrador Principal', :email, :hash, 1, TRUE)
        ON CONFLICT (email) 
        DO UPDATE SET password_hash = :hash, activo = TRUE
    ");
    
    $stmt->execute([
        'email' => $email_admin,
        'hash'  => $hash_real
    ]);

    echo "<h2 style='color: green;'>✅ ¡Base de datos vinculada y Usuario Admin creado!</h2>";
    echo "<p><strong>Usuario:</strong> admin@sistema.com</p>";
    echo "<p><strong>Contraseña:</strong> admin123</p>";
    echo "<br><a href='login.php' style='font-size: 18px; font-weight: bold;'>👉 Ir al Login</a>";

} catch (PDOException $e) {
    echo "<h2 style='color: red;'>❌ Error:</h2><p>" . $e->getMessage() . "</p>";
}
?>