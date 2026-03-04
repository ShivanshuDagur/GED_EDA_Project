# =============================================================================
# GED PERFORMANCE DISPARITY — DIANA HIERARCHICAL CLUSTERING
# =============================================================================
# Goal: Segment GED candidates into meaningful groups based on performance,
#       demographics, geography, and preparation behaviors.
#
# Method: Divisive hierarchical clustering (DIANA (Top-Down)). Starts with all candidates
#         in one group and recursively splits the most dissimilar group apart.
#
# Cluster count:
#   K is selected by inspecting the silhouette plot produced in Section 6.
#   The plot shows average silhouette width for k = 2 through 8. After
#   reviewing the plot, set K manually at the top of Section 6 and re-run
#   from that section onwards. The statistical optimum (highest silhouette)
#   is highlighted automatically, but you may prefer a higher k if the
#   optimum produces clusters that are too coarse to be interpretable.
#
# Update INPUT_FILE below, then run the full script (Ctrl+A → Ctrl+Enter).
# =============================================================================

set.seed(1234)

INPUT_FILE    <- "C:/Users/davey/OneDrive/Desktop/5_test_candidate_cleaned_final.csv"
VAR_THRESHOLD <- 0.02  # Features with normalized variance below this are dropped

# ── PACKAGES ──────────────────────────────────────────────────────────────────

required <- c("tidyverse", "cluster", "scales", "RColorBrewer", "knitr")
new_pkgs <- required[!(required %in% installed.packages()[, "Package"])]
if (length(new_pkgs)) install.packages(new_pkgs, dependencies = TRUE)
invisible(suppressPackageStartupMessages(
  lapply(required, library, character.only = TRUE)
))

# ── SECTION 1: LOAD DATA ──────────────────────────────────────────────────────

raw <- read_csv(INPUT_FILE, show_col_types = FALSE)

cat("Raw data dimensions:", nrow(raw), "rows x", ncol(raw), "columns\n")
cat("Unique candidates  :", n_distinct(raw$CANDIDATE_ID), "\n")

# ── SECTION 2: BUILD CANDIDATE-LEVEL DATASET ──────────────────────────────────
# The raw data is at the exam attempt level (one row per subject per attempt).
# We aggregate to one row per candidate before clustering.
#
# Geography note: T_STATE is excluded. ~61% of online attempts are routed
# through a Bloomington, MN hub (center 66745), making T_STATE a delivery
# artifact rather than a geographic signal. C_STATE (candidate home state)
# is used instead.

candidates <- raw %>%
  mutate(score_clean = if_else(SCORE_MISSING == 1L, NA_real_, SCORE)) %>%
  group_by(CANDIDATE_ID) %>%
  summarise(
    
    # --- Performance ---
    avg_score          = mean(score_clean, na.rm = TRUE),
    pass_rate          = mean(if_else(!is.na(score_clean) & score_clean >= 145,
                                      1L, 0L), na.rm = TRUE),
    college_ready_rate = mean(if_else(!is.na(score_clean) & score_clean >= 165,
                                      1L, 0L), na.rm = TRUE),
    total_attempts     = n(),
    avg_retakes        = (n() / n_distinct(EXAM_SUBJECT)) - 1,
    credential_earned  = as.integer(any(!is.na(CREDENTIAL_DATE))),
    
    # Subject scores — NA when that subject was never attempted
    # Encoding: Math=1, Science=2, Reasoning=3, Social Studies=4
    score_math           = mean(score_clean[EXAM_SUBJECT == 1], na.rm = TRUE),
    score_science        = mean(score_clean[EXAM_SUBJECT == 2], na.rm = TRUE),
    score_reasoning      = mean(score_clean[EXAM_SUBJECT == 3], na.rm = TRUE),
    score_social_studies = mean(score_clean[EXAM_SUBJECT == 4], na.rm = TRUE),
    
    # --- Delivery ---
    pct_online     = mean(as.integer(ON_VUE == 1), na.rm = TRUE),
    used_ged_ready = as.integer(any(GED_READY == 1, na.rm = TRUE)),
    
    # --- Demographics (stable per candidate; first() is safe here) ---
    # Encoding: Male=1, Female=2, Nonbinary=3, Decline=4, Unknown=0
    gender = first(GENDER),
    # Encoding: English=1, Spanish=2, Unknown=0
    language_code = first(LANGUAGE_CODE),
    # Encoding: Under $5K=1 ... $75K+=8, Unknown=0
    last_year_income = first(LAST_YEAR_INCOME),
    # Encoding: PreK-5=1, 6-8=2, 9th=3, 10th=4, 11th=5, 12th=6,
    #           Don't Remember=7, Other=8, Never=9, Unknown=0
    highest_grade = first(HIGHEST_GRADE_COMPLETED),
    # Encoding: Non-Hispanic=1, Hispanic=2, Decline=3, Unknown=0
    ethnicity     = first(ETHNICITY),
    race_white    = first(WHITE),
    race_black    = first(AFRICAN_AMERICAN),
    race_asian    = first(ASIAN),
    race_native   = first(INDIAN_OR_ALASKAN),
    race_pacific  = first(HAWAIIAN_OR_PACIFIC),
    race_declined = first(RACE_DECLINE),
    race_none     = first(RACE_NONE),
    birth_year    = first(BIRTH_YEAR),
    
    # --- Geography ---
    c_state = first(C_STATE),
    
    # --- Preparation and motivation ---
    studied_for_ged          = first(STUDIED_FOR_GED),
    # Encoding: Work=1, Ed. Gain=2, Personal=3, Military=4, Special=5, Unknown=0
    testing_reason           = first(TESTING_REASON),
    # Encoding: Academic=1, Personal=2, Both=3, Neither=4,
    #           Homeschool=5, Foreign Diploma=6, Unknown=0
    school_incomplete_reason = first(SCHOOL_INCOMPLETE_REASON),
    # Encoding: Interested=1, Contacted=2, Enrolled=3,
    #           Credentialed=4, Dismissed=5, Unknown=0
    enrollment_status        = first(ENROLLMENT_STATUS),
    has_prep_center          = as.integer(first(PREP_CENTER) != "UNKNOWN"),
    study_adult_ed_class     = first(STUDY_HELPFUL_ADULT_EDUCATION_CLASS),
    study_books              = first(STUDY_HELPFUL_BOOKS_PRINTED_STUDY_MATERIAL),
    study_online_video       = first(STUDY_HELPFUL_ONLINE_COURSE_VIDEO_STUDY_MATERIALS),
    
    .groups = "drop"
  ) %>%
  mutate(
    across(c(score_math, score_science, score_reasoning, score_social_studies),
           ~ if_else(is.nan(.x), NA_real_, .x)),
    age = 2024 - birth_year,
    
    census_region = case_when(
      c_state %in% c("CT","ME","MA","NH","RI","VT","NJ","NY","PA") ~ "Northeast",
      c_state %in% c("IL","IN","MI","OH","WI","IA","KS","MN",
                     "MO","NE","ND","SD")                          ~ "Midwest",
      c_state %in% c("DE","FL","GA","MD","NC","SC","VA","WV","DC",
                     "AL","KY","MS","TN","AR","LA","OK","TX")      ~ "South",
      c_state %in% c("AZ","CO","ID","MT","NV","NM","UT","WY",
                     "AK","CA","HI","OR","WA")                     ~ "West",
      TRUE                                                          ~ "Other"
    ),
    
    race_category = case_when(
      race_declined == 1               ~ "Declined",
      race_none     == 1               ~ "Not Reported",
      race_black == 1 & ethnicity == 2 ~ "Black Hispanic",
      race_black == 1                  ~ "Black Non-Hispanic",
      ethnicity  == 2                  ~ "Hispanic",
      race_white == 1                  ~ "White Non-Hispanic",
      race_asian == 1                  ~ "Asian",
      race_native == 1                 ~ "Native American",
      race_pacific == 1                ~ "Pacific Islander",
      TRUE                             ~ "Multiracial/Other"
    ),
    
    gender_label = case_when(
      gender == 1 ~ "Male",   gender == 2 ~ "Female",
      gender == 3 ~ "Nonbinary", gender == 4 ~ "Decline",
      TRUE ~ "Unknown"
    ),
    language_label = case_when(
      language_code == 1 ~ "English", language_code == 2 ~ "Spanish",
      TRUE ~ "Unknown"
    ),
    income_label = case_when(
      last_year_income == 1 ~ "Under $5K",    last_year_income == 2 ~ "$5K-$9,999",
      last_year_income == 3 ~ "$10K-$19,999", last_year_income == 4 ~ "$20K-$29,999",
      last_year_income == 5 ~ "$30K-$39,999", last_year_income == 6 ~ "$40K-$49,999",
      last_year_income == 7 ~ "$50K-$74,999", last_year_income == 8 ~ "$75K+",
      TRUE ~ "Unknown"
    ),
    edlevel_label = case_when(
      highest_grade == 1 ~ "Pre-K to 5th",  highest_grade == 2 ~ "6th-8th",
      highest_grade == 3 ~ "9th Grade",     highest_grade == 4 ~ "10th Grade",
      highest_grade == 5 ~ "11th Grade",    highest_grade == 6 ~ "12th Grade",
      highest_grade == 7 ~ "Don't Remember", highest_grade == 8 ~ "Other",
      highest_grade == 9 ~ "Never Attended", TRUE ~ "Unknown"
    ),
    testing_reason_label = case_when(
      testing_reason == 1 ~ "Work",      testing_reason == 2 ~ "Education",
      testing_reason == 3 ~ "Personal",  testing_reason == 4 ~ "Military",
      testing_reason == 5 ~ "Special Req.", TRUE ~ "Unknown"
    ),
    school_incomplete_label = case_when(
      school_incomplete_reason == 1 ~ "Academic",
      school_incomplete_reason == 2 ~ "Personal",
      school_incomplete_reason == 3 ~ "Personal & Academic",
      school_incomplete_reason == 4 ~ "Neither",
      school_incomplete_reason == 5 ~ "Home Schooled",
      school_incomplete_reason == 6 ~ "Foreign Diploma",
      TRUE ~ "Unknown"
    ),
    enrollment_label = case_when(
      enrollment_status == 1 ~ "Interested", enrollment_status == 2 ~ "Contacted",
      enrollment_status == 3 ~ "Enrolled",   enrollment_status == 4 ~ "Credentialed",
      enrollment_status == 5 ~ "Dismissed",  TRUE ~ "Unknown"
    )
  )

cat("Candidates after aggregation:", nrow(candidates), "\n")

# ── SECTION 3: VARIANCE-BASED FEATURE SELECTION ───────────────────────────────
# Features that barely vary across candidates provide little separation power
# and can distort distance calculations by adding noise without signal.
# We use variance filtering to drop those features before clustering.
#
# However, demographic features are always kept regardless of their variance.
# Even if a demographic group is a small minority in the sample, excluding
# them would mean the clustering cannot detect disparities affecting that
# group — which is central to the research question. Low variance in a
# demographic feature often reflects real population composition, not a
# lack of relevance.
#
# Filtering rules:
#   Numeric (non-demographic): coefficient of variation (SD / mean).
#     CV < VAR_THRESHOLD → dropped.
#   Nominal (non-demographic): 1 - proportion of dominant category.
#     Value < VAR_THRESHOLD → dropped.
#   Demographic features: always retained.

# Features that are always kept regardless of variance
demographic_features <- c(
  # Numeric demographics
  "age",
  # Nominal demographics
  "gender_label", "language_label", "race_category",
  "income_label", "edlevel_label", "census_region"
)

numeric_cols <- c("avg_score", "pass_rate", "college_ready_rate", "avg_retakes",
                  "credential_earned", "pct_online", "used_ged_ready",
                  "studied_for_ged", "has_prep_center",
                  "study_adult_ed_class", "study_books", "study_online_video",
                  "age", "score_math", "score_science",
                  "score_reasoning", "score_social_studies")

nominal_cols <- c("gender_label", "language_label", "race_category",
                  "income_label", "edlevel_label", "testing_reason_label",
                  "school_incomplete_label", "enrollment_label", "census_region")

numeric_var <- tibble(feature = numeric_cols) %>%
  mutate(
    variance = map_dbl(feature, ~ {
      x <- candidates[[.x]]; x <- x[!is.na(x)]
      if (mean(x) == 0) return(0)
      sd(x) / abs(mean(x))
    }),
    type      = "Numeric",
    protected = feature %in% demographic_features,
    retain    = protected | variance >= VAR_THRESHOLD
  )

nominal_var <- tibble(feature = nominal_cols) %>%
  mutate(
    variance = map_dbl(feature, ~ {
      x <- candidates[[.x]]
      1 - max(table(x) / length(x))
    }),
    type      = "Nominal",
    protected = feature %in% demographic_features,
    retain    = protected | variance >= VAR_THRESHOLD
  )

variance_report <- bind_rows(numeric_var, nominal_var) %>%
  arrange(desc(variance)) %>%
  mutate(
    variance = round(variance, 4),
    Status   = case_when(
      protected & variance < VAR_THRESHOLD ~ "Keep (demographic — protected)",
      retain                               ~ "Keep",
      TRUE                                 ~ "Drop"
    )
  )

cat("\n--- FEATURE SELECTION ---\n")
cat(sprintf("Variance threshold: %.2f  |  Demographic features always retained\n\n",
            VAR_THRESHOLD))
print(kable(variance_report %>% select(feature, type, variance, Status),
            col.names = c("Feature", "Type", "Variance", "Status"),
            format = "simple"))

retained_numeric <- numeric_var %>% filter(retain) %>% pull(feature)
retained_nominal <- nominal_var %>% filter(retain) %>% pull(feature)
dropped          <- variance_report %>% filter(!retain) %>% pull(feature)
protected_kept   <- variance_report %>%
  filter(protected, variance < VAR_THRESHOLD) %>% pull(feature)

cat(sprintf("\nRetained: %d numeric, %d nominal\n",
            length(retained_numeric), length(retained_nominal)))
if (length(protected_kept) > 0)
  cat("Protected (low variance but kept):",
      paste(protected_kept, collapse = ", "), "\n")
if (length(dropped) > 0)
  cat("Dropped  :", paste(dropped, collapse = ", "), "\n")

# ── SECTION 4: BUILD THE CLUSTERING MATRIX ────────────────────────────────────
# Numeric features are split into two groups:
#
#   Continuous  → z-score normalized (mean = 0, SD = 1) so that features
#                 with different scales (e.g., raw scores vs. proportions)
#                 contribute equally to the distance calculation.
#
#   Binary flags → kept as raw 0/1. daisy() requires exact integer 0/1
#                  values for asymmetric binary features. Z-scoring would
#                  convert them to non-integer values and cause an error.
#
# Nominal features are cast to factor so daisy() applies simple-matching
# distance rather than treating the integer codes as numeric.
#
# Subject score NAs (candidate never sat that subject) are left as NA —
# Gower distance handles them by excluding that feature from the pairwise
# distance calculation rather than imputing or dropping the row.

binary_cols     <- intersect(
  c("used_ged_ready", "studied_for_ged", "has_prep_center", "credential_earned",
    "study_adult_ed_class", "study_books", "study_online_video"),
  retained_numeric
)
continuous_cols <- setdiff(retained_numeric, binary_cols)

subject_score_cols <- c("score_math", "score_science",
                        "score_reasoning", "score_social_studies")

cluster_df <- candidates %>%
  select(CANDIDATE_ID,
         all_of(continuous_cols),
         all_of(binary_cols),
         all_of(retained_nominal)) %>%
  # Z-score continuous features only
  mutate(across(
    all_of(continuous_cols),
    ~ { v <- .x[!is.na(.x)]; (.x - mean(v)) / sd(v) }
  )) %>%
  # Non-structural NAs in continuous columns → 0 (the z-score mean).
  # Subject score NAs are structural and intentionally preserved.
  mutate(across(
    all_of(setdiff(continuous_cols, subject_score_cols)),
    ~ replace_na(.x, 0)
  )) %>%
  mutate(across(all_of(binary_cols),    as.integer)) %>%
  mutate(across(all_of(retained_nominal), as.factor))

cat("\nClustering matrix:", nrow(cluster_df), "candidates x",
    ncol(cluster_df) - 1, "features\n")

# ── SECTION 5: GOWER DISTANCE MATRIX ─────────────────────────────────────────
# Gower distance handles mixed feature types by computing a type-appropriate
# partial dissimilarity for each feature, then averaging across features.
# This makes it the standard choice for datasets that mix continuous,
# binary, and nominal variables.
#
# The 'asymm' flag marks binary features where both candidates scoring 0
# (e.g., neither used GED Ready) should NOT count as similarity. Without
# this, rare behaviors would artificially inflate similarity scores.

cat("\nComputing Gower distance matrix...\n")

gower_dist <- daisy(
  cluster_df %>% select(-CANDIDATE_ID),
  metric = "gower",
  type   = list(asymm = binary_cols)
)

cat("Distance matrix complete.\n")

# ── SECTION 6: DIANA CLUSTERING + SILHOUETTE ANALYSIS ────────────────────────
# DIANA (Divisive ANAlysis) is a top-down algorithm. It begins with all
# candidates in one group, then repeatedly finds the most dissimilar
# group and splits it, until every candidate is its own group.
#
# The Divisive Coefficient (DC) summarizes overall clustering strength:
#   DC > 0.70 indicates meaningful structure in the data.
#   DC close to 1.0 = strong, well-separated clusters.
#
# STEP 1: Run the full section once to see the silhouette plot.
# STEP 2: Choose K based on the plot (see guidance below the plot).
# STEP 3: Set K here, then re-run from this section downwards.

K <- 4  # <-- SET THIS after reviewing the silhouette plot. Re-run from here.

cat("\nRunning DIANA...\n")
diana_model <- diana(gower_dist, diss = TRUE)
cat(sprintf("Divisive Coefficient: %.4f\n", diana_model$dc))
cat("DC > 0.70 indicates meaningful cluster structure.\n")

hc <- as.hclust(diana_model)

# --- Silhouette analysis ---
# Silhouette width measures how well each candidate fits its assigned cluster
# vs. the next-best cluster. Values range from -1 to 1:
#   Near  1 = candidate is well-matched to its cluster
#   Near  0 = candidate sits on the boundary between two clusters
#   Near -1 = candidate may be misclassified
# We compute the average across all candidates for each value of k.

cat("\nComputing silhouette widths for k = 2 through 8...\n")

sil_results <- map_dfr(2:8, function(k) {
  labels <- cutree(hc, k = k)
  sil    <- silhouette(labels, gower_dist)
  tibble(k = k, avg_silhouette = round(mean(sil[, 3]), 4))
})

stat_opt <- sil_results$k[which.max(sil_results$avg_silhouette)]

# Print table with the statistical optimum flagged
sil_results %>%
  mutate(Note = if_else(k == stat_opt, "<-- statistical optimum", "")) %>%
  kable(format = "simple", col.names = c("k", "Avg Silhouette", "")) %>%
  print()

cat(sprintf("\nStatistical optimum: k = %d (avg silhouette = %.4f)\n",
            stat_opt, max(sil_results$avg_silhouette)))
cat(sprintf("Currently selected:  k = %d\n", K))

# --- Silhouette plot ---
# How to read this plot:
#   - Higher silhouette = better-separated, more internally cohesive clusters
#   - The grey diamond marks the statistical optimum (highest silhouette)
#   - The red dot marks your selected K
#   - If the optimum produces only 2 clusters, consider whether that is
#     granular enough for your research question before accepting it

print(
  ggplot(sil_results, aes(x = k, y = avg_silhouette)) +
    geom_line(color = "#2166AC", linewidth = 1.3) +
    geom_point(size = 4.5, color = "#2166AC") +
    
    # Statistical optimum — grey diamond
    geom_point(data = filter(sil_results, k == stat_opt),
               size = 7, shape = 18, color = "grey30") +
    annotate("text",
             x     = stat_opt,
             y     = sil_results$avg_silhouette[sil_results$k == stat_opt],
             label = sprintf("Statistical optimum\n(k = %d, sil = %.3f)",
                             stat_opt,
                             sil_results$avg_silhouette[sil_results$k == stat_opt]),
             hjust = -0.1, vjust = 0.5, size = 3.2, color = "grey30") +
    
    # Selected K — red dot (shown only if different from stat_opt)
    {if (K != stat_opt)
      list(
        geom_point(data = filter(sil_results, k == K),
                   size = 7, shape = 21, fill = "#D6604D",
                   color = "white", stroke = 2),
        annotate("text",
                 x     = K,
                 y     = sil_results$avg_silhouette[sil_results$k == K],
                 label = sprintf("Selected\n(k = %d, sil = %.3f)",
                                 K,
                                 sil_results$avg_silhouette[sil_results$k == K]),
                 hjust = 1.1, vjust = -0.3, size = 3.2, color = "#D6604D"),
        # Shaded band between stat optimum and selected K
        annotate("rect",
                 xmin  = min(stat_opt, K) - 0.3,
                 xmax  = max(stat_opt, K) + 0.3,
                 ymin  = -Inf, ymax = Inf,
                 fill  = "#FEE8C8", alpha = 0.35)
      )
    } +
    
    scale_x_continuous(breaks = 2:8) +
    scale_y_continuous(labels = number_format(accuracy = 0.001)) +
    labs(
      title    = "Silhouette Analysis — How Many Clusters?",
      subtitle = sprintf(
        "Grey diamond = statistical optimum (k = %d)%s\nHigher silhouette = better cluster separation",
        stat_opt,
        if (K != stat_opt) sprintf("  |  Red dot = selected k = %d", K) else ""
      ),
      x = "Number of Clusters (k)",
      y = "Average Silhouette Width",
      caption = "Tip: if the optimum is k = 2 and feels too coarse, look for the next local peak"
    ) +
    theme_minimal(base_size = 12) +
    theme(
      plot.title    = element_text(face = "bold"),
      plot.subtitle = element_text(color = "grey40", size = 9.5),
      plot.caption  = element_text(color = "grey50", size = 8.5, face = "italic")
    )
)

# --- Dendrogram ---
# With ~4,691 candidates the dendrogram is dense, so individual candidate
# labels are suppressed (labels = FALSE) to keep it readable.
# The "display list redraw incomplete" warning is suppressed — it is harmless
# and only means the Plots pane had to rescale during rendering.
par(mar = c(3, 4, 4, 1))
suppressWarnings(
  plot(hc,
       main   = sprintf("DIANA Dendrogram  |  k = %d  |  DC = %.3f",
                        K, diana_model$dc),
       xlab   = "Candidates",
       ylab   = "Dissimilarity",
       labels = FALSE,
       hang   = -1)
)
rect.hclust(hc,
            k      = K,
            border = brewer.pal(max(K, 3), "Set1")[1:K])
# Reset margins to R defaults so subsequent plots are unaffected
par(mar = c(5.1, 4.1, 4.1, 2.1))

# ── SECTION 7: ASSIGN CLUSTERS AND NAME THEM ──────────────────────────────────
# Each cluster gets a short two-part name:
#   Part 1 — Performance tier, ranked by average score (1 = highest)
#   Part 2 — The single most distinctive trait for that cluster, identified
#             by finding which behavioral or demographic feature has the
#             largest z-score relative to the overall sample average.
# This ensures every cluster has a unique, data-driven name.

candidates <- candidates %>%
  mutate(cluster = cutree(hc, k = K))

profile <- candidates %>%
  group_by(cluster) %>%
  summarise(
    n                  = n(),
    avg_score          = round(mean(avg_score,          na.rm = TRUE), 1),
    pass_rate          = round(mean(pass_rate,          na.rm = TRUE), 3),
    college_ready_rate = round(mean(college_ready_rate, na.rm = TRUE), 3),
    credential_pct     = round(mean(credential_earned,  na.rm = TRUE), 3),
    avg_retakes        = round(mean(avg_retakes,        na.rm = TRUE), 2),
    pct_online         = round(mean(pct_online,         na.rm = TRUE), 3),
    pct_ged_ready      = round(mean(used_ged_ready,     na.rm = TRUE), 3),
    pct_prep_center    = round(mean(has_prep_center,    na.rm = TRUE), 3),
    pct_studied        = round(mean(studied_for_ged,    na.rm = TRUE), 3),
    pct_spanish        = round(mean(language_code == 2, na.rm = TRUE), 3),
    pct_black          = round(mean(race_black,         na.rm = TRUE), 3),
    pct_hispanic       = round(mean(ethnicity == 2,     na.rm = TRUE), 3),
    avg_age            = round(mean(age,                na.rm = TRUE), 1),
    .groups = "drop"
  ) %>%
  arrange(desc(avg_score)) %>%
  mutate(perf_rank = row_number())

# Performance tier names — one per rank level up to k = 6
tier_names <- c(
  "High Achievers",        # rank 1: best scores
  "Solid Performers",      # rank 2
  "Developing Learners",   # rank 3
  "Struggling Learners",   # rank 4
  "At-Risk Candidates",    # rank 5
  "Critical Needs"         # rank 6: lowest scores
)

# Distinctive trait lookup — maps profile column names to readable labels
trait_labels <- c(
  pct_online      = "Online-Heavy",
  pct_ged_ready   = "GED Ready Users",
  pct_prep_center = "Prep Supported",
  pct_studied     = "Self-Studiers",
  pct_spanish     = "Spanish Speaking",
  pct_black       = "Black Candidates",
  pct_hispanic    = "Hispanic Candidates",
  avg_age         = "Older Learners",
  avg_retakes     = "High Retakers"
)

# Sample-wide averages used as baseline for z-score comparison
benchmarks <- list(
  pct_online      = mean(candidates$pct_online,         na.rm = TRUE),
  pct_ged_ready   = mean(candidates$used_ged_ready,     na.rm = TRUE),
  pct_prep_center = mean(candidates$has_prep_center,    na.rm = TRUE),
  pct_studied     = mean(candidates$studied_for_ged,    na.rm = TRUE),
  pct_spanish     = mean(candidates$language_code == 2, na.rm = TRUE),
  pct_black       = mean(candidates$race_black,         na.rm = TRUE),
  pct_hispanic    = mean(candidates$ethnicity == 2,     na.rm = TRUE),
  avg_age         = mean(candidates$age,                na.rm = TRUE),
  avg_retakes     = mean(candidates$avg_retakes,        na.rm = TRUE)
)

cluster_names <- profile %>%
  mutate(
    tier  = tier_names[perf_rank],
    trait = map_chr(seq_len(n()), function(i) {
      row <- profile[i, ]
      z_scores <- map_dbl(names(trait_labels), function(feat) {
        val  <- as.numeric(row[[feat]])
        avg  <- benchmarks[[feat]]
        sdev <- sd(profile[[feat]], na.rm = TRUE)
        if (is.na(sdev) | sdev == 0) return(0)
        (val - avg) / sdev
      })
      names(z_scores) <- names(trait_labels)
      trait_labels[names(which.max(abs(z_scores)))]
    }),
    cluster_name = paste0(tier, " — ", trait)
  ) %>%
  # If two clusters share the same name (rare), append a number to distinguish
  group_by(cluster_name) %>%
  mutate(cluster_name = if_else(
    n() > 1,
    paste0(cluster_name, " (", row_number(), ")"),
    cluster_name
  )) %>%
  ungroup() %>%
  select(cluster, cluster_name)

candidates <- left_join(candidates, cluster_names, by = "cluster")

# ── SECTION 8: CLUSTER SUMMARY ────────────────────────────────────────────────
# The summary is split into four tables so it stays readable in the console:
#   (1) Performance       — scores, pass rate, retakes, credential
#   (2) Subject scores    — Math, Science, Reasoning, Social Studies
#   (3) Preparation       — study behaviors, GED Ready, prep center
#   (4) Demographics &
#       Geography         — race, language, gender, age, region, income, education

cat("\n=== CLUSTER SUMMARY ===\n")

# Helper: compute mean for a column, formatted as percent or rounded number
pct  <- function(x) percent(mean(x, na.rm = TRUE), 0.1)
avg  <- function(x) round(mean(x, na.rm = TRUE), 1)
avg2 <- function(x) round(mean(x, na.rm = TRUE), 2)

base_profile <- candidates %>%
  group_by(Cluster = cluster, Name = cluster_name) %>%
  summarise(N = n(), .groups = "drop") %>%
  arrange(Cluster)

# --- Table 1: Performance ---
cat("\n--- Performance ---\n")
candidates %>%
  group_by(Cluster = cluster) %>%
  summarise(
    `Avg Score`          = avg(avg_score),
    `Pass Rate`          = pct(pass_rate),
    `College Ready`      = pct(college_ready_rate),
    `Credential Earned`  = pct(credential_earned),
    `Total Attempts`     = avg2(total_attempts),
    `Avg Retakes`        = avg2(avg_retakes),
    .groups = "drop"
  ) %>%
  left_join(base_profile %>% select(Cluster, Name, N), by = "Cluster") %>%
  select(Cluster, Name, N, everything()) %>%
  arrange(Cluster) %>%
  kable(format = "simple") %>%
  print()

# --- Table 2: Subject Scores ---
cat("\n--- Subject Scores (passing threshold = 145) ---\n")
candidates %>%
  group_by(Cluster = cluster) %>%
  summarise(
    `Math`          = avg(score_math),
    `Science`       = avg(score_science),
    `Reasoning`     = avg(score_reasoning),
    `Social Studies`= avg(score_social_studies),
    .groups = "drop"
  ) %>%
  left_join(base_profile %>% select(Cluster, Name), by = "Cluster") %>%
  select(Cluster, Name, everything()) %>%
  arrange(Cluster) %>%
  kable(format = "simple") %>%
  print()

# --- Table 3: Preparation Behaviors ---
cat("\n--- Preparation Behaviors ---\n")
candidates %>%
  group_by(Cluster = cluster) %>%
  summarise(
    `Studied for GED`     = pct(studied_for_ged),
    `Used GED Ready`      = pct(used_ged_ready),
    `Has Prep Center`     = pct(has_prep_center),
    `Online Testing`      = pct(pct_online),
    `Study: Adult Ed`     = pct(study_adult_ed_class),
    `Study: Books`        = pct(study_books),
    `Study: Online Video` = pct(study_online_video),
    .groups = "drop"
  ) %>%
  left_join(base_profile %>% select(Cluster, Name), by = "Cluster") %>%
  select(Cluster, Name, everything()) %>%
  arrange(Cluster) %>%
  kable(format = "simple") %>%
  print()

# --- Table 4: Demographics & Geography ---
cat("\n--- Demographics & Geography ---\n")
candidates %>%
  group_by(Cluster = cluster) %>%
  summarise(
    `Avg Age`          = avg(age),
    `Male`             = pct(gender == 1),
    `Female`           = pct(gender == 2),
    `Black`            = pct(race_black == 1),
    `White`            = pct(race_white == 1),
    `Hispanic`         = pct(ethnicity == 2),
    `Asian`            = pct(race_asian == 1),
    `Spanish Lang`     = pct(language_code == 2),
    `Top Region`       = names(sort(table(census_region), decreasing = TRUE))[1],
    `Top State`        = names(sort(table(c_state),       decreasing = TRUE))[1],
    `Income Unknown`   = pct(last_year_income == 0),
    `Ed: 9th or Below` = pct(highest_grade <= 3 & highest_grade > 0),
    .groups = "drop"
  ) %>%
  left_join(base_profile %>% select(Cluster, Name), by = "Cluster") %>%
  select(Cluster, Name, everything()) %>%
  arrange(Cluster) %>%
  kable(format = "simple") %>%
  print()

cat(sprintf(
  "\nDIANA complete | DC = %.4f | k = %d | Features used = %d\n",
  diana_model$dc, K,
  length(retained_numeric) + length(retained_nominal)
))
