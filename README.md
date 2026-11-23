# The World — 22 November 2026

A classic newspaper front page summing up Sunday, 22 November 2026.

[![news-image-20261122](https://make.fun/badge/news-image-20261122.svg)](https://make.fun/bounty/news-image-20261122)
[![rank](https://make.fun/badge/news-image-20261122/Rifat7600/news-image-20261122/rank.svg)](https://make.fun/bounty/news-image-20261122)
[![reward](https://make.fun/badge/news-image-20261122/Rifat7600/news-image-20261122/reward.svg)](https://make.fun/bounty/news-image-20261122)

Entry for the [make.fun bounty "Sum up 22 November's world news in one image"](https://make.fun/bounty/news-image-20261122).

## The front page

- **Lead story:** COP31 climate talks collapse in Antalya — no deal, as the fossil-fuel row sinks the summit.
- **Democrats win the House:** the largest majority since 1992, decided by a North Carolina recount (Hubbard beats Foxx by about 330 votes; 258 of 435 seats).
- **Two supertankers hit by mines** near the Strait of Hormuz.
- **Also on the page:** a Ukraine drone strike hits the Russian warship Merkury off Libya; Sudan drone attacks kill four and damage a UN building; cartel leader "El Chapo Isidro" captured in Mexico.

## How it works

`main.py` (Python 3.13, standard library only) draws the whole front page
with a hand-made 5×7 bitmap font and a small zlib-based PNG writer, then
writes `/output/entry.png` (or `$MAKEFUN_OUTPUT_DIR/entry.png`). It runs
twice and writes byte-identical bytes both times.

## License

MIT — see [LICENSE](LICENSE).
