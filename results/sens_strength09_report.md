# Results: sens_strength09.jsonl

Source hash `0560a1c88e53f6af`, map seeds 1000–1299, parameters {"strength": 0.9, "block_mult": 0.8, "kappa": 0.95, "delta": 0.1, "n_patch": 8, "resolved": 0.95, "ig_resolved": 0.9, "probe_cap": 20, "margin": 0.25}.

Regret is actions minus the oracle's actions on the same map and random stream. Brackets are 95% paired-bootstrap intervals.

## Board 15×15

| Condition | n | No revision | Revise + replan | Posterior sampling | Generic probing | Indexed repair | Indexed repair + probing | Replan + probing |
|---|---|---|---|---|---|---|---|---|
| none | 300 | 0.3 [0.1, 0.5] | 1.1 [0.7, 1.5] | 2.5 [1.9, 3.2] | 1.6 [1.1, 2.1] | 1.1 [0.7, 1.5] | 0.8 [0.4, 1.3] | 0.8 [0.4, 1.3] |
| block | 224 | 34.5 [31.4, 37.8] | 10.2 [8.6, 12.0] | 10.4 [8.8, 12.1] | 13.7 [12.3, 15.2] | 10.2 [8.6, 12.0] | 9.7 [8.1, 11.5] | 9.7 [8.1, 11.5] |
| slow | 224 | 1.3 [0.8, 1.9] | 2.9 [2.0, 3.9] | 6.4 [5.1, 7.7] | 4.8 [3.8, 6.0] | 2.9 [2.0, 3.9] | 2.7 [1.8, 3.8] | 2.7 [1.8, 3.7] |
| unlock | 260 | 4.2 [3.5, 5.0] | 3.5 [2.9, 4.0] | 5.8 [4.9, 6.8] | 4.1 [3.5, 4.8] | 3.5 [2.9, 4.0] | 3.3 [2.7, 3.9] | 3.3 [2.7, 3.9] |
| irrelevant | 165 | 0.8 [0.2, 1.5] | 0.8 [0.3, 1.3] | 2.8 [1.8, 3.8] | 1.3 [0.8, 1.9] | 0.8 [0.3, 1.3] | 0.6 [0.2, 1.1] | 0.6 [0.2, 1.1] |
| ool | 224 | 17.6 [14.7, 20.8] | 7.8 [6.2, 9.6] | 8.3 [6.7, 10.1] | 9.8 [8.2, 11.6] | 7.8 [6.2, 9.6] | 7.3 [5.7, 9.1] | 7.3 [5.7, 9.1] |

Planning node expansions after the initial plan (mean):

| Condition | No revision | Revise + replan | Posterior sampling | Generic probing | Indexed repair | Indexed repair + probing | Replan + probing |
|---|---|---|---|---|---|---|---|
| none | 9 | 429 | 1304 | 545 | 280 | 7055 | 16405 |
| block | 848 | 1269 | 1996 | 2140 | 678 | 13286 | 26510 |
| slow | 30 | 847 | 1734 | 1505 | 488 | 10597 | 22280 |
| unlock | 11 | 441 | 1368 | 598 | 290 | 7749 | 17004 |
| irrelevant | 13 | 292 | 1031 | 404 | 189 | 4258 | 14396 |
| ool | 459 | 954 | 1821 | 1406 | 536 | 10887 | 22338 |

## Board 31×31

| Condition | n | No revision | Revise + replan | Posterior sampling | Generic probing | Indexed repair | Indexed repair + probing | Replan + probing |
|---|---|---|---|---|---|---|---|---|
| none | 300 | 0.5 [0.1, 1.1] | 4.2 [3.1, 5.5] | 8.5 [6.6, 10.5] | 4.4 [3.2, 5.7] | 4.2 [3.1, 5.5] | 4.0 [2.9, 5.3] | 4.0 [2.9, 5.3] |
| block | 261 | 101.9 [92.3, 112.3] | 19.0 [16.2, 22.1] | 27.2 [22.8, 32.4] | 21.5 [18.8, 24.3] | 19.0 [16.2, 22.1] | 16.7 [14.0, 19.6] | 16.7 [14.0, 19.6] |
| slow | 261 | 4.4 [3.0, 6.2] | 7.5 [5.8, 9.3] | 19.9 [16.8, 23.3] | 8.0 [6.4, 9.8] | 7.5 [5.8, 9.3] | 7.6 [6.0, 9.4] | 7.6 [6.0, 9.4] |
| unlock | 294 | 11.9 [10.3, 13.6] | 11.3 [9.8, 12.9] | 17.2 [14.9, 19.6] | 11.8 [10.3, 13.3] | 11.3 [9.8, 12.9] | 9.2 [8.0, 10.6] | 9.2 [8.0, 10.6] |
| irrelevant | 28 | 0.2 [0.0, 0.5] | 0.9 [0.2, 1.9] | 0.9 [0.2, 1.6] | 1.0 [0.4, 2.0] | 0.9 [0.2, 1.9] | 0.9 [0.2, 1.9] | 0.9 [0.2, 1.9] |
| ool | 261 | 45.3 [38.6, 52.3] | 20.7 [16.7, 24.9] | 27.7 [23.2, 32.6] | 23.6 [19.4, 28.0] | 20.7 [16.7, 24.9] | 22.3 [17.9, 27.1] | 22.3 [17.9, 27.1] |

Planning node expansions after the initial plan (mean):

| Condition | No revision | Revise + replan | Posterior sampling | Generic probing | Indexed repair | Indexed repair + probing | Replan + probing |
|---|---|---|---|---|---|---|---|
| none | 72 | 3940 | 10705 | 4533 | 3110 | 67129 | 99396 |
| block | 10282 | 8143 | 15832 | 13033 | 5090 | 111859 | 164592 |
| slow | 271 | 6574 | 13679 | 9429 | 4709 | 100464 | 147466 |
| unlock | 73 | 3737 | 10499 | 4389 | 3000 | 68299 | 100716 |
| irrelevant | 8 | 1422 | 4831 | 1606 | 1072 | 25789 | 63236 |
| ool | 4513 | 7004 | 16732 | 9942 | 4702 | 96741 | 141227 |

## Board 51×51

| Condition | n | No revision | Revise + replan | Posterior sampling | Generic probing | Indexed repair | Indexed repair + probing | Replan + probing |
|---|---|---|---|---|---|---|---|---|
| none | 300 | 1.6 [0.3, 3.2] | 13.2 [10.1, 16.5] | 17.8 [14.3, 21.7] | 13.2 [10.2, 16.6] | 13.2 [10.1, 16.5] | 11.5 [8.7, 14.6] | 11.5 [8.7, 14.6] |
| block | 256 | 194.8 [176.4, 213.3] | 34.3 [29.4, 39.5] | 44.3 [38.2, 50.6] | 37.7 [32.5, 43.2] | 34.3 [29.4, 39.5] | 31.4 [26.5, 36.3] | 31.4 [26.5, 36.3] |
| slow | 256 | 8.5 [5.8, 11.5] | 23.4 [18.9, 28.4] | 39.1 [32.9, 45.9] | 21.3 [16.8, 26.1] | 23.4 [18.9, 28.4] | 19.4 [15.1, 24.1] | 19.4 [15.1, 24.1] |
| unlock | 300 | 26.6 [22.9, 30.6] | 27.1 [23.5, 31.0] | 35.6 [30.8, 40.5] | 26.8 [23.2, 30.6] | 27.1 [23.5, 31.0] | 17.0 [14.5, 19.8] | 17.0 [14.5, 19.8] |
| irrelevant | 4 | 0.0 [0.0, 0.0] | 3.5 [0.5, 8.0] | 4.0 [0.0, 12.0] | 2.2 [0.5, 4.2] | 3.5 [0.5, 8.0] | 0.2 [0.0, 0.8] | 0.2 [0.0, 0.8] |
| ool | 256 | 83.2 [70.2, 96.3] | 39.7 [33.2, 46.5] | 53.6 [45.2, 62.6] | 44.0 [37.0, 51.3] | 39.7 [33.2, 46.5] | 45.8 [38.3, 53.7] | 45.8 [38.3, 53.7] |

Planning node expansions after the initial plan (mean):

| Condition | No revision | Revise + replan | Posterior sampling | Generic probing | Indexed repair | Indexed repair + probing | Replan + probing |
|---|---|---|---|---|---|---|---|
| none | 391 | 15141 | 44935 | 17176 | 11256 | 243308 | 338654 |
| block | 60365 | 25848 | 61077 | 40805 | 15691 | 390305 | 554196 |
| slow | 1563 | 22524 | 59060 | 34376 | 15639 | 349143 | 484725 |
| unlock | 391 | 14636 | 43594 | 16836 | 11027 | 252064 | 348929 |
| irrelevant | 0 | 1555 | 9368 | 4126 | 727 | 93088 | 165160 |
| ool | 21341 | 23824 | 67033 | 32788 | 16265 | 336871 | 471591 |

## Primary comparisons (block, slow and unlock pooled)

| Board | Comparison | n | A | B | A − B [95% CI] | A/B | Holm p |
|---|---|---|---|---|---|---|---|
| 15 | P1 compute: indexed repair vs replan | 708 | 475.2 | 831.3 | -356.1 [-397.1, -318.3] | 0.57 | 2.6e-103 |
| 15 | P1 actions: indexed repair vs replan | 708 | 57.5 | 57.5 | 0.0 [0.0, 0.0] | 1.00 | identical in every episode |
| 15 | P2 actions: probing vs no probing | 708 | 57.2 | 57.5 | -0.3 [-0.5, -0.1] | 1.00 | 1 |
| 15 | P3 actions: probing vs posterior sampling | 708 | 57.2 | 59.5 | -2.3 [-3.0, -1.6] | 0.96 | 4.3e-10 |
| 15 | P4 actions: plan-relevant vs generic probing | 708 | 57.2 | 59.4 | -2.2 [-2.5, -1.9] | 0.96 | 3.4e-44 |
| 15 | P5 compute: indexed vs unindexed probing | 708 | 10401.8 | 21681.1 | -11279.3 [-11686.4, -10896.6] | 0.48 | 2.4e-116 |
| 15 | P5 actions: indexed vs unindexed probing | 708 | 57.2 | 57.2 | 0.0 [-0.0, 0.0] | 1.00 | 1 |
| 31 | P1 compute: indexed repair vs replan | 816 | 4215.1 | 6053.7 | -1838.6 [-2030.7, -1660.8] | 0.70 | 5.8e-125 |
| 31 | P1 actions: indexed repair vs replan | 816 | 133.5 | 133.5 | 0.0 [0.0, 0.0] | 1.00 | identical in every episode |
| 31 | P2 actions: probing vs no probing | 816 | 132.0 | 133.5 | -1.5 [-2.2, -0.7] | 0.99 | 0.19 |
| 31 | P3 actions: probing vs posterior sampling | 816 | 132.0 | 142.2 | -10.2 [-12.1, -8.3] | 0.93 | 2.3e-29 |
| 31 | P4 actions: plan-relevant vs generic probing | 816 | 132.0 | 134.6 | -2.6 [-3.3, -1.9] | 0.98 | 6.7e-30 |
| 31 | P5 compute: indexed vs unindexed probing | 816 | 92520.2 | 136100.0 | -43579.9 [-45152.0, -42065.1] | 0.68 | 7.2e-134 |
| 31 | P5 actions: indexed vs unindexed probing | 816 | 132.0 | 132.0 | -0.0 [-0.0, 0.0] | 1.00 | 1 |
| 51 | P1 compute: indexed repair vs replan | 812 | 13951.5 | 20657.7 | -6706.2 [-7494.5, -5968.6] | 0.68 | 2.1e-126 |
| 51 | P1 actions: indexed repair vs replan | 812 | 243.7 | 243.7 | 0.0 [0.0, 0.0] | 1.00 | identical in every episode |
| 51 | P2 actions: probing vs no probing | 812 | 237.8 | 243.7 | -5.9 [-7.4, -4.5] | 0.98 | 3.4e-13 |
| 51 | P3 actions: probing vs posterior sampling | 812 | 237.8 | 255.0 | -17.1 [-20.5, -13.8] | 0.93 | 6e-25 |
| 51 | P4 actions: plan-relevant vs generic probing | 812 | 237.8 | 244.0 | -6.2 [-7.8, -4.6] | 0.97 | 2e-32 |
| 51 | P5 compute: indexed vs unindexed probing | 812 | 326253.5 | 456456.2 | -130202.8 [-136028.4, -124444.2] | 0.71 | 3.1e-133 |
| 51 | P5 actions: indexed vs unindexed probing | 812 | 237.8 | 237.8 | 0.0 [0.0, 0.0] | 1.00 | identical in every episode |

## Controls and out-of-language condition (difference in actions, A − B)

| Board | Condition | A | B | n | A − B [95% CI] | Oracle actions |
|---|---|---|---|---|---|---|
| 15 | none | Indexed repair + probing | Indexed repair | 300 | -0.2 [-0.4, -0.1] | 50.0 |
| 15 | none | Indexed repair | No revision | 300 | 0.8 [0.4, 1.3] | 50.0 |
| 15 | none | Indexed repair | Posterior sampling | 300 | -1.4 [-2.2, -0.7] | 50.0 |
| 15 | irrelevant | Indexed repair + probing | Indexed repair | 165 | -0.2 [-0.3, -0.1] | 46.9 |
| 15 | irrelevant | Indexed repair | No revision | 165 | 0.0 [-0.6, 0.4] | 46.9 |
| 15 | irrelevant | Indexed repair | Posterior sampling | 165 | -2.0 [-3.0, -1.1] | 46.9 |
| 15 | ool | Indexed repair + probing | Indexed repair | 224 | -0.5 [-0.9, -0.1] | 53.7 |
| 15 | ool | Indexed repair | No revision | 224 | -9.8 [-12.2, -7.4] | 53.7 |
| 15 | ool | Indexed repair | Posterior sampling | 224 | -0.5 [-1.9, 0.8] | 53.7 |
| 31 | none | Indexed repair + probing | Indexed repair | 300 | -0.2 [-0.8, 0.4] | 118.0 |
| 31 | none | Indexed repair | No revision | 300 | 3.7 [2.7, 4.8] | 118.0 |
| 31 | none | Indexed repair | Posterior sampling | 300 | -4.2 [-6.3, -2.3] | 118.0 |
| 31 | irrelevant | Indexed repair + probing | Indexed repair | 28 | 0.1 [-0.7, 1.1] | 99.1 |
| 31 | irrelevant | Indexed repair | No revision | 28 | 0.7 [0.1, 1.6] | 99.1 |
| 31 | irrelevant | Indexed repair | Posterior sampling | 28 | 0.0 [-1.0, 1.2] | 99.1 |
| 31 | ool | Indexed repair + probing | Indexed repair | 261 | 1.6 [-0.4, 4.0] | 125.8 |
| 31 | ool | Indexed repair | No revision | 261 | -24.6 [-30.5, -19.0] | 125.8 |
| 31 | ool | Indexed repair | Posterior sampling | 261 | -7.0 [-11.0, -3.1] | 125.8 |
| 51 | none | Indexed repair + probing | Indexed repair | 300 | -1.6 [-2.8, -0.6] | 212.3 |
| 51 | none | Indexed repair | No revision | 300 | 11.6 [9.0, 14.4] | 212.3 |
| 51 | none | Indexed repair | Posterior sampling | 300 | -4.7 [-8.8, -0.7] | 212.3 |
| 51 | irrelevant | Indexed repair + probing | Indexed repair | 4 | -3.2 [-7.2, -0.5] | 150.0 |
| 51 | irrelevant | Indexed repair | No revision | 4 | 3.5 [0.5, 8.0] | 150.0 |
| 51 | irrelevant | Indexed repair | Posterior sampling | 4 | -0.5 [-11.5, 8.0] | 150.0 |
| 51 | ool | Indexed repair + probing | Indexed repair | 256 | 6.1 [1.3, 11.3] | 228.7 |
| 51 | ool | Indexed repair | No revision | 256 | -43.5 [-56.3, -31.2] | 228.7 |
| 51 | ool | Indexed repair | Posterior sampling | 256 | -13.9 [-21.4, -6.7] | 228.7 |

## Total-cost regret, actions + λ × expansions (violations pooled)

| Board | λ | No revision | Revise + replan | Posterior sampling | Generic probing | Indexed repair | Indexed repair + probing | Replan + probing |
|---|---|---|---|---|---|---|---|---|
| 15 | 0.0 | 12.9 | 5.4 | 7.4 | 7.4 | 5.4 | 5.1 | 5.1 |
| 15 | 0.001 | 13.7 | 6.8 | 9.6 | 9.3 | 6.4 | 16.1 | 27.3 |
| 15 | 0.01 | 21.0 | 19.0 | 29.5 | 26.4 | 15.5 | 114.5 | 227.3 |
| 31 | 0.0 | 38.3 | 12.6 | 21.3 | 13.7 | 12.6 | 11.1 | 11.1 |
| 31 | 0.001 | 44.3 | 21.4 | 37.1 | 25.2 | 19.6 | 106.4 | 150.0 |
| 31 | 0.01 | 98.5 | 100.9 | 179.5 | 129.1 | 82.5 | 964.0 | 1399.8 |
| 51 | 0.0 | 73.9 | 28.2 | 39.4 | 28.5 | 28.2 | 22.3 | 22.3 |
| 51 | 0.001 | 101.1 | 56.7 | 100.7 | 66.2 | 50.0 | 356.4 | 486.6 |
| 51 | 0.01 | 346.0 | 313.2 | 652.4 | 406.1 | 246.1 | 3363.3 | 4665.3 |

## Skipped episodes (no rule on the map fits the condition)

15/block: 76, 15/irrelevant: 135, 15/ool: 76, 15/slow: 76, 15/unlock: 40, 31/block: 39, 31/irrelevant: 272, 31/ool: 39, 31/slow: 39, 31/unlock: 6, 51/block: 44, 51/irrelevant: 296, 51/ool: 44, 51/slow: 44
