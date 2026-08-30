<?php
// diagnostico_encoding_zh.php
// Ejecutar: php diagnostico_encoding_zh.php
// No toca la base de datos ni dompdf, solo revisa el traductor.

require_once __DIR__ . '/config/traductor.php';

echo "== Diagnóstico de codificación de cadenas chinas ==\n\n";

$muestras = [
    'Fabricante:',
    'Producto:',
    'Marca Comercial:',
];

foreach ($muestras as $clave) {
    $traducido = traducirTexto($clave, 'zh');

    echo "Clave original: $clave\n";
    echo "Traducción devuelta (raw print): $traducido\n";
    echo "Longitud en bytes: " . strlen($traducido) . "\n";
    echo "¿Es UTF-8 válido? " . (mb_check_encoding($traducido, 'UTF-8') ? 'SÍ' : 'NO ⚠️') . "\n";
    echo "Hex de los primeros 30 bytes: " . bin2hex(substr($traducido, 0, 30)) . "\n";

    $escapado = htmlspecialchars($traducido, ENT_QUOTES, 'UTF-8');
    echo "Resultado de htmlspecialchars(): '" . $escapado . "'\n";
    echo "¿htmlspecialchars devolvió vacío? " . ($escapado === '' && $traducido !== '' ? 'SÍ ⚠️ ESTE ES EL PROBLEMA' : 'no') . "\n";
    echo str_repeat('-', 50) . "\n";
}

echo "\n== Info de entorno PHP ==\n";
echo "mbstring cargado: " . (extension_loaded('mbstring') ? 'sí' : 'NO ⚠️') . "\n";
echo "default_charset: " . ini_get('default_charset') . "\n";
echo "mb_internal_encoding: " . mb_internal_encoding() . "\n";

echo "\n== Info del archivo traductor.php ==\n";
$contenido = file_get_contents(__DIR__ . '/config/traductor.php');
echo "Tamaño del archivo: " . strlen($contenido) . " bytes\n";
echo "¿El archivo completo es UTF-8 válido? " . (mb_check_encoding($contenido, 'UTF-8') ? 'sí' : 'NO ⚠️') . "\n";

// Detectar BOM
$bom = substr($contenido, 0, 3);
echo "¿Tiene BOM UTF-8? " . ($bom === "\xEF\xBB\xBF" ? 'sí' : 'no') . "\n";