param([string]$dir, [string]$prompt)
Set-Location $dir
Remove-Item Env:CLAUDECODE -ErrorAction SilentlyContinue
claude $prompt
