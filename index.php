<?php
// index.php
session_start();

// Si el usuario ya inició sesión, redirigir al Dashboard; de lo contrario, al Login
if (isset($_SESSION['usuario_id'])) {
    header("Location: dashboard.php");
} else {
    header("Location: login.php");
}
exit;
?>