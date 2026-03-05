# =============================================================================
# GED PERFORMANCE DISPARITY — DIANA HIERARCHICAL CLUSTERING
# =============================================================================
# Goal: Segment GED candidates into meaningful groups based on performance,
#       demographics, geography, and preparation behaviors.
#
# Method: Divisive hierarchical clustering (DIANA). Starts with all candidates
#         in one group and recursively splits the most dissimilar group apart.
#
# Design decision — demographics excluded from clustering:
#   Demographic features (race, gender, language, age, income, education,
#   geography) are intentionally excluded from the clustering feature set.
#   Because the downstream goal is to analyze performance disparities across
#   demographic groups, including those features in the model would cause
#   bias leakage — the algorithm would group candidates partly by who they
#   are rather than how they performed, and the disparity analysis would
#   then be measuring what we told the model to find rather than discovering
#   it independently.
#
#   Clusters are built on performance and preparation behavior features only.
#   Demographic features are retained in the candidates dataframe and used
#   in Section 8 to profile the clusters post-hoc, which is the correct
#   separation between modeling and analysis.
#
# Cluster count:
#   K is selected by inspecting the silhouette plot in Section 6. Run the
#   full script once, review the plot, then set K and re-run from Section 6.
#
# Update INPUT_FILE below, then run the full script (Ctrl+A → Ctrl+Enter).
# =============================================================================

set.seed(1234)

INPUT_FILE    <- "C:/Users/davey/OneDrive/Desktop/5_test_candidate_cleaned_final.csv"
VAR_THRESHOLD          <- 0.15  # Clustering features below this variance are dropped
COR_THRESHOLD          <- 0.80  # If two clustering features correlate above this,
# the lower-variance one is dropped to reduce redundancy
COMPLETENESS_THRESHOLD <- 0.70  # Candidates with fewer than this proportion of
# clustering fields present are removed before
# clustering to prevent missingness artifact clusters

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
# is used for post-hoc geographic profiling only.

candidates <- raw %>%
  mutate(score_clean = if_else(SCORE_MISSING == 1L, NA_real_, SCORE)) %>%
  group_by(CANDIDATE_ID) %>%
  summarise(
    
    # --- Performance (used in clustering) ---
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
    
    # --- Delivery (used in clustering) ---
    pct_online     = mean(as.integer(ON_VUE == 1), na.rm = TRUE),
    used_ged_ready = as.integer(any(GED_READY == 1, na.rm = TRUE)),
    
    # --- Preparation (used in clustering) ---
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
    
    # --- Demographics (analysis only — NOT used in clustering) ---
    # Encoding: Male=1, Female=2, Nonbinary=3, Decline=4, Unknown=0
    gender           = first(GENDER),
    # Encoding: English=1, Spanish=2, Unknown=0
    language_code    = first(LANGUAGE_CODE),
    # Encoding: Under $5K=1 ... $75K+=8, Unknown=0
    last_year_income = first(LAST_YEAR_INCOME),
    # Encoding: PreK-5=1, 6-8=2, 9th=3, 10th=4, 11th=5, 12th=6,
    #           Don't Remember=7, Other=8, Never=9, Unknown=0
    highest_grade    = first(HIGHEST_GRADE_COMPLETED),
    # Encoding: Non-Hispanic=1, Hispanic=2, Decline=3, Unknown=0
    ethnicity        = first(ETHNICITY),
    race_white       = first(WHITE),
    race_black       = first(AFRICAN_AMERICAN),
    race_asian       = first(ASIAN),
    race_native      = first(INDIAN_OR_ALASKAN),
    race_pacific     = first(HAWAIIAN_OR_PACIFIC),
    race_declined    = first(RACE_DECLINE),
    race_none        = first(RACE_NONE),
    birth_year       = first(BIRTH_YEAR),
    
    # --- Geography (analysis only — NOT used in clustering) ---
    c_state = first(C_STATE),
    
    .groups = "drop"
  ) %>%
  mutate(
    across(c(score_math, score_science, score_reasoning, score_social_studies),
           ~ if_else(is.nan(.x), NA_real_, .x)),
    
    # --- Derived demographic labels (analysis only) ---
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
      gender == 1 ~ "Male",      gender == 2 ~ "Female",
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
      highest_grade == 1 ~ "Pre-K to 5th",   highest_grade == 2 ~ "6th-8th",
      highest_grade == 3 ~ "9th Grade",      highest_grade == 4 ~ "10th Grade",
      highest_grade == 5 ~ "11th Grade",     highest_grade == 6 ~ "12th Grade",
      highest_grade == 7 ~ "Don't Remember", highest_grade == 8 ~ "Other",
      highest_grade == 9 ~ "Never Attended", TRUE ~ "Unknown"
    ),
    testing_reason_label = case_when(
      testing_reason == 1 ~ "Work",         testing_reason == 2 ~ "Education",
      testing_reason == 3 ~ "Personal",     testing_reason == 4 ~ "Military",
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

# --- Data quality filter ---
# Records with too many missing fields cluster together based on shared
# missingness rather than shared behavior, producing uninterpretable
# artifact clusters.
#
# Two-stage filter:
#
# Stage 1 — General completeness check
#   Score each candidate by the proportion of key fields that are present.
#   Several demographic fields use 0 as a sentinel for "Unknown" rather than
#   NA, so we convert those to NA before scoring. Candidates below
#   COMPLETENESS_THRESHOLD are removed.
#
# Stage 2 — Demographic completeness check
#   Stage 1 alone is insufficient because demographic fields are only 7 of
#   26 checked fields. A record with all clustering fields populated but all
#   demographic fields blank still scores ~73% and passes Stage 1.
#   Stage 2 explicitly removes any candidate where ALL of the following are
#   true simultaneously: gender unknown, race unknown, and ethnicity unknown.
#   This directly targets the observed artifact pattern (Cluster 4 had ~96%
#   gender=0, ~2% race recorded, ~96% ethnicity=0) without being broad
#   enough to accidentally remove real candidates with partial demographics.
#   A candidate who is missing one demographic field is kept; one who has
#   no demographic identity recorded at all is removed.

# Stage 1: convert sentinel 0s to NA for demographic fields
candidates <- candidates %>%
  mutate(
    gender_check    = na_if(gender,           0L),
    income_check    = na_if(last_year_income, 0L),
    grade_check     = na_if(highest_grade,    0L),
    ethnicity_check = na_if(ethnicity,        0L)
  )

clustering_check_cols <- c(
  "avg_score", "pass_rate", "college_ready_rate", "avg_retakes",
  "credential_earned", "pct_online", "used_ged_ready", "studied_for_ged",
  "has_prep_center", "study_adult_ed_class", "study_books",
  "study_online_video", "score_math", "score_science",
  "score_reasoning", "score_social_studies",
  "testing_reason", "school_incomplete_reason", "enrollment_status",
  "gender_check", "income_check", "grade_check", "ethnicity_check",
  "race_black", "race_white", "birth_year"
)

candidates <- candidates %>%
  mutate(
    completeness = rowMeans(!is.na(select(., all_of(clustering_check_cols))))
  )

n_before   <- nrow(candidates)
candidates <- candidates %>% filter(completeness >= COMPLETENESS_THRESHOLD)
n_stage1   <- n_before - nrow(candidates)

# Stage 2: remove records with no demographic identity at all
# A record is flagged if gender is unknown AND all race fields are 0 or NA
# AND ethnicity is unknown. This is the precise signature of the artifact
# cluster identified in diagnostics.
no_race <- (
  (is.na(candidates$race_black)  | candidates$race_black  == 0) &
    (is.na(candidates$race_white)  | candidates$race_white  == 0) &
    (is.na(candidates$race_asian)  | candidates$race_asian  == 0) &
    (is.na(candidates$race_native) | candidates$race_native == 0) &
    (is.na(candidates$race_pacific)| candidates$race_pacific== 0)
)
no_gender    <- is.na(candidates$gender_check)
no_ethnicity <- is.na(candidates$ethnicity_check)

n_before2  <- nrow(candidates)
candidates <- candidates %>%
  filter(!(no_gender & no_race & no_ethnicity))
n_stage2   <- n_before2 - nrow(candidates)

n_removed  <- n_stage1 + n_stage2

cat(sprintf(
  "Completeness filter — Stage 1 (>= %.0f%% fields): %d removed\n",
  COMPLETENESS_THRESHOLD * 100, n_stage1
))
cat(sprintf(
  "Completeness filter — Stage 2 (no demographic identity): %d removed\n",
  n_stage2
))
cat(sprintf(
  "Total removed: %d  |  Candidates retained: %d\n",
  n_removed, nrow(candidates)
))

# ── SECTION 3: FEATURE SELECTION ─────────────────────────────────────────────
#
# Clustering is anchored on performance outcomes. Study behavior features
# (studied_for_ged, study_adult_ed_class, study_books, study_online_video)
# are intentionally excluded from the clustering feature set.
#
# Rationale: in the previous run those four binary flags dominated the
# distance matrix, splitting candidates almost entirely into "reported
# studying vs. did not report studying" groups. The resulting clusters had
# only a 4-point score spread across all four groups — far too narrow to
# be useful for performance disparity analysis. The research question is
# about performance gaps, not study behavior differences.
#
# Study behavior features are retained in the candidates dataframe and
# appear in the Table 3 post-hoc summary alongside demographics, where
# they describe each cluster rather than define it.
#
# Nominal preparation features (testing reason, school incomplete reason,
# enrollment status) are also excluded — they capture motivation and
# background context, not performance outcomes, and their inclusion risks
# the same over-splitting problem.
#
# Step 1 — Variance filtering
#   Features with low variance carry little discriminating power.
#   Numeric: coefficient of variation (SD / mean).
#   avg_score is always kept regardless of variance.
#
# Step 2 — Correlation filtering (numeric features only)
#   Pairs with |r| > COR_THRESHOLD are redundant. The lower-variance
#   feature is dropped. avg_score is never dropped.

# The only protected feature for clustering purposes
protected_clustering <- "avg_score"

# Performance and delivery features only — study behavior excluded
numeric_cols <- c(
  "avg_score", "pass_rate", "college_ready_rate", "avg_retakes",
  "credential_earned", "pct_online", "used_ged_ready", "has_prep_center",
  "score_math", "score_science", "score_reasoning", "score_social_studies"
)

# No nominal features — all nominal candidates capture motivation/context,
# not performance outcomes
nominal_cols <- character(0)

# --- Step 1: Variance filtering ---

numeric_var <- tibble(feature = numeric_cols) %>%
  mutate(
    variance  = map_dbl(feature, ~ {
      x <- candidates[[.x]]; x <- x[!is.na(x)]
      if (mean(x) == 0) return(0)
      sd(x) / abs(mean(x))
    }),
    type      = "Numeric",
    protected = feature == protected_clustering,
    retain    = protected | variance >= VAR_THRESHOLD
  )

nominal_var <- tibble(feature = nominal_cols) %>%
  mutate(
    variance  = map_dbl(feature, ~ {
      x <- candidates[[.x]]
      1 - max(table(x) / length(x))
    }),
    type      = "Nominal",
    protected = FALSE,
    retain    = variance >= VAR_THRESHOLD
  )

variance_report <- bind_rows(numeric_var, nominal_var) %>%
  arrange(desc(variance)) %>%
  mutate(
    variance = round(variance, 4),
    Status   = case_when(
      protected & variance < VAR_THRESHOLD ~ "Keep (protected — avg_score)",
      retain                               ~ "Keep",
      TRUE                                 ~ "Drop"
    )
  )

cat("\n--- STEP 1: VARIANCE FILTERING ---\n")
cat(sprintf(
  "Threshold: %.2f  |  avg_score always kept  |  Demographics excluded from clustering\n\n",
  VAR_THRESHOLD
))
print(kable(
  variance_report %>% select(feature, type, variance, Status),
  col.names = c("Feature", "Type", "Variance", "Status"),
  format = "simple"
))

retained_numeric <- numeric_var %>% filter(retain) %>% pull(feature)
retained_nominal <- nominal_var %>% filter(retain) %>% pull(feature)
var_dropped      <- variance_report %>% filter(!retain) %>% pull(feature)

cat(sprintf("\nRetained after variance filter: %d numeric, %d nominal\n",
            length(retained_numeric), length(retained_nominal)))
if (length(var_dropped) > 0)
  cat("Dropped (variance):", paste(var_dropped, collapse = ", "), "\n")

# --- Step 2: Correlation filtering (numeric only) ---

cat(sprintf("\n--- STEP 2: CORRELATION FILTERING (threshold = %.2f) ---\n",
            COR_THRESHOLD))

numeric_for_cor <- candidates %>%
  select(all_of(retained_numeric)) %>%
  select(where(is.numeric))

cor_matrix <- cor(numeric_for_cor, use = "pairwise.complete.obs")

# Run drop decisions first so Status column in the report reflects outcomes
high_cor_pairs <- which(
  abs(cor_matrix) > COR_THRESHOLD & upper.tri(cor_matrix),
  arr.ind = TRUE
)

cor_dropped <- character(0)

if (nrow(high_cor_pairs) > 0) {
  for (i in seq_len(nrow(high_cor_pairs))) {
    feat_a <- rownames(cor_matrix)[high_cor_pairs[i, 1]]
    feat_b <- colnames(cor_matrix)[high_cor_pairs[i, 2]]
    
    if (feat_a %in% cor_dropped | feat_b %in% cor_dropped) next
    
    a_protected <- feat_a == protected_clustering
    b_protected <- feat_b == protected_clustering
    
    if (a_protected & b_protected) next
    
    var_a     <- numeric_var$variance[numeric_var$feature == feat_a]
    var_b     <- numeric_var$variance[numeric_var$feature == feat_b]
    drop_feat <- if (!b_protected & (a_protected | var_a >= var_b)) feat_b else feat_a
    cor_dropped <- c(cor_dropped, drop_feat)
  }
}

# Build full pairwise report with Status column populated
cor_report <- as_tibble(
  which(upper.tri(cor_matrix), arr.ind = TRUE),
  .name_repair = "minimal"
) %>%
  rename(row = 1, col = 2) %>%
  mutate(
    Feature_A = rownames(cor_matrix)[row],
    Feature_B = colnames(cor_matrix)[col],
    r         = round(cor_matrix[cbind(row, col)], 3),
    `|r|`     = round(abs(r), 3),
    Status    = case_when(
      `|r|` <= COR_THRESHOLD                                        ~ "Keep",
      Feature_A == protected_clustering &
        Feature_B == protected_clustering                           ~ "Keep",
      Feature_A %in% cor_dropped                                    ~ paste("Drop", Feature_A),
      Feature_B %in% cor_dropped                                    ~ paste("Drop", Feature_B),
      TRUE                                                           ~ "Keep"
    )
  ) %>%
  arrange(desc(`|r|`)) %>%
  select(Feature_A, Feature_B, r, `|r|`, Status)

cat("\nFull pairwise correlation report (sorted by |r|, descending):\n\n")
print(kable(cor_report,
            col.names = c("Feature A", "Feature B", "r", "|r|", "Status"),
            format = "simple"))

retained_numeric <- setdiff(retained_numeric, cor_dropped)

cat(sprintf("\nDropped (correlation) : %s\n",
            if (length(cor_dropped) > 0) paste(cor_dropped, collapse = ", ") else "none"))
cat(sprintf("Final feature set     : %d numeric, %d nominal\n",
            length(retained_numeric), length(retained_nominal)))

# ── SECTION 4: BUILD THE CLUSTERING MATRIX ────────────────────────────────────
# Numeric features are split into two groups before normalization:
#
#   Continuous  → z-score normalized (mean = 0, SD = 1).
#   Binary flags → kept as raw 0/1. daisy() requires exact integer 0/1 for
#                  asymmetric binary features — z-scoring would break this.
#
# Subject score NAs (candidate never sat that subject) are left as NA.
# Gower distance handles them natively by excluding that feature from the
# pairwise distance for that candidate rather than imputing a value.
#
# Demographic features are deliberately NOT included here.

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
  mutate(across(
    all_of(continuous_cols),
    ~ { v <- .x[!is.na(.x)]; (.x - mean(v)) / sd(v) }
  )) %>%
  mutate(across(
    all_of(setdiff(continuous_cols, subject_score_cols)),
    ~ replace_na(.x, 0)
  )) %>%
  mutate(across(all_of(binary_cols),     as.integer)) %>%
  mutate(across(all_of(retained_nominal), as.factor))

cat("\nClustering matrix:", nrow(cluster_df), "candidates x",
    ncol(cluster_df) - 1, "features (demographics excluded)\n")

# ── SECTION 5: GOWER DISTANCE MATRIX ─────────────────────────────────────────
# Gower distance handles mixed feature types (continuous + binary + nominal)
# by computing a type-appropriate partial dissimilarity per feature and
# averaging across all features. This is standard for mixed-type data.
#
# The 'asymm' flag marks binary features where joint-absence (both candidates
# scoring 0) should NOT count as similarity — appropriate for rare
# behavioral flags where 0 simply means the behavior did not occur.

cat("\nComputing Gower distance matrix...\n")

gower_dist <- daisy(
  cluster_df %>% select(-CANDIDATE_ID),
  metric = "gower",
  type   = list(asymm = binary_cols)
)

cat("Distance matrix complete.\n")

# ── SECTION 6: DIANA CLUSTERING + SILHOUETTE ANALYSIS ────────────────────────
# DIANA (Divisive ANAlysis) is a top-down algorithm. It begins with all
# candidates in one group, then repeatedly finds the most heterogeneous
# group and splits it until every candidate is its own group.
#
# The Divisive Coefficient (DC) summarizes overall clustering strength:
#   DC > 0.70 = meaningful structure; DC close to 1.0 = strong separation.
#
# STEP 1: Run the full script once to see the silhouette plot.
# STEP 2: Set K below based on the plot, then re-run from here downward.

K <- 5  # <-- SET THIS after reviewing the silhouette plot. Re-run from here.

cat("\nRunning DIANA...\n")
diana_model <- diana(gower_dist, diss = TRUE)
cat(sprintf("Divisive Coefficient: %.4f\n", diana_model$dc))
cat("DC > 0.70 indicates meaningful cluster structure.\n")

hc <- as.hclust(diana_model)

# --- Silhouette analysis ---
cat("\nComputing silhouette widths for k = 2 through 8...\n")

sil_results <- map_dfr(2:8, function(k) {
  labels <- cutree(hc, k = k)
  sil    <- silhouette(labels, gower_dist)
  tibble(k = k, avg_silhouette = round(mean(sil[, 3]), 4))
})

stat_opt <- sil_results$k[which.max(sil_results$avg_silhouette)]

sil_results %>%
  mutate(Note = if_else(k == stat_opt, "<-- statistical optimum", "")) %>%
  kable(format = "simple", col.names = c("k", "Avg Silhouette", "")) %>%
  print()

cat(sprintf("\nStatistical optimum: k = %d  |  Currently selected: k = %d\n",
            stat_opt, K))

# --- Silhouette plot ---
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
    
    # Selected K — red dot (only shown when different from stat_opt)
    { if (K != stat_opt) list(
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
      annotate("rect",
               xmin = min(stat_opt, K) - 0.3, xmax = max(stat_opt, K) + 0.3,
               ymin = -Inf, ymax = Inf,
               fill = "#FEE8C8", alpha = 0.35)
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
      x       = "Number of Clusters (k)",
      y       = "Average Silhouette Width",
      caption = "Tip: if k = 2 feels too coarse, look for the next local peak"
    ) +
    theme_minimal(base_size = 12) +
    theme(
      plot.title    = element_text(face = "bold"),
      plot.subtitle = element_text(color = "grey40", size = 9.5),
      plot.caption  = element_text(color = "grey50", size = 8.5, face = "italic")
    )
)

# --- Dendrogram ---
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
par(mar = c(5.1, 4.1, 4.1, 2.1))

# ── SECTION 7: ASSIGN CLUSTERS AND NAME THEM ──────────────────────────────────
# Each cluster gets a short two-part name:
#   Part 1 — Performance tier (ranked by average score, 1 = highest)
#   Part 2 — The most distinctive preparation or delivery behavior for that
#             cluster, identified by the largest absolute z-score relative
#             to the sample mean across clusters.
#
# Note: because demographics are not in the clustering model, the trait
# descriptor is drawn only from performance and behavioral features.
# Demographic patterns will be revealed in Section 8 as a post-hoc finding.

candidates <- candidates %>%
  mutate(cluster = cutree(hc, k = K))

# Profile is built from clustering features only.
# Study behavior columns (pct_studied, pct_adult_ed, pct_books,
# pct_online_video) are deliberately excluded — they were removed from
# the clustering model and must not influence cluster naming either.
# Including them here would cause the naming logic to describe clusters
# by post-hoc observations rather than the features that actually formed
# the groups, implying a causal link that doesn't exist.
profile <- candidates %>%
  group_by(cluster) %>%
  summarise(
    n               = n(),
    avg_score       = round(mean(avg_score,        na.rm = TRUE), 1),
    pass_rate       = round(mean(pass_rate,        na.rm = TRUE), 3),
    college_ready   = round(mean(college_ready_rate, na.rm = TRUE), 3),
    credential_pct  = round(mean(credential_earned, na.rm = TRUE), 3),
    avg_retakes     = round(mean(avg_retakes,      na.rm = TRUE), 2),
    pct_online      = round(mean(pct_online,       na.rm = TRUE), 3),
    pct_ged_ready   = round(mean(used_ged_ready,   na.rm = TRUE), 3),
    pct_prep_center = round(mean(has_prep_center,  na.rm = TRUE), 3),
    .groups = "drop"
  ) %>%
  arrange(desc(avg_score)) %>%
  mutate(perf_rank = row_number())

# Performance tier names — one per rank up to K
all_tier_names <- c(
  "High Achievers",          # rank 1: best scores
  "Strong Performers",       # rank 2
  "Solid Performers",        # rank 3
  "Developing Learners",     # rank 4
  "Below Average Learners",  # rank 5
  "Struggling Learners",     # rank 6
  "At-Risk Candidates",      # rank 7
  "Critical Needs"           # rank 8: lowest scores
)
tier_names <- all_tier_names[1:K]

# Trait labels restricted to features that were actually in the clustering
# model. Study behaviors (studied_for_ged, adult ed, books, online video)
# are excluded — they are post-hoc observations and must not drive naming.
# Only pct_online, pct_ged_ready, pct_prep_center, and avg_retakes
# were clustering inputs alongside the performance outcome features.
trait_labels_pos <- c(
  pct_online      = "Online-Heavy",
  pct_ged_ready   = "GED Ready Users",
  pct_prep_center = "Prep Supported",
  avg_retakes     = "High Retakers"
)
trait_labels_neg <- c(
  pct_online      = "In-Person Testers",
  pct_ged_ready   = "No GED Ready",
  pct_prep_center = "No Prep Center",
  avg_retakes     = "First-Attempt Passers"
)

# Sample-wide averages as baseline for z-score comparison
# Only includes the four clustering features eligible for naming
benchmarks <- list(
  pct_online      = mean(candidates$pct_online,      na.rm = TRUE),
  pct_ged_ready   = mean(candidates$used_ged_ready,  na.rm = TRUE),
  pct_prep_center = mean(candidates$has_prep_center, na.rm = TRUE),
  avg_retakes     = mean(candidates$avg_retakes,     na.rm = TRUE)
)

cluster_names <- profile %>%
  mutate(
    tier  = tier_names[perf_rank],
    trait = map_chr(seq_len(n()), function(i) {
      row <- profile[i, ]
      z_scores <- map_dbl(names(trait_labels_pos), function(feat) {
        val  <- as.numeric(row[[feat]])
        avg  <- benchmarks[[feat]]
        sdev <- sd(profile[[feat]], na.rm = TRUE)
        if (is.na(sdev) | sdev == 0) return(0)
        (val - avg) / sdev
      })
      names(z_scores) <- names(trait_labels_pos)
      
      # Pick the feature with the largest absolute z-score
      best_feat <- names(which.max(abs(z_scores)))
      
      # Choose the positive or negative label based on the direction of the z-score
      if (z_scores[best_feat] >= 0) {
        trait_labels_pos[best_feat]
      } else {
        trait_labels_neg[best_feat]
      }
    }),
    cluster_name = paste0(tier, " — ", trait)
  ) %>%
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
# Tables 1–2 cover the features used in clustering (performance outcomes).
# Tables 3–4 are post-hoc profiles — these features did not influence the
# clusters, so any patterns found here are genuine discoveries:
#   Table 3 — Preparation behaviors (study methods, GED Ready, prep center)
#   Table 4 — Demographic composition (race, gender, language, geography)

cat("\n=== CLUSTER SUMMARY ===\n")

pct  <- function(x) percent(mean(x, na.rm = TRUE), 0.1)
avg  <- function(x) round(mean(x, na.rm = TRUE), 1)
avg2 <- function(x) round(mean(x, na.rm = TRUE), 2)

base_profile <- candidates %>%
  group_by(Cluster = cluster, Name = cluster_name) %>%
  summarise(N = n(), .groups = "drop") %>%
  arrange(Cluster)

# --- Table 1: Performance ---
cat("\n--- Performance (clustering features) ---\n")
candidates %>%
  group_by(Cluster = cluster) %>%
  summarise(
    `Avg Score`         = avg(avg_score),
    `Pass Rate`         = pct(pass_rate),
    `College Ready`     = pct(college_ready_rate),
    `Credential Earned` = pct(credential_earned),
    `Total Attempts`    = avg2(total_attempts),
    `Avg Retakes`       = avg2(avg_retakes),
    .groups = "drop"
  ) %>%
  left_join(base_profile %>% select(Cluster, Name, N), by = "Cluster") %>%
  select(Cluster, Name, N, everything()) %>%
  arrange(Cluster) %>%
  kable(format = "simple") %>%
  print()

# --- Table 2: Subject Scores ---
cat("\n--- Subject Scores (clustering features | passing threshold = 145) ---\n")
candidates %>%
  group_by(Cluster = cluster) %>%
  summarise(
    `Math`           = avg(score_math),
    `Science`        = avg(score_science),
    `Reasoning`      = avg(score_reasoning),
    `Social Studies` = avg(score_social_studies),
    .groups = "drop"
  ) %>%
  left_join(base_profile %>% select(Cluster, Name), by = "Cluster") %>%
  select(Cluster, Name, everything()) %>%
  arrange(Cluster) %>%
  kable(format = "simple") %>%
  print()

# --- Table 3: Preparation Behaviors ---
cat("\n--- Preparation Behaviors (post-hoc — not used in clustering) ---\n")
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

# --- Table 4: Demographic Profile (post-hoc — NOT used in clustering) ---
cat("\n--- Demographic Profile (post-hoc observation — not used in clustering) ---\n")
cat("    These patterns emerged from the data; they were not inputs to the model.\n\n")
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
  "\nDIANA complete | DC = %.4f | k = %d | Clustering features = %d\n",
  diana_model$dc, K,
  length(retained_numeric) + length(retained_nominal)
))
cat("Demographics are post-hoc only and were not used in clustering.\n")