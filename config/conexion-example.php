<?php
// config/conexion.php
$host     = "localhost";
$port     = "5432";
$dbname   = "certificaciones_db";
$user     = "postgres";
$password = "postgres";

try {
    // Forzar codificación UTF-8 en la conexión
    $dsn = "pgsql:host=$host;port=$port;dbname=$dbname;options='--client_encoding=UTF8'";
    $pdo = new PDO($dsn, $user, $password, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
    ]);
    // Asegurar codificación (opcional pero recomendado)
    $pdo->exec("SET client_encoding TO 'UTF8'");
} catch (PDOException $e) {
    die("Error de conexión a la base de datos: " . $e->getMessage());
}
?>