# FX Pair Correlation Buckets

Pairs grouped into 5 buckets to minimize intra-bucket absolute correlation (Daily).

## Bucket 1

| | AUDUSD | GBPUSD | AUDNZD | NZDCHF | GBPCAD |
|---|---|---|---|---|---|
| AUDUSD | 100 | <span style="color:red">**95.4**</span> | 48.0 | 58.7 | 36.7 |
| GBPUSD | <span style="color:red">**95.4**</span> | 100 | 35.2 | 52.5 | 35.0 |
| AUDNZD | 48.0 | 35.2 | 100 | -12.6 | 54.0 |
| NZDCHF | 58.7 | 52.5 | -12.6 | 100 | 20.0 |
| GBPCAD | 36.7 | 35.0 | 54.0 | 20.0 | 100 |

## Bucket 2

| | EURNZD | EURGBP | EURUSD | EURCAD | AUDJPY | EURCHF |
|---|---|---|---|---|---|---|
| EURNZD | 100 | 62.6 | -49.7 | 58.5 | -61.4 | -48.9 |
| EURGBP | 62.6 | 100 | -37.3 | 60.4 | <span style="color:red">**-91.4**</span> | -17.1 |
| EURUSD | -49.7 | -37.3 | 100 | -62.5 | 52.1 | 0.9 |
| EURCAD | 58.5 | 60.4 | -62.5 | 100 | <span style="color:red">**-73.5**</span> | -22.2 |
| AUDJPY | -61.4 | <span style="color:red">**-91.4**</span> | 52.1 | <span style="color:red">**-73.5**</span> | 100 | 12.4 |
| EURCHF | -48.9 | -17.1 | 0.9 | -22.2 | 12.4 | 100 |

## Bucket 3

| | GBPCHF | NZDJPY | GBPNZD | GBPAUD | CADJPY | USDCHF |
|---|---|---|---|---|---|---|
| GBPCHF | 100 | <span style="color:red">**78.0**</span> | 5.6 | -53.2 | 64.5 | 5.8 |
| NZDJPY | <span style="color:red">**78.0**</span> | 100 | -7.0 | -58.9 | <span style="color:red">**91.3**</span> | -45.3 |
| GBPNZD | 5.6 | -7.0 | 100 | 8.9 | 19.3 | -2.9 |
| GBPAUD | -53.2 | -58.9 | 8.9 | 100 | -49.6 | 10.6 |
| CADJPY | 64.5 | <span style="color:red">**91.3**</span> | 19.3 | -49.6 | 100 | -53.5 |
| USDCHF | 5.8 | -45.3 | -2.9 | 10.6 | -53.5 | 100 |

## Bucket 4

| | CHFJPY | AUDCHF | USDCAD | EURAUD | USDJPY | NZDCAD |
|---|---|---|---|---|---|---|
| CHFJPY | 100 | 37.1 | -64.5 | -57.3 | 59.5 | -18.5 |
| AUDCHF | 37.1 | 100 | -47.3 | <span style="color:red">**-93.6**</span> | 50.3 | 45.3 |
| USDCAD | -64.5 | -47.3 | 100 | 50.7 | -1.7 | -6.3 |
| EURAUD | -57.3 | <span style="color:red">**-93.6**</span> | 50.7 | 100 | -55.0 | -34.3 |
| USDJPY | 59.5 | 50.3 | -1.7 | -55.0 | 100 | -13.5 |
| NZDCAD | -18.5 | 45.3 | -6.3 | -34.3 | -13.5 | 100 |

## Bucket 5

| | AUDCAD | NZDUSD | CADCHF | EURJPY | GBPJPY |
|---|---|---|---|---|---|
| AUDCAD | 100 | 34.2 | 22.5 | 46.6 | <span style="color:red">**65.1**</span> |
| NZDUSD | 34.2 | 100 | 64.3 | 62.2 | 64.0 |
| CADCHF | 22.5 | 64.3 | 100 | 50.5 | 53.6 |
| EURJPY | 46.6 | 62.2 | 50.5 | 100 | <span style="color:red">**95.9**</span> |
| GBPJPY | <span style="color:red">**65.1**</span> | 64.0 | 53.6 | <span style="color:red">**95.9**</span> | 100 |

