<?php
// config/traductor.php - Diccionario Dinámico Ampliado para Múltiples Tipos de Certificados

function obtenerDiccionario() {
    return [
        // --- TIPOS DE CERTIFICADOS COMUNES ---
        'CERTIFICATE OF COMPLIANCE' => [
            'es' => 'CERTIFICADO DE CUMPLIMIENTO',
            'en' => 'CERTIFICATE OF COMPLIANCE',
            'zh' => '合规证书'
        ],
        'CERTIFICATE OF CONFORMITY & QUALITY' => [
            'es' => 'CERTIFICADO DE CONFORMIDAD Y CALIDAD',
            'en' => 'CERTIFICATE OF CONFORMITY & QUALITY',
            'zh' => '合格与质量证书'
        ],
        'CERTIFICATE OF CONFORMITY' => [
            'es' => 'CERTIFICADO DE CONFORMIDAD',
            'en' => 'CERTIFICATE OF CONFORMITY',
            'zh' => '符合性证书'
        ],
        'CERTIFICATE OF QUALITY' => [
            'es' => 'CERTIFICADO DE CALIDAD',
            'en' => 'CERTIFICATE OF QUALITY',
            'zh' => '质量证书'
        ],
        'CERTIFICATE OF ANALYSIS' => [
            'es' => 'CERTIFICADO DE ANÁLISIS',
            'en' => 'CERTIFICATE OF ANALYSIS',
            'zh' => '分析证书'
        ],
        'DECLARATION OF CONFORMITY' => [
            'es' => 'DECLARACIÓN DE CONFORMIDAD',
            'en' => 'DECLARATION OF CONFORMITY',
            'zh' => '符合性声明'
        ],

        // --- ETIQUETAS FIJAS DEL SISTEMA ---
        'Fabricante:' => [
            'es' => 'Fabricante:',
            'en' => 'Manufacturer:',
            'zh' => '制造商:'
        ],
        'Producto:' => [
            'es' => 'Producto:',
            'en' => 'Product:',
            'zh' => '产品:'
        ],
        'Marca Comercial:' => [
            'es' => 'Marca Comercial:',
            'en' => 'Trademark:',
            'zh' => '商标:'
        ],
        'Modelo(s):' => [
            'es' => 'Modelo(s):',
            'en' => 'Model(s):',
            'zh' => '型号:'
        ],
        'Parámetros de Ensayo:' => [
            'es' => 'Parámetros de Ensayo:',
            'en' => 'Test Parameters:',
            'zh' => '测试参数:'
        ],
        'Probado según norma:' => [
            'es' => 'Probado según norma:',
            'en' => 'Tested according to standard:',
            'zh' => '按标准测试:'
        ],
        'Informe de ensayo N°:' => [
            'es' => 'Informe de ensayo N°:',
            'en' => 'Test report No.:',
            'zh' => '检测报告编号:'
        ],
        'Validez:' => [
            'es' => 'Validez:',
            'en' => 'Validity:',
            'zh' => '有效性:'
        ],
        'Emisión' => [
            'es' => 'Emisión',
            'en' => 'Emission',
            'zh' => '排放'
        ],
        'ANEXO DE MODELOS CERTIFICADOS' => [
            'es' => 'ANEXO DE MODELOS CERTIFICADOS',
            'en' => 'ANNEX OF CERTIFIED MODELS',
            'zh' => '认证型号附件'
        ],
        'Lista de Modelos Certificados:' => [
            'es' => 'Lista de Modelos Certificados:',
            'en' => 'List of Certified Models:',
            'zh' => '认证型号列表:'
        ],
        'Ver Anexo Adjunto (Página 2)' => [
            'es' => 'Ver Anexo Adjunto (Página 2)',
            'en' => 'See Attached Annex (Page 2)',
            'zh' => '见附件(第2页)'
        ],
        'El producto fue probado de forma voluntaria y cumple con los requisitos esenciales de calidad y seguridad.' => [
            'es' => 'El producto fue probado de forma voluntaria y cumple con los requisitos esenciales de calidad y seguridad.',
            'en' => 'The product was tested voluntarily and meets essential quality and safety requirements.',
            'zh' => '该产品经过自愿测试，符合基本的质量和安全要求。'
        ]
    ];
}

function traducirTexto($texto, $idiomaDestino = 'es') {
    $textoTrim = trim($texto);
    if (empty($textoTrim)) {
        return $texto;
    }

    $diccionario = obtenerDiccionario();

    // 1. Coincidencia exacta (mayúsculas/minúsculas)
    if (isset($diccionario[$textoTrim][$idiomaDestino])) {
        return $diccionario[$textoTrim][$idiomaDestino];
    }

    // 2. Coincidencia insensible a mayúsculas
    $textoUpper = strtoupper($textoTrim);
    foreach ($diccionario as $clave => $traducciones) {
        if (strtoupper($clave) === $textoUpper && isset($traducciones[$idiomaDestino])) {
            return $traducciones[$idiomaDestino];
        }
    }

    if ($idiomaDestino === 'es') {
        return $texto;
    }

    // 3. Fallback a la API de Google Translate para cualquier otro valor nuevo/personalizado
    $targetLang = ($idiomaDestino === 'zh') ? 'zh-CN' : $idiomaDestino;
    $url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=" . $targetLang . "&dt=t&q=" . urlencode($textoTrim);

    $ch = curl_init();
    curl_setopt($ch, CURLOPT_URL, $url);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
    curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)');
    curl_setopt($ch, CURLOPT_TIMEOUT, 4);
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