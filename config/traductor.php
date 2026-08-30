<?php
// config/traductor.php

function traducirTexto($texto, $idiomaDestino = 'es') {
    if (empty(trim($texto))) {
        return $texto;
    }

    // Normalización de códigos de idioma para Google API
    if ($idiomaDestino === 'zh') {
        $idiomaDestino = 'zh-CN';
    }

    // Petición a la API de Google Translate
    $url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=" . $idiomaDestino . "&dt=t&q=" . urlencode($texto);

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

    return $texto;
}
?>