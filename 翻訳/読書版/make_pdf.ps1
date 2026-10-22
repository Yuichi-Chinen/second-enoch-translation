# 第二エノク書 読書版PDFを生成する（HTML生成 → 仮印刷 → 目次ページ番号取得 → 本印刷）
$ErrorActionPreference = 'Stop'
$here = $PSScriptRoot
$edge = 'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
$html = Join-Path $here '第二エノク書_読書版.html'
$tmpPdf = Join-Path $env:TEMP 'enoch2_reading_pass1.pdf'
$pagesJson = Join-Path $env:TEMP 'enoch2_reading_pages.json'
$pdf = Join-Path $here '第二エノク書_日本語訳_読書版_A5縦書き.pdf'
$url = 'file:///' + ($html -replace '\\', '/')

function Print-Pdf($out) {
    $profile = Join-Path $env:TEMP 'enoch_edge_profile'
    Start-Process -FilePath $edge -Wait -ArgumentList @(
        '--headless=new', '--disable-gpu', '--no-pdf-header-footer',
        '--generate-pdf-document-outline', "--user-data-dir=`"$profile`"",
        '--virtual-time-budget=30000', "--print-to-pdf=`"$out`"", "`"$url`"")
}

python (Join-Path $here 'build.py')
Print-Pdf $tmpPdf
python (Join-Path $here 'pages.py') $tmpPdf $pagesJson
python (Join-Path $here 'build.py') --pages $pagesJson
Print-Pdf $pdf
Write-Output "出力: $pdf"
