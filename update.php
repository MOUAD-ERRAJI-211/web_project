<?php
$db = new PDO('sqlite:student_records.db');

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $tableName = $_POST['table'];
    $names = $_POST['name'];
    $absences = $_POST['absences'];
    $cheatAttempts = $_POST['cheat_attempts'];
    $points = $_POST['points'];
    $ids = $_POST['ids'];

    for ($i = 0; $i < count($ids); $i++) {
        $stmt = $db->prepare("UPDATE $tableName SET NAME = ?, NB_ABSENCE = ?, NB_CHEAT_ATTEMPT = ?, POINTS = ? WHERE ID = ?");
        $stmt->execute([$names[$i], $absences[$i], $cheatAttempts[$i], $points[$i], $ids[$i]]);
    }

    header("Location: botbot.php");
    exit();
}