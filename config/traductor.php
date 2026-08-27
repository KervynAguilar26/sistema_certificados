<?php
// config/traductor.php

/**
 * Traduce un texto dinámicamente al idioma destino usando el motor de traducción de Google.
 *
 * @param string $texto Texto original a traducir.
 * @param string $idiomaDestino Código del idioma (es, en, zh-CN, fr, pt, etc.).
 * @return string Texto traducido.
 */
function traducirTexto($texto, $idiomaDestino = 'es') {
    // Si el texto está vacío o el idioma es español predeterminado, no se procesa
    if (empty(trim($texto)) || $idiomaDestino === 'es') {
        return $texto;
    }

    // Mapeo especial para códigos de idioma
    if ($idiomaDestino === 'zh') {
        $idiomaDestino = 'zh-CN'; // Chino simplificado
    }

    $url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=" . $idiomaDestino . "&dt=t&q=" . urlencode($texto);

    // Ejecutar petición HTTP
    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
    curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0');
    curl_setopt($ch, CURLOPT_TIMEOUT, 5);
    $response = curl_exec($ch);
    curl_close($ch);

    if ($response) {
        $data = json_decode($response, true);
        if (isset($data[0]) && is_array($data[0])) {
            $resultado = '';
            foreach ($data[0] as $segmento) {
                $resultado .= $segmento[0] ?? '';
            }
            return !empty($resultado) ? $resultado : $texto;
        }
    }

    return $texto; // Si falla la conexión, retorna el texto original
}
?>