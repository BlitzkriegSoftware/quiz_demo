# Command file for Sphinx documentation

Push-Location $PSScriptRoot

if (-not $env:SPHINXBUILD) {
    $SPHINXBUILD = "sphinx-build"
}
else {
    $SPHINXBUILD = $env:SPHINXBUILD
}

$SOURCEDIR = "docs/source"
$BUILDDIR = "docs/build"

# Check that sphinx-build is available
$sphinxCmd = Get-Command $SPHINXBUILD -ErrorAction SilentlyContinue
if (-not $sphinxCmd) {
    Write-Host ""
    Write-Host "The 'sphinx-build' command was not found. Make sure you have Sphinx"
    Write-Host "installed, then set the SPHINXBUILD environment variable to point"
    Write-Host "to the full path of the 'sphinx-build' executable. Alternatively you"
    Write-Host "may add the Sphinx directory to PATH."
    Write-Host ""
    Write-Host "If you don't have Sphinx installed, grab it from"
    Write-Host "https://www.sphinx-doc.org/"
    Pop-Location
    exit 1
}

$target = $args[0]
$SPHINXOPTS = $env:SPHINXOPTS
$O = $env:O

if (-not $target) {
    $target = "help"
}

& $SPHINXBUILD -M $target $SOURCEDIR $BUILDDIR $SPHINXOPTS $O

Pop-Location
