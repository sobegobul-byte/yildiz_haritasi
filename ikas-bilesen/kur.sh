#!/bin/bash
# ikas code components projende çalıştır:  bash /yol/yildiz_haritasi/ikas-bilesen/kur.sh
# (ikas.config.json'un bulunduğu klasörde olmalısın)
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
C=YildizHaritasiTasarim
[ -f ikas.config.json ] || { echo "Bu komutu ikas projesinin klasöründe çalıştır (ikas.config.json yok)"; exit 1; }

npx ikas-component config add-component --name "$C" --type section --props "$(cat "$HERE/props.json")"
npx ikas-component config add-prop-group --component $C --id settings --name "Ayarlar"
npx ikas-component config add-prop-group --component $C --id texts --name "Metinler"
for p in designerUrl designOptionName woodOptionName frameHeight autoAddToCart; do
  npx ikas-component config update-prop --component $C --prop $p --group settings > /dev/null
done
for p in frameTitle addingText addedText filledText errorText missingOptionText; do
  npx ikas-component config update-prop --component $C --prop $p --group texts > /dev/null
done

cp "$HERE/$C/index.tsx" "$HERE/$C/styles.css" "src/components/$C/"
npx ikas-component check --json
npx ikas-component build
echo "Tamam: $C bileşeni eklendi ve derlendi."
