<?php
session_start();

$TTL = 8 * 3600; // la sesión dura 8 horas

$tiene_sesion   = isset($_SESSION['griff_auth']) && $_SESSION['griff_auth'] === true;
$sesion_vigente = (time() - ($_SESSION['griff_ts'] ?? 0)) < $TTL;

if (!$tiene_sesion || !$sesion_vigente) {
    session_destroy();
    header('Location: /3_RESULTADOS/3_RESULTADOS/login.php');
    exit;
}
?>