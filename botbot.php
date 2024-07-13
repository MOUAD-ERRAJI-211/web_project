<?php
$db = new PDO('sqlite:student_records.db');
function displayTableData($tableName) {
    global $db;
    $stmt = $db->prepare("SELECT * FROM $tableName");
    $stmt->execute();
    $result = $stmt->fetchAll(PDO::FETCH_ASSOC);

    if ($result) {
        echo "<h2>$tableName Table</h2>";
        echo "<form method='post' action='update.php'>";
        echo "<table>";
        echo "<tr><th>ID</th><th>Name</th><th>Absences</th><th>Cheat Attempts</th><th>Points</th><th>Action</th></tr>";

        foreach ($result as $row) {
            echo "<tr>";
            echo "<td>" . $row['ID'] . "</td>";
            echo "<td><input type='text' name='name[]' value='" . $row['NAME'] . "' readonly></td>";
            echo "<td><input type='number' name='absences[]' value='" . $row['NB_ABSENCE'] . "'></td>";
            echo "<td><input type='number' name='cheat_attempts[]' value='" . $row['NB_CHEAT_ATTEMPT'] . "'></td>";
            echo "<td><input type='number' name='points[]' value='" . $row['POINTS'] . "'></td>";
            echo "<td><input type='hidden' name='ids[]' value='" . $row['ID'] . "'><button type='submit' name='table' value='$tableName'>Update</button></td>";
            echo "</tr>";
        }

        echo "</table>";
        echo "</form>";
    } else {
        echo "Error retrieving data from $tableName table.";
    }
}
?>

<!DOCTYPE html>
<html>
<head>
    <title>Student Records</title>
    <style>
        table {
            border-collapse: collapse;
            width: 100%;
        }

        th, td {
            padding: 8px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }

        th {
            background-color: #f2f2f2;
        }
    </style>
</head>
<body>
    <?php
    displayTableData('GI');
    displayTableData('IDSD');
    ?>
</body>
</html>