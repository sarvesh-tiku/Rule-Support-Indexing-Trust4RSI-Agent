# Results: pilot.jsonl

Source hash `80ea12951f7ca399`, map seeds 0–29, parameters {"strength": 0.7, "block_mult": 0.8, "kappa": 0.95, "delta": 0.1, "n_patch": 8, "resolved": 0.95, "ig_resolved": 0.9, "probe_cap": 20, "margin": 0.25}.

Regret is actions minus the oracle's actions on the same map and random stream. Brackets are 95% paired-bootstrap intervals.

## Board 15×15

| Condition | n | No revision | Revise + replan | Posterior sampling | Generic probing | Indexed repair | Indexed repair + probing | Replan + probing |
|---|---|---|---|---|---|---|---|---|
| none | 30 | 0.1 [0.0, 0.2] | 1.9 [0.3, 3.8] | 4.0 [2.0, 6.5] | 34.0 [28.7, 39.8] | 1.9 [0.3, 3.8] | 0.6 [-0.2, 1.4] | 0.6 [-0.2, 1.4] |
| block | 20 | 46.0 [36.7, 56.0] | 16.1 [10.7, 22.3] | 14.8 [9.1, 21.2] | 46.4 [38.9, 54.1] | 16.1 [10.7, 22.3] | 14.5 [10.1, 19.3] | 14.5 [10.1, 19.3] |
| slow | 20 | 0.3 [-0.9, 1.5] | 1.7 [-0.7, 4.9] | 7.7 [3.9, 11.7] | 38.1 [32.6, 44.1] | 1.7 [-0.7, 4.9] | 1.9 [-0.5, 5.0] | 1.9 [-0.5, 5.0] |
| unlock | 28 | 2.3 [1.4, 3.3] | 4.1 [2.2, 6.2] | 6.0 [3.7, 8.7] | 29.5 [25.5, 33.8] | 4.1 [2.2, 6.2] | 2.7 [1.3, 4.2] | 2.7 [1.3, 4.2] |
| irrelevant | 15 | 8.5 [0.0, 24.4] | 1.6 [0.4, 3.4] | 2.6 [0.9, 4.7] | 45.2 [37.1, 53.1] | 1.6 [0.4, 3.4] | 0.9 [0.2, 1.6] | 0.9 [0.2, 1.6] |
| ool | 20 | 18.1 [10.1, 26.4] | 7.7 [2.6, 14.1] | 11.8 [6.8, 17.6] | 39.1 [33.3, 45.6] | 7.7 [2.6, 14.1] | 6.0 [1.5, 11.4] | 6.0 [1.5, 11.4] |

Planning node expansions after the initial plan (mean):

| Condition | No revision | Revise + replan | Posterior sampling | Generic probing | Indexed repair | Indexed repair + probing | Replan + probing |
|---|---|---|---|---|---|---|---|
| none | 6 | 333 | 1131 | 5948 | 223 | 8951 | 19607 |
| block | 1038 | 1410 | 1849 | 8522 | 693 | 16628 | 32187 |
| slow | 35 | 913 | 1459 | 8054 | 486 | 12783 | 26670 |
| unlock | 7 | 310 | 1119 | 6148 | 212 | 9459 | 19557 |
| irrelevant | 94 | 208 | 903 | 6956 | 135 | 5782 | 16899 |
| ool | 551 | 999 | 1700 | 7207 | 498 | 13634 | 27152 |

## Board 31×31

| Condition | n | No revision | Revise + replan | Posterior sampling | Generic probing | Indexed repair | Indexed repair + probing | Replan + probing |
|---|---|---|---|---|---|---|---|---|
| none | 30 | 1.4 [-0.2, 4.4] | 14.2 [8.1, 21.5] | 23.4 [14.9, 33.5] | 55.9 [46.4, 66.1] | 14.2 [8.1, 21.5] | 15.2 [8.9, 22.5] | 15.2 [8.9, 22.5] |
| block | 25 | 109.8 [74.4, 151.6] | 29.1 [19.5, 40.0] | 33.4 [24.0, 43.8] | 78.7 [65.7, 92.6] | 29.1 [19.5, 40.0] | 26.7 [17.4, 37.5] | 26.7 [17.4, 37.5] |
| slow | 25 | 7.0 [-0.2, 17.0] | 19.8 [9.9, 31.1] | 42.5 [30.6, 55.4] | 66.6 [55.3, 78.4] | 19.8 [9.9, 31.1] | 17.3 [10.1, 25.4] | 17.3 [10.1, 25.4] |
| unlock | 30 | 19.5 [12.1, 27.7] | 15.6 [9.3, 23.4] | 28.2 [20.0, 37.5] | 38.8 [32.3, 45.5] | 15.6 [9.3, 23.4] | 6.5 [3.9, 9.7] | 6.5 [3.9, 9.7] |
| ool | 25 | 71.1 [40.3, 108.1] | 37.6 [19.4, 62.6] | 30.4 [21.6, 39.8] | 100.4 [79.8, 125.6] | 37.6 [19.4, 62.6] | 45.8 [24.4, 73.4] | 45.8 [24.4, 73.4] |

Planning node expansions after the initial plan (mean):

| Condition | No revision | Revise + replan | Posterior sampling | Generic probing | Indexed repair | Indexed repair + probing | Replan + probing |
|---|---|---|---|---|---|---|---|
| none | 74 | 5042 | 7679 | 32432 | 3796 | 98928 | 138489 |
| block | 8765 | 7926 | 8522 | 40860 | 4404 | 127368 | 181278 |
| slow | 264 | 7430 | 8367 | 40534 | 4767 | 124777 | 174899 |
| unlock | 74 | 3747 | 7015 | 30800 | 2962 | 89315 | 127205 |
| ool | 5021 | 7074 | 7942 | 39116 | 4417 | 119302 | 167816 |

## Board 51×51

| Condition | n | No revision | Revise + replan | Posterior sampling | Generic probing | Indexed repair | Indexed repair + probing | Replan + probing |
|---|---|---|---|---|---|---|---|---|
| none | 30 | 0.5 [0.0, 1.5] | 22.2 [12.3, 34.1] | 38.2 [22.7, 55.7] | 84.2 [71.6, 98.3] | 22.2 [12.3, 34.1] | 18.2 [8.4, 30.7] | 18.2 [8.4, 30.7] |
| block | 20 | 255.9 [190.3, 321.9] | 38.1 [23.2, 55.1] | 46.0 [30.4, 63.0] | 98.8 [78.8, 120.8] | 38.1 [23.2, 55.1] | 35.0 [19.8, 52.1] | 35.0 [19.8, 52.1] |
| slow | 20 | 12.2 [3.6, 23.8] | 21.8 [11.2, 34.8] | 51.6 [31.2, 75.0] | 97.0 [83.0, 112.6] | 21.8 [11.2, 34.8] | 27.6 [12.9, 46.2] | 27.6 [12.9, 46.2] |
| unlock | 30 | 26.8 [15.8, 40.1] | 29.3 [19.9, 40.7] | 64.6 [43.4, 87.7] | 55.6 [48.1, 63.8] | 29.3 [19.9, 40.7] | 14.9 [10.4, 20.1] | 14.9 [10.4, 20.1] |
| irrelevant | 1 | 0.0 [nan, nan] | 0.0 [nan, nan] | 54.0 [nan, nan] | 152.0 [nan, nan] | 0.0 [nan, nan] | 0.0 [nan, nan] | 0.0 [nan, nan] |
| ool | 20 | 129.2 [84.3, 179.8] | 51.5 [29.0, 78.3] | 107.2 [62.9, 161.3] | 143.7 [108.2, 180.8] | 51.5 [29.0, 78.3] | 76.1 [46.8, 106.2] | 76.1 [46.8, 106.2] |

Planning node expansions after the initial plan (mean):

| Condition | No revision | Revise + replan | Posterior sampling | Generic probing | Indexed repair | Indexed repair + probing | Replan + probing |
|---|---|---|---|---|---|---|---|
| none | 75 | 10779 | 21269 | 87423 | 7991 | 323127 | 451711 |
| block | 90857 | 21584 | 32196 | 125831 | 12503 | 472176 | 678329 |
| slow | 4491 | 15631 | 31011 | 127545 | 11178 | 443392 | 621495 |
| unlock | 75 | 9496 | 21028 | 100546 | 7103 | 293714 | 408253 |
| irrelevant | 0 | 2114 | 4483 | 124659 | 1927 | 69731 | 159297 |
| ool | 39328 | 18370 | 32377 | 129059 | 11676 | 462908 | 658173 |

## Primary comparisons (block, slow and unlock pooled)

| Board | Comparison | n | A | B | A − B [95% CI] | A/B | Holm p |
|---|---|---|---|---|---|---|---|
| 15 | P1 compute: indexed repair vs replan | 68 | 434.1 | 810.7 | -376.6 [-528.4, -241.5] | 0.54 | 1.4e-09 |
| 15 | P1 actions: indexed repair vs replan | 68 | 58.1 | 58.1 | 0.0 [0.0, 0.0] | 1.00 | identical in every episode |
| 15 | P2 actions: probing vs no probing | 68 | 57.1 | 58.1 | -1.0 [-2.1, -0.0] | 0.98 | 1 |
| 15 | P3 actions: probing vs posterior sampling | 68 | 57.1 | 60.3 | -3.2 [-6.0, -0.5] | 0.95 | 0.14 |
| 15 | P4 actions: plan-relevant vs generic probing | 68 | 57.1 | 88.2 | -31.1 [-34.4, -27.9] | 0.65 | 1.3e-11 |
| 15 | P5 compute: indexed vs unindexed probing | 68 | 12545.4 | 25364.0 | -12818.6 [-14521.7, -11271.2] | 0.49 | 1.3e-11 |
| 15 | P5 actions: indexed vs unindexed probing | 68 | 57.1 | 57.1 | 0.0 [0.0, 0.0] | 1.00 | identical in every episode |
| 31 | P1 compute: indexed repair vs replan | 80 | 3976.7 | 6203.6 | -2227.0 [-2944.9, -1563.0] | 0.64 | 6.7e-12 |
| 31 | P1 actions: indexed repair vs replan | 80 | 150.4 | 150.4 | 0.0 [0.0, 0.0] | 1.00 | identical in every episode |
| 31 | P2 actions: probing vs no probing | 80 | 145.4 | 150.4 | -4.9 [-8.8, -1.6] | 0.97 | 0.41 |
| 31 | P3 actions: probing vs posterior sampling | 80 | 145.4 | 163.6 | -18.1 [-24.7, -11.9] | 0.89 | 4.3e-07 |
| 31 | P4 actions: plan-relevant vs generic probing | 80 | 145.4 | 189.2 | -43.7 [-50.3, -37.5] | 0.77 | 2.2e-13 |
| 31 | P5 compute: indexed vs unindexed probing | 80 | 112288.6 | 159007.2 | -46718.6 [-51766.1, -41823.9] | 0.71 | 1.6e-13 |
| 31 | P5 actions: indexed vs unindexed probing | 80 | 145.4 | 145.4 | 0.0 [0.0, 0.0] | 1.00 | identical in every episode |
| 51 | P1 compute: indexed repair vs replan | 70 | 9810.2 | 14702.8 | -4892.6 [-6731.1, -3236.2] | 0.67 | 7.7e-11 |
| 51 | P1 actions: indexed repair vs replan | 70 | 239.3 | 239.3 | 0.0 [0.0, 0.0] | 1.00 | identical in every episode |
| 51 | P2 actions: probing vs no probing | 70 | 233.9 | 239.3 | -5.4 [-11.7, 1.3] | 0.98 | 0.056 |
| 51 | P3 actions: probing vs posterior sampling | 70 | 233.9 | 265.2 | -31.3 [-44.9, -18.1] | 0.88 | 7.1e-06 |
| 51 | P4 actions: plan-relevant vs generic probing | 70 | 233.9 | 289.4 | -55.5 [-65.4, -45.5] | 0.81 | 5.9e-10 |
| 51 | P5 compute: indexed vs unindexed probing | 70 | 387468.3 | 546344.1 | -158875.8 [-177980.5, -141182.1] | 0.71 | 6.7e-12 |
| 51 | P5 actions: indexed vs unindexed probing | 70 | 233.9 | 233.9 | 0.0 [0.0, 0.0] | 1.00 | identical in every episode |

## Controls and out-of-language condition (difference in actions, A − B)

| Board | Condition | A | B | n | A − B [95% CI] | Oracle actions |
|---|---|---|---|---|---|---|
| 15 | none | Indexed repair + probing | Indexed repair | 30 | -1.2 [-3.0, -0.0] | 49.4 |
| 15 | none | Indexed repair | No revision | 30 | 1.8 [0.2, 3.7] | 49.4 |
| 15 | none | Indexed repair | Posterior sampling | 30 | -2.2 [-5.0, 0.3] | 49.4 |
| 15 | irrelevant | Indexed repair + probing | Indexed repair | 15 | -0.7 [-2.3, 0.3] | 47.3 |
| 15 | irrelevant | Indexed repair | No revision | 15 | -6.9 [-22.9, 2.4] | 47.3 |
| 15 | irrelevant | Indexed repair | Posterior sampling | 15 | -1.0 [-3.7, 1.6] | 47.3 |
| 15 | ool | Indexed repair + probing | Indexed repair | 20 | -1.8 [-4.0, 0.1] | 51.8 |
| 15 | ool | Indexed repair | No revision | 20 | -10.4 [-18.5, -2.5] | 51.8 |
| 15 | ool | Indexed repair | Posterior sampling | 20 | -4.2 [-9.3, 1.3] | 51.8 |
| 31 | none | Indexed repair + probing | Indexed repair | 30 | 1.0 [-1.5, 3.7] | 127.7 |
| 31 | none | Indexed repair | No revision | 30 | 12.8 [7.3, 19.5] | 127.7 |
| 31 | none | Indexed repair | Posterior sampling | 30 | -9.2 [-19.4, 0.4] | 127.7 |
| 31 | ool | Indexed repair + probing | Indexed repair | 25 | 8.2 [2.0, 17.8] | 138.1 |
| 31 | ool | Indexed repair | No revision | 25 | -33.5 [-67.2, -4.2] | 138.1 |
| 31 | ool | Indexed repair | Posterior sampling | 25 | 7.2 [-9.8, 27.6] | 138.1 |
| 51 | none | Indexed repair + probing | Indexed repair | 30 | -4.0 [-11.1, 5.0] | 207.2 |
| 51 | none | Indexed repair | No revision | 30 | 21.7 [12.3, 33.1] | 207.2 |
| 51 | none | Indexed repair | Posterior sampling | 30 | -16.0 [-35.8, 1.0] | 207.2 |
| 51 | ool | Indexed repair + probing | Indexed repair | 20 | 24.6 [4.0, 46.9] | 223.6 |
| 51 | ool | Indexed repair | No revision | 20 | -77.7 [-126.1, -36.2] | 223.6 |
| 51 | ool | Indexed repair | Posterior sampling | 20 | -55.6 [-110.2, -14.2] | 223.6 |

## Total-cost regret, actions + λ × expansions (violations pooled)

| Board | λ | No revision | Revise + replan | Posterior sampling | Generic probing | Indexed repair | Indexed repair + probing | Replan + probing |
|---|---|---|---|---|---|---|---|---|
| 15 | 0.0 | 14.6 | 6.9 | 9.1 | 37.0 | 6.9 | 5.9 | 5.9 |
| 15 | 0.001 | 15.4 | 8.4 | 11.1 | 45.0 | 8.0 | 19.1 | 31.9 |
| 15 | 0.01 | 23.1 | 21.4 | 29.0 | 117.5 | 17.7 | 137.8 | 266.0 |
| 31 | 0.0 | 43.8 | 21.1 | 34.3 | 59.9 | 21.1 | 16.2 | 16.2 |
| 31 | 0.001 | 49.3 | 30.1 | 44.5 | 99.7 | 27.9 | 131.3 | 178.0 |
| 31 | 0.01 | 98.8 | 111.1 | 136.7 | 457.7 | 88.8 | 1167.0 | 1634.2 |
| 51 | 0.0 | 88.1 | 29.7 | 55.6 | 79.8 | 29.7 | 24.3 | 24.3 |
| 51 | 0.001 | 122.9 | 52.2 | 89.9 | 203.1 | 47.3 | 419.6 | 578.5 |
| 51 | 0.01 | 436.1 | 255.1 | 398.9 | 1313.0 | 206.2 | 3977.4 | 5566.1 |

## Skipped episodes (no rule on the map fits the condition)

15/block: 10, 15/irrelevant: 15, 15/ool: 10, 15/slow: 10, 15/unlock: 2, 31/block: 5, 31/irrelevant: 30, 31/ool: 5, 31/slow: 5, 51/block: 10, 51/irrelevant: 29, 51/ool: 10, 51/slow: 10
