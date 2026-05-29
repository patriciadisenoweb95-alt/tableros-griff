<?php
session_start();
require_once __DIR__ . '/config/clave.php';

$error = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $ingresada = $_POST['clave'] ?? '';
    if (password_verify($ingresada, $CLAVE_HASH)) {
        $_SESSION['griff_auth'] = true;
        $_SESSION['griff_ts']   = time();
        header('Location: /INICIO.php');
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
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Acceso — Griff Salud</title>
    <style>
        :root {
            --azul: #1A2D9C;
            --celeste: #29ABE2;
            --bg: #eef2f9;
            --card: #ffffff;
            --line: #e2e7f0;
            --muted: #6b7793;
            --azul-txt: #15246E;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
            background: var(--bg);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 24px;
        }
        .wrap {
            width: 100%;
            max-width: 420px;
        }
        .card {
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 14px;
            border-top: 4px solid var(--celeste);
            padding: 36px 32px;
        }
        .head {
            display: flex;
            align-items: center;
            gap: 16px;
            margin-bottom: 28px;
            padding-bottom: 24px;
            border-bottom: 1px solid var(--line);
        }
        .head img {
            height: 52px;
            width: auto;
        }
        .head h1 {
            font-size: 17px;
            font-weight: 700;
            color: var(--azul);
        }
        .head p {
            font-size: 12px;
            color: var(--muted);
            margin-top: 3px;
        }
        label {
            display: block;
            font-size: 13px;
            font-weight: 600;
            color: var(--azul-txt);
            margin-bottom: 7px;
        }
        input[type=password] {
            width: 100%;
            padding: 10px 14px;
            border: 1px solid var(--line);
            border-radius: 8px;
            font-size: 14px;
            color: var(--azul-txt);
            background: #f8fafd;
            outline: none;
            transition: border-color .15s;
        }
        input[type=password]:focus {
            border-color: var(--celeste);
            background: #fff;
        }
        button {
            width: 100%;
            margin-top: 18px;
            padding: 11px;
            background: var(--azul);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: background .15s;
        }
        button:hover { background: #152380; }
        .error {
            background: #fff0f0;
            border: 1px solid #fcc;
            border-radius: 8px;
            padding: 10px 14px;
            font-size: 13px;
            color: #c0392b;
            margin-bottom: 16px;
        }
        .foot {
            text-align: center;
            font-size: 11px;
            color: var(--muted);
            margin-top: 20px;
        }
    </style>
</head>
<body>
<div class="wrap">
    <div class="card">
        <div class="head">
            <img src="/assets/griff.png" alt="Griff Salud">
            <div>
                <h1>Tableros General de Informes</h1>
                <p>Ingresá tu contraseña para acceder</p>
            </div>
        </div>
        <?php if ($error): ?>
            <div class="error"><?= htmlspecialchars($error) ?></div>
        <?php endif; ?>
        <form method="POST">
            <label>Contraseña de acceso</label>
            <input type="password" name="clave" autofocus placeholder="••••••••">
            <button type="submit">Ingresar →</button>
        </form>
    </div>
    <div class="foot">Griff Salud · Acceso restringido</div>
</div>
</body>
</html>
