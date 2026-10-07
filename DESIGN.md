# DESIGN.md

> Arah desain ini disusun oleh agent (bukan brand guide bawaan produk). Secara jujur: arah buatan agent cenderung condong ke default AI. Brief dari pemilik: screener swing IDX harian untuk trader retail Indonesia, dipakai saat jam market. Koreksi arah selalu diterima, dan file ini sumber kebenarannya.

## Design Read

Reading this as: trading dashboard harian untuk swing trader IDX, dengan bahasa visual market terminal yang rapi, dial ENERGY 2 / RHYTHM 2 / MOTION 1.

## Dials

- ENERGY 2: tidak datar, tidak berteriak. Kepadatan data tinggi, tapi hierarki tegas.
- RHYTHM 2: dominan satu pola (tabel hasil scan) dengan satu break sengaja (rail kanan di halaman detail, susunan asimetris).
- MOTION 1: hover dan focus transition saja. Tidak ada animasi masuk, tidak ada loop.

## Identity

- Nama kerja: **Swing Screener IDX** (deskriptif; bukan brand final).
- Maskot arah: pita harga (tape). Motif pengulang: **signal meter** bertakik 0 sampai 100, muncul di baris tabel dan besar di halaman detail. Satu motif, diulang konsisten.
- Keputusan inti yang didukung layar: "dari daftar ini, mana yang layak ditradingkan besok, dan di harga berapa entry/SL/TP-nya." Tabel hasil adalah halaman; bukan sidebar plus kartu statistik.

## Palette

Dua mode, keduanya wajib jalan. Dark adalah default karena dipakai saat jam market dan berdampingan dengan aplikasi broker; light untuk pemakaian siang.

- Inti netral: ink/near-black (dark) atau paper gray (light).
- Hijau pasar = naik, positif, POTENTIAL BUY. Merah pasar = turun, negatif, risiko.
- Satu aksen: **amber sinyal**. Dipakai hanya untuk: focus ring, baris terpilih, meter skor bagian atas, dan EMA20 di chart.
- Rasio teks utama minimal WCAG AA 4.5:1 di kedua mode.

## Tipografi

- **Plus Jakarta Sans** (400/500/600/700): teks UI. Dipilih karena grotesque geometris yang netral dan buatan Indonesia, konteksnya IDX.
- **Source Serif 4** (600): wordmark dan judul halaman. Memberi suara "riset", bukan "startup".
- **JetBrains Mono** (400/500/600): semua angka (harga, RSI, skor di tabel, R:R). Bukan gaya-gayaan: angka kolom butuh lebar tetap supaya bisa discan vertikal.

## Semantics

- Badge status sinyal sah karena menandai state nyata: POTENTIAL BUY (hijau), WATCHLIST (amber), SKIP (netral).
- Skor tidak pernah hanya warna: selalu ada angka dan meter bertakik.
- Ikon minimal, glyph dari karakter yang sudah tersedia (+, -, panah teks), bukan pustaka ikon default.

## Motion

Hover: background, border, dan color transition 120ms. Focus: ring 2px warna aksen. Tidak ada entrance animation, autoplay, atau pulse berulang.

## Layout

- Header: wordmark, toggle tema, status market dan info run terakhir dalam satu strip tipis dengan hairline rule.
- Scanner: filter bar satu baris (wrap di mobile), lalu tabel padat. Tabel punya garis hairline, bukan kartu per baris.
- Detail ticker: chart sebagai fokus (kiri, lebar), rail kanan berisi plan R:R dan checklist sinyal. Statistik indikator masuk ke rail sebagai baris angka, bukan kartu-kartu.
- Empty, loading, dan error state eksplisit di semua tampilan data.
