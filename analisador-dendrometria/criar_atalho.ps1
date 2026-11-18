# Cria atalhos "Analisador de Dendrometria" (com logo) na Area de Trabalho e na pasta do programa.
$ErrorActionPreference = "Stop"
$pasta = Split-Path -Parent $MyInvocation.MyCommand.Path
$alvo  = Join-Path $pasta "iniciar_analises.bat"
$icone = Join-Path $pasta "assets\icone.ico"
$nome  = "Analisador de Dendrometria.lnk"
$destinos = @([Environment]::GetFolderPath("Desktop"), $pasta)
$shell = New-Object -ComObject WScript.Shell
foreach ($d in $destinos) {
    $lnk = $shell.CreateShortcut((Join-Path $d $nome))
    $lnk.TargetPath       = $alvo
    $lnk.WorkingDirectory = $pasta
    $lnk.IconLocation     = "$icone,0"
    $lnk.Description      = "Analisador de Dendrometria - Coleta Verde / CEPLAC"
    $lnk.WindowStyle      = 7   # janela do console minimizada
    $lnk.Save()
    Write-Host "Atalho criado em: $d"
}
