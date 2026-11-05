<?php
if ($menu === 'content') {
    echo '<li><a href="plugin.php?plugin='
       . urlencode($plugin)
       . '&page=content.php">'
       . 'Audio Streaming Settings</a></li>';
}
?>
