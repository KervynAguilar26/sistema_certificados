<?php
// includes/qr_generator.php - Generación de QR con Idioma Chino por Defecto

function obtenerRutaQR($token) {
    $ipLocal  = "192.168.110.101";
    $proyecto = "sistema_certificaciones";
    
    // Configurar lang=zh por defecto en el enlace del QR
    $baseUrl = "http://" . $ipLocal . "/" . $proyecto . "/verificar.php"; 
    $qrUrl   = $baseUrl . "?token=" . urlencode($token) . "&lang=zh";
    
    $dirQR = __DIR__ . '/../assets/qr/';
    if (!file_exists($dirQR)) {
        mkdir($dirQR, 0777, true);
    }
    
    $filename = $dirQR . 'qr_' . $token . '.png';
    
    if (!file_exists($filename)) {
        $rutaLibreria = __DIR__ . '/phpqrcode/qrlib.php';
        if (file_exists($rutaLibreria)) {
            require_once $rutaLibreria;
            if (class_exists('QRcode')) {
                QRcode::png($qrUrl, $filename, QR_ECLEVEL_M, 4);
                return $filename;
            }
        }

        // Fallback vía API de QR
        $apiUrl = "https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=" . urlencode($qrUrl);
        $imgData = @file_get_contents($apiUrl);
        if ($imgData !== false) {
            file_put_contents($filename, $imgData);
        }
    }
    
    return $filename;
}