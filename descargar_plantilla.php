<?php
// descargar_plantilla.php
header('Content-Type: text/csv; charset=utf-8');
header('Content-Disposition: attachment; filename=plantilla_modelos.csv');

$output = fopen('php://output', 'w');
fputcsv($output, ['Modelos']);
fputcsv($output, ['MODELO-001']);
fputcsv($output, ['MODELO-002']);
fputcsv($output, ['MODELO-003']);
fclose($output);
exit;