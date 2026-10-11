# Zombie citations: numbers

- retracted papers with 10+ citations joined to Retraction Watch: 19,586
- analysis set (retracted 2015-2023, 3+ citations a year before): 5,516, matched 5,433; match levels {'same field': 4238, 'any field': 1195, 'unmatched': 83}; distinct controls 17,717
- citations to papers in years after their retraction, 2013-2025: 208,330
- citations in 2025 to papers retracted by 2022: 10,536, spread over 4,354 of 10,339 papers
- half-life after retraction: 0.80 years (matched controls 3.00)
- share of expected citations kept 3-5 years on: 26.8% (25.0% to 28.4%)
- matched retracted papers (retracted by 2022) cited in 2025 at or above their old rate: 2.5%

## Event study (citations relative to the two years before)

|   k |    n |   treated |   control |   ratio |   ratio_lo |   ratio_hi |
|----:|-----:|----------:|----------:|--------:|-----------:|-----------:|
|  -3 | 5433 |     0.579 |     0.56  |   1.033 |      1.024 |      1.042 |
|  -2 | 5433 |     0.842 |     0.809 |   1.04  |      1.033 |      1.047 |
|  -1 | 5433 |     1.158 |     1.109 |   1.045 |      1.037 |      1.053 |
|   0 | 5433 |     1.04  |     1.214 |   0.857 |      0.837 |      0.876 |
|   1 | 5433 |     0.633 |     1.251 |   0.506 |      0.485 |      0.524 |
|   2 | 5433 |     0.388 |     1.18  |   0.328 |      0.313 |      0.344 |
|   3 | 3825 |     0.292 |     1.076 |   0.271 |      0.255 |      0.289 |
|   4 | 2599 |     0.28  |     1.053 |   0.266 |      0.245 |      0.285 |
|   5 | 1777 |     0.272 |     1.037 |   0.262 |      0.238 |      0.287 |
|   6 | 1339 |     0.227 |     0.973 |   0.234 |      0.21  |      0.262 |
|   7 | 1046 |     0.185 |     0.909 |   0.204 |      0.176 |      0.228 |
|   8 |  756 |     0.161 |     0.82  |   0.196 |      0.174 |      0.226 |
|   9 |  503 |     0.127 |     0.736 |   0.172 |      0.142 |      0.204 |
|  10 |  228 |     0.096 |     0.697 |   0.137 |      0.102 |      0.179 |

## By field

| group                      |    n |   share_kept_3to5y |   share_lo |   share_hi |   half_life |   half_life_lo |   half_life_hi |   control_half_life |
|:---------------------------|-----:|-------------------:|-----------:|-----------:|------------:|---------------:|---------------:|--------------------:|
| All fields                 | 5433 |               0.27 |       0.25 |       0.28 |        0.8  |           0.75 |           0.83 |                3    |
| Physical & earth sciences  |  245 |               0.21 |       0.17 |       0.25 |        0.73 |           0.5  |           0.88 |                3.75 |
| Molecular & cell biology   | 1995 |               0.21 |       0.19 |       0.24 |        0.62 |           0.58 |           0.69 |                2.75 |
| Engineering & computing    | 1074 |               0.25 |       0.22 |       0.29 |        1.17 |           1    |           1.33 |                4.5  |
| Social sciences & business |  170 |               0.26 |       0.2  |       0.34 |        1.67 |           1.5  |           1.78 |                4.92 |
| Medicine                   | 1608 |               0.34 |       0.31 |       0.37 |        0.8  |           0.75 |           0.83 |                2.64 |
| Agriculture & ecology      |  149 |               0.35 |       0.27 |       0.44 |        1.25 |           0.91 |           1.56 |                5.75 |
| Neuroscience & psychology  |  191 |               0.37 |       0.23 |       0.57 |        0.83 |           0.66 |           1.12 |                3    |

## By reason

| group                              |    n |   share_kept_3to5y |   share_lo |   share_hi |   half_life |   half_life_lo |   half_life_hi |   control_half_life |
|:-----------------------------------|-----:|-------------------:|-----------:|-----------:|------------:|---------------:|---------------:|--------------------:|
| All fields                         | 5433 |               0.27 |       0.25 |       0.28 |        0.8  |           0.75 |           0.83 |                3    |
| paper mill / fake review           |  959 |               0.21 |       0.18 |       0.26 |        1.5  |           1.33 |           1.55 |                4.75 |
| honest error                       |  566 |               0.25 |       0.19 |       0.31 |        0.81 |           0.75 |           0.88 |                3.75 |
| misconduct / image problems        | 2802 |               0.25 |       0.24 |       0.27 |        0.64 |           0.61 |           0.67 |                2.6  |
| other / unstated                   |  624 |               0.28 |       0.22 |       0.36 |        0.9  |           0.83 |           0.97 |                3.25 |
| plagiarism / duplicate publication |  482 |               0.36 |       0.32 |       0.4  |        0.95 |           0.83 |           1.12 |                2.9  |

## Sensitivity

| variant                     |    n |   share_kept_3to5y |   pre_gap_k-1 |   share_kept_pre_adjusted |   half_life |   control_half_life |
|:----------------------------|-----:|-------------------:|--------------:|--------------------------:|------------:|--------------------:|
| main analysis               | 5433 |              0.268 |         1.045 |                     0.256 |       0.8   |               3     |
| baseline at least 5 a year  | 3409 |              0.267 |         1.046 |                     0.255 |       0.75  |               3.694 |
| baseline at least 10 a year | 1377 |              0.272 |         1.048 |                     0.259 |       0.75  |               4.833 |
| tighter caliper (0.2)       | 5108 |              0.255 |         1.016 |                     0.251 |       0.833 |               3.583 |
| looser caliper (0.5)        | 5501 |              0.266 |         1.08  |                     0.246 |       0.789 |               2.955 |
| same-field controls only    | 4238 |              0.264 |         1.044 |                     0.253 |       0.833 |               3.417 |
| retracted 2015-2020 only    | 1777 |              0.297 |         1.028 |                     0.289 |       0.833 |               3.25  |
| retracted 2018-2023 only    | 4677 |              0.247 |         1.047 |                     0.236 |       0.812 |               3.083 |

## Top zombies (61 papers fetched)

- citations since retraction: 18,038; from works mentioning retraction in title or abstract: 240 (1.3%); papers where none do: 35
- peak citation year after the retraction year: 25; cited more in 2025 than the year before retraction: 23
|   rank | title                                                                  | journal                                                 |   ret_year | reason_group                       |   cites_year_before |   cites_2025 |   cites_after_retraction |   share_mentioning_retraction |
|-------:|:-----------------------------------------------------------------------|:--------------------------------------------------------|-----------:|:-----------------------------------|--------------------:|-------------:|-------------------------:|------------------------------:|
|      1 | Ileal-lymphoid-nodular hyperplasia, non-specific colitis, and pervasiv | The Lancet                                              |       2010 | misconduct / image problems        |                  96 |           79 |                     1945 |                           5   |
|      2 | Carbon Nanotubes Are Able To Penetrate Plant Seed Coat and Dramaticall | ACS Nano                                                |       2012 | misconduct / image problems        |                  26 |           79 |                      980 |                           0.3 |
|      3 | Association Between Physician Burnout and Patient Safety, Professional | JAMA Internal Medicine                                  |       2020 | honest error                       |                 128 |           59 |                      504 |                           0   |
|      4 | A mathematical model explains saturating axon guidance responses to mo | eLife                                                   |       2018 | honest error                       |                  88 |           56 |                      988 |                           0.4 |
|      5 | Quality of service (QoS) and priority aware models for energy efficien | Journal of Ambient Intelligence and Humanized Computing |       2022 | paper mill / fake review           |                   5 |           51 |                       68 |                           0   |
|      6 | Roles of the PI3K/AKT/mTOR signalling pathways in neurodegenerative di | Cell & Bioscience                                       |       2021 | plagiarism / duplicate publication |                  27 |           44 |                      349 |                           0.3 |
|      7 | Surface Functional Groups and Interlayer Water Determine the Electroch | ACS Nano                                                |       2021 | misconduct / image problems        |                  95 |           43 |                      186 |                           0   |
|      8 | Ammonia synthesis by N 2 and steam electrolysis in molten hydroxide su | Science                                                 |       2020 | honest error                       |                 112 |           42 |                      314 |                           0   |
|      9 | An enhanced transient expression system in plants based on suppression | The Plant Journal                                       |       2015 | misconduct / image problems        |                 153 |           39 |                      615 |                           0.3 |
|     10 | A Comprehensive Review on Metabolic Syndrome                           | Cardiology Research and Practice                        |       2019 | plagiarism / duplicate publication |                 306 |           38 |                      691 |                           0   |
|     11 | The role of nitric oxide in inflammatory reactions                     | FEMS Immunology & Medical Microbiology                  |       2012 | plagiarism / duplicate publication |                  20 |           38 |                      411 |                           0   |
|     12 | Apoptosis and Molecular Targeting Therapy in Cancer                    | BioMed Research International                           |       2020 | plagiarism / duplicate publication |                 158 |           36 |                      426 |                           1.2 |
|     13 | The Nature of Creativity                                               | Creativity Research Journal                             |       2019 | plagiarism / duplicate publication |                  98 |           35 |                      362 |                           0.3 |
|     14 | Absorptive Capacity, Environmental Turbulence, and the Complementarity | Academy of Management Journal                           |       2013 | misconduct / image problems        |                  83 |           34 |                      654 |                           0.3 |
|     15 | Employees’ Perceptions of Green HRM and Non-Green Employee Work Outcom | Group & Organization Management                         |       2022 | honest error                       |                  28 |           32 |                      122 |                           0   |
