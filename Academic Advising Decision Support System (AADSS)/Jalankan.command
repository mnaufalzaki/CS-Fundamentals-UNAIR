#!/bin/zsh
cd "$(dirname "$0")" || exit 1
if ! python3 -c 'import streamlit,pandas,plotly' >/dev/null 2>&1; then
  echo 'Dependensi belum tersedia. Ikuti langkah instalasi di README.md.'
  read -r '?Tekan Enter untuk menutup.'
  exit 1
fi
python3 -m streamlit run app.py --server.address 127.0.0.1
