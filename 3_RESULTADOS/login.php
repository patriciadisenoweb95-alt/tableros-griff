<?php
session_start();
require_once __DIR__ . '/config/clave.php';

$error = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $ingresada = $_POST['clave'] ?? '';

    if (password_verify($ingresada, $CLAVE_HASH)) {
        $_SESSION['griff_auth'] = true;
        $_SESSION['griff_ts']   = time();
        header('Location: /3_RESULTADOS/3_RESULTADOS/INICIO.php');
        exit;
    } else {
        $error = 'Contraseña incorrecta.';
    }
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Acceso — Griff</title>
    <style>
        body { font-family: sans-serif; background: #f4f4f4;
               display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
        .box { background: white; padding: 2rem; border-radius: 8px;
               box-shadow: 0 2px 10px rgba(0,0,0,.1); width: 300px; }
        h2 { margin-top: 0; }
        input[type=password] { width: 100%; padding: .5rem; margin: .5rem 0 1rem;
                               box-sizing: border-box; border: 1px solid #ccc; border-radius: 4px; }
        button { width: 100%; padding: .6rem; background: #1a56db;
                 color: white; border: none; border-radius: 4px; cursor: pointer; }
        .error { color: red; font-size: .9rem; }
    </style>
</head>
<body>
<div class="box">
    <h2>Tableros Griff</h2>
    <?php if ($error): ?>
        <p class="error"><?= htmlspecialchars($error) ?></p>
    <?php endif; ?>
    <form method="POST">
        <label>Contraseña</label>
        <input type="password" name="clave" autofocus>
        <button type="submit">Ingresar</button>
    </form>
</div>
</body>
</html>