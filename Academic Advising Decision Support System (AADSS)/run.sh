#!/usr/bin/env bash
# Menjalankan AADSS di Linux/macOS (bash).
cd "$(dirname "$0")" || exit 1
if ! python3 -c 'import streamlit,pandas,plotly' >/dev/null 2>&1; then
  echo 'Dependensi belum tersedia. Jalankan: pip install -r requirements.txt'
  exit 1
fi
exec python3 -m streamlit run app.py --server.address 127.0.0.1
