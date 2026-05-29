<?php
session_start();
session_destroy();
header('Location: /3_RESULTADOS/3_RESULTADOS/login.php');
exit;
?>