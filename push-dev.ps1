$git = "C:\Program Files\Git\cmd\git.exe"
$date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
& $git add .
& $git commit -m "Update from Antigravity - $date"
& $git push origin dev
Write-Host "Pushed successfully to branch 'dev'!" -ForegroundColor Green
