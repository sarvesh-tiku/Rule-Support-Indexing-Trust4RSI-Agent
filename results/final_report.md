# Results: final.jsonl

Source hash `0560a1c88e53f6af`, map seeds 1000–1299, parameters {"strength": 0.7, "block_mult": 0.8, "kappa": 0.95, "delta": 0.1, "n_patch": 8, "resolved": 0.95, "ig_resolved": 0.9, "probe_cap": 20, "margin": 0.25}.

Regret is actions minus the oracle's actions on the same map and random stream. Brackets are 95% paired-bootstrap intervals.

## Board 15×15

| Condition | n | No revision | Revise + replan | Posterior sampling | Generic probing | Indexed repair | Indexed repair + probing | Replan + probing |
|---|---|---|---|---|---|---|---|---|
| none | 300 | 0.3 [0.1, 0.5] | 3.0 [2.3, 3.7] | 5.5 [4.5, 6.7] | 33.9 [32.5, 35.3] | 3.0 [2.3, 3.7] | 2.4 [1.8, 3.1] | 2.4 [1.7, 3.1] |
| block | 169 | 40.2 [36.9, 43.8] | 15.2 [12.9, 17.6] | 14.4 [12.4, 16.6] | 48.3 [45.6, 51.2] | 15.2 [12.9, 17.6] | 13.9 [11.6, 16.3] | 13.9 [11.7, 16.3] |
| slow | 169 | 0.9 [0.4, 1.5] | 3.9 [2.8, 5.2] | 10.3 [8.6, 12.1] | 38.6 [36.3, 40.9] | 3.9 [2.8, 5.2] | 3.7 [2.6, 5.0] | 3.7 [2.5, 4.9] |
| unlock | 262 | 4.2 [3.4, 5.0] | 4.0 [3.5, 4.6] | 7.5 [6.3, 8.8] | 29.5 [28.2, 30.8] | 4.0 [3.5, 4.6] | 2.6 [2.2, 3.0] | 2.6 [2.2, 3.0] |
| irrelevant | 158 | 1.5 [0.6, 2.5] | 1.7 [1.2, 2.3] | 4.1 [2.9, 5.3] | 43.1 [40.9, 45.5] | 1.7 [1.2, 2.3] | 1.3 [0.8, 1.9] | 1.3 [0.8, 1.9] |
| ool | 169 | 20.3 [16.8, 23.9] | 11.6 [9.4, 14.0] | 12.6 [10.3, 15.2] | 47.7 [44.4, 51.2] | 11.6 [9.4, 14.0] | 10.8 [8.6, 13.1] | 10.8 [8.6, 13.2] |

Planning node expansions after the initial plan (mean):

| Condition | No revision | Revise + replan | Posterior sampling | Generic probing | Indexed repair | Indexed repair + probing | Replan + probing |
|---|---|---|---|---|---|---|---|
| none | 9 | 497 | 1303 | 5423 | 298 | 8602 | 19711 |
| block | 964 | 1545 | 2075 | 7879 | 830 | 16038 | 30967 |
| slow | 25 | 935 | 1843 | 7007 | 512 | 12646 | 25857 |
| unlock | 11 | 462 | 1357 | 5937 | 289 | 8857 | 19666 |
| irrelevant | 18 | 322 | 1024 | 6194 | 194 | 4992 | 16628 |
| ool | 534 | 1143 | 1990 | 7177 | 633 | 13326 | 26777 |

## Board 31×31

| Condition | n | No revision | Revise + replan | Posterior sampling | Generic probing | Indexed repair | Indexed repair + probing | Replan + probing |
|---|---|---|---|---|---|---|---|---|
| none | 300 | 0.5 [0.1, 1.1] | 8.3 [6.9, 9.8] | 20.4 [17.2, 23.7] | 55.3 [52.3, 58.5] | 8.3 [6.9, 9.8] | 7.4 [6.0, 8.8] | 7.4 [6.0, 8.8] |
| block | 229 | 103.5 [93.3, 114.1] | 24.9 [21.3, 28.8] | 39.9 [33.5, 47.1] | 77.5 [72.6, 82.7] | 24.9 [21.3, 28.8] | 22.1 [18.6, 26.1] | 22.1 [18.6, 26.1] |
| slow | 229 | 3.5 [2.1, 5.2] | 12.2 [10.0, 14.5] | 34.3 [29.5, 39.4] | 63.4 [59.2, 68.0] | 12.2 [10.0, 14.5] | 11.1 [9.2, 13.2] | 11.1 [9.2, 13.2] |
| unlock | 295 | 11.9 [10.3, 13.6] | 12.9 [11.5, 14.4] | 21.7 [19.0, 24.6] | 41.4 [39.5, 43.3] | 12.9 [11.5, 14.4] | 8.0 [7.0, 9.1] | 8.0 [7.0, 9.1] |
| irrelevant | 24 | 0.0 [0.0, 0.0] | 2.0 [0.5, 4.0] | 6.2 [1.0, 15.1] | 71.9 [57.0, 88.2] | 2.0 [0.5, 4.0] | 1.3 [0.4, 2.5] | 1.3 [0.4, 2.5] |
| ool | 229 | 48.2 [41.1, 55.8] | 24.8 [20.2, 30.0] | 41.3 [34.2, 49.5] | 85.9 [79.2, 92.9] | 24.8 [20.2, 30.0] | 27.0 [21.9, 32.4] | 27.0 [21.9, 32.4] |

Planning node expansions after the initial plan (mean):

| Condition | No revision | Revise + replan | Posterior sampling | Generic probing | Indexed repair | Indexed repair + probing | Replan + probing |
|---|---|---|---|---|---|---|---|
| none | 72 | 3714 | 11022 | 31325 | 2833 | 90638 | 134749 |
| block | 10281 | 8769 | 15207 | 41741 | 5213 | 140090 | 206311 |
| slow | 265 | 6298 | 14032 | 39064 | 4198 | 120027 | 177179 |
| unlock | 73 | 3165 | 10291 | 32127 | 2526 | 89779 | 132578 |
| irrelevant | 10 | 580 | 4225 | 31832 | 459 | 25467 | 64863 |
| ool | 4698 | 7090 | 16221 | 39954 | 4627 | 124175 | 182563 |

## Board 51×51

| Condition | n | No revision | Revise + replan | Posterior sampling | Generic probing | Indexed repair | Indexed repair + probing | Replan + probing |
|---|---|---|---|---|---|---|---|---|
| none | 300 | 1.6 [0.3, 3.2] | 21.4 [18.2, 24.8] | 38.2 [32.3, 44.8] | 79.7 [74.0, 85.4] | 21.4 [18.2, 24.8] | 19.2 [15.8, 22.8] | 19.2 [15.8, 22.8] |
| block | 214 | 212.8 [192.7, 233.6] | 42.7 [36.9, 48.9] | 65.7 [56.5, 75.9] | 106.3 [98.5, 114.3] | 42.7 [36.9, 48.9] | 38.1 [32.1, 44.6] | 38.1 [32.1, 44.6] |
| slow | 214 | 7.5 [4.9, 10.6] | 31.4 [25.9, 37.4] | 63.6 [54.7, 73.1] | 93.8 [86.1, 101.7] | 31.4 [25.9, 37.4] | 28.4 [22.9, 34.6] | 28.4 [22.9, 34.6] |
| unlock | 300 | 26.2 [22.6, 30.1] | 31.5 [28.0, 35.1] | 42.8 [37.4, 48.8] | 54.4 [50.7, 58.2] | 31.5 [28.0, 35.1] | 17.0 [14.6, 19.6] | 17.0 [14.6, 19.6] |
| irrelevant | 2 | 0.0 [0.0, 0.0] | 2.0 [2.0, 2.0] | 2.0 [2.0, 2.0] | 67.0 [66.0, 68.0] | 2.0 [2.0, 2.0] | 0.0 [0.0, 0.0] | 0.0 [0.0, 0.0] |
| ool | 214 | 91.0 [76.4, 106.4] | 48.0 [40.2, 56.4] | 86.1 [70.5, 103.3] | 137.1 [125.0, 149.8] | 48.0 [40.2, 56.4] | 54.6 [45.4, 64.1] | 54.6 [45.4, 64.1] |

Planning node expansions after the initial plan (mean):

| Condition | No revision | Revise + replan | Posterior sampling | Generic probing | Indexed repair | Indexed repair + probing | Replan + probing |
|---|---|---|---|---|---|---|---|
| none | 391 | 13486 | 44083 | 93491 | 9790 | 342349 | 479076 |
| block | 64182 | 24476 | 57056 | 119144 | 14418 | 483303 | 691898 |
| slow | 1409 | 19866 | 53061 | 114016 | 13487 | 439078 | 620049 |
| unlock | 391 | 12376 | 43376 | 100878 | 9370 | 341786 | 471194 |
| irrelevant | 0 | 56 | 4791 | 61363 | 42 | 74662 | 139537 |
| ool | 22008 | 21671 | 72740 | 117202 | 14656 | 451318 | 633503 |

## Primary comparisons (block, slow and unlock pooled)

| Board | Comparison | n | A | B | A − B [95% CI] | A/B | Holm p |
|---|---|---|---|---|---|---|---|
| 15 | P1 compute: indexed repair vs replan | 600 | 503.9 | 900.3 | -396.4 [-448.3, -347.5] | 0.56 | 7.1e-81 |
| 15 | P1 actions: indexed repair vs replan | 600 | 58.9 | 58.9 | 0.0 [0.0, 0.0] | 1.00 | identical in every episode |
| 15 | P2 actions: probing vs no probing | 600 | 57.9 | 58.9 | -1.0 [-1.4, -0.7] | 0.98 | 2.6e-08 |
| 15 | P3 actions: probing vs posterior sampling | 600 | 57.9 | 62.0 | -4.2 [-5.1, -3.2] | 0.93 | 1.4e-17 |
| 15 | P4 actions: plan-relevant vs generic probing | 600 | 57.9 | 89.1 | -31.3 [-32.5, -30.0] | 0.65 | 5.4e-96 |
| 15 | P5 compute: indexed vs unindexed probing | 600 | 11947.0 | 24592.7 | -12645.7 [-13114.8, -12195.7] | 0.49 | 9.6e-99 |
| 15 | P5 actions: indexed vs unindexed probing | 600 | 57.9 | 57.9 | 0.0 [-0.0, 0.1] | 1.00 | 1 |
| 31 | P1 compute: indexed repair vs replan | 753 | 3851.7 | 5822.0 | -1970.3 [-2215.8, -1739.4] | 0.66 | 3.1e-112 |
| 31 | P1 actions: indexed repair vs replan | 753 | 136.7 | 136.7 | 0.0 [0.0, 0.0] | 1.00 | identical in every episode |
| 31 | P2 actions: probing vs no probing | 753 | 133.6 | 136.7 | -3.1 [-4.0, -2.2] | 0.98 | 2.4e-08 |
| 31 | P3 actions: probing vs posterior sampling | 753 | 133.6 | 151.4 | -17.8 [-20.6, -15.3] | 0.88 | 5.5e-39 |
| 31 | P4 actions: plan-relevant vs generic probing | 753 | 133.6 | 179.4 | -45.8 [-48.2, -43.5] | 0.74 | 1.7e-117 |
| 31 | P5 compute: indexed vs unindexed probing | 753 | 114278.4 | 168565.4 | -54287.0 [-56356.1, -52152.5] | 0.68 | 1.4e-123 |
| 31 | P5 actions: indexed vs unindexed probing | 753 | 133.6 | 133.6 | 0.0 [0.0, 0.0] | 1.00 | identical in every episode |
| 51 | P1 compute: indexed repair vs replan | 728 | 12064.5 | 18134.6 | -6070.1 [-6852.1, -5322.4] | 0.67 | 4.8e-107 |
| 51 | P1 actions: indexed repair vs replan | 728 | 249.0 | 249.0 | 0.0 [0.0, 0.0] | 1.00 | identical in every episode |
| 51 | P2 actions: probing vs no probing | 728 | 240.8 | 249.0 | -8.2 [-10.0, -6.4] | 0.97 | 1.1e-17 |
| 51 | P3 actions: probing vs posterior sampling | 728 | 240.8 | 269.9 | -29.1 [-33.7, -24.6] | 0.89 | 1.2e-37 |
| 51 | P4 actions: plan-relevant vs generic probing | 728 | 240.8 | 295.4 | -54.7 [-58.7, -50.6] | 0.81 | 8.8e-97 |
| 51 | P5 compute: indexed vs unindexed probing | 728 | 411985.5 | 579828.2 | -167842.7 [-175608.0, -160241.3] | 0.71 | 1.5e-119 |
| 51 | P5 actions: indexed vs unindexed probing | 728 | 240.8 | 240.8 | 0.0 [0.0, 0.0] | 1.00 | identical in every episode |

## Controls and out-of-language condition (difference in actions, A − B)

| Board | Condition | A | B | n | A − B [95% CI] | Oracle actions |
|---|---|---|---|---|---|---|
| 15 | none | Indexed repair + probing | Indexed repair | 300 | -0.6 [-0.9, -0.3] | 50.0 |
| 15 | none | Indexed repair | No revision | 300 | 2.7 [2.1, 3.5] | 50.0 |
| 15 | none | Indexed repair | Posterior sampling | 300 | -2.6 [-3.7, -1.5] | 50.0 |
| 15 | irrelevant | Indexed repair + probing | Indexed repair | 158 | -0.4 [-0.6, -0.1] | 47.2 |
| 15 | irrelevant | Indexed repair | No revision | 158 | 0.2 [-0.7, 1.1] | 47.2 |
| 15 | irrelevant | Indexed repair | Posterior sampling | 158 | -2.4 [-3.5, -1.3] | 47.2 |
| 15 | ool | Indexed repair + probing | Indexed repair | 169 | -0.8 [-1.8, 0.0] | 54.1 |
| 15 | ool | Indexed repair | No revision | 169 | -8.7 [-11.8, -5.5] | 54.1 |
| 15 | ool | Indexed repair | Posterior sampling | 169 | -1.0 [-3.2, 1.2] | 54.1 |
| 31 | none | Indexed repair + probing | Indexed repair | 300 | -0.9 [-1.8, -0.2] | 118.0 |
| 31 | none | Indexed repair | No revision | 300 | 7.8 [6.4, 9.2] | 118.0 |
| 31 | none | Indexed repair | Posterior sampling | 300 | -12.1 [-15.5, -8.9] | 118.0 |
| 31 | irrelevant | Indexed repair + probing | Indexed repair | 24 | -0.6 [-1.8, 0.2] | 100.3 |
| 31 | irrelevant | Indexed repair | No revision | 24 | 2.0 [0.5, 4.0] | 100.3 |
| 31 | irrelevant | Indexed repair | Posterior sampling | 24 | -4.2 [-12.5, 0.5] | 100.3 |
| 31 | ool | Indexed repair + probing | Indexed repair | 229 | 2.2 [-0.9, 5.5] | 125.9 |
| 31 | ool | Indexed repair | No revision | 229 | -23.4 [-29.9, -17.1] | 125.9 |
| 31 | ool | Indexed repair | Posterior sampling | 229 | -16.5 [-24.1, -9.9] | 125.9 |
| 51 | none | Indexed repair + probing | Indexed repair | 300 | -2.2 [-3.8, -0.6] | 212.3 |
| 51 | none | Indexed repair | No revision | 300 | 19.8 [16.9, 22.8] | 212.3 |
| 51 | none | Indexed repair | Posterior sampling | 300 | -16.8 [-23.0, -11.0] | 212.3 |
| 51 | irrelevant | Indexed repair + probing | Indexed repair | 2 | -2.0 [-2.0, -2.0] | 153.0 |
| 51 | irrelevant | Indexed repair | No revision | 2 | 2.0 [2.0, 2.0] | 153.0 |
| 51 | irrelevant | Indexed repair | Posterior sampling | 2 | 0.0 [0.0, 0.0] | 153.0 |
| 51 | ool | Indexed repair + probing | Indexed repair | 214 | 6.6 [0.8, 12.7] | 229.6 |
| 51 | ool | Indexed repair | No revision | 214 | -43.0 [-57.9, -28.7] | 229.6 |
| 51 | ool | Indexed repair | Posterior sampling | 214 | -38.1 [-53.3, -24.5] | 229.6 |

## Total-cost regret, actions + λ × expansions (violations pooled)

| Board | λ | No revision | Revise + replan | Posterior sampling | Generic probing | Indexed repair | Indexed repair + probing | Replan + probing |
|---|---|---|---|---|---|---|---|---|
| 15 | 0.0 | 13.4 | 7.1 | 10.2 | 37.4 | 7.1 | 6.1 | 6.1 |
| 15 | 0.001 | 14.2 | 8.6 | 12.5 | 44.7 | 8.2 | 18.6 | 31.2 |
| 15 | 0.01 | 21.5 | 21.9 | 32.4 | 111.0 | 18.0 | 131.4 | 257.8 |
| 31 | 0.0 | 37.2 | 16.4 | 31.1 | 59.1 | 16.4 | 13.2 | 13.2 |
| 31 | 0.001 | 43.0 | 25.2 | 46.5 | 99.2 | 23.2 | 130.5 | 184.8 |
| 31 | 0.01 | 95.6 | 104.3 | 185.8 | 460.4 | 84.6 | 1185.8 | 1728.6 |
| 51 | 0.0 | 75.6 | 34.8 | 55.7 | 81.2 | 34.8 | 26.6 | 26.6 |
| 51 | 0.001 | 102.5 | 60.9 | 113.0 | 199.3 | 54.8 | 446.5 | 614.3 |
| 51 | 0.01 | 345.2 | 295.7 | 628.9 | 1261.9 | 235.0 | 4226.0 | 5904.5 |

## Skipped episodes (no rule on the map fits the condition)

15/block: 131, 15/irrelevant: 142, 15/ool: 131, 15/slow: 131, 15/unlock: 38, 31/block: 71, 31/irrelevant: 276, 31/ool: 71, 31/slow: 71, 31/unlock: 5, 51/block: 86, 51/irrelevant: 298, 51/ool: 86, 51/slow: 86
